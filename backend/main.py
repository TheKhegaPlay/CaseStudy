"""
FastAPI Backend for Forensic GAN Platform
Provides image inpainting via AOT-GAN model
"""

import os
import sys
import logging
from pathlib import Path
from typing import Optional
from datetime import datetime

from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import torch
import numpy as np
import cv2

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import local modules
from inference import get_model, AOTGANInference
from utils import (
    image_to_base64,
    base64_to_image,
    generate_random_mask,
    load_mask_from_file,
    apply_mask_to_image,
    validate_image,
)

# Initialize FastAPI app
app = FastAPI(
    title="Forensic GAN Platform - Backend",
    description="Image inpainting service using AOT-GAN model",
    version="1.0.0"
)

# CORS middleware for connecting to Angular frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200", "http://localhost:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# Data Models
# ============================================================================

class RestoreRequest(BaseModel):
    """Request schema for image restoration."""
    image: str  # base64 encoded image
    mask: Optional[str] = None  # base64 encoded mask, or generate randomly if None
    mask_type: str = 'irregular'  # 'irregular', 'center', 'rectangular', 'random_brush'
    mask_ratio: float = 0.3  # percentage of image to mask (0.0 to 1.0)


class RestoreResponse(BaseModel):
    """Response schema for image restoration."""
    success: bool
    original_image: str  # base64
    masked_image: str  # base64 (for visualization)
    restored_image: str  # base64
    confidence_score: float  # [0, 1]
    metrics: dict  # {ssim, psnr, mse}
    processing_time_ms: float
    timestamp: str


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    model_loaded: bool
    device: str
    model_params: int
    version: str


# ============================================================================
# Global state
# ============================================================================

model_instance: Optional[AOTGANInference] = None
model_ready = False


def get_device() -> str:
    """Determine device to use for inference."""
    if torch.cuda.is_available():
        logger.info("✓ CUDA available, using GPU")
        return "cuda"
    else:
        logger.info("ℹ CUDA not available, using CPU")
        return "cpu"


def init_model():
    """Initialize the model on startup."""
    global model_instance, model_ready
    
    try:
        device = get_device()
        logger.info(f"Initializing AOT-GAN model on {device}...")
        
        model_instance = get_model(device=device)
        model_ready = True
        
        logger.info("✓ Model initialization complete")
    except Exception as e:
        logger.error(f"✗ Failed to initialize model: {e}")
        model_ready = False


# ============================================================================
# Startup/Shutdown Events
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Initialize model on app startup."""
    logger.info("🚀 Starting Forensic GAN Platform Backend...")
    init_model()
    logger.info("✓ Backend startup complete")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on app shutdown."""
    logger.info("🛑 Shutting down backend...")
    global model_instance
    model_instance = None


