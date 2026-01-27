import sys
import os
import json
import logging
from pathlib import Path
from qdrant_client import QdrantClient
from qdrant_client.http import models

# --- PATH SAFETY SETUP ---
# Ensure we can import from src folders
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))

# Import your REAL AI Encoder
try:
    from encoders.protein_encoder import ProteinEncoder
except ImportError as e:
    print(f"❌ Could not import ProteinEncoder: {e}")
    sys.exit(1)

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("IngestionPipeline")

# --- CONFIGURATION ---
COLLECTION_NAME = "synapse_v1"
VECTOR_SIZE = 768  # Must match the Output of your Projection Layer
JSON_DATA_PATH = BASE_DIR / "Backend" / "Data" / "proteins.json"

def ingest_data():
    logger.info("🚀 Starting Vector Ingestion Pipeline...")

    # 1. Initialize Qdrant
    # Assumes Qdrant is running via Docker on localhost:6333
    client = QdrantClient(host="localhost", port=6333)

    # 2. Reset Collection (Clean Slate)
    # We recreate it to ensure the dimensions (768) are correct
    client.recreate_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=models.VectorParams(
            size=VECTOR_SIZE, 
            distance=models.Distance.COSINE
        )
    )
    logger.info(f"✅ Collection '{COLLECTION_NAME}' reset with size {VECTOR_SIZE}.")

    # 3. Initialize the AI Model (Heavy Load)
    logger.info("🧬 Loading SOTA Protein Encoder (ESM-2 650M)... This may take a minute.")
    encoder = ProteinEncoder() 
    logger.info("✅ Encoder Loaded.")

    # 4. Load Raw Data
    if not JSON_DATA_PATH.exists():
        logger.error(f"❌ Data file not found at {JSON_DATA_PATH}")
        return

    with open(JSON_DATA_PATH, 'r') as f:
        proteins = json.load(f)

    # 5. The Loop: Text -> AI -> Vector -> DB
    points = []
    logger.info(f"⚙️ Processing {len(proteins)} proteins...")

    for i, prot in enumerate(proteins):
        seq = prot.get("sequence", "")
        name = prot.get("name", "Unknown")
        
        if len(seq) < 5: 
            logger.warning(f"⚠️ Skipping {name}: Sequence too short.")
            continue

        try:
            # A. Generate Vector (The Magic Step)
            vector_numpy = encoder.get_vector(seq)
            vector_list = vector_numpy.tolist()

            # B. Prepare Qdrant Point
            # We store the metadata (payload) so we can read it back later
            point = models.PointStruct(
                id=i,  # Simple integer ID
                vector=vector_list,
                payload={
                    "protein_name": name,
                    "function": prot.get("function", "Unknown"),
                    "sequence": seq
                }
            )
            points.append(point)
            print(f"   Converted: {name}")

        except Exception as e:
            logger.error(f"❌ Failed to encode {name}: {e}")

    # 6. Bulk Upload
    if points:
        client.upsert(
            collection_name=COLLECTION_NAME,
            points=points
        )
        logger.info(f"🎉 Successfully uploaded {len(points)} vectors to Qdrant!")
    else:
        logger.warning("⚠️ No vectors were generated.")

if __name__ == "__main__":
    ingest_data()