import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np

class SynapseProjectionHead(nn.Module):
    """
    DeepMind-Style Projection Head.
    Input: Raw Embedding (1536/1280) -> Output: Latent Alignment (768)
    Math: x -> Linear -> LayerNorm -> GELU -> Linear -> LayerNorm -> x_out
    """
    def __init__(self, input_dim, output_dim=768, dropout=0.1):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, output_dim),
            nn.LayerNorm(output_dim),      # Vital for contrastive stability
            nn.GELU(),                     # SOTA activation (better than ReLU)
            nn.Dropout(dropout),
            nn.Linear(output_dim, output_dim),
            nn.LayerNorm(output_dim)       # Final Norm before hypersphere projection
        )

    def forward(self, x):
        return self.net(x)

class SynapseDualEncoder(nn.Module):
    """
    The Main Brain. Holds both encoders and the learned temperature.
    """
    def __init__(self, dna_model, prot_model):
        super().__init__()
        self.dna_model = dna_model      # Your NTv3 Model
        self.prot_model = prot_model    # Your ESM-2 Model
        
        # SOTA Projection Heads
        self.dna_projector = SynapseProjectionHead(input_dim=1536, output_dim=768)
        self.prot_projector = SynapseProjectionHead(input_dim=1280, output_dim=768)
        
        # LEARNABLE TEMPERATURE (The Secret Sauce)
        # Initialized to ln(1/0.07) ~= 2.659
        self.logit_scale = nn.Parameter(torch.ones([]) * np.log(1 / 0.07))

    def forward(self, dna_inputs, prot_inputs):
        # 1. Encode DNA
        dna_outputs = self.dna_model(**dna_inputs)
        dna_raw = torch.mean(dna_outputs.hidden_states[-1], dim=1) # Mean Pool
        
        # 2. Encode Protein
        prot_outputs = self.prot_model(**prot_inputs)
        prot_raw = torch.mean(prot_outputs.last_hidden_state, dim=1) # Mean Pool
        
        # 3. Project
        dna_feat = self.dna_projector(dna_raw)
        prot_feat = self.prot_projector(prot_raw)
        
        # 4. Normalize (Hypersphere Projection)
        dna_feat = F.normalize(dna_feat, dim=1)
        prot_feat = F.normalize(prot_feat, dim=1)
        
        return dna_feat, prot_feat, self.logit_scale.exp()

def info_nce_loss(dna_feat, prot_feat, logit_scale):
    """
    Symmetric Contrastive Loss (CLIP Style).
    Math: L_i = -log( exp(sim(i,i)*scale) / sum(exp(sim(i,j)*scale)) )
    """
    # 1. Calculate Cosine Similarity Matrix
    # [Batch, Dim] @ [Dim, Batch] -> [Batch, Batch]
    logits = (dna_feat @ prot_feat.T) * logit_scale
    
    # 2. Labels are the diagonal (Item 0 matches Item 0)
    labels = torch.arange(len(logits), device=logits.device)
    
    # 3. Calculate Loss in both directions (DNA->Prot and Prot->DNA)
    loss_i = F.cross_entropy(logits, labels)
    loss_t = F.cross_entropy(logits.T, labels)
    
    return (loss_i + loss_t) / 2