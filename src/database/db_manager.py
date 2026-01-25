import os
from typing import List, Dict, Any
from qdrant_client import QdrantClient
from qdrant_client.http import models

class VectorDB:
    def __init__(self, host: str = "localhost", port: int = 6333):
        """
        Connects to the Qdrant Docker container.
        """
        self.client = QdrantClient(host=host, port=port)
        self.collection_name = "synapse_v1"
        print(f"✅ Connected to Qdrant at {host}:{port}")

    def search_similar(self, vector: List[float], top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Real Semantic Search:
        1. Takes the input vector (DNA embedding).
        2. Asks Qdrant for the 'closest' vectors in the multi-dimensional space.
        3. Returns the Metadata (Payload) of those vectors.
        """
        try:
            search_result = self.client.search(
                collection_name=self.collection_name,
                query_vector=vector,
                limit=top_k
            )
            
            # Convert Qdrant objects to simple dictionaries for the Frontend
            results = []
            for hit in search_result:
                results.append({
                    "id": hit.id,
                    "score": hit.score,
                    # The 'payload' contains the real protein name and info
                    "metadata": hit.payload 
                })
            
            return results
            
        except Exception as e:
            print(f"❌ Database Error: {e}")
            return []

# Quick Test (Only works if Docker is running and data is loaded)
if __name__ == "__main__":
    db = VectorDB()
    # Dummy vector for testing connection
    print(db.search_similar([0.1] * 768))