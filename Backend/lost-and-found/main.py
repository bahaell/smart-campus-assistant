import uuid
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from image_recognition import YOLOv5Detector
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from datetime import datetime
from enum import Enum
import os
import shutil
import uvicorn
from email_utils import send_match_email, validate_email
from bson.objectid import ObjectId

app = FastAPI(title="Lost and Found API")
app.mount("/data", StaticFiles(directory="data"), name="data")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200", "http://localhost:8080", "http://127.0.0.1:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# MongoDB
MONGO_URI = os.environ.get("MONGO_URI", "mongodb://mongodb:27017/")
try:
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    client.server_info()
    print(f"Successfully connected to MongoDB at {MONGO_URI}")
except (ConnectionFailure, ServerSelectionTimeoutError) as e:
    print(f"Failed to connect to MongoDB at {MONGO_URI}: {e}")
    raise Exception("Cannot connect to MongoDB")

db = client["lost_and_found"]
collection = db["items"]

# YOLOv5 Detector
try:
    detector = YOLOv5Detector(model_path='yolov5su.pt')
    print("Successfully loaded YOLOv5 model")
except Exception as e:
    print(f"Failed to load YOLOv5 model: {e}")
    raise Exception("Cannot load YOLOv5 model")

class Item(BaseModel):
    description: str

class ItemType(str, Enum):
    LOST = "lost"
    FOUND = "found"

def calculate_image_similarity(detections1: list, detections2: list) -> float:
    """Calculate similarity between two sets of YOLOv5 detections."""
    if not detections1 or not detections2:
        print("No detections provided for similarity calculation")
        return 0.0

    try:
        classes1 = {det["name"] for det in detections1 if det.get("confidence", 0) > 0.5}
        classes2 = {det["name"] for det in detections2 if det.get("confidence", 0) > 0.5}
        print(f"Classes detected in first image: {classes1}")
        print(f"Classes detected in second image: {classes2}")
    except KeyError as e:
        print(f"KeyError in calculate_image_similarity: {e}. Expected key 'name' in detections.")
        return 0.0

    if not classes1 or not classes2:
        print("No classes with confidence > 0.5 found in one or both images")
        return 0.0

    intersection = len(classes1.intersection(classes2))
    union = len(classes1.union(classes2))
    similarity = intersection / union if union > 0 else 0.0
    print(f"Similarity score: {similarity}")
    return similarity

@app.post("/upload")
async def upload_item(
    type: ItemType = Form(...),
    description: str = Form(...),
    location: str = Form(None),
    contactInfo: str = Form(None),
    file: UploadFile = File(...)
):
    print(f"Received upload request: type={type}, description={description}, location={location}, contactInfo={contactInfo}")

    if not description:
        raise HTTPException(status_code=400, detail="Description is required")

    if type == ItemType.LOST:
        if not contactInfo:
            raise HTTPException(status_code=400, detail="Contact information is required for lost items")
        if not validate_email(contactInfo):
            raise HTTPException(status_code=400, detail="Invalid contact email address")

    filename = f"{uuid.uuid4()}_{file.filename}"
    file_path = f"data/{filename}"
    print(f"Saving file to {file_path}")
    try:
        os.makedirs('data', exist_ok=True)
        with open(file_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
        os.chmod(file_path, 0o644)
        image_path = file_path
    except Exception as e:
        print(f"Failed to save image: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to save image: {str(e)}")

    try:
        print("Running YOLOv5 detection...")
        detections = detector.detect(file_path)
        print(f"Detections: {detections}")
        if not detections:
            raise HTTPException(status_code=400, detail="No objects detected in the image")
    except Exception as e:
        print(f"Error during detection: {e}")
        raise HTTPException(status_code=400, detail=f"Failed to process image: {str(e)}")

    item = {
        "type": type.value,
        "description": description,
        "location": location,
        "contactInfo": contactInfo,
        "image_path": image_path , 
        "detections": detections,
        "timestamp": datetime.utcnow().isoformat(),
        "matches": []
    }

    print("Inserting item into MongoDB...")
    try:
        result = collection.insert_one(item)
        print(f"Inserted item with ID: {result.inserted_id}")
    except Exception as e:
        print(f"Failed to insert item into MongoDB: {e}")
        raise HTTPException(status_code=500, detail="Failed to save item to database")

    print("Matching item...")
    try:
        matches = await match_item(detections)
        print(f"Matches found: {matches}")
    except Exception as e:
        print(f"Failed to match item: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to match item: {str(e)}")

    if matches["matches"]:
        item["matches"] = matches["matches"]
        print("Updating item with matches...")
        try:
            collection.update_one({"_id": result.inserted_id}, {"$set": {"matches": matches["matches"]}})
        except Exception as e:
            print(f"Failed to update item with matches: {e}")
            raise HTTPException(status_code=500, detail="Failed to update item with matches")

        for match in matches["matches"]:
            try:
                match_id = ObjectId(match["id"])
            except Exception as e:
                print(f"Invalid match ID format: {match['id']}, error: {e}")
                continue

            print(f"Finding matched item with ID: {match_id}")
            try:
                matched_item = collection.find_one({"_id": match_id})
            except Exception as e:
                print(f"Failed to find matched item: {e}")
                continue

            if not matched_item:
                print(f"No matched item found for ID: {match_id}")
                continue

            if (
                matched_item.get("type") == "lost"
                and matched_item.get("contactInfo")
                and validate_email(matched_item["contactInfo"])
            ):
                print(f"Sending email to {matched_item['contactInfo']}...")
                try:
                    send_match_email(
                        to_email=matched_item["contactInfo"],
                        item_description=matched_item["description"],
                        match_description=description,
                        similarity=match["similarity"]
                    )
                except Exception as e:
                    print(f"Failed to send email: {e}")

            print(f"Updating matched item {match_id} with new match...")
            try:
                collection.update_one(
                    {"_id": match_id},
                    {
                        "$push": {
                            "matches": {
                                "id": str(result.inserted_id),
                                "description": description,
                                "similarity": match["similarity"]
                            }
                        }
                    }
                )
            except Exception as e:
                print(f"Failed to update matched item: {e}")

    return {"id": str(result.inserted_id), "detections": detections}

@app.get("/items")
async def get_items():
    try:
        items = collection.find()
        items_list = [
            {
                "id": str(item["_id"]),
                "type": item["type"],
                "description": item["description"],
                "location": item.get("location"),
                "contactInfo": item.get("contactInfo"),
                "image_path": item.get("image_path"),
                "detections": item.get("detections", []),
                "timestamp": item["timestamp"],
                "matches": item.get("matches", [])
            }
            for item in items
        ]
        return items_list
    except Exception as e:
        print(f"Failed to fetch items from MongoDB: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch items from database")

@app.post("/match")
async def match_item(detections: list):
    print(f"Matching detections: {detections}")
    try:
        items = collection.find({"detections": {"$exists": True, "$ne": []}})
    except Exception as e:
        print(f"Failed to query items for matching: {e}")
        raise HTTPException(status_code=500, detail="Failed to query items for matching")

    matches = []
    for db_item in items:
        db_detections = db_item.get("detections", [])
        similarity = calculate_image_similarity(detections, db_detections)
        if similarity > 0.5:
            matches.append({
                "id": str(db_item["_id"]),
                "description": db_item["description"],
                "similarity": similarity
            })

    return {"matches": matches}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8002)