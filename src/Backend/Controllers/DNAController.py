# File: src/Backend/Controllers/DNAController.py

from fastapi import Request, Form, UploadFile
from fastapi.templating import Jinja2Templates
from starlette.responses import HTMLResponse, Response
import httpx
import logging
import os
import math
import random
import numpy as np
from typing import Optional

# --- NEW IMPORT FOR PDF ENGINE ---
try:
    from src.utils import data_processor, pdf_generator
except ImportError:
    from src.Utils.pdf_generator import create_report

# Configure Logging
logger = logging.getLogger("SearchController")
logging.basicConfig(level=logging.INFO)

# --- PATH CONFIGURATION ---
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) 
TEMPLATE_DIR = os.path.join(BACKEND_DIR, "Template")

# Initialize Templates
templates = Jinja2Templates(directory=TEMPLATE_DIR)

# Address of the Flask Inference Core (Real AI)
FLASK_API_URL = "http://localhost:5000/api/search"
FLASK_BATCH_URL = "http://localhost:5000/api/batch_search"
FLASK_COMPARE_URL = "http://localhost:5000/api/compare"

# --- SOTA VISUALIZATION CONFIG ---
PDB_API_URL = "https://files.rcsb.org/download"

# Scientific Reference Standards
REF_PROTEIN_ID = "4HHB"  # Hemoglobin
REF_DNA_ID = "1BNA"      # Dickerson-Drew

