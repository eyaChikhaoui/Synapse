from flask import Flask, request, jsonify
from flask_cors import CORS
import sys
import os
import numpy as np

# إضافة المسارات
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# استيراد الأكواد الحقيقية من الفريق
try:
    from encoders.dna_encoder import DNAEncoder
    from encoders.protein_encoder import ProteinEncoder
    from database.db_manager import VectorDB
    # from database.mock_db import MockVectorDB # فكي التعليق إذا لم يعمل Docker
except ImportError as e:
    print(f"❌ Error importing modules: {e}")

app = Flask(__name__)
CORS(app)

# بناء الـ Orchestrator لربط الفريق
class SynapseOrchestrator:
    def __init__(self):
        print("🚀 [Synapse] Initializing Multimodal Orchestrator...")
        self.dna_engine = DNAEncoder()
        try:
            self.db = VectorDB()
            print("✅ [Synapse] Database Connection Established.")
        except Exception as e:
            print(f"⚠️ [Synapse] DB Connection Failed: {e}")
            self.db = None

    def find_protein_match(self, dna_sequence, top_k=3):
        # تحويل الـ DNA لمتجه (كود P1)
        vector = self.dna_engine.get_vector(dna_sequence)
        # البحث في القاعدة (كود P2)
        if self.db:
            return self.db.search_similar(vector.tolist(), top_k=top_k)
        return [{"error": "Database not connected"}]

# إنشاء نسخة من المحرك
synapse = SynapseOrchestrator()

# --- الروابط (Routes) للشخص الرابع P4 ---

@app.route('/api/search', methods=['POST'])
def search():
    data = request.get_json()
    dna = data.get('dna_sequence', '')
    
    if not dna:
        return jsonify({"error": "No DNA sequence"}), 400
        
    try:
        # تشغيل العملية الكاملة
        results = synapse.find_protein_match(dna)
        return jsonify({"status": "success", "results": results})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print("🌍 Synapse Server running on http://localhost:5000")
    app.run(debug=True, port=5000)