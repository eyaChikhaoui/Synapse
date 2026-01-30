import torch
import torch.nn as nn
import torch.nn.functional as F
import logging
from pathlib import Path
from transformers import AutoTokenizer, AutoModelForMaskedLM

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("DNAEncoder")

class SOTADNAProjector(nn.Module):
    def __init__(self):
        super().__init__()
        # FIX: Added the 5th layer (index 4) to match the saved .pth weights
        self.net = nn.Sequential(
            nn.Linear(1536, 768),   # 0
            nn.LayerNorm(768),      # 1
            nn.GELU(),              # 2
            nn.Linear(768, 768),    # 3
            nn.LayerNorm(768)       # 4 <-- ADDED THIS (Matches "4.weight" error)
        )
    def forward(self, x):
        return self.net(x)

class DNAEncoder:
    def __init__(self, model_name="InstaDeepAI/NTv3_650M_pre", device=None):
        self.device = device if device else ("cuda" if torch.cuda.is_available() else "cpu")
        logger.info(f"🧬 Initializing NTv3 (SOTA) on device: {self.device}")
        
        self.tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
        self.model = AutoModelForMaskedLM.from_pretrained(model_name, trust_remote_code=True, output_hidden_states=True).to(self.device)
        self.model.eval()

        self.adapter = SOTADNAProjector().to(self.device)
        self.adapter.eval()
        
        # Robust path finding for weights
        weight_path = Path(__file__).resolve().parent.parent / "models" / "dna_projection.pth"
        if weight_path.exists():
            try:
                self.adapter.net.load_state_dict(torch.load(weight_path, map_location=self.device))
                logger.info("✅ DNA Weights Loaded")
            except Exception as e:
                logger.error(f"❌ Failed to load DNA weights: {e}")
        else:
            logger.warning(f"⚠️ Weights file not found at: {weight_path}")

    def get_vector(self, sequence):
        if not sequence: return None
        # Clean and truncate
        sequence = "".join(sequence.split()).upper()[:1024] 
        
        # Tokenize with STRICT padding to 1024
        inputs = self.tokenizer(
            sequence, 
            return_tensors="pt", 
            padding="max_length", 
            truncation=True, 
            max_length=1024, 
            add_special_tokens=True
        )
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        
        # --- ROBUST MASK EXTRACTION ---
        if 'attention_mask' in inputs:
            attention_mask = inputs['attention_mask']
        else:
            # Create mask if missing (1=Real, 0=Pad)
            pad_id = self.tokenizer.pad_token_id if self.tokenizer.pad_token_id is not None else 0
            attention_mask = (inputs['input_ids'] != pad_id).long()
        
        # NTv3 optimization: remove mask from kwargs if it causes issues
        model_inputs = {k: v for k, v in inputs.items() if k != 'attention_mask'}

        with torch.no_grad():
            outputs = self.model(**model_inputs)
            hidden = outputs.hidden_states[-1] # [Batch, Seq, 1536]
            
            # --- MASKED POOLING ---
            mask_expanded = attention_mask.unsqueeze(-1).expand(hidden.size()).float()
            
            sum_embeddings = torch.sum(hidden * mask_expanded, 1)
            sum_mask = torch.clamp(mask_expanded.sum(1), min=1e-9)
            
            raw_vec = sum_embeddings / sum_mask
            
            # Project & Normalize
            projected_vec = self.adapter(raw_vec)
            final_vec = F.normalize(projected_vec, p=2, dim=1)
            
            return final_vec.squeeze().cpu().numpy()