from fastapi import APIRouter, Request, Form
from Controllers.DNAController import DNAController

router = APIRouter()

@router.get("/")
async def get_index(request: Request):
    return await DNAController.render_index(request)

@router.post("/analyze")
async def post_analyze(request: Request, dna_input: str = Form(...)):
    return await DNAController.analyze_sequence(request, dna_input)