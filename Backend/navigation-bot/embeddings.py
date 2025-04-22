import json
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
import pickle
import os

# Vérifier et créer le répertoire data/ si nécessaire
if not os.path.exists('data'):
    os.makedirs('data')

# Load location data
def load_locations(file_path):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Location file not found at {file_path}")
    with open(file_path, 'r') as f:
        return json.load(f)

# Generate embeddings and store in FAISS
def create_faiss_index(location_data, output_path='faiss_index.bin'):
    # Initialize SentenceTransformer model (local)
    model = SentenceTransformer('all-MiniLM-L6-v2')
    
    # Extract location titles for embedding
    titles = [item['title'] for item in location_data]
    embeddings = model.encode(titles, convert_to_numpy=True)
    
    # Create FAISS index
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(embeddings)
    
    # Save index and location data
    faiss.write_index(index, output_path)
    with open('location_data.pkl', 'wb') as f:
        pickle.dump(location_data, f)
    
    return index

if __name__ == "__main__":
    # Charger les données de localisation et créer l'index FAISS
    location_data = load_locations('data/location.json')
    create_faiss_index(location_data)
    print("FAISS index created successfully for locations.")