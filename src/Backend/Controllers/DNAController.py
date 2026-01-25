from fastapi import Request, Form, Response
from fastapi.templating import Jinja2Templates
from starlette.responses import HTMLResponse

templates = Jinja2Templates(directory="Template")


class DNAController:
    @staticmethod
    async def render_index(request: Request):
        return templates.TemplateResponse("index.html", {"request": request})

    @staticmethod
    async def analyze_sequence(request: Request, dna_input: str):
        # Business Logic
        seq = dna_input.strip().upper()

        # Calculation

        html_content = f"""
        <div class="output-box">
            <label>Analysis Result</label>
            <p>{seq}%</p>
        </div>
        """
        # Return only the fragment (The "View")
        return HTMLResponse(content=html_content)