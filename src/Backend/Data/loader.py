import sys
import os
import logging
import pandas as pd
from pathlib import Path
from qdrant_client import QdrantClient
from qdrant_client.http import models

# --- CONFIGURATION ---
print("\n" + "="*60)
print("🚀 SYNAPSE: SMART PARQUET LOADER")
print("   Target: Qdrant Vector Database")
print("   Mode: SOTA Ingestion (768 Dimensions)")
print("="*60 + "\n")

# --- ROBUST PATH FINDING (Fixes the "File Not Found" errors) ---
current_file = Path(__file__).resolve()
# Walk up to find "Synapse-main" root
project_root = current_file.parent
while not (project_root.name == "Synapse-main" or str(project_root) == str(project_root.parent)):
    project_root = project_root.parent

DATA_DIR = project_root / "src" / "Backend" / "Data"

# 1. SMART PATH SELECTION (Prioritize SOTA files)
GENE_PARQUET = DATA_DIR / "human_genes_sota.parquet"
if not GENE_PARQUET.exists():
    GENE_PARQUET = DATA_DIR / "human_genes.parquet"

PROTEIN_PARQUET = DATA_DIR / "human_proteins_sota.parquet"
if not PROTEIN_PARQUET.exists():
    PROTEIN_PARQUET = DATA_DIR / "human_proteins.parquet"

# --- QDRANT SETUP ---
QDRANT_HOST = "localhost"
QDRANT_PORT = 6333
BATCH_SIZE = 250 

# --- LOGGING ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger("SynapseLoader")

def upload_collection(client, parquet_path, collection_name, vector_size):
    """
    Reads a Parquet file and uploads it to Qdrant.
    """
    if not parquet_path.exists():
        logger.warning(f"⚠️ File not found: {parquet_path}")
        logger.warning(f"   (Checked: {parquet_path})")
        return

    logger.info(f"📂 Loading {parquet_path.name}...")
    
    try:
        df = pd.read_parquet(parquet_path, engine='pyarrow')
    except Exception as e:
        logger.error(f"❌ Failed to read parquet: {e}")
        return

    total_records = len(df)
    
    # Validation Check
    if total_records > 0:
        sample_vec = df.iloc[0]['vector']
        actual_dim = len(sample_vec)
        if actual_dim != vector_size:
            logger.error(f"❌ DIMENSION MISMATCH! Qdrant expects {vector_size}, but file has {actual_dim}.")
            logger.error("👉 Please regenerate your Parquet files using the SOTA generator scripts.")
            return
        logger.info(f"   📊 Verified Dimensions: {actual_dim} (Matches Config)")

    logger.info(f"   📊 Found {total_records} records.")

    # 1. Reset Collection
    try:
        client.recreate_collection(
            collection_name=collection_name,
            vectors_config=models.VectorParams(
                size=vector_size, 
                distance=models.Distance.COSINE
            )
        )
        logger.info(f"   ♻️  Collection '{collection_name}' reset to {vector_size} dims.")
    except Exception as e:
        logger.error(f"❌ Qdrant Connection Failed: {e}")
        return

    # 2. Upload Loop
    points_buffer = []
    uploaded_count = 0

    print(f"   🚀 Uploading to {collection_name}...")

    for index, row in df.iterrows():
        try:
            vector = row['vector']
            
            point = models.PointStruct(
                id=int(index), 
                vector=vector.tolist() if hasattr(vector, 'tolist') else vector,
                payload=row['payload']
            )
            points_buffer.append(point)

            if len(points_buffer) >= BATCH_SIZE:
                client.upsert(
                    collection_name=collection_name,
                    points=points_buffer
                )
                uploaded_count += len(points_buffer)
                print(f"\r      ✅ Indexed: {uploaded_count}/{total_records}", end="", flush=True)
                points_buffer = []

        except Exception as e:
            continue

    # Final batch
    if points_buffer:
        client.upsert(
            collection_name=collection_name,
            points=points_buffer
        )
        uploaded_count += len(points_buffer)
    
    print(f"\r      ✅ Indexed: {uploaded_count}/{total_records} (Complete)   \n")


def main():
    try:
        client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
        logger.info("🔌 Connected to Qdrant.")
    except Exception as e:
        logger.critical(f"❌ Could not connect to Qdrant: {e}")
        sys.exit(1)

    # --- 1. UPLOAD GENES ---
    upload_collection(
        client=client, 
        parquet_path=GENE_PARQUET, 
        collection_name="synapse_genes", 
        vector_size=768 
    )

    # --- 2. UPLOAD PROTEINS ---
    upload_collection(
        client=client, 
        parquet_path=PROTEIN_PARQUET, 
        collection_name="synapse_proteins", 
        vector_size=768 
    )

    print("🎉 SOTA DATABASE LIVE! You are ready to search.")

if __name__ == "__main__":
    main()