import torch
import numpy as np
import json
from datetime import datetime

class MockEncoder:
    """
    Person 1 (ML Lead) Deliverable.
    Simulates the Shared Latent Space output (768 dimensions)
    to unblock Database (P2) and Frontend (P4) development.
    """
    def __init__(self, dimension: int = 768):
        self.dimension = dimension
        print(f"🚀 [MockEncoder] Initialized with Dimension: {self.dimension}")

    def encode(self, sequence: str) -> np.ndarray:
        """
        Simulates a forward pass. 
        In production, this will be replaced by the NTv2/ESM2 models.
        """
        # Deterministic seed based on string length to simulate consistent embeddings
        np.random.seed(len(sequence))
        embedding = np.random.randn(self.dimension).astype(np.float32)
        
        # Normalize to unit length (Standard practice for Vector Search)
        norm = np.linalg.norm(embedding)
        return embedding / norm

    def get_sample_json(self, sequence: str, seq_type: str = "DNA"):
        """
        Deliverable for Person 4 (Frontend).
        Provides the exact data structure the API will return.
        """
        vector = self.encode(sequence)
        
        payload = {
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "sequence_type": seq_type,
                "sequence_length": len(sequence),
                "model_version": "Synapse-v1-Mock"
            },
            "sequence": sequence,
            "embedding_preview": vector[:5].tolist(), # Show first 5 values
            "vector_dimension": len(vector),
            "status": "success"
        }
        return json.dumps(payload, indent=4)

if __name__ == "__main__":
    # --- Quick Smoke Test ---
    encoder = MockEncoder(dimension=768)
    
    test_dna = "ATGCGTACGTTAG"
    sample_output = encoder.get_sample_json(test_dna)
    
    print("\n📦 [Deliverable: Sample JSON for P4]")
    print(sample_output)
    
    print("\n✅ [Deliverable: Vector for P2]")
    vector = encoder.encode(test_dna)
    print(f"Vector Length: {len(vector)} (Matches Qdrant Schema)")
    