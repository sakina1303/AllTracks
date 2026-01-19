"""
UIDAI SITAA Track C - Demo API (Without Model)
Simple matching demo for testing frontend
"""

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import time
import random

app = FastAPI(
    title="UIDAI SITAA Track C API (Demo)",
    description="Contactless-to-Contact Fingerprint Matching Demo",
    version="1.0.0"
)

# CORS for React Native
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Health check"""
    return {
        "status": "online",
        "service": "UIDAI SITAA Track C API (Demo Mode - No Model)",
        "version": "1.0.0",
        "endpoints": {
            "health": "GET /health",
            "upload_match": "POST /api/upload_match"
        }
    }

@app.get("/health")
async def health():
    """Detailed health check"""
    return {
        "status": "healthy",
        "model_loaded": False,
        "mode": "demo",
        "timestamp": time.time()
    }

@app.post("/api/upload_match")
async def upload_match(
    contactless: UploadFile = File(...),
    contact: UploadFile = File(...),
    threshold: float = 0.8
):
    """
    Demo matching function - returns random scores for testing
    """
    start_time = time.time()
    
    try:
        # Simulate processing time
        await contactless.read()
        await contact.read()
        
        # Random score for demo purposes
        score = random.uniform(0.5, 0.95)
        
        # Decision
        decision = "MATCH" if score >= threshold else "NO MATCH"
        
        # Confidence
        distance = abs(score - threshold)
        if distance > 0.3:
            confidence = "High"
        elif distance > 0.15:
            confidence = "Medium"
        else:
            confidence = "Low"
        
        processing_time = (time.time() - start_time) * 1000
        
        return {
            "score": round(score, 4),
            "decision": decision,
            "threshold": threshold,
            "confidence": confidence,
            "processing_time_ms": round(processing_time, 2),
            "mode": "demo",
            "timestamp": time.time()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
