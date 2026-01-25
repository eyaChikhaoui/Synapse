import os
from typing import List, Dict, Any
from qdrant_client import QdrantClient

class VectorDB:
    def __init__(self, host: str = "localhost", port: int = 6333):
        try:
            # We skip printing the version because it crashes on your machine
            self.client = QdrantClient(host=host, port=port)
            self.collection_name = "synapse_v1"
            
            # Simple connection test
            self.client.get_collections()
            print(f"✅ Connected to Qdrant at {host}:{port}")
        except Exception as e:
            print(f"⚠️ Could not connect to Qdrant: {e}")
            self.client = None

    def search_similar(self, vector: List[float], top_k: int = 3) -> List[Dict[str, Any]]:
        if not self.client:
            return [{"error": "DB not initialized"}]

        try:
            # Ensure vector is a list
            if hasattr(vector, 'tolist'):
                vector = vector.tolist()

            print(f"🔍 Searching... (Dim: {len(vector)})")
            
            # --- ATTEMPT 1: Standard Search ---
            if hasattr(self.client, 'search'):
                search_result = self.client.search(
                    collection_name=self.collection_name,
                    query_vector=vector,
                    limit=top_k
                )
            else:
                # --- ATTEMPT 2: Fallback (Older versions or Sync/Async mixup) ---
                print("⚠️ '.search()' not found. Trying '.query_points()'...")
                search_result = self.client.query_points(
                    collection_name=self.collection_name,
                    query=vector,
                    limit=top_k
                ).points

            # Process Results
            results = []
            for hit in search_result:
                # Handle difference between object types
                payload = getattr(hit, 'payload', {})
                score = getattr(hit, 'score', 0.0)
                doc_id = getattr(hit, 'id', 'unknown')
                
                results.append({
                    "id": doc_id,
                    "score": score,
                    "metadata": payload 
                })
            
            print(f"✅ Found {len(results)} matches.")
            return results
            
        except Exception as e:
            print(f"❌ Database Error: {e}")
            # DEBUGGING: Print what IS available
            print(f"ℹ️ Client methods available: {[m for m in dir(self.client) if not m.startswith('_')]}")
            return []

if __name__ == "__main__":
    db = VectorDB()