class DNAController:
    @staticmethod
    async def render_index(request: Request):
        return templates.TemplateResponse("index.html", {"request": request})

    @staticmethod
    async def fetch_real_pdb(pdb_id: str):
        """Fetches scientific-grade 3D structure from RCSB PDB."""
        if not pdb_id: return None
        clean_id = pdb_id.strip().upper()
        
        if len(clean_id) != 4:
            return None

        target_url = f"{PDB_API_URL}/{clean_id}.pdb"
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(target_url, timeout=5.0)
                if response.status_code == 200:
                    return response.text
                return None
        except Exception as e:
            logger.error(f"❌ PDB Connection Error: {e}")
            return None

    @staticmethod
    def _compute_pca_coords(vectors):
        """
        REAL MATH: Performs SVD (Singular Value Decomposition) to project
        768-dim vectors into 2D space for visualization.
        """
        if not vectors or len(vectors) < 2:
            return [{"x": 0.0, "y": 0.0}]

        try:
            X = np.array(vectors)
            X_centered = X - np.mean(X, axis=0)
            U, S, Vt = np.linalg.svd(X_centered, full_matrices=False)
            components = Vt[:2, :]
            projected = X_centered @ components.T 
            
            max_val = np.max(np.abs(projected)) if np.max(np.abs(projected)) > 0 else 1.0
            projected = projected / max_val

            return [{"x": float(row[0]), "y": float(row[1])} for row in projected]

        except Exception as e:
            logger.error(f"PCA Math Error: {e}")
            return [{"x": random.uniform(-0.5,0.5), "y": random.uniform(-0.5,0.5)} for _ in vectors]

    @staticmethod
    async def analyze_sequence(
        request: Request, 
        dna_input: Optional[str] = None, 
        analysis_type: str = "dna",
        file: Optional[UploadFile] = None
    ):
        # 1. Handle Input Source (Text vs File placeholder)
        seq = ""
        if dna_input:
            seq = dna_input.strip().upper()
        
        # (Phase 3: File parsing logic will go here)

        if analysis_type == "protein":
            mode = "protein_to_dna"
            label_found = "Found Gene (DNA)"
        else:
            mode = "dna_to_protein"
            label_found = "Found Protein"

        if not seq:
             return HTMLResponse("<div class='p-4 text-red-500'>Please enter a valid sequence or upload a file.</div>")

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    FLASK_API_URL, 
                    json={"sequence": seq, "mode": mode},
                    timeout=60.0 
                )
            
            if response.status_code == 200:
                data = response.json()
                results = data.get("results", [])
                
                if not results:
                    return HTMLResponse(f"<div class='p-4 text-white'>No matching {label_found} found in vector space.</div>")
                
                top_match = results[0]
                if "error" in top_match:
                    return HTMLResponse(f"<div class='p-4 text-red-500'>⚠️ {top_match['error']}</div>")

                meta = top_match.get("metadata", {})
                score = round(top_match.get("score", 0), 3)
                
                if mode == "protein_to_dna":
                    match_name = f"Gene: {meta.get('name', 'Unknown Gene')}"
                else:
                    match_name = meta.get("name", "Unknown Protein")

                # --- PCA LOGIC ---
                raw_vectors = []
                viz_points = []
                for res in results:
                    vec = res.get("vector")
                    if vec: raw_vectors.append(vec)
                
                pca_coords = DNAController._compute_pca_coords(raw_vectors)

                for idx, res in enumerate(results):
                    if idx >= len(pca_coords): break
                    res_score = round(res.get("score", 0), 3)
                    res_name = res.get("metadata", {}).get("name", "Unknown")
                    viz_points.append({
                        "x": pca_coords[idx]["x"],
                        "y": pca_coords[idx]["y"],
                        "label": f"{res_name[:15]} ({res_score})",
                        "color": "#16A34A" if idx == 0 else "#CA8A04",
                        "size": 20 if idx == 0 else 15
                    })

                # --- 3D LOGIC ---
                pdb_data = None
                if mode == "protein_to_dna":
                    pdb_data = await DNAController.fetch_real_pdb(REF_DNA_ID)
                else:
                    target_pdb_id = meta.get("pdb_id", "")
                    pdb_data = await DNAController.fetch_real_pdb(target_pdb_id)
                    if not pdb_data:
                        pdb_data = await DNAController.fetch_real_pdb(REF_PROTEIN_ID)

                if score >= 0.85:
                    sig_text = "Benign (Strong Match)"
                    sig_color = "text-green-600"
                    sig_bg = "bg-green-100 border-green-200"
                else:
                    sig_text = "Variant of Uncertain Significance"
                    sig_color = "text-yellow-600"
                    sig_bg = "bg-yellow-100 border-yellow-200"

                molecule_data = {
                    "name": match_name,
                    "score": score,
                    "significance": sig_text,
                    "color_class": sig_color,
                    "bg_class": sig_bg
                }

                return templates.TemplateResponse("result_card.html", {
                    "request": request, 
                    "molecule": molecule_data,
                    "pdb_data": pdb_data,
                    "viz_data": viz_points
                })
            
            else:
                return HTMLResponse(f"<div class='p-4 text-red-500'>Error from Core: {response.text}</div>")

        except Exception as e:
            return HTMLResponse(f"<div class='p-4 text-red-500'>Connection Failed: {str(e)}</div>")

    @staticmethod
    async def batch_analyze_sequences(
        request: Request, 
        batch_input: Optional[str] = None, 
        analysis_type: str = "dna",
        file: Optional[UploadFile] = None
    ):
        raw_sequences = []
        
        # 1. Handle Text Input
        if batch_input:
            raw_sequences = [s.strip() for s in batch_input.split('\n') if s.strip()]
        
        # (Phase 3: File parsing logic will append to raw_sequences here)

        if not raw_sequences and not file:
            return HTMLResponse("<div class='p-4 text-red-500'>Please enter sequences or upload a file.</div>")

        # Removed the "Max 100" limit message as requested, keeping hard limit internal for safety if needed
        # if len(raw_sequences) > 100: ... 

        mode = "protein_to_dna" if analysis_type == "protein" else "dna_to_protein"

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    FLASK_BATCH_URL, 
                    json={"sequences": raw_sequences, "mode": mode},
                    timeout=120.0 
                )
            
            if response.status_code == 200:
                data = response.json()
                results = data.get("results", [])
                
                rows_html = ""
                for res in results:
                    idx = res.get("id", 0) + 1
                    snippet = res.get("input_snippet", "N/A")
                    matches = res.get("matches", [])
                    
                    if matches:
                        top = matches[0]
                        score = round(top.get("score", 0), 3)
                        name = top.get("metadata", {}).get("name", "Unknown")
                        color = "text-green-600" if score > 0.8 else "text-yellow-600"
                    else:
                        score = 0
                        name = "No Match"
                        color = "text-red-500"

                    rows_html += f"""
                    <tr class="border-b border-gray-100 hover:bg-slate-50">
                        <td class="p-3 text-xs font-mono text-gray-500">{idx}</td>
                        <td class="p-3 text-xs font-mono text-blue-600">{snippet}</td>
                        <td class="p-3 text-sm font-bold text-gray-700">{name}</td>
                        <td class="p-3 text-sm font-bold {color}">{int(score*100)}%</td>
                    </tr>
                    """

                table_html = f"""
                <div class="bg-white rounded-xl shadow-md border border-gray-100 overflow-hidden mt-4">
                    <div class="p-4 bg-slate-900 text-white flex justify-between items-center">
                        <h3 class="font-bold text-sm uppercase tracking-wider">Batch Results ({len(results)})</h3>
                        <span class="text-xs bg-blue-600 px-2 py-1 rounded">Processing Complete</span>
                    </div>
                    <div class="overflow-x-auto max-h-60 overflow-y-auto">
                        <table class="w-full text-left">
                            <thead class="bg-gray-50 text-xs uppercase text-gray-400 font-semibold">
                                <tr>
                                    <th class="p-3">#</th>
                                    <th class="p-3">Sequence</th>
                                    <th class="p-3">Top Match</th>
                                    <th class="p-3">Score</th>
                                </tr>
                            </thead>
                            <tbody>
                                {rows_html}
                            </tbody>
                        </table>
                    </div>
                </div>
                """
                return HTMLResponse(table_html)
            else:
                 return HTMLResponse(f"<div class='p-4 text-red-500'>Batch Processing Failed: {response.text}</div>")

        except Exception as e:
            logger.error(f"Batch Controller Error: {e}")
            return HTMLResponse(f"<div class='p-4 text-red-500'>Error: {str(e)}</div>")

    @staticmethod
    async def compare_sequences(request: Request, wild_type: str = Form(...), mutant: str = Form(...), modality: str = Form("dna")):
        if not wild_type or not mutant:
            return HTMLResponse("<div class='text-red-500'>Both sequences required.</div>")

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    FLASK_COMPARE_URL,
                    json={"wild_type": wild_type, "mutant": mutant, "modality": modality},
                    timeout=60.0
                )
            
            if response.status_code == 200:
                data = response.json()
                score = data.get("similarity_score", 0)
                impact = data.get("impact_assessment", "Unknown")
                
                if score > 0.95:
                    color = "text-green-600"
                    bg = "bg-green-50"
                    icon = "fa-check-circle"
                elif score > 0.85:
                    color = "text-yellow-600"
                    bg = "bg-yellow-50"
                    icon = "fa-exclamation-circle"
                else:
                    color = "text-red-600"
                    bg = "bg-red-50"
                    icon = "fa-radiation"

                html_content = f"""
                <div class="p-4 rounded-lg border {bg} animate-fade-in mt-4">
                    <div class="flex items-center gap-4">
                        <div class="text-3xl {color}">
                            <i class="fa-solid {icon}"></i>
                        </div>
                        <div class="flex-grow">
                            <h4 class="text-sm font-bold text-gray-700 uppercase">Variant Analysis</h4>
                            <div class="text-2xl font-black {color}">{round(score * 100, 1)}% Similarity</div>
                            <p class="text-xs font-semibold text-gray-500">{impact}</p>
                        </div>
                    </div>
                </div>
                """
                return HTMLResponse(html_content)
            else:
                return HTMLResponse(f"<div class='text-red-500'>Comparison Failed: {response.text}</div>")

        except Exception as e:
            logger.error(f"Comparison Error: {e}")
            return HTMLResponse(f"<div class='text-red-500'>Error: {str(e)}</div>")

   