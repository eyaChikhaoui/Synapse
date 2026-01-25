import numpy as np
from qdrant_client import QdrantClient
from qdrant_client.http import models

# --- CONFIGURATION (MATCHING PERSON 1) ---
COLLECTION_NAME = "synapse_v1"
VECTOR_SIZE = 768  # <--- CRITICAL UPDATE: Matches P1's Encoders 
QDRANT_HOST = "localhost"
QDRANT_PORT = 6333

def initialize_database():
    client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)

    # 1. Recreate Collection with Correct Dimensions
    client.recreate_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=models.VectorParams(
            size=VECTOR_SIZE, 
            distance=models.Distance.COSINE
        )
    )
    print(f"✅ Collection '{COLLECTION_NAME}' created with dimension {VECTOR_SIZE} (Aligned with NTv2/ESM2).")

    # 2. Upload Dummy Data (Placeholder until P1 sends .npy files)
    # We create 10 fake proteins that live in the 768-dim space
    num_vectors = 10
    vectors = np.random.rand(num_vectors, VECTOR_SIZE).tolist()
    
    payloads = []
    for i in range(num_vectors):
        payloads.append({
            "protein_name": f"Protein_{i}_Beta_Sheet",
            "function": "Metabolic Regulation",
            "source": "UniProt_Mock"
        })

    client.upload_collection(
        collection_name=COLLECTION_NAME,
        vectors=vectors,
        payload=payloads,
        ids=list(range(num_vectors))
    )
    print(f"✅ Uploaded {num_vectors} mock vectors to Qdrant.")

if __name__ == "__main__":
    initialize_database()