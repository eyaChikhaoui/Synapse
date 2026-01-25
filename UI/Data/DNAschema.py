from pydantic import BaseModel

class DNARequest(BaseModel):
    dna_input: str

class DNAResponse(BaseModel):
    length: int
    result: str