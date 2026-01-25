from fastapi import APIRouter
from Controllers.DNAController1 import DNAController
from Data.DNAschema import DNARequest, DNAResponse

# 2. INITIALIZE THE ROUTER (This defines 'router' so the code below works)
router = APIRouter() 

@router.post("/analyze", response_model=DNAResponse)
async def analyze_dna(data: DNARequest): 
    return await DNAController.process_analysis(data.dna_input)