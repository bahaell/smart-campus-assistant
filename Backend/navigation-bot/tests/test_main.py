import sys
import os
# Ajouter le répertoire parent au chemin d'importation
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from fastapi.testclient import TestClient
from main import app, load_faiss_index
from unittest.mock import MagicMock
import numpy as np

# Créer un client de test pour l'API FastAPI
client = TestClient(app)

@pytest.fixture
def mock_faiss_and_locations(monkeypatch):
    # Simuler les données de location et l'index FAISS
    mock_location_data = [
        {
            "title": "Bloc Prepa",
            "location": {
                "lat": 36.8344411,
                "lng": 10.1456052
            }
        }
    ]
    mock_index = MagicMock()
    # Simuler une recherche FAISS qui renvoie un index et une distance
    mock_index.search.return_value = (np.array([[0.1]]), np.array([[0]]))
    
    monkeypatch.setattr("main.load_faiss_index", lambda: (mock_index, mock_location_data))
    return mock_index, mock_location_data

@pytest.mark.asyncio
async def test_ask_endpoint_success(mock_faiss_and_locations):
    # Teste une requête valide
    response = client.post("/ask", json={"query": "Where is Bloc Prepa?"})
    assert response.status_code == 200
    
    response_json = response.json()
    assert response_json["answer"] == "L'emplacement 'Bloc Prepa' se trouve ici :"
    assert response_json["source"]["type"] == "location"
    assert response_json["source"]["title"] == "Bloc Prepa"
    assert response_json["source"]["lat"] == 36.8344411
    assert response_json["source"]["lng"] == 10.1456052
    assert response_json["source"]["distance"] == 0.1

@pytest.mark.asyncio
async def test_ask_endpoint_invalid_request():
    # Teste une requête mal formée (manque le champ "query")
    response = client.post("/ask", json={"invalid_field": "Where is Bloc Prepa?"})
    assert response.status_code == 422  # Erreur de validation (FastAPI)
    assert "query" in response.json()["detail"][0]["loc"]

@pytest.mark.asyncio
async def test_ask_endpoint_empty_query():
    # Teste une requête avec un champ "query" vide
    response = client.post("/ask", json={"query": ""})
    assert response.status_code == 200  # L'API devrait quand même répondre
    assert "answer" in response.json()
    assert "source" in response.json()

@pytest.mark.asyncio
async def test_cors_headers():
    # Teste que les en-têtes CORS sont présents
    response = client.post("/ask", json={"query": "Where is Bloc Prepa?"}, headers={"Origin": "http://frontend:8080"})
    assert response.status_code == 200
    assert "access-control-allow-origin" in response.headers
    assert response.headers["access-control-allow-origin"] == "http://frontend:8080"