import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from fastapi.testclient import TestClient
from datetime import datetime
from bson.objectid import ObjectId

@pytest.mark.asyncio
async def test_upload_lost_item(client, collection, mock_yolo_detector, mock_email_utils):
    # Teste l'upload d'un élément "lost" avec une image
    form_data = {
        "type": "lost",
        "description": "Lost a black wallet",
        "location": "Bloc Prepa",
        "contactInfo": "john.doe@example.com"
    }
    files = {
        "file": ("test.jpg", b"fake image content", "image/jpeg")
    }

    response = client.post("/upload", data=form_data, files=files)
    assert response.status_code == 200

    response_json = response.json()
    assert "id" in response_json
    assert response_json["detections"] == [{"name": "wallet", "confidence": 0.9}]

    # Vérifier que l'élément est bien dans MongoDB
    item = collection.find_one({"description": "Lost a black wallet"})
    assert item is not None
    assert item["type"] == "lost"
    assert item["description"] == "Lost a black wallet"
    assert item["location"] == "Bloc Prepa"
    assert item["contactInfo"] == "john.doe@example.com"
    assert item["image_path"].startswith("/data/")

@pytest.mark.asyncio
async def test_upload_found_item(client, collection, mock_yolo_detector):
    # Teste l'upload d'un élément "found" sans contactInfo
    form_data = {
        "type": "found",
        "description": "Found a black wallet",
        "location": "Bloc Prepa"
    }
    files = {
        "file": ("test.jpg", b"fake image content", "image/jpeg")
    }

    response = client.post("/upload", data=form_data, files=files)
    assert response.status_code == 200

    # Vérifier que l'élément est bien dans MongoDB
    item = collection.find_one({"description": "Found a black wallet"})
    assert item is not None
    assert item["type"] == "found"

@pytest.mark.asyncio
async def test_upload_invalid_item(client):
    # Teste un upload avec des données invalides (description manquante)
    form_data = {
        "type": "lost",
        "contactInfo": "john.doe@example.com"
    }
    files = {
        "file": ("test.jpg", b"fake image content", "image/jpeg")
    }

    response = client.post("/upload", data=form_data, files=files)
    assert response.status_code == 400
    assert response.json()["detail"] == "Description is required"

@pytest.mark.asyncio
async def test_get_items(client, collection):
    # Insère un élément dans MongoDB
    item = {
        "type": "found",
        "description": "Found a black wallet",
        "location": "Bloc Prepa",
        "contactInfo": None,
        "image_path": "/data/test.jpg",
        "detections": [{"name": "wallet", "confidence": 0.9}],
        "timestamp": datetime.utcnow().isoformat(),
        "matches": []
    }
    inserted_item = collection.insert_one(item)

    # Teste la récupération des éléments
    response = client.get("/items")
    assert response.status_code == 200

    items = response.json()
    assert len(items) == 1
    assert items[0]["id"] == str(inserted_item.inserted_id)
    assert items[0]["description"] == "Found a black wallet"

@pytest.mark.asyncio
async def test_match_item(client, collection):
    # Insère un élément existant dans MongoDB
    item = {
        "type": "lost",
        "description": "Lost a black wallet",
        "detections": [{"name": "wallet", "confidence": 0.9}],
        "timestamp": datetime.utcnow().isoformat(),
        "matches": []
    }
    inserted_item = collection.insert_one(item)

    # Teste le matching avec des détections similaires
    detections = [{"name": "wallet", "confidence": 0.9}]
    response = client.post("/match", json=detections)
    assert response.status_code == 200

    matches = response.json()["matches"]
    assert len(matches) == 1
    assert matches[0]["id"] == str(inserted_item.inserted_id)
    assert matches[0]["description"] == "Lost a black wallet"
    assert matches[0]["similarity"] == 1.0

@pytest.mark.asyncio
async def test_cors_headers(client):
    # Teste que les en-têtes CORS sont présents
    response = client.post("/upload", data={"type": "lost", "description": "Test", "contactInfo": "test@example.com"}, 
                          files={"file": ("test.jpg", b"fake image content", "image/jpeg")},
                          headers={"Origin": "http://frontend:8080"})
    assert response.status_code == 200
    assert "access-control-allow-origin" in response.headers
    assert response.headers["access-control-allow-origin"] == "http://frontend:8080"