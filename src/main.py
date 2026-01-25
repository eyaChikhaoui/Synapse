<<<<<<< HEAD
from flask import Flask, request, jsonify
from flask_cors import CORS
import sys
import os

# إضافة المسار الحالي لكي يرى بايثون المجلدات
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# استدعاء ملفات أصدقائك (التي صنعتها لتوك)
from encoders.mock_encoder import encode_dna
from database.mock_db import search_similar

app = Flask(__name__)
CORS(app)

@app.route('/api/search', methods=['POST'])
def search():
    data = request.get_json()
    dna = data.get('dna_sequence', '')
    
    if not dna:
        return jsonify({"error": "No DNA sequence"}), 400
        
    # تشغيل كود P1
    vector = encode_dna(dna)
    
    # تشغيل كود P2
    results = search_similar(vector)
    
    return jsonify({"results": results})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
=======
import numpy as np
from encoders.dna_encoder import DNAEncoder
from encoders.protein_encoder import ProteinEncoder

class SynapseOrchestrator:
    """
    The Central AI Brain of Synapse.
    Managed by Person 1 (ML Lead).
    """
    def __init__(self):
        print("🚀 [Synapse] Initializing Multimodal Orchestrator...")
        self.dna_engine = DNAEncoder()
        self.protein_engine = ProteinEncoder()
        print("✅ [Synapse] All systems online. Shared Latent Space (768) active.")

    def process_sequence(self, sequence: str, mode: str = "dna"):
        """
        Routes a sequence to the correct encoder and returns the 768-dim vector.
        """
        mode = mode.lower()
        if mode == "dna":
            return self.dna_engine.get_vector(sequence)
        elif mode == "protein" or mode == "prot":
            return self.protein_engine.get_vector(sequence)
        else:
            raise ValueError("Invalid mode. Choose 'dna' or 'protein'.")

if __name__ == "__main__":
    # --- DAY 1 FINAL DEMO ---
    synapse = SynapseOrchestrator()
    
    # 1. Process DNA
    dna_seq = "ATGCGTACGTTAG"
    dna_vector = synapse.process_sequence(dna_seq, mode="dna")
    
    # 2. Process Protein
    prot_seq = "GIVEQCCTSICSLYQLENYCN"
    prot_vector = synapse.process_sequence(prot_seq, mode="protein")
    
    print("\n--- DAY 1 FINAL REPORT ---")
    print(f"🔹 DNA Input: {dna_seq} -> Vector({len(dna_vector)})")
    print(f"🔹 Protein Input: {prot_seq} -> Vector({len(prot_vector)})")
    
    # Cross-check
    if len(dna_vector) == len(prot_vector) == 768:
        print("\n🏆 STATUS: MISSION ACCOMPLISHED.")
        print("The Shared Latent Space is unified at 768 dimensions.")
    else:
        print("\n⚠️ STATUS: CRITICAL FAILURE. Dimension desync detected.")
>>>>>>> 3b31a8e (feat: implement shared latent space (768-dim) and real encoders)
