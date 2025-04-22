import json
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
import pickle
import os

# Vérifier et créer le répertoire data/ si nécessaire
if not os.path.exists('data'):
    os.makedirs('data')

# Load FAQ data
def load_faq(file_path):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"FAQ file not found at {file_path}")
    with open(file_path, 'r') as f:
        return json.load(f)

# Generate embeddings and store in FAISS
def create_faiss_index(faq_data, output_path='faiss_index.bin'):
    # Initialize SentenceTransformer model (local)
    model = SentenceTransformer('all-MiniLM-L6-v2')
    
    # Extract questions for embedding
    questions = [item['question'] for item in faq_data]
    embeddings = model.encode(questions, convert_to_numpy=True)
    
    # Create FAISS index
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(embeddings)
    
    # Save index and FAQ data
    faiss.write_index(index, output_path)
    with open('faq_data.pkl', 'wb') as f:
        pickle.dump(faq_data, f)
    
    return index

if __name__ == "__main__":
    faq_data = load_faq('data/faq.json')
    create_faiss_index(faq_data)
    print("FAISS index created successfully.")
