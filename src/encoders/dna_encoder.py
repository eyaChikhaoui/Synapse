import torch
import torch.nn as nn
from transformers import AutoTokenizer, AutoModelForMaskedLM
import logging
from pathlib import Path

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DNAEncoder(nn.Module):
    """
    SOTA DNA Encoder for Synapse.
    Backbone: InstaDeepAI/NTv3_650M_pre
    Architecture: NTv3 -> Mean Pool -> MLP Projection (768)
    """
    def __init__(self, model_id="InstaDeepAI/NTv3_650M_pre"):
        super().__init__()
        
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        logger.info(f"🧬 [DNAEncoder] Initializing on {self.device}...")
        
        # 1. Load NTv3 Foundation Model
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True)
            self.model = AutoModelForMaskedLM.from_pretrained(
                model_id, 
                trust_remote_code=True
            ).to(self.device)
        except Exception as e:
            logger.error(f"Failed to load NTv3 model: {e}")
            raise

        # 2. Define SOTA Projection Head
        # NTv3 650M hidden size is 1536
        self.projection = nn.Sequential(
            nn.Linear(1536, 768),
            nn.LayerNorm(768),
            nn.GELU(),
            nn.Linear(768, 768)
        ).to(self.device)
        
        self._load_weights()

    def _load_weights(self):
        """Loads trained SOTA weights from the models directory."""
        base_path = Path(__file__).resolve().parent.parent
        weight_path = base_path / "models" / "dna_sota.pth"

        if weight_path.exists():
            try:
                state_dict = torch.load(weight_path, map_location=self.device)
                self.projection.load_state_dict(state_dict)
                logger.info(f"✅ DNA SOTA Weights Loaded from {weight_path}")
            except Exception as e:
                logger.error(f"❌ Error loading weights: {e}")
        else:
            logger.warning(f"⚠️ Weight file not found at {weight_path}. Using random weights.")

    def get_vector(self, sequence: str):
        """DNA Sequence -> Latent Vector (768)"""
        if not sequence:
            return None
            
        clean_seq = sequence.upper().replace(" ", "")
        inputs = self.tokenizer(
            clean_seq, 
            return_tensors="pt", 
            padding=True, 
            truncation=True, 
            max_length=1024
        ).to(self.device)
        
        with torch.no_grad():
            outputs = self.model(**inputs, output_hidden_states=True)
            # NTv3 uses specific hidden state indexing; -1 is the last layer
            hidden_states = outputs.hidden_states[-1]
            # Mean Pooling
            embeddings = hidden_states.mean(dim=1)
            # Project to shared 768 space
            projected_vec = self.projection(embeddings)
            
            return projected_vec.squeeze().cpu().numpy()