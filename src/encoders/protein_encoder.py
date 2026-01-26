import torch
import torch.nn as nn
from transformers import AutoTokenizer, AutoModel

class ProteinEncoder(nn.Module):
    """
    Production Protein Encoder for Synapse.
    
    Implements the "Bridge" logic:
    Projects ESM-2 Embeddings (320-dim) -> Shared Latent Space (768-dim).
    
    Reference: Synapse Technical Deep Dive, Section 1.3
    """
    def __init__(self, model_id="facebook/esm2_t6_8M_UR50D"):
        super().__init__()
        print(f"🧬 [ProteinEncoder] Initializing with base: {model_id}")
        
        # 1. Load Standard ESM2 Model 
        # The 8M parameter model has a hidden size of 320 
        self.tokenizer = AutoTokenizer.from_pretrained(model_id)
        self.base_model = AutoModel.from_pretrained(model_id)
        
        # 2. Projection Layer
        # Input: 320 (ESM-2 Hidden Size) -> Output: 768 (Synapse Shared Space)
        # Weights: W_prot in R^{768x320}
        self.projection = nn.Linear(320, 768) # [cite: 67]
        
        print(f"✅ [ProteinEncoder] Ready. Projection: 320 -> 768")

    def get_vector(self, sequence: str):
        """
        Tokenizes input, generates embedding, and projects to latent space.
        Returns: numpy array of shape (768,)
        """
        # Sanitation: Proteins use single-letter codes, must be Upper
        clean_seq = sequence.upper().replace(" ", "")
        
        inputs = self.tokenizer(clean_seq, return_tensors="pt")
        
        with torch.no_grad():
            outputs = self.base_model(**inputs)
            
            # Mean Pooling
            embeddings = outputs.last_hidden_state.mean(dim=1)
            
            # Project to Shared Latent Space
            projected_vec = self.projection(embeddings)
            
        return projected_vec.squeeze().numpy()

if __name__ == "__main__":
    # Smoke Test
    encoder = ProteinEncoder()
    # Insulin snippet
    test_prot = "GIVEQCCTSICSLYQLENYCN" 
    vector = encoder.get_vector(test_prot)
    
    print(f"\n🧪 Protein Smoke Test:")
    print(f"Sequence: {test_prot}")
    print(f"Vector Shape: {vector.shape}")
    
    if vector.shape == (768,):
        print("🎉 SUCCESS: Protein Vector aligned to 768 dimensions.")
    else:
        print(f"❌ ERROR: Expected (768,), got {vector.shape}")