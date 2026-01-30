from fastapi import Request, Form
from fastapi.templating import Jinja2Templates
from starlette.responses import HTMLResponse
import httpx  # Client to talk to Flask
import json

templates = Jinja2Templates(directory="Template")

# The address of your Flask "Brain" (main.py)
FLASK_API_URL = "http://localhost:8000/api/search"

class DNAController:
    @staticmethod
    async def render_index(request: Request):
        return templates.TemplateResponse("index.html", {"request": request})

    @staticmethod
    async def analyze_sequence(request: Request, dna_input: str = Form(...)):
        seq = dna_input.strip().upper()
        
        if not seq:
             return HTMLResponse("<div class='error'>Please enter a sequence.</div>")

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    FLASK_API_URL, 
                    json={"dna_sequence": seq},
                    timeout=30.0
                )
            
            if response.status_code == 200:
                data = response.json()
                results = data.get("results", [])
                
                results_html = ""
                
                if not results:
                    results_html = "<p>No matching proteins found.</p>"
                else:
                    for item in results:
                        # --- FIX: Check if the result is actually an error ---
                        if "error" in item:
                            return HTMLResponse(f"""
                            <div class="result-card" style="background: rgba(255, 0, 0, 0.2); border-left: 4px solid red; padding: 15px;">
                                <h3 style="color: #ff5252;">⚠️ System Error</h3>
                                <p>{item['error']}</p>
                            </div>
                            """)

                        # Extract data from Qdrant payload
                        meta = item.get("metadata", {})
                        score = round(item.get("score", 0) * 100, 2)
                        name = meta.get("protein_name", "Unknown Protein")
                        func = meta.get("function", "N/A")
                        
                        results_html += f"""
                        <div class="result-card" style="background: rgba(255,255,255,0.05); padding: 15px; margin-bottom: 10px; border-radius: 8px; border-left: 4px solid #FF5252;">
                            <h3 style="margin: 0; color: #fff;">{name}</h3>
                            <p style="color: #b0aec4; margin: 5px 0;">Function: {func}</p>
                            <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 10px;">
                                <span style="font-size: 0.8rem; background: #311B92; padding: 2px 8px; border-radius: 4px;">ID: {item.get('id')}</span>
                                <span style="font-weight: bold; color: #FF5252;">Match: {score}%</span>
                            </div>
                        </div>
                        """

                final_html = f"""
                <div class="output-box animate-fade-in">
                    <label style="color: #FF5252;">Analysis Complete</label>
                    <div class="results-list" style="margin-top: 15px;">
                        {results_html}
                    </div>
                </div>
                """
                return HTMLResponse(content=final_html)
            
            else:
                return HTMLResponse(f"<div class='error'>Error from Core: {response.text}</div>")

        except Exception as e:
            return HTMLResponse(f"<div class='error'>Connection Failed: {str(e)}</div>")