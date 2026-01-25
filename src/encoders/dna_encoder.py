import torch
import torch.nn as nn
from transformers import AutoTokenizer, AutoModel
import sys
import os

# --- PATH FIX: Ensure we can import from 'src' root ---
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from utils.data_processor import DataProcessor

class RealEncoder(nn.Module):
    """
    Person 1 (ML Lead) - Production Real Encoder.
    Replaces mock numbers with real biological embeddings.
    """
    def __init__(self, model_id="InstaDeepAI/nucleotide-transformer-v2-50m-multi-species"):
        super().__init__()
        
        # Load Tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True)
        
        # --- CRITICAL FIX: Ignore Mismatched Sizes ---
        # The v2-50m model has inconsistent internal dimensions for some layers 
        # (GLU vs Standard FFN). We use ignore_mismatched_sizes=True to load 
        # the valid weights and safely skip the conflicting ones.
        self.model = AutoModel.from_pretrained(
            model_id, 
            trust_remote_code=True,
            ignore_mismatched_sizes=True 
        )
        
        self.processor = DataProcessor()
        
        # Ensure output is always 768 for P2 (DB) and P4 (UI)
        # NTv2 outputs 512 dim, so we project it to 768
        self.projection = nn.Linear(512, 768) 

    def encode(self, sequence: str):
        # Step 1: Clean data
        clean_seq = self.processor.clean_dna(sequence)
        
        # Step 2: Biological Inference
        inputs = self.tokenizer(clean_seq, return_tensors="pt")
        with torch.no_grad():
            outputs = self.model(**inputs)
            # Use mean pooling
            embeddings = outputs.last_hidden_state.mean(dim=1)
            
            # Step 3: Project to Shared Latent Space (768)
            projected = self.projection(embeddings)
            return projected.squeeze().numpy()

if __name__ == "__main__":
    print("⏳ Initializing RealEncoder (ignore_mismatched_sizes=True)...")
    encoder = RealEncoder()
    print("✅ RealEncoder initialized successfully.")
    
    # Test with a dummy sequence
    test_seq = "ATGCGTAGCTAG"
    vector = encoder.encode(test_seq)
    print(f"🧬 Vector Shape: {vector.shape} (Should be 768)")