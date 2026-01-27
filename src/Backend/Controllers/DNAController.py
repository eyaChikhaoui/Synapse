from fastapi import Request, Form
from fastapi.templating import Jinja2Templates
from starlette.responses import HTMLResponse
import httpx
import logging

# Configure Logging
logger = logging.getLogger("DNAController")
logging.basicConfig(level=logging.INFO)

templates = Jinja2Templates(directory="Template")

# Address of the Flask Inference Core
FLASK_API_URL = "http://localhost:5000/api/search"

class DNAController:
    @staticmethod
    async def render_index(request: Request):
        return templates.TemplateResponse("index.html", {"request": request})

    @staticmethod
    async def analyze_sequence(request: Request, dna_input: str = Form(...)):
        seq = dna_input.strip().upper()
        
        if not seq:
             return HTMLResponse("<div class='error'>Please enter a valid DNA sequence.</div>")

        try:
            # Communicate with Flask Core
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    FLASK_API_URL, 
                    json={"dna_sequence": seq},
                    timeout=60.0 # Increased timeout for heavy model inference
                )
            
            if response.status_code == 200:
                data = response.json()
                results = data.get("results", [])
                
                results_html = ""
                
                if not results:
                    results_html = "<p style='color: white;'>No matching proteins found in the vector space.</p>"
                else:
                    for item in results:
                        # Error Handling from Core
                        if "error" in item:
                            return HTMLResponse(f"""
                            <div class="result-card" style="background: rgba(255, 0, 0, 0.2); border-left: 4px solid red; padding: 15px;">
                                <h3 style="color: #ff5252;">⚠️ Core Error</h3>
                                <p style="color: white;">{item['error']}</p>
                            </div>
                            """)

                        # Extract Metadata
                        meta = item.get("metadata", {})
                        score = round(item.get("score", 0) * 100, 2)
                        
                        name = meta.get("protein_name", "Unknown Protein")
                        func = meta.get("function", "Function not catalogued.")
                        source = meta.get("source", "System")
                        
                        # Truncate long descriptions for the card view
                        short_func = func[:180] + "..." if len(func) > 180 else func
                        
                        results_html += f"""
                        <div class="result-card" style="background: rgba(255,255,255,0.05); padding: 15px; margin-bottom: 12px; border-radius: 8px; border-left: 4px solid #FF5252; transition: all 0.3s ease;">
                            <div style="display: flex; justify-content: space-between; align-items: start;">
                                <h3 style="margin: 0; color: #fff; font-size: 1.1rem;">{name}</h3>
                                <span style="background: rgba(255, 82, 82, 0.2); color: #FF5252; padding: 2px 8px; border-radius: 12px; font-size: 0.8rem; font-weight: bold;">{score}% Match</span>
                            </div>
                            
                            <p style="color: #b0aec4; margin: 8px 0; font-size: 0.9rem; line-height: 1.4;">{short_func}</p>
                            
                            <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 10px; border-top: 1px solid rgba(255,255,255,0.1); padding-top: 8px;">
                                <span style="font-size: 0.75rem; color: #888;">Source: {source}</span>
                                <span style="font-size: 0.75rem; background: #311B92; color: white; padding: 2px 6px; border-radius: 4px;">ID: {item.get('id')}</span>
                            </div>
                        </div>
                        """

                final_html = f"""
                <div class="output-box animate-fade-in">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
                        <label style="color: #FF5252; font-weight: bold;">Top Semantic Matches</label>
                        <span style="font-size: 0.8rem; color: #888;">Latent Space: 768-dim</span>
                    </div>
                    <div class="results-list">
                        {results_html}
                    </div>
                </div>
                """
                return HTMLResponse(content=final_html)
            
            else:
                return HTMLResponse(f"<div class='error'>Error from Core (Status {response.status_code}): {response.text}</div>")

        except Exception as e:
            logger.error(f"Controller Error: {e}")
            return HTMLResponse(f"<div class='error'>Connection Failed. Is the Flask Core running? <br><small>{str(e)}</small></div>")