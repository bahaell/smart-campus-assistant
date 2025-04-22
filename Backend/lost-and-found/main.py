import uuid
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from image_recognition import YOLOv5Detector
from text_matching import TextMatcher
from pymongo import MongoClient
from datetime import datetime
from enum import Enum
import os
import shutil
import numpy as np
import uvicorn

app = FastAPI(title="Lost and Found API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200", "http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files from the 'data' directory
app.mount("/data", StaticFiles(directory="data"), name="data")

# MongoDB client
client = MongoClient("mongodb://mongodb:27017/")
db = client["lost_and_found"]
collection = db["items"]

# Initialize models
detector = YOLOv5Detector(model_path='yolov5s.pt')
matcher = TextMatcher()

# Pydantic model for item matching request
class Item(BaseModel):
    description: str

# Enum for item type validation
class ItemType(str, Enum):
    LOST = "lost"
    FOUND = "found"

@app.post("/upload")
async def upload_item(
    type: ItemType = Form(...),
    description: str = Form(...),
    location: str = Form(None),
    contactInfo: str = Form(None),
    file: UploadFile = File(None)
):
    """
    Upload an item with a description, type, location, contact info, and optional image.
    Args:
        type (ItemType): 'lost' or 'found'.
        description (str): Text description of the item.
        location (str): Location where the item was lost or found.
        contactInfo (str): Contact information for the user.
        file (UploadFile): Optional image file of the item.
    Returns:
        dict: Item ID and detected objects.
    """
    # Save uploaded image if provided with a unique filename
    image_path = None
    detections = []
    if file:
        # Generate a unique filename
        filename = f"{uuid.uuid4()}_{file.filename}"
        file_path = f"data/{filename}"
        os.makedirs('data', exist_ok=True)
        with open(file_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
        # Set proper file permissions
        os.chmod(file_path, 0o644)
        image_path = file_path
        # Detect objects in image with error handling
        try:
            detections = detector.detect(file_path)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to process image: {str(e)}")

    # Compute embedding for description
    embedding = matcher.model.encode(description, convert_to_tensor=False).tolist()

    # Store item in MongoDB
    item = {
        "type": type.value,
        "description": description,
        "location": location,
        "contactInfo": contactInfo,
        "image_path": image_path,
        "detections": detections,
        "embedding": embedding,
        "timestamp": datetime.utcnow().isoformat(),
        "matches": []
    }
    result = collection.insert_one(item)

    # Find matches for the new item
    matches = await match_item(Item(description=description))
    if matches["matches"]:
        item["matches"] = matches["matches"]
        collection.update_one({"_id": result.inserted_id}, {"$set": {"matches": matches["matches"]}})
        # Update matching items
        for match in matches["matches"]:
            collection.update_one(
                {"_id": match["id"]},
                {"$push": {"matches": {"id": str(result.inserted_id), "description": description, "similarity": match["similarity"]}}}
            )

    return {"id": str(result.inserted_id), "detections": detections}

@app.get("/items")
async def get_items():
    """
    Retrieve all items from the database.
    Returns:
        list: List of all items with formatted fields.
    """
    items = collection.find()
    return [{
        "id": str(item["_id"]),
        "type": item["type"],
        "description": item["description"],
        "location": item.get("location"),
        "contactInfo": item.get("contactInfo"),
        "image_path": item.get("image_path"),
        "detections": item.get("detections", []),
        "timestamp": item["timestamp"],
        "matches": item.get("matches", [])
    } for item in items]

@app.post("/match")
async def match_item(item: Item):
    """
    Match an item description against stored items using precomputed embeddings.
    Args:
        item (Item): Item with description to match.
    Returns:
        dict: List of matching items with similarity scores.
    """
    # Compute embedding for the input description
    query_embedding = matcher.model.encode(item.description, convert_to_tensor=False)

    # Find similar items
    items = collection.find()
    matches = []

    for db_item in items:
        if "embedding" in db_item:
            # Compute cosine similarity using precomputed embeddings
            db_embedding = np.array(db_item["embedding"])
            sim = np.dot(query_embedding, db_embedding) / (np.linalg.norm(query_embedding) * np.linalg.norm(db_embedding))
            if sim > 0.7:  # Threshold for matching
                matches.append({
                    "id": str(db_item["_id"]),
                    "description": db_item["description"],
                    "similarity": float(sim)
                })

    return {"matches": matches}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8002)