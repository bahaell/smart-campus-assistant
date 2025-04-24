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
    if not detections1 or not detections2:
        return 0.0
    try:
        classes1 = {det["name"] for det in detections1 if det.get("confidence", 0) > 0.5}
        classes2 = {det["name"] for det in detections2 if det.get("confidence", 0) > 0.5}
    except KeyError:
        return 0.0
    if not classes1 or not classes2:
        return 0.0
    intersection = len(classes1.intersection(classes2))
    union = len(classes1.union(classes2))
    return intersection / union if union > 0 else 0.0

@app.post("/upload")
async def upload_item(
    type: ItemType = Form(...),
    description: str = Form(...),
    location: str = Form(None),
    contactInfo: str = Form(None),
    file: UploadFile = File(...)
):
    if not description:
        raise HTTPException(status_code=400, detail="Description is required")
    if type == ItemType.LOST:
        if not contactInfo or not validate_email(contactInfo):
            raise HTTPException(status_code=400, detail="Valid contact email is required for lost items")
    filename = f"{uuid.uuid4()}_{file.filename}"
    file_path = f"data/{filename}"
    os.makedirs('data', exist_ok=True)
    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    os.chmod(file_path, 0o644)
    detections = detector.detect(file_path)
    if not detections:
        raise HTTPException(status_code=400, detail="No objects detected in the image")
    item = {
        "type": type.value,
        "description": description,
        "location": location,
        "contactInfo": contactInfo,
        "image_path": file_path,
        "detections": detections,
        "timestamp": datetime.utcnow().isoformat(),
        "matches": []
    }
    result = collection.insert_one(item)

    # Match only if it's a FOUND item
    if type == ItemType.FOUND:
        matches = await match_item(detections)
        if matches["matches"]:
            item["matches"] = matches["matches"]
            collection.update_one({"_id": result.inserted_id}, {"$set": {"matches": matches["matches"]}})
            for match in matches["matches"]:
                match_id = ObjectId(match["id"])
                matched_item = collection.find_one({"_id": match_id})
                if matched_item and matched_item.get("type") == "lost" and validate_email(matched_item.get("contactInfo", "")):
                    send_match_email(
                        to_email=matched_item["contactInfo"],
                        item_description=matched_item["description"],
                        match_description=description,
                        similarity=match["similarity"],
                        finder_email=contactInfo
                    )
                    collection.update_one(
                        {"_id": match_id},
                        {"$push": {
                            "matches": {
                                "id": str(result.inserted_id),
                                "description": description,
                                "similarity": match["similarity"],
                                "finder_email": contactInfo,
                                "type":matched_item.get("type")
                            }
                        }}
                    )
    return {"id": str(result.inserted_id), "detections": detections}

@app.get("/items")
async def get_items():
    items = collection.find()
    return [
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
        } for item in items
    ]

@app.post("/match")
async def match_item(detections: list):
    candidates = collection.find({"type": "lost", "detections": {"$exists": True, "$ne": []}})
    matches = []
    for db_item in candidates:
        similarity = calculate_image_similarity(detections, db_item.get("detections", []))
        if similarity > 0.5:
            matches.append({
                "id": str(db_item["_id"]),
                "description": db_item["description"],
                "similarity": similarity
            })
    return {"matches": matches}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8002)