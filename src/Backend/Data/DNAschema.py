from pydantic import BaseModel

class DNARequest(BaseModel):
    dna_input: str

class DNAResponse(BaseModel):
    status: str
    results: list