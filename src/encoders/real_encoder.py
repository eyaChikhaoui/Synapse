import torch
import torch.nn as nn
from transformers import AutoTokenizer, AutoModel
from utils.data_processor import DataProcessor

class RealEncoder(nn.Module):
    """
    Person 1 (ML Lead) - Production Real Encoder.
    Replaces mock numbers with real biological embeddings.
    """
    def __init__(self, model_id="InstaDeepAI/nucleotide-transformer-v2-50m-multi-species"):
        super().__init__()
        # Load weights from the specified local path
        self.tokenizer = AutoTokenizer.from_pretrained(model_id)
        self.model = AutoModel.from_pretrained(model_id, cache_dir="./data/weights/")
        self.processor = DataProcessor()
        # Ensure output is always 768 for P2 (DB) and P4 (UI)
        self.projection = nn.Linear(512, 768) 

    def encode(self, sequence: str):
        # Step 1: Clean data using your DataProcessor logic
        clean_seq = self.processor.clean_dna(sequence)
        
        # Step 2: Biological Inference
        inputs = self.tokenizer(clean_seq, return_tensors="pt")
        with torch.no_grad():
            outputs = self.model(**inputs)
            # Use mean pooling and project to 768 dimensions
            embeddings = outputs.last_hidden_state.mean(dim=1)
            return self.projection(embeddings).squeeze().numpy()