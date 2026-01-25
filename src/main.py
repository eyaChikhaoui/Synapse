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