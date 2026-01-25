# --- FILE: src/main.py ---
from flask import Flask, request, jsonify
from flask_cors import CORS
import sys
import os
import numpy as np

# Add src to path so we can import modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    # Import the Worker Classes
    from encoders.dna_encoder import DNAEncoder
    from encoders.protein_encoder import ProteinEncoder
    from database.db_manager import VectorDB
except ImportError as e:
    print(f"❌ Error importing modules: {e}")

app = Flask(__name__)
CORS(app)

class SynapseOrchestrator:
    def __init__(self):
        print("🚀 [Synapse] Initializing Multimodal Orchestrator...")
        # Initialize the AI Model
        self.dna_engine = DNAEncoder()
        
        # Initialize the Database
        try:
            self.db = VectorDB()
            print("✅ [Synapse] Database Connection Established.")
        except Exception as e:
            print(f"⚠️ [Synapse] DB Connection Failed: {e}")
            self.db = None

    def find_protein_match(self, dna_sequence, top_k=3):
        # Step 1: Convert DNA to Vector using the Encoder
        vector = self.dna_engine.get_vector(dna_sequence)
        
        # Step 2: Search in Database
        if self.db:
            return self.db.search_similar(vector.tolist(), top_k=top_k)
        return [{"error": "Database not connected"}]

# Initialize the System
synapse = SynapseOrchestrator()

# --- API ROUTES ---

@app.route('/api/search', methods=['POST'])
def search():
    data = request.get_json()
    dna = data.get('dna_sequence', '')
    
    if not dna:
        return jsonify({"error": "No DNA sequence"}), 400
        
    try:
        # Run the search
        results = synapse.find_protein_match(dna)
        return jsonify({"status": "success", "results": results})
    except Exception as e:
        print(f"❌ Error during search: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print("🌍 Synapse Server running on http://localhost:5000")
    app.run(debug=True, port=5000)