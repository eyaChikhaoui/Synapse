import torch
import torch.nn as nn
import torch.nn.functional as F
from transformers import AutoTokenizer, AutoModel
import logging
from pathlib import Path

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ProteinEncoder")

class SOTAProteinProjector(nn.Module):
    """
    Projects ESM-2 embeddings (1280 dim) to Synapse Latent Space (768 dim).
    """
    def __init__(self):
        super().__init__()
        # FIX: Added the 5th layer (index 4) to match the saved .pth weights
        self.net = nn.Sequential(
            nn.Linear(1280, 768),   # 0
            nn.LayerNorm(768),      # 1
            nn.GELU(),              # 2
            nn.Linear(768, 768),    # 3
            nn.LayerNorm(768)       # 4 <-- ADDED THIS (Matches "4.weight" error)
        )
    def forward(self, x):
        return self.net(x)

class ProteinEncoder(nn.Module):
    def __init__(self, model_id="facebook/esm2_t33_650M_UR50D"):
        super().__init__()
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        logger.info(f"🧬 [ProteinEncoder] Initializing SOTA on {self.device}...")
        
        # Load SOTA Model & Tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(model_id)
        self.base_model = AutoModel.from_pretrained(model_id).to(self.device)
        self.projector = SOTAProteinProjector().to(self.device)
        
        # Load Custom Projection Weights
        weight_path = Path(__file__).resolve().parent.parent / "models" / "prot_projection.pth"
        
        if weight_path.exists():
            try:
                self.projector.net.load_state_dict(torch.load(weight_path, map_location=self.device))
                logger.info("✅ Protein Weights Loaded")
            except Exception as e:
                logger.error(f"❌ Failed to load Protein weights: {e}")
        else:
            logger.warning(f"⚠️ Weights file not found at: {weight_path}")

    def get_vector(self, sequence: str):
        if not sequence: return None
        # Clean & Truncate (Standardize input)
        clean_seq = sequence.upper().replace(" ", "")[:1022] 

        # Tokenize with STRICT padding to 1024
        inputs = self.tokenizer(
            clean_seq, 
            return_tensors="pt", 
            truncation=True, 
            padding="max_length",
            max_length=1024,
            add_special_tokens=True
        ).to(self.device)
        
        # --- ROBUST MASK EXTRACTION ---
        if 'attention_mask' in inputs:
            attention_mask = inputs['attention_mask']
        else:
            pad_id = self.tokenizer.pad_token_id if self.tokenizer.pad_token_id is not None else 0
            attention_mask = (inputs['input_ids'] != pad_id).long()

        with torch.no_grad():
            outputs = self.base_model(**inputs)
            hidden = outputs.last_hidden_state 
            
            # --- MASKED POOLING ---
            mask_expanded = attention_mask.unsqueeze(-1).expand(hidden.size()).float()
            sum_embeddings = torch.sum(hidden * mask_expanded, 1)
            sum_mask = torch.clamp(mask_expanded.sum(1), min=1e-9)
            
            raw_vec = sum_embeddings / sum_mask
            
            # Project & Normalize
            projected_vec = self.projector(raw_vec)
            final_vec = F.normalize(projected_vec, p=2, dim=1)
            
        return final_vec.squeeze().cpu().numpy()