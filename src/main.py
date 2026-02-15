from flask import Flask, request, jsonify
from flask_cors import CORS
import sys
import os
import logging
import numpy as np
from pathlib import Path

# --- PATH SAFETY BOOTSTRAP ---
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))

# Initialize Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("SynapseCore")

# --- PRODUCTION IMPORTS ----
# We force these. If they fail, the app should crash (Fail Fast).
try:
    from encoders.dna_encoder import DNAEncoder
    from encoders.protein_encoder import ProteinEncoder
    from database.db_manager import VectorDB
except ImportError as e:
    logger.critical(f"❌ CRITICAL: Missing Core Module. {e}")
    sys.exit(1)

app = Flask(__name__)
CORS(app)

class SynapseOrchestrator:
    def __init__(self):
        logger.info(f"🚀 [Synapse] Initializing PRODUCTION Orchestrator (SOTA-768)...")
        
        # 1. Initialize DNA Engine
        try:
            self.dna_engine = DNAEncoder()
            logger.info("✅ DNA Engine Online.")
        except Exception as e:
            logger.critical(f"❌ DNA Engine Failed: {e}")
            self.dna_engine = None

        # 2. Initialize Protein Engine
        try:
            self.prot_engine = ProteinEncoder()
            logger.info("✅ Protein Engine Online.")
        except Exception as e:
            logger.critical(f"❌ Protein Engine Failed: {e}")
            self.prot_engine = None

        # 3. Initialize Database
        try:
            self.db = VectorDB()
            logger.info("✅ Database Connection Established.")
        except Exception as e:
            logger.critical(f"⚠️ DB Connection Failed: {e}")
            self.db = None

    def _cosine_similarity(self, vec_a, vec_b):
        """Helper: Calculates cosine similarity between two 1D vectors."""
        a = np.array(vec_a)
        b = np.array(vec_b)
        
        dot_product = np.dot(a, b)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        
        if norm_a == 0 or norm_b == 0:
            return 0.0
            
        return float(dot_product / (norm_a * norm_b))

    def search(self, sequence, mode="dna_to_protein", top_k=3):
        vector = None
        target_collection = ""

        if mode == "dna_to_protein":
            if not self.dna_engine: return [{"error": "DNA Engine Offline"}]
            try:
                vector = self.dna_engine.get_vector(sequence)
                target_collection = "synapse_proteins"
            except Exception as e:
                return [{"error": f"DNA Inference Failed: {str(e)}"}]

        elif mode == "protein_to_dna":
            if not self.prot_engine: return [{"error": "Protein Engine Offline"}]
            try:
                vector = self.prot_engine.get_vector(sequence)
                target_collection = "synapse_genes"
            except Exception as e:
                return [{"error": f"Protein Inference Failed: {str(e)}"}]
        
        else:
            return [{"error": f"Invalid Mode: {mode}"}]

        if vector is not None and self.db:
            try:
                vec_list = vector.tolist() if hasattr(vector, 'tolist') else vector
                return self.db.search_similar(vec_list, collection=target_collection, top_k=top_k)
            except Exception as e:
                return [{"error": f"DB Search Failed: {str(e)}"}]
        
        return [{"error": "Database not connected"}]

    def batch_search(self, sequences, mode="dna_to_protein", top_k=3):
        """
        Batch processing for high-throughput analysis (Feature #07).
        Takes a list of sequences and returns matches for each.
        """
        results = []
        target_collection = ""
        engine = None

        # 1. Select Engine
        if mode == "dna_to_protein":
            if not self.dna_engine: return {"error": "DNA Engine Offline"}
            engine = self.dna_engine
            target_collection = "synapse_proteins"
        elif mode == "protein_to_dna":
            if not self.prot_engine: return {"error": "Protein Engine Offline"}
            engine = self.prot_engine
            target_collection = "synapse_genes"
        else:
            return {"error": f"Invalid Mode: {mode}"}

        # 2. Loop Processing (Robustness over complexity for Hackathon)
        # Note: In a V2, we would modify encoders to accept batch inputs directly.
        for idx, seq in enumerate(sequences):
            try:
                if not seq:
                    results.append({"id": idx, "error": "Empty sequence"})
                    continue
                
                # Encode
                vector = engine.get_vector(seq)
                
                # Search
                if vector is not None and self.db:
                    vec_list = vector.tolist() if hasattr(vector, 'tolist') else vector
                    matches = self.db.search_similar(vec_list, collection=target_collection, top_k=top_k)
                    results.append({
                        "id": idx,
                        "input_snippet": seq[:15] + "...",
                        "matches": matches
                    })
                else:
                    results.append({"id": idx, "error": "Vectorization failed"})
                    
            except Exception as e:
                logger.error(f"Batch Error at index {idx}: {e}")
                results.append({"id": idx, "error": str(e)})

        return results

    def compare_variants(self, seq_wild, seq_mutant, modality="dna"):
        """Zero-Shot Variant Scoring (Deal Breaker #1)"""
        engine = self.dna_engine if modality == "dna" else self.prot_engine
        if not engine:
            return {"error": f"{modality.upper()} Engine Offline"}

        try:
            vec_a = engine.get_vector(seq_wild)
            vec_b = engine.get_vector(seq_mutant)

            score = self._cosine_similarity(vec_a, vec_b)
            
            impact = "Low Impact (Benign)"
            if score < 0.95: impact = "Moderate Shift"
            if score < 0.85: impact = "High Impact (Pathogenic Likely)"

            return {
                "similarity_score": round(score, 5),
                "impact_assessment": impact,
                "modality": modality
            }

        except Exception as e:
            logger.error(f"Comparison Error: {e}")
            return {"error": str(e)}

    def get_reward_score(self, dna_seq, protein_seq):
        """RL-Ready Reward API (Deal Breaker #2)"""
        if not self.dna_engine or not self.prot_engine:
            return {"error": "Engines Offline"}

        try:
            vec_dna = self.dna_engine.get_vector(dna_seq)
            vec_prot = self.prot_engine.get_vector(protein_seq)

            score = self._cosine_similarity(vec_dna, vec_prot)

            return {"reward": float(score)}

        except Exception as e:
            logger.error(f"Reward Calculation Error: {e}")
            return {"error": str(e)}


