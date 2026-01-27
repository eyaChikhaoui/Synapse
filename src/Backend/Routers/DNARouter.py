from fastapi import Request, Form
from fastapi.templating import Jinja2Templates
from starlette.responses import HTMLResponse
import httpx
import logging

# Configure Logging
logger = logging.getLogger("SearchController")
logging.basicConfig(level=logging.INFO)

templates = Jinja2Templates(directory="Template")

# Address of the Flask Inference Core
FLASK_API_URL = "http://localhost:5000/api/search"

class DNAController:
    @staticmethod
    async def render_index(request: Request):
        return templates.TemplateResponse("index.html", {"request": request})

    @staticmethod
    async def analyze_sequence(request: Request, dna_input: str = Form(...), analysis_type: str = Form("dna")):
        """
        Handles both DNA->Protein and Protein->DNA analysis.
        'analysis_type' comes from the frontend form (value='dna' or 'protein').
        """
        seq = dna_input.strip().upper()
        
        # Determine Mode
        if analysis_type == "protein":
            mode = "protein_to_dna"
            label_found = "Found Gene (DNA)"
        else:
            mode = "dna_to_protein"
            label_found = "Found Protein"

        if not seq:
             return HTMLResponse("<div class='error'>Please enter a valid sequence.</div>")

        try:
            # Communicate with Flask Core
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    FLASK_API_URL, 
                    json={"sequence": seq, "mode": mode},
                    timeout=60.0 
                )
            
            if response.status_code == 200:
                data = response.json()
                results = data.get("results", [])
                
                results_html = ""
                
                if not results:
                    results_html = f"<p style='color: white;'>No matching {label_found} found in vector space.</p>"
                else:
                    for item in results:
                        if "error" in item:
                            return HTMLResponse(f"<div class='error'>⚠️ {item['error']}</div>")

                        # Extract Metadata
                        meta = item.get("metadata", {})
                        score = round(item.get("score", 0) * 100, 2)
                        
                        # Handle Dynamic Metadata (Gene vs Protein keys)
                        if mode == "protein_to_dna":
                            # Gene Result
                            title = f"Gene ID: {meta.get('gene_id', 'Unknown')}"
                            desc = f"Sequence Segment: {meta.get('sequence', '')[:50]}..."
                            badge_color = "#00897B" # Teal for Genes
                        else:
                            # Protein Result
                            title = meta.get("protein_name", "Unknown Protein")
                            desc = meta.get("function", "Function not catalogued.")[:180] + "..."
                            badge_color = "#FF5252" # Red for Proteins

                        results_html += f"""
                        <div class="result-card" style="background: rgba(255,255,255,0.05); padding: 15px; margin-bottom: 12px; border-radius: 8px; border-left: 4px solid {badge_color};">
                            <div style="display: flex; justify-content: space-between; align-items: start;">
                                <h3 style="margin: 0; color: #fff; font-size: 1.1rem;">{title}</h3>
                                <span style="background: rgba(255,255,255,0.1); color: {badge_color}; padding: 2px 8px; border-radius: 12px; font-size: 0.8rem; font-weight: bold;">{score}% Match</span>
                            </div>
                            <p style="color: #b0aec4; margin: 8px 0; font-size: 0.9rem;">{desc}</p>
                        </div>
                        """

                final_html = f"""
                <div class="output-box animate-fade-in">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
                        <label style="color: white; font-weight: bold;">{label_found}</label>
                        <span style="font-size: 0.8rem; color: #888;">Mode: {mode}</span>
                    </div>
                    <div class="results-list">
                        {results_html}
                    </div>
                </div>
                """
                return HTMLResponse(content=final_html)
            
            else:
                return HTMLResponse(f"<div class='error'>Error from Core: {response.text}</div>")

        except Exception as e:
            logger.error(f"Controller Error: {e}")
            return HTMLResponse(f"<div class='error'>Connection Failed: {str(e)}</div>")