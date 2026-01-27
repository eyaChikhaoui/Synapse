from flask import Flask, request, jsonify
from flask_cors import CORS
import sys
import os
import logging
from pathlib import Path

# --- PATH SAFETY BOOTSTRAP ---
# Calculates the 'src' directory path regardless of where the script is run
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))

# Initialize Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("SynapseCore")

# Import Modules
try:
    from encoders.dna_encoder import DNAEncoder
    from encoders.protein_encoder import ProteinEncoder
    from database.db_manager import VectorDB
except ImportError as e:
    logger.critical(f"❌ Critical Import Error: {e}")
    logger.critical("   Ensure you are running from the project root or src folder.")
    sys.exit(1)

app = Flask(__name__)
CORS(app)

class SynapseOrchestrator:
    def __init__(self):
        logger.info("🚀 [Synapse] Initializing Dual-Core Orchestrator...")
        
        # 1. Initialize DNA Engine
        try:
            self.dna_engine = DNAEncoder()
            logger.info("✅ DNA Engine Online (NTv3-650M).")
        except Exception as e:
            logger.error(f"❌ DNA Engine Failed: {e}")
            self.dna_engine = None

        # 2. Initialize Protein Engine
        try:
            self.prot_engine = ProteinEncoder()
            logger.info("✅ Protein Engine Online (ESM2-650M).")
        except Exception as e:
            logger.error(f"❌ Protein Engine Failed: {e}")
            self.prot_engine = None

        # 3. Initialize Database
        try:
            self.db = VectorDB()
            logger.info("✅ Database Connection Established.")
        except Exception as e:
            logger.warning(f"⚠️ DB Connection Failed: {e}")
            self.db = None

    def search(self, sequence, mode="dna_to_protein", top_k=3):
        """
        Orchestrates the search based on the input mode.
        """
        vector = None
        target_collection = ""

        # MODE A: DNA -> Find Proteins
        if mode == "dna_to_protein":
            if not self.dna_engine: return [{"error": "DNA Engine Offline"}]
            try:
                # Encode DNA
                vector = self.dna_engine.get_vector(sequence)
                # Search in Protein DB
                target_collection = "synapse_v1" 
            except Exception as e:
                return [{"error": f"DNA Inference Failed: {str(e)}"}]

        # MODE B: Protein -> Find Genes
        elif mode == "protein_to_dna":
            if not self.prot_engine: return [{"error": "Protein Engine Offline"}]
            try:
                # Encode Protein
                vector = self.prot_engine.get_vector(sequence)
                # Search in Gene DB
                target_collection = "synapse_genes"
            except Exception as e:
                return [{"error": f"Protein Inference Failed: {str(e)}"}]
        
        else:
            return [{"error": f"Invalid Mode: {mode}"}]

        # Perform the Search in Qdrant
        if self.db:
            # We assume db_manager.py was updated to accept 'collection' arg
            # If not, it defaults to synapse_v1, which is fine for MVP but check db_manager code
            if hasattr(self.db, 'search_similar'):
                 # Try passing collection if supported, else fallback will use default
                try:
                    return self.db.search_similar(vector.tolist(), collection=target_collection, top_k=top_k)
                except TypeError:
                    # Fallback if db_manager wasn't updated to take 'collection'
                    logger.warning("⚠️ DB Manager doesn't support dynamic collections yet. Searching default.")
                    return self.db.search_similar(vector.tolist(), top_k=top_k)
        
        return [{"error": "Database not connected"}]

# Initialize Singleton
synapse = SynapseOrchestrator()

# --- API ROUTES ---

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({
        "status": "online", 
        "dna_engine": "active" if synapse.dna_engine else "offline",
        "prot_engine": "active" if synapse.prot_engine else "offline"
    })

@app.route('/api/search', methods=['POST'])
def search_route():
    data = request.get_json()
    seq = data.get('sequence', '')
    mode = data.get('mode', 'dna_to_protein') # Default to standard flow
    
    if not seq:
        return jsonify({"error": "No sequence provided"}), 400
        
    try:
        results = synapse.search(seq, mode=mode)
        return jsonify({"status": "success", "results": results})
    except Exception as e:
        logger.error(f"Search Route Error: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    logger.info("🌍 Synapse Dual-Core Inference System running on port 5000")
    app.run(debug=True, port=5000)