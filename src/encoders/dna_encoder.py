import torch
import torch.nn as nn
from transformers import AutoTokenizer, AutoModel, AutoConfig

class DNAEncoder(nn.Module):
    """
    Person 1 (ML Lead) - Production DNA Encoder.
    Uses InstaDeep's Nucleotide Transformer v2 with a Projection Head 
    to align with the 768-dimension Shared Latent Space.
    """
    def __init__(self, model_id="InstaDeepAI/nucleotide-transformer-v2-50m-multi-species", target_dim=768):
        super().__init__()
        print(f"🧬 [DNAEncoder] Initializing with base: {model_id}")
        
        # 1. Load Patched Config & Model (Based on your successful diagnostics)
        config = AutoConfig.from_pretrained(model_id, trust_remote_code=True)
        config.intermediate_size = 4096 # Apply your verified patch
        
        self.tokenizer = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True)
        self.base_model = AutoModel.from_pretrained(
            model_id, 
            config=config, 
            trust_remote_code=True,
            ignore_mismatched_sizes=True
        )
        
        # 2. Projection Layer (The Bridge)
        # Up-scales the 512-dim output of NTv2 to our 768-dim Shared Latent Space
        self.projection = nn.Linear(self.base_model.config.hidden_size, target_dim)
        
        print(f"✅ [DNAEncoder] Ready. Projection: {self.base_model.config.hidden_size} -> {target_dim}")

    def forward(self, sequence: str):
        # Clean sequence (Standard Bio-Cleaning)
        sequence = sequence.upper().replace(" ", "")
        
        # Tokenize
        inputs = self.tokenizer(sequence, return_tensors="pt")
        
        # Inference
        with torch.no_grad():
            outputs = self.base_model(**inputs)
            # Use Mean Pooling across the sequence length (dim 1)
            embeddings = outputs.last_hidden_state.mean(dim=1)
            
            # Project to Shared Latent Space
            projected_embeddings = self.projection(embeddings)
            
        return projected_embeddings

    def get_vector(self, sequence: str):
        """Helper to return a flat numpy array for the DB."""
        tensor = self.forward(sequence)
        return tensor.squeeze().numpy()

if __name__ == "__main__":
    # Smoke Test for Step 2
    encoder = DNAEncoder()
    test_seq = "GATCCA"
    vector = encoder.get_vector(test_seq)
    
    print(f"\n🧪 Smoke Test Output:")
    print(f"Sequence: {test_seq}")
    print(f"Final Vector Shape: {vector.shape}") # MUST BE (768,)
    
    if vector.shape[0] == 768:
        print("🎉 SUCCESS: DNA is now aligned with the Shared Latent Space.")
    else:
        print("❌ ERROR: Dimension mismatch.")