import requests
import gzip
import shutil
import os
import sys
from pathlib import Path

# --- CONFIGURATION ---
BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_FILE = BASE_DIR / "Backend" / "Data" / "human_genes.fasta"

# NCBI Consensus Coding Sequence (CCDS) - The Gold Standard for Human Genes
CCDS_URL = "https://ftp.ncbi.nlm.nih.gov/pub/CCDS/current_human/CCDS_nucleotide.current.fna.gz"

def fetch_human_genes():
    """
    Downloads the official Human Consensus Coding Sequence (CCDS) dataset.
    This contains ~34,000 high-confidence gene sequences.
    """
    print("🚀 Starting High-Performance Gene Download (CCDS)...")
    
    zip_path = str(OUTPUT_FILE) + ".gz"
    
    # 1. Download
    try:
        print("🌍 Downloading from NCBI FTP...")
        with requests.get(CCDS_URL, stream=True) as r:
            r.raise_for_status()
            with open(zip_path, 'wb') as f:
                shutil.copyfileobj(r.raw, f)
        print("✅ Download complete.")
    except Exception as e:
        print(f"❌ Download failed: {e}")
        return

    # 2. Extract
    print("📦 Extracting FASTA sequences...")
    try:
        os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
        with gzip.open(zip_path, 'rb') as f_in:
            with open(OUTPUT_FILE, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        
        # Cleanup zip
        os.remove(zip_path)
        print(f"✅ Success! Human Genes saved to:\n   📂 {OUTPUT_FILE}")
        
    except Exception as e:
        print(f"❌ Extraction failed: {e}")

if __name__ == "__main__":
    fetch_human_genes()