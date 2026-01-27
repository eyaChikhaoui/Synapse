import torch
import torch.nn as nn
from transformers import AutoTokenizer, AutoModel
import logging
from pathlib import Path

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ProteinEncoder(nn.Module):
    """
    SOTA Protein Encoder for Synapse.
    Backbone: facebook/esm2_t33_650M_UR50D
    Architecture: ESM-2 -> Mean Pool -> MLP Projection (768)
    """
    def __init__(self, model_id="facebook/esm2_t33_650M_UR50D"):
        super().__init__()
        
        # Device management (Optimized for your RTX 3050 Ti)
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        logger.info(f"🧬 [ProteinEncoder] Initializing on {self.device}...")
        
        # 1. Load ESM-2 Foundation Model
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(model_id)
            self.base_model = AutoModel.from_pretrained(model_id).to(self.device)
        except Exception as e:
            logger.error(f"Failed to load ESM-2 model: {e}")
            raise

        # 2. Define SOTA Projection Head (Must match training script exactly)
        # ESM-2 650M hidden size is 1280
        self.projection = nn.Sequential(
            nn.Linear(1280, 768),
            nn.LayerNorm(768),
            nn.GELU(),
            nn.Linear(768, 768)
        ).to(self.device)
        
        self._load_weights()

    def _load_weights(self):
        """Loads trained SOTA weights from the models directory."""
        base_path = Path(__file__).resolve().parent.parent
        weight_path = base_path / "models" / "prot_sota.pth"

        if weight_path.exists():
            try:
                state_dict = torch.load(weight_path, map_location=self.device)
                self.projection.load_state_dict(state_dict)
                logger.info(f"✅ Protein SOTA Weights Loaded from {weight_path}")
            except Exception as e:
                logger.error(f"❌ Error loading weights: {e}")
        else:
            logger.warning(f"⚠️ Weight file not found at {weight_path}. Using random weights.")

    def get_vector(self, sequence: str):
        """Sequence -> Latent Vector (768)"""
        if not sequence:
            return None
            
        clean_seq = sequence.upper().replace(" ", "")
        inputs = self.tokenizer(
            clean_seq, 
            return_tensors="pt", 
            truncation=True, 
            max_length=1024
        ).to(self.device)
        
        with torch.no_grad():
            outputs = self.base_model(**inputs)
            # Mean Pooling over the sequence length dimension
            embeddings = outputs.last_hidden_state.mean(dim=1)
            # Project to shared 768 space
            projected_vec = self.projection(embeddings)
            
        return projected_vec.squeeze().cpu().numpy()