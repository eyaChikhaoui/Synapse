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
import sys
import os

# Ensure we can import from local folders
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from encoders.dna_encoder import DNAEncoder
from encoders.protein_encoder import ProteinEncoder
from database.db_manager import VectorDB
# from database.mock_db import MockVectorDB  # Un-comment this line if Docker is NOT running

class SynapseOrchestrator:
    """
    The Central AI Brain of Synapse.
    Integrates Person 1's Models with Person 2's Database.
    """
    def __init__(self):
        print("🚀 [Synapse] Initializing Multimodal Orchestrator...")
        
        # --- PERSON 1: LOADING ENCODERS ---
        # These models turn text into 768-dimensional vectors
        self.dna_engine = DNAEncoder()
        self.protein_engine = ProteinEncoder()
        print("✅ [Synapse] Encoders Online. Shared Latent Space (768) active.")

        # --- PERSON 2: LOADING DATABASE ---
        # Connects to the Qdrant Docker container
        try:
            self.db = VectorDB() # Expects Docker at localhost:6333
            # self.db = MockVectorDB() # Use this fallback if Docker is down
            print("✅ [Synapse] Database Connection Established.")
        except Exception as e:
            print(f"⚠️ [Synapse] DB Connection Failed: {e}")
            self.db = None

    def process_sequence(self, sequence: str, mode: str = "dna"):
        """
        Routes a sequence to the correct encoder and returns the vector.
        """
        mode = mode.lower()
        if mode == "dna":
            return self.dna_engine.get_vector(sequence)
        elif mode.startswith("prot"):
            return self.protein_engine.get_vector(sequence)
        else:
            raise ValueError("Invalid mode. Choose 'dna' or 'protein'.")

    def find_protein_match(self, dna_sequence: str, top_k: int = 3):
        """
        End-to-End Pipeline:
        1. DNA Text -> Vector (Person 1)
        2. Vector -> Protein Search (Person 2)
        """
        # Step 1: Encode
        print(f"\n🧬 Encoding DNA Sequence: {dna_sequence[:10]}...")
        vector = self.process_sequence(dna_sequence, mode="dna")
        
        # Step 2: Search
        if self.db:
            print(f"🔎 Searching Qdrant for nearest protein neighbors...")
            # We convert numpy array to list for the DB
            results = self.db.search_similar(vector.tolist(), top_k=top_k)
            return results
        else:
            return [{"error": "Database not connected"}]

if __name__ == "__main__":
    # --- SYNAPSE INTEGRATION TEST ---
    synapse = SynapseOrchestrator()
    
    # 1. Define a Query (Simulating a user searching for a gene)
    target_dna = "ATGCGTACGTTAG"
    
    # 2. Run the Pipeline
    matches = synapse.find_protein_match(target_dna)
    
    # 3. Report Results
    print("\n--- 🏆 FINAL SYSTEM REPORT ---")
    print(f"Input DNA: {target_dna}")
    print(f"Matches Found: {len(matches)}")
    
    for i, match in enumerate(matches):
        meta = match.get('metadata', {})
        score = match.get('score', 0.0)
        name = meta.get('protein_name', 'Unknown')
        print(f"   {i+1}. {name} (Confidence: {score:.4f})")
>>>>>>> 72f6233b6c18d5c0c844a9fd9ea1160810c80b74
