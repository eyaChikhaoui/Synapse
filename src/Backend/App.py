import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from Routers.DNARouter import router as dna_router
from Routers.DNARouter1 import router as dna_router1
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Mount static files (for your CSS)
app.mount("/static", StaticFiles(directory="static"), name="static")


origins = ["*"]

# 2. ADD MIDDLEWARE (The Gatekeeper)
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Include your routes
app.include_router(dna_router)
app.include_router(dna_router1, prefix="/CSR")


if __name__ == "__main__":
    uvicorn.run("App:App", reload=True)