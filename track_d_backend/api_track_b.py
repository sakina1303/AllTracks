"""
UIDAI SITAA Track D - Liveness/Spoof Detection API
Motion-based cue, Texture Analysis, Multi-frame Consistency
"""

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import cv2
import numpy as np
from typing import List
import uvicorn
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="UIDAI SITAA Track D - Liveness Detection",
    description="Anti-spoofing with motion, texture, and consistency checks",
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
# LIVENESS DETECTION ALGORITHMS
# ============================================================================

def calculate_optical_flow(frame1, frame2):
    """Calculate optical flow between two frames to detect motion"""
    gray1 = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY)
    gray2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)
    
    # Farneback optical flow
    flow = cv2.calcOpticalFlowFarneback(gray1, gray2, None, 0.5, 3, 15, 3, 5, 1.2, 0)
    magnitude, _ = cv2.cartToPolar(flow[..., 0], flow[..., 1])
    
    # Calculate average motion
    avg_motion = np.mean(magnitude)
    return float(avg_motion)

def calculate_texture_score(frame):
    """Analyze texture using Laplacian variance (blur/print detection)"""
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
    
    # Normalize to 0-1 scale (higher = more texture detail)
    # Lowered threshold from 500 to 100 to account for mobile camera compression/lighting
    score = min(laplacian_var / 100.0, 1.0)
    return float(score)

def calculate_consistency_score(frames):
    """Check consistency across frames (lighting, position)"""
    if len(frames) < 2:
        return 0.5
    
    # Calculate histogram similarity between consecutive frames
    similarities = []
    for i in range(len(frames) - 1):
        hist1 = cv2.calcHist([frames[i]], [0, 1, 2], None, [8, 8, 8], [0, 256, 0, 256, 0, 256])
        hist2 = cv2.calcHist([frames[i+1]], [0, 1, 2], None, [8, 8, 8], [0, 256, 0, 256, 0, 256])
        
        hist1 = cv2.normalize(hist1, hist1).flatten()
        hist2 = cv2.normalize(hist2, hist2).flatten()
        
        similarity = cv2.compareHist(hist1, hist2, cv2.HISTCMP_CORREL)
        similarities.append(similarity)
    
    # Average similarity (high = consistent, low = inconsistent)
    avg_similarity = np.mean(similarities)
    return float(avg_similarity)

# ============================================================================
# ENDPOINTS
# ============================================================================

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "Track D - Liveness Detection"
    }

@app.post("/api/liveness_check")
async def liveness_check(frames: List[UploadFile] = File(...)):
    """
    Perform liveness detection on multiple frames.
    Checks for:
    1. Motion-based cue (optical flow)
    2. Texture analysis (Laplacian variance)
    3. Multi-frame consistency (histogram correlation)
    """
    import time
    start_time = time.time()
    
    try:
        if len(frames) < 2:
            raise HTTPException(
                status_code=400, 
                detail="At least 2 frames required for liveness detection"
            )
        
        logger.info(f"Processing {len(frames)} frames for liveness detection")
        
        # Read all frames
        frame_images = []
        for frame_file in frames:
            contents = await frame_file.read()
            nparr = np.frombuffer(contents, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if img is None:
                raise HTTPException(status_code=400, detail="Invalid image format")
            frame_images.append(img)
        
        # 1. MOTION SCORE: Calculate optical flow between consecutive frames
        motion_scores = []
        for i in range(len(frame_images) - 1):
            motion = calculate_optical_flow(frame_images[i], frame_images[i+1])
            motion_scores.append(motion)
        avg_motion = np.mean(motion_scores)
        
        # Normalize motion score (typical range: 0.5-5.0 for live, <0.5 for spoof)
        motion_score = min(avg_motion / 3.0, 1.0)
        
        # 2. TEXTURE SCORE: Average across all frames
        texture_scores = [calculate_texture_score(frame) for frame in frame_images]
        texture_score = np.mean(texture_scores)
        
        # 3. CONSISTENCY SCORE: Frame-to-frame similarity
        consistency_score = calculate_consistency_score(frame_images)
        
        # LIVENESS DECISION: Weighted Scoring Logic (More Robust)
        # We value Texture (detail) and Consistency more than Motion (to allow steady hands)
        
        # motion_score: 0.0 (static) to 1.0 (lots of movement)
        # texture_score: 0.0 (blur) to 1.0 (sharp/pores visible)
        # consistency_score: 0.0 (random images) to 1.0 (smooth video)

        # Weighted Score Calculation
        # Texture is most important for fingerprints
        weighted_score = (
            motion_score * 0.2 +       # Reduced weight on motion (allows steady hands)
            texture_score * 0.6 +      # High weight on texture (skin detail)
            consistency_score * 0.2    # Moderate weight on sequence
        )

        # Decision Threshold
        # If texture is very high (good print), we can tolerate low motion
        if texture_score > 0.5:
             # Very detailed image - likely real even if still
             is_live = True
        else:
             # Standard threshold check
             # Relaxed motion threshold from 0.15 to 0.05
             is_live = (weighted_score > 0.4) and (motion_score > 0.05 or texture_score > 0.4)
        
        # Overall confidence (weighted average)
        confidence = weighted_score
        
        # Calculate processing time
        processing_time_ms = (time.time() - start_time) * 1000
        
        logger.info(
            f"Liveness result: {is_live}, "
            f"motion={motion_score:.3f}, "
            f"texture={texture_score:.3f}, "
            f"consistency={consistency_score:.3f}, "
            f"time={processing_time_ms:.1f}ms"
        )
        
        return JSONResponse(content={
            "is_live": bool(is_live),
            "confidence": float(confidence),
            "motion_score": float(motion_score),
            "texture_score": float(texture_score),
            "consistency_score": float(consistency_score),
            "processing_time_ms": float(processing_time_ms),
            "frames_analyzed": len(frame_images),
            "message": "LIVE" if is_live else "SPOOF DETECTED"
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in liveness detection: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# STARTUP
# ============================================================================

if __name__ == "__main__":
    print("=" * 80)
    print("TRACK D - LIVENESS DETECTION API")
    print("=" * 80)
    print("\nFeatures:")
    print("  ✓ Motion-based cue detection (Optical Flow)")
    print("  ✓ Texture analysis (Laplacian Variance)")
    print("  ✓ Multi-frame consistency (Histogram Correlation)")
    print("\nEndpoints:")
    print("  GET  /health             - Health check")
    print("  POST /api/liveness_check - Liveness detection")
    print("\nAPI Docs: http://localhost:8001/docs")
    print("=" * 80)
    uvicorn.run(app, host="0.0.0.0", port=8001)
