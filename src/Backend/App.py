import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from Routers.DNARouter import router as dna_router

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(dna_router)


if __name__ == "__main__":
    uvicorn.run("App:App", reload=True)