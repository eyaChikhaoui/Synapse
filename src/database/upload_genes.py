import sys
import os
import logging
from pathlib import Path
from qdrant_client import QdrantClient
from qdrant_client.http import models

# Path Safety
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))

# Import DNA Encoder
try:
    from encoders.dna_encoder import DNAEncoder
except ImportError:
    print("❌ Could not import DNAEncoder")
    sys.exit(1)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("GeneIngestion")

COLLECTION_NAME = "synapse_genes" # <--- NEW COLLECTION
VECTOR_SIZE = 768
FASTA_FILE = BASE_DIR / "Backend" / "Data" / "human_genes.fasta"

def ingest_genes():
    client = QdrantClient(host="localhost", port=6333)
    
    # 1. Create Gene Collection
    client.recreate_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=models.VectorParams(size=VECTOR_SIZE, distance=models.Distance.COSINE)
    )
    logger.info(f"✅ Created collection: {COLLECTION_NAME}")

    # 2. Load Model
    encoder = DNAEncoder()
    logger.info("🧬 DNA Encoder Loaded.")

    # 3. Parse FASTA (Manual parsing to avoid heavy Biopython dependency if not needed)
    points = []
    current_header = ""
    current_seq = []
    
    # Limit for demo/MVP to avoid waiting 5 hours
    # Set to None to do ALL 30,000 genes
    LIMIT = 2000 
    count = 0

    if not FASTA_FILE.exists():
        logger.error("❌ FASTA file not found. Run fetch_genes.py first.")
        return

    logger.info("⚙️ Processing Genes...")
    
    with open(FASTA_FILE, 'r') as f:
        for line in f:
            line = line.strip()
            if line.startswith(">"):
                # Process previous entry
                if current_header and current_seq:
                    full_seq = "".join(current_seq)
                    if len(full_seq) < 2000: # Context window safety
                        try:
                            vec = encoder.get_vector(full_seq)
                            points.append(models.PointStruct(
                                id=count,
                                vector=vec.tolist(),
                                payload={"gene_id": current_header[1:], "sequence": full_seq, "type": "gene"}
                            ))
                            count += 1
                            if count % 100 == 0: print(f"   Processed {count} genes...")
                        except:
                            pass
                
                if count >= LIMIT: break
                current_header = line
                current_seq = []
            else:
                current_seq.append(line)

    # Upload
    if points:
        client.upsert(collection_name=COLLECTION_NAME, points=points)
        logger.info(f"🎉 Uploaded {len(points)} Human Genes to Qdrant!")

if __name__ == "__main__":
    ingest_genes()