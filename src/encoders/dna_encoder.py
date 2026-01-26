import torch
import torch.nn as nn
from transformers import AutoTokenizer, AutoModel
import os

class DNAEncoder(nn.Module):
    """
    Production DNA Encoder for Synapse.
    
    Implements the "Bridge" logic:
    Projects NTv3 Embeddings (512-dim) -> Shared Latent Space (768-dim).
    
    Reference: Synapse Technical Deep Dive, Section 3.1
    """
    def __init__(self, model_id="InstaDeepAI/nucleotide-transformer-v2-50m-multi-species"):
        super().__init__()
        
        print(f"🧬 [DNAEncoder] Initializing with base: {model_id}")
        
        # 1. Load Tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True)
        
        # 2. Load Foundation Model (NTv3)
        # Critical: ignore_mismatched_sizes=True is required to safely load 
        # pre-trained weights while attaching custom heads if necessary.
        self.model = AutoModel.from_pretrained(
            model_id,
            trust_remote_code=True,
            ignore_mismatched_sizes=True  # [cite: 130]
        )
        
        # 3. The Bridge Projection Layer
        # Input: 512 (NTv3 Hidden Size) -> Output: 768 (Synapse Shared Space)
        # Weights: W_dna in R^{768x512}
        self.projection = nn.Linear(512, 768) # [cite: 67]
        
        print("✅ [DNAEncoder] Ready. Projection: 512 -> 768")

    def get_vector(self, sequence: str):
        """
        Tokenizes input, generates embedding, and projects to latent space.
        Returns: numpy array of shape (768,)
        """
        # Sanitation: standardizing input 
        clean_seq = sequence.upper().replace(" ", "")
        
        inputs = self.tokenizer(clean_seq, return_tensors="pt")
        
        with torch.no_grad():
            outputs = self.model(**inputs)
            
            # Mean Pooling to derive sequence vector
            # Listing 3.1 specifies .mean(dim=1) [cite: 138]
            embeddings = outputs.last_hidden_state.mean(dim=1)
            
            # Project to Shared Latent Space
            # Listing 3.1 specifies projection -> squeeze -> numpy [cite: 140]
            projected_vec = self.projection(embeddings)
            
            return projected_vec.squeeze().numpy()

if __name__ == "__main__":
    # Smoke Test
    encoder = DNAEncoder()
    test_seq = "ATGCGTAGCTAG"
    vector = encoder.get_vector(test_seq)
    
    print(f"\n🧪 DNA Smoke Test:")
    print(f"Input: {test_seq}")
    print(f"Vector Shape: {vector.shape}")
    
    if vector.shape == (768,):
        print("🎉 SUCCESS: DNA Vector aligned to 768 dimensions.")
    else:
        print(f"❌ ERROR: Expected (768,), got {vector.shape}")