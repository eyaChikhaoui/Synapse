import torch
import torch.nn as nn
from transformers import AutoTokenizer, AutoModel

class ProteinEncoder(nn.Module):
    """
    Person 1 (ML Lead) - Production Protein Encoder.
    Uses Facebook's ESM2 (Evolutionary Scale Modeling) with a Projection Head
    to align with the 768-dimension Shared Latent Space.
    """
    def __init__(self, model_id="facebook/esm2_t6_8M_UR50D", target_dim=768):
        super().__init__()
        print(f"🧬 [ProteinEncoder] Initializing with base: {model_id}")
        
        # 1. Load Standard ESM2 Model (320-dim hidden size)
        self.tokenizer = AutoTokenizer.from_pretrained(model_id)
        self.base_model = AutoModel.from_pretrained(model_id)
        
        # 2. Projection Layer (The Protein-to-Synapse Bridge)
        # Up-scales the 320-dim output of ESM2 to 768-dim
        self.projection = nn.Linear(self.base_model.config.hidden_size, target_dim)
        
        print(f"✅ [ProteinEncoder] Ready. Projection: {self.base_model.config.hidden_size} -> {target_dim}")

    def forward(self, sequence: str):
        # Clean sequence (Remove whitespace/ensure uppercase)
        sequence = sequence.upper().replace(" ", "")
        
        # Tokenize (Proteins use Amino Acid single-letter codes)
        inputs = self.tokenizer(sequence, return_tensors="pt")
        
        # Inference
        with torch.no_grad():
            outputs = self.base_model(**inputs)
            # Use Mean Pooling to get a single vector for the whole protein
            embeddings = outputs.last_hidden_state.mean(dim=1)
            
            # Project to the same 768-dim space as the DNA
            projected_embeddings = self.projection(embeddings)
            
        return projected_embeddings

    def get_vector(self, sequence: str):
        """Standard output for the Vector Database (Qdrant)"""
        tensor = self.forward(sequence)
        return tensor.squeeze().numpy()

if __name__ == "__main__":
    # Smoke Test for Step 3
    encoder = ProteinEncoder()
    # Sample Protein sequence (Insulin snippet)
    test_prot = "GIVEQCCTSICSLYQLENYCN" 
    vector = encoder.get_vector(test_prot)
    
    print(f"\n🧪 Smoke Test Output:")
    print(f"Sequence: {test_prot}")
    print(f"Final Vector Shape: {vector.shape}") # MUST BE (768,)
    
    if vector.shape[0] == 768:
        print("🎉 SUCCESS: Protein is now aligned with the Shared Latent Space.")
    else:
        print("❌ ERROR: Dimension mismatch.")