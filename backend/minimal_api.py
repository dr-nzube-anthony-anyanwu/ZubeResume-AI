"""
Minimal FastAPI app to test basic server functionality
This removes the multi-agent endpoint to isolate the issue
"""

import os
import logging
from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from datetime import datetime
import uvicorn

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="SmartResume AI API - Minimal",
    description="Minimal version for troubleshooting",
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

# Basic models
class TailorRequest(BaseModel):
    job_description: str
    preferences: dict = {}

# Initialize basic components
try:
    from resume_parser import ResumeParser
    resume_parser = ResumeParser()
    logger.info("✅ Resume parser loaded")
except Exception as e:
    logger.warning(f"❌ Resume parser failed: {e}")
    resume_parser = None

# Global session storage
session_data = {}

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "SmartResume AI API - Minimal Version",
        "version": "1.0.0-minimal",
        "status": "active"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "components": {
            "resume_parser": "active" if resume_parser else "disabled"
        }
    }

@app.post("/upload-resume")
async def upload_resume(file: UploadFile = File(...)):
    """Upload and parse a resume file"""
    try:
        # Validate file type
        allowed_extensions = ['.pdf', '.docx', '.txt']
        file_extension = os.path.splitext(file.filename)[1].lower()
        
        if file_extension not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type. Allowed: {', '.join(allowed_extensions)}"
            )
        
        # Save uploaded file
        file_content = await file.read()
        
        if not resume_parser:
            raise HTTPException(status_code=503, detail="Resume parser not available")
        
        # Parse resume
        result = resume_parser.extract_text(
            file_content=file_content,
            filename=file.filename
        )
        
        if result['status'] == 'error':
            raise HTTPException(status_code=400, detail=result.get('error', 'Failed to parse resume'))
        
        # Store in session
        session_id = f"session_{datetime.now().timestamp()}"
        session_data[session_id] = {
            'resume_data': result,
            'filename': file.filename,
            'uploaded_at': datetime.now().isoformat()
        }
        
        return {
            "session_id": session_id,
            "filename": file.filename,
            "file_type": result['file_type'],
            "word_count": result['word_count'],
            "preview": result['formatted_text'][:500] + "..." if len(result['formatted_text']) > 500 else result['formatted_text'],
            "sections": list(result['sections'].keys()),
            "status": "success"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading resume: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

logger.info("✅ Minimal SmartResume API initialized")