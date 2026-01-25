import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from Routers.DNARouter import router as dna_router

# CHANGE "app" TO "App" (Capital A)
App = FastAPI()

App.mount("/static", StaticFiles(directory="static"), name="static")

App.include_router(dna_router)


if __name__ == "__main__":
    # Now this matches the variable name above
    uvicorn.run("App:App", reload=True)