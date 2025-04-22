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
from email_utils import send_match_email

app = FastAPI(title="Lost and Found API")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200", "http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files
app.mount("/data", StaticFiles(directory="data"), name="data")

# MongoDB
client = MongoClient("mongodb://mongodb:27017/")
db = client["lost_and_found"]
collection = db["items"]

# Models
detector = YOLOv5Detector(model_path='yolov5s.pt')
matcher = TextMatcher()

class Item(BaseModel):
    description: str

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
    image_path = None
    detections = []
    
    if file:
        filename = f"{uuid.uuid4()}_{file.filename}"
        file_path = f"data/{filename}"
        os.makedirs('data', exist_ok=True)
        with open(file_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
        os.chmod(file_path, 0o644)
        image_path = file_path

        try:
            detections = detector.detect(file_path)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to process image: {str(e)}")

    embedding = matcher.model.encode(description, convert_to_tensor=False).tolist()

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

    matches = await match_item(Item(description=description))

    if matches["matches"]:
        item["matches"] = matches["matches"]
        collection.update_one({"_id": result.inserted_id}, {"$set": {"matches": matches["matches"]}})

        for match in matches["matches"]:
            matched_item = collection.find_one({"_id": match["id"]})
            if matched_item and matched_item.get("type") == "lost" and matched_item.get("contactInfo"):
                send_match_email(
                    to_email=matched_item["contactInfo"],
                    item_description=matched_item["description"],
                    match_description=description,
                    similarity=match["similarity"]
                )

            collection.update_one(
                {"_id": match["id"]},
                {"$push": {"matches": {"id": str(result.inserted_id), "description": description, "similarity": match["similarity"]}}}
            )

    return {"id": str(result.inserted_id), "detections": detections}

@app.get("/items")
async def get_items():
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
    query_embedding = matcher.model.encode(item.description, convert_to_tensor=False)
    items = collection.find()
    matches = []

    for db_item in items:
        if "embedding" in db_item:
            db_embedding = np.array(db_item["embedding"])
            sim = np.dot(query_embedding, db_embedding) / (np.linalg.norm(query_embedding) * np.linalg.norm(db_embedding))
            if sim > 0.7:
                matches.append({
                    "id": str(db_item["_id"]),
                    "description": db_item["description"],
                    "similarity": float(sim)
                })

    return {"matches": matches}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8002)
