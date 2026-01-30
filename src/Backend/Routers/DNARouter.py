# File: src/Backend/Routers/DNARouter.py
from fastapi import APIRouter, Request, Form, UploadFile, File
from typing import Optional
from Controllers.DNAController import DNAController 

# ✅ The variable 'router' must exist here for App.py to import it
router = APIRouter(
    prefix="",
    tags=["DNA Processing"]
)

# --- PAGE ROUTES (Browser) ---

@router.get("/")
async def landing(request: Request):
    """
    ROOT ROUTE: Renders the High-End Landing Page.
    User sees this at http://127.0.0.1:8000/
    """
    return await DNAController.render_landing(request)

@router.get("/system")
async def index(request: Request):
    """
    SYSTEM ROUTE: Renders the Main Synapse Application.
    User sees this at http://127.0.0.1:8000/system
    """
    return await DNAController.render_index(request)

# --- ACTION ROUTES (Form Submissions) ---

@router.post("/analyze")
async def analyze(
    request: Request, 
    dna_input: Optional[str] = Form(None), 
    analysis_type: str = Form("dna"),
    file: Optional[UploadFile] = File(None) 
):
    return await DNAController.analyze_sequence(request, dna_input, analysis_type, file)

@router.post("/batch_analyze")
async def batch_analyze(
    request: Request,
    batch_input: Optional[str] = Form(None), 
    analysis_type: str = Form("dna"),
    file: Optional[UploadFile] = File(None) 
):
    return await DNAController.batch_analyze_sequences(request, batch_input, analysis_type, file)

@router.post("/compare")
async def compare(
    request: Request,
    wild_type: str = Form(...),
    mutant: str = Form(...),
    modality: str = Form("dna")
):
    return await DNAController.compare_sequences(request, wild_type, mutant, modality)