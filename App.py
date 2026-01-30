import os
from flask import Flask, render_template, request, flash, redirect, url_for
import time
from difflib import SequenceMatcher # <--- Standard Library for comparing text

# --- 1. SETUP & PATHS ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR = os.path.join(BASE_DIR, 'templates')
STATIC_DIR = os.path.join(BASE_DIR, 'static')

app = Flask(__name__, template_folder=TEMPLATE_DIR, static_folder=STATIC_DIR)
app.secret_key = 'synapse_hackathon_key'

# --- 2. THE "TRUTH" DATA ---
# This acts as our "Wild Type" (Perfect) Reference.
# We compare user input to this to calculate the real mutation score.
REFERENCE_SEQUENCE = "ATGCGTACGTTAGCTAGCTAGCTATGCGTACGTTAGCTAGCTAGCT"

# --- 3. HELPER FUNCTIONS ---
def calculate_similarity(seq1, seq2):
    """Calculates how similar two DNA sequences are (0.0 to 1.0)"""
    return SequenceMatcher(None, seq1, seq2).ratio()

def get_clinical_significance(score):
    """Determines diagnosis based on the score"""
    if score >= 0.99:
        return "Benign (No Mutation)", "text-green-600", "bg-green-100 border-green-200"
    elif score >= 0.80:
        return "Likely Benign", "text-blue-600", "bg-blue-100 border-blue-200"
    elif score >= 0.50:
        return "Variant of Uncertain Significance", "text-yellow-600", "bg-yellow-100 border-yellow-200"
    else:
        return "Pathogenic (High Mutation Load)", "text-red-600", "bg-red-100 border-red-200"

# --- 4. HARDCODED 3D MODELS (OFFLINE) ---
# I've added a second structure so the 3D view changes based on the score!

# Structure A: Healthy / Standard Helix (For High Scores)
PDB_HEALTHY = """
HEADER    ALANINE HELIX
ATOM      1  N   ALA A   1       0.000   0.000   0.000  1.00  0.00           N
ATOM      2  CA  ALA A   1       0.000   0.000   1.426  1.00  0.00           C
ATOM      3  C   ALA A   1       1.278   0.589   1.956  1.00  0.00           C
ATOM      4  O   ALA A   1       1.357   1.808   2.083  1.00  0.00           O
ATOM      5  CB  ALA A   1      -1.255   0.771   1.968  1.00  0.00           C
ATOM      6  N   ALA A   2       2.277  -0.276   2.257  1.00  0.00           N
ATOM      7  CA  ALA A   2       3.585   0.176   2.756  1.00  0.00           C
ATOM      8  C   ALA A   2       4.150   1.314   1.895  1.00  0.00           C
ATOM      9  O   ALA A   2       5.087   1.085   1.127  1.00  0.00           O
ATOM     10  CB  ALA A   2       4.526  -1.031   2.822  1.00  0.00           C
ATOM     11  N   ALA A   3       3.567   2.531   2.043  1.00  0.00           N
ATOM     12  CA  ALA A   3       3.987   3.738   1.332  1.00  0.00           C
ATOM     13  C   ALA A   3       5.474   3.999   1.579  1.00  0.00           C
ATOM     14  O   ALA A   3       6.332   3.816   0.707  1.00  0.00           O
ATOM     15  CB  ALA A   3       3.141   4.945   1.766  1.00  0.00           C
"""

# Structure B: "Mutated" / Unfolded (For Low Scores)
# This is a slightly different arrangement of atoms to visually show a difference
PDB_MUTATED = """
HEADER    MUTANT STRUCTURE
ATOM      1  N   PRO A   1       0.000   0.000   0.000  1.00  0.00           N
ATOM      2  CA  PRO A   1       1.458   0.000   0.000  1.00  0.00           C
ATOM      3  C   PRO A   1       2.059   1.408   0.000  1.00  0.00           C
ATOM      4  O   PRO A   1       1.503   2.399  -0.499  1.00  0.00           O
ATOM      5  CB  PRO A   1       2.029  -0.784  -1.206  1.00  0.00           C
ATOM      6  CG  PRO A   1       0.997  -0.456  -2.235  1.00  0.00           C
ATOM      7  CD  PRO A   1      -0.344  -0.640  -1.589  1.00  0.00           C
ATOM      8  N   GLY A   2       3.197   1.488   0.575  1.00  0.00           N
ATOM      9  CA  GLY A   2       3.876   2.768   0.655  1.00  0.00           C
ATOM     10  C   GLY A   2       4.246   3.332  -0.706  1.00  0.00           C
ATOM     11  O   GLY A   2       5.309   3.024  -1.248  1.00  0.00           O
"""

# --- 5. ROUTES ---

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/about')
def about():
    # Keep your team data here (abbreviated for clarity, add your full list back)
    team = [
        {"name": "Eya Chikhaoui", "role": "Bioinformatics Lead", "icon": "fa-dna", "color": "blue"},
        {"name": "Mouhamed Gharsallah", "role": "Backend Lead", "icon": "fa-server", "color": "green"},
        {"name": "Balkis Mahjoubi", "role": "AI Architect", "icon": "fa-brain", "color": "purple"},
        {"name": "Aziz Mazghouni", "role": "Frontend Lead", "icon": "fa-laptop-code", "color": "orange"}
    ]
    return render_template('about.html', team=team)

@app.route('/services')
def services():
    # Keep your services data here (abbreviated for clarity)
    services = [
         {"title": "Genomic Alignment", "description": "High-speed FASTA processing.", "icon": "fa-dna", "color": "blue"},
         {"title": "Structure Prediction", "description": "Real-time 3D protein folding.", "icon": "fa-cube", "color": "purple"},
         {"title": "Variant Classification", "description": "AI-driven clinical scoring.", "icon": "fa-stethoscope", "color": "green"},
    ]
    return render_template('services.html', services=services)

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/send_message', methods=['POST'])
def send_message():
    flash("Message sent successfully!")
    return redirect(url_for('contact'))

# --- 6. THE NEW INTELLIGENT ANALYZE ROUTE ---
@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        time.sleep(1.0)
        
        # 1. Get User Input
        user_dna = request.form.get('dna_sequence', '').strip().upper()
        
        # 2. REAL MATH: Calculate Similarity Score
        # We compare what the user typed vs the Reference Sequence
        similarity = calculate_similarity(user_dna, REFERENCE_SEQUENCE)
        
        # Round to 3 decimal places (e.g., 0.984)
        score_display = f"{similarity:.3f}"
        
        # 3. REAL LOGIC: Diagnosis based on score
        sig_text, sig_color, sig_bg = get_clinical_significance(similarity)
        
        # 4. REAL VISUALS: Choose 3D model based on health
        if similarity > 0.8:
            pdb_data = PDB_HEALTHY
            model_name = "Hemoglobin Beta (Stable)"
        else:
            pdb_data = PDB_MUTATED
            model_name = "Mutated Variant (Unstable)"

        # 5. Build the object to send to HTML
        molecule = {
            "name": model_name,
            "score": score_display,
            "significance": sig_text,
            "color_class": sig_color, # Pass dynamic colors
            "bg_class": sig_bg
        }

        return render_template('result_card.html', molecule=molecule, pdb_data=pdb_data)
        
    except Exception as e:
        print(f"Error: {e}")
        return f"<div class='text-red-500'>Error: {e}</div>"

if __name__ == '__main__':
    app.run(debug=True, port=8000)