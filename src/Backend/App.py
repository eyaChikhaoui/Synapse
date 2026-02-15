# File: src/Backend/App.py
import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import sys
import os
from pathlib import Path

# --- PATH SAFETY BOOTSTRAP ---
# Identify the root 'src' directory to allow imports from Routers, Data, etc.
CURRENT_FILE = Path(__file__).resolve()
BACKEND_DIR = CURRENT_FILE.parent  # src/Backend
SRC_DIR = BACKEND_DIR.parent       # src

# Add paths to sys.path (insert at 0 to prioritize local modules)
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

# --- IMPORT ROUTER ----

try:
    # This now works because Routers/DNARouter.py defines 'router'
    from Routers.DNARouter import router as dna_router
except ImportError as e:
    print(f"❌ Critical Import Error in App.py: {e}")
    # Troubleshooting tip for the console
    print("👉 Ensure src/Backend/Routers/DNARouter.py contains 'router = APIRouter(...)'")
    sys.exit(1)

App = FastAPI(title="Synapse Edge Gateway")

# --- MOUNT STATIC ASSETS ---
static_path = BACKEND_DIR / "static"
if static_path.exists():
    App.mount("/static", StaticFiles(directory=str(static_path)), name="static")
else:
    # Create directory if missing to avoid startup crash
    static_path.mkdir(parents=True, exist_ok=True)
    print(f"⚠️ Warning: 'static' folder was missing. Created at {static_path}")

# Include Routers
App.include_router(dna_router)

print(f"🌍 Synapse Edge Gateway initializing...")

if __name__ == "__main__":
    # Running via python src/Backend/App.py
    uvicorn.run("App:App", host="127.0.0.1", port=8000, reload=True)