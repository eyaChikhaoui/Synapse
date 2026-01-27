import os
import logging
from typing import List, Dict, Any
from qdrant_client import QdrantClient

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("VectorDB")

class VectorDB:
    def __init__(self, host: str = "localhost", port: int = 6333):
        self.collection_name = "synapse_v1"
        self.client = None
        
        try:
            self.client = QdrantClient(host=host, port=port)
            # Quick connectivity check
            self.client.get_collections()
            logger.info(f"✅ Connected to Qdrant at {host}:{port}")
        except Exception as e:
            logger.critical(f"⚠️ Could not connect to Qdrant: {e}")
            logger.critical("   Ensure the Docker container is running: 'docker-compose up -d'")

    def search_similar(self, vector: List[float], top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Performs Cosine Similarity search in the Shared Latent Space.
        """
        if not self.client:
            return [{"error": "Database not initialized"}]

        try:
            # Ensure input is a standard list of floats
            if hasattr(vector, 'tolist'):
                vector = vector.tolist()

            logger.info(f"🔍 Executing Query (Vector Dim: {len(vector)})...")
            
            search_result = self.client.search(
                collection_name=self.collection_name,
                query_vector=vector,
                limit=top_k
            )

            # Process Results into clean JSON
            results = []
            for hit in search_result:
                results.append({
                    "id": getattr(hit, 'id', 'unknown'),
                    "score": getattr(hit, 'score', 0.0),
                    "metadata": getattr(hit, 'payload', {}) 
                })
            
            logger.info(f"✅ Found {len(results)} matches.")
            return results
            
        except Exception as e:
            logger.error(f"❌ Search Failed: {e}")
            return [{"error": f"Search execution failed: {str(e)}"}]

if __name__ == "__main__":
    db = VectorDB()