import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import sys
import os
from pathlib import Path

# --- PATH SAFETY BOOTSTRAP ---
# Identify the root 'src' directory to allow imports from Routers, Data, etc.
CURRENT_FILE = Path(__file__).resolve()
BACKEND_DIR = CURRENT_FILE.parent
SRC_DIR = BACKEND_DIR.parent

# Add 'src' and 'src/Backend' to path to ensure modules are found
sys.path.append(str(SRC_DIR))
sys.path.append(str(BACKEND_DIR))

try:
    from Routers.DNARouter import router as dna_router
except ImportError as e:
    print(f"❌ Critical Import Error in App.py: {e}")
    sys.exit(1)

App = FastAPI(title="Synapse Edge Gateway")

# --- MOUNT STATIC ASSETS ---
# Robustly find static folder
static_path = BACKEND_DIR / "static"
if static_path.exists():
    App.mount("/static", StaticFiles(directory=str(static_path)), name="static")
else:
    print(f"⚠️ Warning: 'static' folder not found at {static_path}")

# Include Routers
App.include_router(dna_router)

print(f"🌍 Synapse Edge Gateway initializing...")

if __name__ == "__main__":
    # Running via python src/Backend/App.py
    uvicorn.run("App:App", host="127.0.0.1", port=8000, reload=True)