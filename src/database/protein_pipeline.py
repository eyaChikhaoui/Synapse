import sys
import os
import torch
import torch.nn as nn
import numpy as np
import logging
import pandas as pd
import json
from pathlib import Path
from transformers import AutoTokenizer, AutoModel

# --- CONFIGURATION ---
print("\n" + "="*60)
print("🥩 SYNAPSE: PROTEIN SOTA GENERATOR (V4 - UNIVERSAL)")
print("   Status: JSON & FASTA Support + Architecture Fix")
print("="*60 + "\n")

# --- PATHS ---
current_file = Path(__file__).resolve()
project_root = current_file.parent.parent.parent
# This will work for both .fasta and .json now
INPUT_FILE = project_root / "src" / "Backend" / "Data" / "proteins.json"
PARQUET_FILE = project_root / "src" / "Backend" / "Data" / "human_proteins_sota.parquet"
MODELS_DIR = project_root / "src" / "models"

# --- THE PROJECTION HEAD ---
class ProjectionHead(nn.Module):
    def __init__(self, input_dim, output_dim=768): 
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, output_dim),
            nn.LayerNorm(output_dim),
            nn.GELU(),
            nn.Linear(output_dim, output_dim),
            nn.LayerNorm(output_dim)
        )

    def forward(self, x):
        return self.net(x)

# --- ENCODER CLASS ---
class SOTAEncoder:
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"   ⚙️  Loading ESM-2 (Protein Model) on {self.device}...")
        
        self.tokenizer = AutoTokenizer.from_pretrained("facebook/esm2_t33_650M_UR50D")
        self.model = AutoModel.from_pretrained("facebook/esm2_t33_650M_UR50D").to(self.device)
        self.projector = ProjectionHead(input_dim=1280, output_dim=768).to(self.device)
        
        weight_path = MODELS_DIR / "prot_projection.pth"
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
        if not sequence: return None
        sequence = "".join(sequence.split())
        
        inputs = self.tokenizer(
            sequence, 
            return_tensors="pt", 
            padding="max_length", 
            truncation=True, 
            max_length=1024
        ).to(self.device)
        
        with torch.no_grad():
            out = self.model(**inputs)
            hidden_states = out.last_hidden_state
            attention_mask = inputs['attention_mask']
            
            mask_expanded = attention_mask.unsqueeze(-1).expand(hidden_states.size()).float()
            sum_embeddings = torch.sum(hidden_states * mask_expanded, 1)
            sum_mask = torch.clamp(mask_expanded.sum(1), min=1e-9)
            raw_vec = sum_embeddings / sum_mask
            
            sota_vec = self.projector(raw_vec)
            
        return sota_vec.squeeze().cpu().numpy()

# --- MAIN EXECUTION ---
def main():
    print("🚀 STARTING PROTEIN PIPELINE...")
    
    try:
        encoder = SOTAEncoder()
    except Exception as e:
        print(f"❌ Failed to init encoder: {e}")
        return

    if not INPUT_FILE.exists():
        print(f"❌ Input File not found at {INPUT_FILE}!")
        return

    print(f"   📂 Reading {INPUT_FILE.name}...")
    data_buffer = []
    count = 0
    
    # --- HELPER: PROCESS SINGLE SEQUENCE ---
    def process_sequence(name, seq):
        nonlocal count
        print(f"\r   🥩 Processing Protein #{count}: {name[:20]}...", end="", flush=True)
        try:
            vector = encoder.encode(seq)
            if vector is not None:
                entry = {
                    "id": count,
                    "vector": vector.tolist(), 
                    "payload": {
                        "type": "protein_sequence",
                        "name": name,
                        "species": "Homo sapiens", 
                        "function": "SOTA Aligned Protein",
                        "raw_sequence": seq
                    }
                }
                data_buffer.append(entry)
                count += 1
        except Exception as e:
            print(f" ❌ Error processing {name}: {e}")

    # --- MODE DETECTION ---
    if str(INPUT_FILE).endswith('.json'):
        # JSON MODE
        print("   ℹ️  Detected JSON format.")
        try:
            with open(INPUT_FILE, 'r') as f:
                raw_data = json.load(f)
                
            # Handle list or dict wrapper
            items = raw_data if isinstance(raw_data, list) else raw_data.get('proteins', [])
            
            for item in items:
                # Flexible key search
                name = item.get('name') or item.get('id') or item.get('accession') or "Unknown"
                seq = item.get('sequence') or item.get('seq') or item.get('protein_sequence')
                
                if seq:
                    process_sequence(name, seq)
                else:
                    print(f"   ⚠️ Skipping item {name}: No sequence found.")
                    
        except json.JSONDecodeError:
            print("   ❌ Invalid JSON file.")
            return
            
    else:
        # FASTA MODE
        print("   ℹ️  Detected FASTA format.")
        with open(INPUT_FILE, 'r') as f:
            current_header = ""
            current_seq = []
            for line in f:
                line = line.strip()
                if line.startswith(">"):
                    if current_header: 
                        process_sequence(current_header.lstrip('>').split('|')[0], "".join(current_seq))
                    current_header = line
                    current_seq = []
                else:
                    current_seq.append(line)
            if current_header: 
                process_sequence(current_header.lstrip('>').split('|')[0], "".join(current_seq))

    # 3. SAVE
    print(f"\n💾 Saving {len(data_buffer)} records...")
    if data_buffer:
        df = pd.DataFrame(data_buffer)
        df.to_parquet(PARQUET_FILE, engine='pyarrow', index=False)
        print(f"🎉 SUCCESS! Protein Database ({len(data_buffer)} records) saved.")
    else:
        print("⚠️ No data processed. Check your JSON keys (expected 'sequence' or 'seq').")

if __name__ == "__main__":
    main()