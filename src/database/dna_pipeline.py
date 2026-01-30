import sys
import os
import torch
import torch.nn as nn
import numpy as np
import logging
import pandas as pd
from pathlib import Path
from transformers import AutoTokenizer, AutoModelForMaskedLM, AutoModel

# --- CONFIGURATION ---
print("\n" + "="*60)
print("🧬 SYNAPSE: SOTA GENERATOR (V4 - STABLE)")
print("   Status: Fixed Tokenizer Padding (Max Len 1024)")
print("="*60 + "\n")

# --- PATHS ---
current_file = Path(__file__).resolve()
project_root = current_file.parent.parent.parent
FASTA_FILE = project_root / "src" / "Backend" / "Data" / "human_genes.fasta"
PARQUET_FILE = project_root / "src" / "Backend" / "Data" / "human_genes_sota.parquet"
MODELS_DIR = project_root / "src" / "models"

# --- THE PROJECTION HEAD (MATCHING YOUR .PTH REALITY) ---
class ProjectionHead(nn.Module):
    def __init__(self, input_dim, output_dim=768): 
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, output_dim),   # 0
            nn.LayerNorm(output_dim),           # 1
            nn.GELU(),                          # 2
            nn.Linear(output_dim, output_dim),  # 3
            nn.LayerNorm(output_dim)            # 4 <-- ADD THIS (The Missing Layer)
        )

    def forward(self, x):
        return self.net(x)

# --- ENCODER CLASS ---
class SOTAEncoder:
    def __init__(self, modality="dna"):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.modality = modality
        
        if modality == "dna":
            print("   ⚙️  Loading NTv3 (DNA)...")
            self.tokenizer = AutoTokenizer.from_pretrained("InstaDeepAI/NTv3_650M_pre", trust_remote_code=True)
            self.model = AutoModelForMaskedLM.from_pretrained("InstaDeepAI/NTv3_650M_pre", trust_remote_code=True, output_hidden_states=True).to(self.device)
            
            # Input: 1536 -> Output: 768 (Matches .pth)
            self.projector = ProjectionHead(input_dim=1536, output_dim=768).to(self.device)
            weight_path = MODELS_DIR / "dna_projection.pth"
            
        else:
            print("   ⚙️  Loading ESM-2 (Protein)...")
            self.tokenizer = AutoTokenizer.from_pretrained("facebook/esm2_t33_650M_UR50D")
            self.model = AutoModel.from_pretrained("facebook/esm2_t33_650M_UR50D").to(self.device)
            
            # Input: 1280 -> Output: 768 (Matches .pth)
            self.projector = ProjectionHead(input_dim=1280, output_dim=768).to(self.device)
            weight_path = MODELS_DIR / "prot_projection.pth"

        # LOAD WEIGHTS
        if weight_path.exists():
            try:
                self.projector.net.load_state_dict(torch.load(weight_path, map_location=self.device))
                print(f"   ✅ Loaded SOTA Weights: {weight_path.name}")
            except Exception as e:
                print(f"   ❌ Weight Mismatch: {e}")
                sys.exit(1)
        else:
            print(f"   ❌ CRITICAL: Weights not found at {weight_path}")
            sys.exit(1)
            
        self.model.eval()
        self.projector.eval()

    def encode(self, sequence):
        # 1. Clean Sequence
        if not sequence: return None
        # Remove whitespaces/newlines just in case
        sequence = "".join(sequence.split())
        
        # 2. Tokenize with STRICT Padding/Truncation (The Fix)
        # We enforce max_length=1024 to prevent the (14) vs (15) tensor shape crash
        inputs = self.tokenizer(
            sequence, 
            return_tensors="pt", 
            padding="max_length",   # Force fill to 1024
            truncation=True,        # Cut if too long
            max_length=1024,        # Explicit limit
            add_special_tokens=True 
        ).to(self.device)
        
        with torch.no_grad():
            if self.modality == "dna":
                # NTv3 specific cleanup
                if 'attention_mask' in inputs: 
                    attention_mask = inputs['attention_mask']
                    del inputs['attention_mask']
                else:
                    attention_mask = None
                    
                out = self.model(**inputs)
                
                # Mean Pooling with Mask (Ignore Padding)
                hidden_states = out.hidden_states[-1]
                if attention_mask is not None:
                    # Expand mask to [Batch, Seq, Dim]
                    mask_expanded = attention_mask.unsqueeze(-1).expand(hidden_states.size()).float()
                    sum_embeddings = torch.sum(hidden_states * mask_expanded, 1)
                    sum_mask = torch.clamp(mask_expanded.sum(1), min=1e-9)
                    raw_vec = sum_embeddings / sum_mask
                else:
                    raw_vec = torch.mean(hidden_states, dim=1)
                    
            else:
                # ESM-2 Logic
                out = self.model(**inputs)
                raw_vec = torch.mean(out.last_hidden_state, dim=1)
            
            # Apply Trained Projection
            sota_vec = self.projector(raw_vec)
            
        return sota_vec.squeeze().cpu().numpy()

# --- MAIN EXECUTION ---
def main():
    print("🚀 STARTING FULL PIPELINE (UNLIMITED)...")
    
    # 1. SETUP ENCODER
    try:
        encoder = SOTAEncoder("dna")
    except Exception as e:
        print(f"❌ Failed to init encoder: {e}")
        return

    # 2. READ & PROCESS FASTA
    print(f"   📂 Reading {FASTA_FILE.name}...")
    data_buffer = []
    count = 0
    
    def process_entry(header, seq_parts):
        nonlocal count
        if not header or not seq_parts: return
        full_seq = "".join(seq_parts)
        
        # Parse Header
        clean_header = header.lstrip('>')
        parts = clean_header.split('|')
        gene_name = parts[0] if len(parts) > 0 else "Unknown"

        # PROGRESS LOG (Overwrites line to keep console clean)
        print(f"\r   🧬 Processing Gene #{count}: {gene_name}...", end="", flush=True)
        
        # ENCODE
        try:
            vector = encoder.encode(full_seq)
            
            if vector is not None:
                entry = {
                    "id": count,
                    "vector": vector.tolist(), 
                    "payload": {
                        "type": "gene_coding_sequence",
                        "name": gene_name,
                        "pdb_id": gene_name,
                        "species": "Homo sapiens", 
                        "function": "SOTA Aligned Sequence",
                        "is_reference": True,
                        "raw_sequence": full_seq
                    }
                }
                data_buffer.append(entry)
                count += 1
                
                # OPTIONAL: Save chunks every 5000 to avoid RAM overflow
                # (Parquet handles large files well, but saving lists eats RAM)
                
        except Exception as e:
            print(f" ❌ Error: {e}")
            
    # File Reading Loop
    if not FASTA_FILE.exists():
        print("❌ FASTA File not found!")
        return

    with open(FASTA_FILE, 'r') as f:
        current_header = ""
        current_seq = []
        for line in f:
            line = line.strip()
            if line.startswith(">"):
                if current_header: process_entry(current_header, current_seq)
                current_header = line
                current_seq = []
            else:
                current_seq.append(line)
        if current_header: process_entry(current_header, current_seq)

    # 3. SAVE
    print(f"\n💾 Saving {len(data_buffer)} records...")
    if data_buffer:
        df = pd.DataFrame(data_buffer)
        df.to_parquet(PARQUET_FILE, engine='pyarrow', index=False)
        print(f"🎉 SUCCESS! Full DNA Database ({len(data_buffer)} records) saved.")
    else:
        print("⚠️ No data processed.")

if __name__ == "__main__":
    main()