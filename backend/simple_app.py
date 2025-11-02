"""
Simplified backend app for troubleshooting
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import logging
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="SmartResume AI API - Simplified",
    description="Simplified version for troubleshooting",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Basic components that work
try:
    from resume_parser import ResumeParser
    resume_parser = ResumeParser()
    logger.info("✅ Resume parser loaded")
except Exception as e:
    logger.warning(f"❌ Resume parser failed: {e}")
    resume_parser = None

@app.get("/")
async def root():
    return {
        "message": "SmartResume AI API - Simplified Version",
        "status": "active",
        "version": "1.0.0-simplified"
    }

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "components": {
            "resume_parser": "active" if resume_parser else "disabled"
        }
    }

@app.get("/test")
async def test():
    return {"message": "Test endpoint working", "status": "ok"}

logger.info("✅ Simplified SmartResume API initialized")