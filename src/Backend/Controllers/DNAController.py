#backend imports
from fastapi import Request
from fastapi.templating import Jinja2Templates
from starlette.responses import HTMLResponse

#IMPORTING the DNA ENCODER CLASS
from encoders.dna_encoder import RealEncoder

#initiate the class of the dna encoder
encoder = RealEncoder()

templates = Jinja2Templates(directory="Template")

class DNAController:
    @staticmethod
    async def render_index(request: Request):
        return templates.TemplateResponse("index.html", {"request": request})

    @staticmethod
    async def analyze_sequence(request: Request, dna_input: str):
        #getting the DNA sequance from the user interface
        seq = dna_input.strip().upper()
        #Traitement
        #============
        vector = encoder.encode(seq)
        #============
        html_content = f"""
        <div class="output-box">
            <label>Analysis Result</label>
            <p>{vector}%</p>
        </div>
        """
        # Return only the fragment (The "View")
        return HTMLResponse(content=html_content)