# ============================================================================
# API Endpoints
# ============================================================================

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint.
    Returns model status and device info.
    """
    param_count = 0
    if model_instance:
        param_count = sum(p.numel() for p in model_instance.model.parameters())
    
    return HealthResponse(
        status="ready" if model_ready else "initializing",
        model_loaded=model_instance is not None,
        device=model_instance.device.type if model_instance else "unknown",
        model_params=param_count,
        version="1.0.0"
    )


@app.post("/api/restore", response_model=RestoreResponse)
async def restore_image(request: RestoreRequest):
    """
    Main endpoint for image inpainting.
    
    Accepts:
    - image: base64 encoded RGB image
    - mask: optional base64 encoded mask (if not provided, generates random)
    - mask_type: type of mask to generate ('irregular', 'center', 'rectangular', 'random_brush')
    - mask_ratio: percentage of image to damage (0.0 to 1.0)
    
    Returns:
    - original_image: base64
    - masked_image: base64 (original with mask overlay)
    - restored_image: base64 (result of inpainting)
    - confidence_score: float [0, 1]
    - metrics: {ssim, psnr, mse}
    - processing_time_ms: float
    """
    
    if not model_ready or model_instance is None:
        logger.error("Model not ready")
        raise HTTPException(status_code=503, detail="Model not initialized. Try again later.")
    
    try:
        start_time = datetime.now()
        
        # Step 1: Decode image
        logger.info("📥 Decoding input image...")
        image_array = base64_to_image(request.image)
        logger.info(f"✓ Image decoded: shape={image_array.shape}")
        
        # Step 2: Handle mask
        if request.mask:
            logger.info("📥 Using provided mask...")
            mask_array = base64_to_image(request.mask)
            # Convert to grayscale if needed
            if len(mask_array.shape) == 3:
                mask_array = cv2.cvtColor(mask_array, cv2.COLOR_RGB2GRAY)
        else:
            logger.info(f"🎨 Generating {request.mask_type} mask (ratio={request.mask_ratio})...")
            mask_array = generate_random_mask(
                image_array.shape[:2],
                mask_type=request.mask_type,
                mask_ratio=request.mask_ratio
            )
        
        logger.info(f"✓ Mask prepared: shape={mask_array.shape}, damaged_pixels={np.sum(mask_array > 127)}")
        
        # Step 3: Run inference
        logger.info("🤖 Running AOT-GAN inference...")
        restored_image, confidence_score, metrics = model_instance.infer(
            image_array=image_array,
            mask_array=mask_array,
            target_size=512
        )
        logger.info(f"✓ Inference complete: confidence={confidence_score:.4f}")
        
        # Step 4: Create masked visualization
        logger.info("🎨 Creating masked image visualization...")
        masked_image = apply_mask_to_image(image_array, mask_array)
        
        # Step 5: Encode results to base64
        logger.info("📤 Encoding results to base64...")
        original_b64 = image_to_base64(image_array, format='png')
        masked_b64 = image_to_base64(masked_image, format='png')
        restored_b64 = image_to_base64(restored_image, format='png')
        
        processing_time_ms = (datetime.now() - start_time).total_seconds() * 1000
        
        response = RestoreResponse(
            success=True,
            original_image=original_b64,
            masked_image=masked_b64,
            restored_image=restored_b64,
            confidence_score=confidence_score,
            metrics=metrics,
            processing_time_ms=round(processing_time_ms, 2),
            timestamp=datetime.now().isoformat()
        )
        
        logger.info(f"✓ Request complete in {processing_time_ms:.0f}ms")
        return response
    
    except Exception as e:
        logger.error(f"✗ Restoration failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Restoration failed: {str(e)}")


@app.post("/api/upload-mask")
async def upload_custom_mask(file: UploadFile = File(...)):
    """
    Upload a custom mask file.
    
    Accepts PNG or JPEG files.
    Returns base64 encoded mask.
    """
    try:
        contents = await file.read()
        
        # Validate
        is_valid, error_msg = validate_image(contents)
        if not is_valid:
            raise HTTPException(status_code=400, detail=error_msg)
        
        # Decode
        mask_array = base64_to_image(f"data:image/png;base64,{__import__('base64').b64encode(contents).decode()}")
        
        # Convert to grayscale
        if len(mask_array.shape) == 3:
            mask_array = cv2.cvtColor(mask_array, cv2.COLOR_RGB2GRAY)
        
        mask_b64 = image_to_base64(mask_array, format='png')
        
        return JSONResponse({
            "success": True,
            "mask": mask_b64,
            "shape": mask_array.shape
        })
    
    except Exception as e:
        logger.error(f"✗ Mask upload failed: {e}")
        raise HTTPException(status_code=400, detail=f"Mask upload failed: {str(e)}")


@app.get("/api/generate-mask/{mask_type}")
async def generate_mask_endpoint(
    mask_type: str = 'irregular',
    width: int = 512,
    height: int = 512,
    ratio: float = 0.3
):
    """
    Generate a mask of specified type.
    
    Parameters:
    - mask_type: 'irregular', 'center', 'rectangular', 'random_brush'
    - width, height: mask dimensions
    - ratio: mask coverage ratio [0, 1]
    """
    try:
        if ratio < 0 or ratio > 1:
            raise ValueError("ratio must be between 0 and 1")
        
        mask_array = generate_random_mask(
            (height, width),
            mask_type=mask_type,
            mask_ratio=ratio
        )
        
        mask_b64 = image_to_base64(mask_array, format='png')
        
        return JSONResponse({
            "success": True,
            "mask": mask_b64,
            "type": mask_type,
            "shape": mask_array.shape
        })
    
    except Exception as e:
        logger.error(f"✗ Mask generation failed: {e}")
        raise HTTPException(status_code=400, detail=f"Mask generation failed: {str(e)}")


@app.get("/")
async def root():
    """Root endpoint with API documentation."""
    return {
        "message": "Forensic GAN Platform - Backend",
        "version": "1.0.0",
        "endpoints": {
            "health": "GET /health",
            "restore": "POST /api/restore",
            "upload_mask": "POST /api/upload-mask",
            "generate_mask": "GET /api/generate-mask/{mask_type}",
            "docs": "/docs"
        }
    }


# ============================================================================
# Error Handlers
# ============================================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Custom HTTP exception handler."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": exc.detail,
            "status_code": exc.status_code
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Catch-all exception handler."""
    logger.error(f"✗ Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Internal server error",
            "status_code": 500
        }
    )


# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    logger.info("Starting Forensic GAN Backend with Uvicorn...")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
