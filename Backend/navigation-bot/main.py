from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import faiss
import pickle
import numpy as np
from sentence_transformers import SentenceTransformer

app = FastAPI(title="Navigation Bot API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200", "http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic model for request
class QueryRequest(BaseModel):
    query: str

# Load FAISS index and location data
def load_faiss_index(index_path='faiss_index.bin', location_path='location_data.pkl'):
    with open(location_path, 'rb') as f:
        location_data = pickle.load(f)
    index = faiss.read_index(index_path)
    return index, location_data

# Initialize the model and load the index
model = SentenceTransformer('all-MiniLM-L6-v2')
index, location_data = load_faiss_index()

@app.post("/ask")
async def ask_question(request: QueryRequest):
    """
    Answer a user query by finding the most similar location using FAISS.
    
    Args:
        request (QueryRequest): The user's query in JSON format.
    
    Returns:
        dict: A Google Maps URL and metadata of the matched location.
    """
    # Generate embedding for the query
    query_embedding = model.encode([request.query], convert_to_numpy=True)
    
    # Search in FAISS index
    k = 1  # Number of nearest neighbors to retrieve
    distances, indices = index.search(query_embedding, k)
    
    # Get the most similar location
    matched_index = indices[0][0]
    matched_location = location_data[matched_index]
    
    # Generate Google Maps URL
    lat = matched_location['location']['lat']
    lng = matched_location['location']['lng']
    
    return {
        "answer": f"L'emplacement '{matched_location['title']}' se trouve ici :",
        "source": {
            "type": "location",
            "title": matched_location['title'],
            "lat": lat,
            "lng": lng,
            "distance": float(distances[0][0])
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)