from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os

# Import the two applications
# Note: We assume api_track_c.py is in root and track_d_backend is a package/folder
from api_track_c import app as track_c_app
from track_d_backend.api_track_b import app as track_d_app

# Create the main entry point
app = FastAPI(
    title="Finger Match Backend (Merged)",
    description="Combined API for Track C (Matching) and Track D (Liveness)",
    version="1.0.0"
)

# CORS - Allow all origins for the main app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount the sub-applications
# Track C will be available at /track-c/api/match
app.mount("/track-c", track_c_app)

# Track D will be available at /track-d/api/liveness_check
app.mount("/track-d", track_d_app)

@app.get("/")
def root():
    return {
        "message": "Finger Match Backend Operational",
        "endpoints": {
            "track_c": "/track-c/api/match",
            "track_d": "/track-d/api/liveness_check"
        }
    }

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