# Initialize Production Singleton
synapse = SynapseOrchestrator()

# --- API ROUTES ---

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({
        "status": "online", 
        "mode": "SOTA (768 dims)",
        "dna_engine": "active" if synapse.dna_engine else "offline",
        "prot_engine": "active" if synapse.prot_engine else "offline"
    })

@app.route('/api/search', methods=['POST'])
def search_route():
    data = request.get_json()
    seq = data.get('sequence', '')
    mode = data.get('mode', 'dna_to_protein')
    
    if not seq:
        return jsonify({"error": "No sequence provided"}), 400
        
    try:
        results = synapse.search(seq, mode=mode)
        return jsonify({"status": "success", "results": results})
    except Exception as e:
        logger.error(f"Search Route Error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/batch_search', methods=['POST'])
def batch_search_route():
    """
    Endpoint for Batch Processing (Feature #07).
    Expects: { "sequences": ["ATCG...", "GGG..."], "mode": "dna_to_protein" }
    """
    data = request.get_json()
    sequences = data.get('sequences', [])
    mode = data.get('mode', 'dna_to_protein')
    
    if not sequences or not isinstance(sequences, list):
        return jsonify({"error": "Requires 'sequences' list"}), 400
        
    try:
        # Calls the new batch logic
        results = synapse.batch_search(sequences, mode=mode)
        return jsonify({"status": "success", "count": len(results), "results": results})
    except Exception as e:
        logger.error(f"Batch Route Error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/compare', methods=['POST'])
def compare_route():
    """Endpoint for Variant Scoring"""
    data = request.get_json()
    seq_a = data.get('wild_type', '')
    seq_b = data.get('mutant', '')
    modality = data.get('modality', 'dna')

    if not seq_a or not seq_b:
        return jsonify({"error": "Both 'wild_type' and 'mutant' sequences are required"}), 400

    result = synapse.compare_variants(seq_a, seq_b, modality=modality)
    return jsonify(result)

@app.route('/api/reward', methods=['POST'])
def reward_route():
    """Endpoint for RL Agents"""
    data = request.get_json()
    dna = data.get('dna_sequence', '')
    prot = data.get('protein_sequence', '')

    if not dna or not prot:
        return jsonify({"error": "Requires 'dna_sequence' and 'protein_sequence'"}), 400

    result = synapse.get_reward_score(dna, prot)
    return jsonify(result)

if __name__ == '__main__':
    logger.info("🌍 Synapse Production System running on port 5000")
    app.run(debug=True, port=5000)