import pytest
from pymongo import MongoClient
from fastapi.testclient import TestClient
from main import app
from unittest.mock import patch

@pytest.fixture(scope="module")
def client():
    return TestClient(app)

@pytest.fixture(scope="module")
def mongo_db():
    # Connexion à MongoDB dans l'environnement Docker
    client = MongoClient("mongodb://mongodb:27017")
    db = client["test_db"]
    yield db
    # Nettoyage après les tests
    client.drop_database("test_db")
    client.close()

@pytest.fixture
def collection(mongo_db):
    collection = mongo_db["items"]
    collection.delete_many({})  # Nettoyer la collection avant chaque test
    return collection

@pytest.fixture
def mock_yolo_detector(monkeypatch):
    # Simuler le détecteur YOLOv5
    def mock_detect(file_path):
        return [{"name": "wallet", "confidence": 0.9}]
    monkeypatch.setattr("main.YOLOv5Detector.detect", mock_detect)

@pytest.fixture
def mock_email_utils(monkeypatch):
    # Simuler l'envoi d'email et la validation
    monkeypatch.setattr("main.validate_email", lambda x: True)
    monkeypatch.setattr("main.send_match_email", lambda to_email, item_description, match_description, similarity: None)