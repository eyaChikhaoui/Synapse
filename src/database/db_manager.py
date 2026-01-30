import os
import logging
import qdrant_client  # Import the package to check version
from typing import List, Dict, Any
from qdrant_client import QdrantClient

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("VectorDB")

class VectorDB:
    def __init__(self, host: str = "localhost", port: int = 6333):
        self.default_collection = "synapse_v1"
        self.client = None

        # --- DIAGNOSTIC LOGGING ---
        try:
            version = qdrant_client.__version__
            logger.info(f"📦 INSTALLED QDRANT CLIENT VERSION: {version}")
        except:
            logger.info("📦 INSTALLED QDRANT CLIENT VERSION: Unknown (Too old to report version)")

        try:
            self.client = QdrantClient(host=host, port=port)
            
            # --- SMOKING GUN CHECK ---
            # We list exactly what methods exist on the client object
            client_methods = [m for m in dir(self.client) if not m.startswith("_")]
            has_search = "search" in client_methods
            
            logger.info(f"✅ Connected to Qdrant at {host}:{port}")
            logger.info(f"🔍 Client has 'search' method? {'✅ YES' if has_search else '❌ NO'}")
            
            if not has_search:
                logger.critical("🚨 CRITICAL API MISMATCH: Your 'QdrantClient' is missing the 'search' method.")
                logger.critical(f"👉 Available methods similar to 'search': {[m for m in client_methods if 'search' in m]}")
                
        except Exception as e:
            logger.critical(f"⚠️ Initialization Error: {e}")

    def search_similar(self, vector: List[float], collection: str = None, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Searches for similar vectors in Qdrant.
        UPDATED: Now requests 'with_vectors=True' to enable Real-Time PCA/SVD.
        """
        if not self.client:
            return [{"error": "Database not initialized"}]

        target_collection = collection if collection else self.default_collection

        # Ensure vector is list
        if hasattr(vector, 'tolist'):
            vector = vector.tolist()

        try:
            logger.info(f"🚀 Attempting search on '{target_collection}'...")

            # --- ADAPTIVE SEARCH CALL ---
            # If 'search' exists, use it (v1.x). If not, try legacy methods.
            if hasattr(self.client, "search"):
                search_result = self.client.search(
                    collection_name=target_collection,
                    query_vector=vector,
                    limit=top_k,
                    with_vectors=True # <--- CRITICAL UPDATE FOR REAL MATH
                )
            else:
                # FALLBACK FOR OLD VERSIONS (v0.x)
                logger.warning("⚠️ Using Legacy 'search_points' API (Old Client Detected)")
                search_result = self.client.search(
                    collection_name=target_collection,
                    query_vector=vector,
                    limit=top_k,
                    with_vectors=True # <--- CRITICAL UPDATE FOR REAL MATH
                )

            # Process Results (Works for both object and dict responses)
            results = []
            for hit in search_result:
                # Handle v1.x objects vs v0.x dicts
                hit_id = hit.id if hasattr(hit, 'id') else hit.get('id')
                hit_score = hit.score if hasattr(hit, 'score') else hit.get('score')
                hit_payload = hit.payload if hasattr(hit, 'payload') else hit.get('payload', {})
                hit_vector = hit.vector if hasattr(hit, 'vector') else hit.get('vector', []) # <--- CAPTURE VECTOR
                
                results.append({
                    "id": hit_id,
                    "score": hit_score,
                    "metadata": hit_payload,
                    "vector": hit_vector # <--- PASS VECTOR UPSTREAM
                })
            
            logger.info(f"✅ Found {len(results)} matches (Vectors Included).")
            return results
            
        except AttributeError as e:
            logger.error(f"❌ API Attribute Error: {e}")
            logger.error("💡 FIX: You MUST run 'pip install qdrant-client==1.7.0' in the CORRECT terminal.")
            return [{"error": f"Client Version Mismatch: {e}"}]
        except Exception as e:
            logger.error(f"❌ General Search Failed: {e}")
            return [{"error": str(e)}]

if __name__ == "__main__":
    db = VectorDB()