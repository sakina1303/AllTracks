"""
UIDAI SITAA Track C - Production API
All functions from Gradio demo as REST endpoints
"""

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import tensorflow as tf
import cv2
import numpy as np
import base64
import io
from PIL import Image
import time
import os

# ============================================================================
# FASTAPI APP
# ============================================================================

app = FastAPI(
    title="UIDAI SITAA Track C API",
    description="Contactless-to-Contact Fingerprint Matching",
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

# ============================================================================
# LOAD MODEL ON STARTUP
# ============================================================================

MODEL_PATH = "track_c_final.h5"
model = None

@app.on_event("startup")
async def load_model():
    global model
    try:
        print(f"Loading model from {MODEL_PATH}...")
        model = tf.keras.models.load_model(MODEL_PATH, compile=False)
        print("✓ Model loaded successfully")
    except Exception as e:
        print(f"❌ Error loading model: {e}")
        raise

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def base64_to_image(base64_string: str) -> np.ndarray:
    """Convert base64 to numpy array"""
    try:
        if ',' in base64_string:
            base64_string = base64_string.split(',')[1]
        
        image_bytes = base64.b64decode(base64_string)
        image = Image.open(io.BytesIO(image_bytes))
        image_array = np.array(image)
        
        if len(image_array.shape) == 3 and image_array.shape[2] == 3:
            image_array = cv2.cvtColor(image_array, cv2.COLOR_RGB2BGR)
        
        return image_array
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid image: {str(e)}")

def quality_check(image: np.ndarray) -> float:
    """
    NEW: Check if image is too blurry or dark
    Returns score 0.0 (bad) to 1.0 (good)
    """
    try:
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
            
        # 1. Blur Check (Variance of Laplacian)
        blur_score = cv2.Laplacian(gray, cv2.CV_64F).var()
        # Normalizing: < 100 is usually blurry
        norm_blur = min(blur_score / 300.0, 1.0)
        
        # 2. Contrast/Brightness Check
        contrast_score = np.std(gray)
        norm_contrast = min(contrast_score / 50.0, 1.0)
        
        # Weighted Score (Blur matters more)
        quality = (0.7 * norm_blur) + (0.3 * norm_contrast)
        return quality
    except:
        return 0.5  # Fail safe default

def preprocess_fingerprint(img: np.ndarray) -> np.ndarray:
    """Preprocess fingerprint - CLAHE enhancement"""
    img = cv2.resize(img, (224, 224))
    
    if len(img.shape) == 3:
        lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        l = clahe.apply(l)
        enhanced = cv2.merge([l, a, b])
        enhanced = cv2.cvtColor(enhanced, cv2.COLOR_LAB2RGB)
    else:
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(img)
        enhanced = cv2.cvtColor(enhanced, cv2.COLOR_GRAY2RGB)
    
    return enhanced.astype(np.float32) / 255.0

# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class MatchRequest(BaseModel):
    contactless_image: str  # base64
    contact_image: str      # base64
    threshold: Optional[float] = 0.8

class BatchMatchRequest(BaseModel):
    contactless_image: str
    contact_images: List[str]
    threshold: Optional[float] = 0.8

# ============================================================================
# API ENDPOINTS - MATCHING ALL GRADIO FUNCTIONS
# ============================================================================

@app.get("/")
async def root():
    """Health check"""
    return {
        "status": "online",
        "service": "UIDAI SITAA Track C API",
        "version": "1.0.0",
        "endpoints": {
            "health": "GET /health",
            "match": "POST /api/match",
            "batch_match": "POST /api/batch_match",
            "upload_match": "POST /api/upload_match",
            "pipeline": "GET /api/pipeline"
        }
    }

@app.get("/health")
async def health():
    """Detailed health check"""
    return {
        "status": "healthy",
        "model_loaded": model is not None,
        "model_path": MODEL_PATH,
        "timestamp": time.time()
    }

@app.post("/api/match")
async def match_fingerprints(request: MatchRequest):
    """
    MAIN MATCHING FUNCTION
    Same as Gradio demo "Match Fingerprints" button
    
    Returns: score, decision, confidence, processing_time
    """
    start_time = time.time()
    
    try:
        # Decode images
        contactless_img = base64_to_image(request.contactless_image)
        contact_img = base64_to_image(request.contact_image)
        
        # --- NEW: QUALITY CHECK ---
        q1 = quality_check(contactless_img)
        q2 = quality_check(contact_img)
        
        # If blurry, return early
        if q1 < 0.3 or q2 < 0.3:
            processing_time = (time.time() - start_time) * 1000
            return {
                "score": 0.0,
                "decision": "RECAPTURE (Low Quality)",
                "threshold": request.threshold,
                "confidence": "Low",
                "processing_time_ms": round(processing_time, 2),
                "timestamp": time.time()
            }
        
        # Preprocess
        contactless_processed = preprocess_fingerprint(contactless_img)
        contact_processed = preprocess_fingerprint(contact_img)
        
        # Predict
        contactless_batch = np.expand_dims(contactless_processed, axis=0)
        contact_batch = np.expand_dims(contact_processed, axis=0)
        
        score = float(model.predict(
            [contactless_batch, contact_batch], 
            verbose=0
        )[0][0])
        
        # Decision (Enforcing 0.75 minimum for safety)
        SAFE_THRESHOLD = max(request.threshold, 0.75)
        decision = "MATCH" if score >= SAFE_THRESHOLD else "NO MATCH"
        
        # Confidence
        distance = abs(score - SAFE_THRESHOLD)
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
            "threshold": SAFE_THRESHOLD,
            "confidence": confidence,
            "processing_time_ms": round(processing_time, 2),
            "timestamp": time.time()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/batch_match")
async def batch_match(request: BatchMatchRequest):
    """
    BATCH MATCHING (1 vs Many)
    Match one contactless against multiple contact images
    
    Returns: list of results + best match
    """
    start_time = time.time()
    
    try:
        contactless_img = base64_to_image(request.contactless_image)
        
        # --- NEW: Probe Quality Check ---
        if quality_check(contactless_img) < 0.3:
             processing_time = (time.time() - start_time) * 1000
             return {
                "results": [],
                "best_match": None,
                "error": "Probe image too blurry (Quality Check Failed)",
                "processing_time_ms": round(processing_time, 2),
                "timestamp": time.time()
            }

        contactless_processed = preprocess_fingerprint(contactless_img)
        
        results = []
        best_match = None
        best_score = -1
        
        for idx, contact_b64 in enumerate(request.contact_images):
            try:
                contact_img = base64_to_image(contact_b64)
                contact_processed = preprocess_fingerprint(contact_img)
                
                contactless_batch = np.expand_dims(contactless_processed, axis=0)
                contact_batch = np.expand_dims(contact_processed, axis=0)
                
                score = float(model.predict(
                    [contactless_batch, contact_batch],
                    verbose=0
                )[0][0])
                
                # Decision (Enforcing 0.75)
                SAFE_THRESHOLD = 0.75
                decision = "MATCH" if score >= SAFE_THRESHOLD else "NO MATCH"
                
                result = {
                    "id": idx,
                    "score": round(score, 4),
                    "decision": decision
                }
                
                results.append(result)
                
                if score > best_score:
                    best_score = score
                    best_match = result
            
            except Exception as e:
                results.append({"id": idx, "error": str(e)})
        
        processing_time = (time.time() - start_time) * 1000
        
        return {
            "results": results,
            "best_match": best_match,
            "total_compared": len(request.contact_images),
            "processing_time_ms": round(processing_time, 2),
            "timestamp": time.time()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/upload_match")
async def upload_match(
    contactless: UploadFile = File(...),
    contact: UploadFile = File(...),
    threshold: float = 0.8
):
    """
    ALTERNATIVE: File upload instead of base64
    Useful for testing from Postman/browser
    """
    start_time = time.time()
    
    try:
        # Read files
        contactless_bytes = await contactless.read()
        contact_bytes = await contact.read()
        
        # Convert to numpy
        contactless_img = cv2.imdecode(
            np.frombuffer(contactless_bytes, np.uint8),
            cv2.IMREAD_COLOR
        )
        contact_img = cv2.imdecode(
            np.frombuffer(contact_bytes, np.uint8),
            cv2.IMREAD_COLOR
        )
        
        # Preprocess
        contactless_processed = preprocess_fingerprint(contactless_img)
        contact_processed = preprocess_fingerprint(contact_img)
        
        # Predict
        contactless_batch = np.expand_dims(contactless_processed, axis=0)
        contact_batch = np.expand_dims(contact_processed, axis=0)
        
        score = float(model.predict(
            [contactless_batch, contact_batch],
            verbose=0
        )[0][0])
        
        decision = "MATCH" if score >= threshold else "NO MATCH"
        
        processing_time = (time.time() - start_time) * 1000
        
        return {
            "score": round(score, 4),
            "decision": decision,
            "threshold": threshold,
            "processing_time_ms": round(processing_time, 2)
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/pipeline")
async def get_pipeline():
    """
    PIPELINE DOCUMENTATION
    Returns Track C implementation details
    """
    return {
        "track": "C - Contactless-to-Contact Matching",
        "requirements": [
            "1. Import contact-based fingerprint images",
            "2. Capture or import contactless finger image",
            "3. Extract basic features (surrogate features via CNN)",
            "4. Produce a similarity score",
            "5. Display match / no-match decision"
        ],
        "pipeline_steps": [
            "Input: Contact & Contactless images",
            "Preprocessing: CLAHE enhancement, Resize to 224×224",
            "Feature Extraction: Siamese CNN (MobileNetV2)",
            "Comparison: Deep feature similarity",
            "Scoring: 0-1 similarity score",
            "Decision: Threshold-based match/no-match"
        ],
        "model_specs": {
            "architecture": "Siamese Neural Network",
            "base_model": "MobileNetV2 (fine-tuned)",
            "input_size": "224×224×3",
            "validation_accuracy": "70%",
            "model_size_mb": 25,
            "parameters": "~6.5M"
        },
        "api_version": "1.0.0",
        "deployment": "GCP Cloud Run"
    }

# ============================================================================
# RUN LOCALLY
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    print("=" * 80)
    print("TRACK C API - LOCAL SERVER")
    print("=" * 80)
    print("\nEndpoints:")
    print("  GET  /              - Health check")
    print("  GET  /health        - Status")
    print("  POST /api/match     - Single match (base64)")
    print("  POST /api/batch_match - Batch match (base64)")
    print("  POST /api/upload_match - File upload")
    print("  GET  /api/pipeline  - Documentation")
    print("\nAPI Docs: http://localhost:8000/docs")
    print("=" * 80)
    
    import os
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
