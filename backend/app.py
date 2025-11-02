"""
FastAPI Backend Application for SmartResume AI
Main application with API endpoints for resume tailoring
"""

import os
import logging
import shutil
from typing import Optional, List
from datetime import datetime
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uvicorn
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import our custom modules  
try:
    # Try relative imports first (for uvicorn module loading)
    from .resume_parser import ResumeParser
    from .file_generator import FileGenerator
except ImportError:
    # Fall back to absolute imports (for direct execution)
    from resume_parser import ResumeParser
    from file_generator import FileGenerator
# Note: job_parser, AITailor and RAGEngine are imported lazily to avoid startup crashes

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="SmartResume AI API",
    description="AI-powered resume tailoring and optimization service",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
resume_parser = ResumeParser()
file_generator = FileGenerator()
# job_parser, ai_tailor, and rag_engine are initialized lazily

# Ensure directories exist
os.makedirs("uploads", exist_ok=True)
os.makedirs("outputs", exist_ok=True)

# Pydantic models for request/response
class TailorRequest(BaseModel):
    job_description: str
    preferences: Optional[dict] = {}

class TailorResponse(BaseModel):
    tailored_resume: str
    original_resume: str = ""
    improvement_metrics: dict = {}
    improvement_notes: List[str] = []
    tokens_used: int
    method: str = "standard"
    agents_used: List[str] = []
    processing_messages: List[str] = []
    status: str

class TailoringResponse(BaseModel):
    tailored_resume: str
    improvement_score: float
    keyword_matches: int
    keyword_percentage: float
    readability_score: float
    ats_score: float
    tokens_used: int
    method: str = "standard"
    rag_context_summary: str = ""
    status: str

class AnalysisResponse(BaseModel):
    overall_score: float
    keyword_score: float
    structure_score: float
    skills_score: float
    experience_score: float
    matched_keywords: List[str]
    missing_keywords: List[str]
    recommendations: List[str]
    status: str

class JobAnalysisResponse(BaseModel):
    keywords: List[str]
    technical_skills: List[str]
    soft_skills: List[str]
    requirements: List[str]
    experience_level: str
    status: str

# Global variables to store session data
session_data = {}

# @app.on_event("startup")
# async def startup_event():
#     """Initialize components on startup"""
#     logger.info("Starting SmartResume AI API...")
#     
#     # Try to initialize AI Tailor if API key is available
#     try:
#         global ai_tailor
#         ai_tailor = AITailor()
#         logger.info("AI Tailor initialized successfully with Groq")
#     except Exception as e:
#         logger.warning(f"AI Tailor initialization failed: {str(e)}")
#         logger.info("AI features will be disabled until Groq API key is configured")

# Initialize components lazily to avoid startup crashes
logger.info("Starting SmartResume AI API...")

# Global variables for lazy initialization
rag_engine = None
ai_tailor = None
job_parser = None

def get_rag_engine():
    """Lazy initialization of RAG Engine"""
    global rag_engine
    if rag_engine is None:
        try:
            try:
                from .rag_engine import RAGEngine
            except ImportError:
                from rag_engine import RAGEngine
            rag_engine = RAGEngine()
            logger.info("RAG Engine initialized successfully")
        except Exception as e:
            logger.warning(f"RAG Engine initialization failed: {str(e)}")
            rag_engine = False  # Mark as failed to avoid repeated attempts
    return rag_engine if rag_engine is not False else None

def get_ai_tailor():
    """Lazy initialization of AI Tailor"""
    global ai_tailor
    if ai_tailor is None:
        try:
            try:
                from .ai_tailor import AITailor
            except ImportError:
                from ai_tailor import AITailor
            ai_tailor = AITailor()
            logger.info("AI Tailor initialized successfully with Groq")
        except Exception as e:
            logger.warning(f"AI Tailor initialization failed: {str(e)}")
            ai_tailor = False  # Mark as failed to avoid repeated attempts
    return ai_tailor if ai_tailor is not False else None

def get_job_parser():
    """Lazy initialization of Job Parser"""
    global job_parser
    if job_parser is None:
        try:
            try:
                from .job_parser import JobParser
            except ImportError:
                from job_parser import JobParser
            job_parser = JobParser()
            logger.info("Job Parser initialized successfully")
        except Exception as e:
            logger.warning(f"Job Parser initialization failed: {str(e)}")
            job_parser = False  # Mark as failed to avoid repeated attempts
    return job_parser if job_parser is not False else None

@app.get("/")
async def root():
    """Root endpoint with API information"""
    ai_tailor_instance = get_ai_tailor()
    return {
        "message": "Welcome to SmartResume AI API",
        "version": "1.0.0",
        "docs": "/docs",
        "status": "active",
        "ai_enabled": ai_tailor_instance is not None
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    ai_tailor_instance = get_ai_tailor()
    rag_engine_instance = get_rag_engine()
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "model_loaded": ai_tailor_instance is not None,
        "components": {
            "resume_parser": "active",
            "job_parser": "active", 
            "ai_tailor": "active" if ai_tailor_instance else "disabled",
            "rag_engine": "active" if rag_engine_instance else "disabled",
            "file_generator": "active"
        }
    }

@app.post("/upload-resume")
async def upload_resume(file: UploadFile = File(...)):
    """
    Upload and parse a resume file
    Supports PDF, DOCX, and TXT formats
    """
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
        
        # Parse resume
        result = resume_parser.extract_text(
            file_content=file_content,
            filename=file.filename
        )
        
        if result['status'] == 'error':
            raise HTTPException(status_code=400, detail=result.get('error', 'Failed to parse resume'))
        
        # Store in session (in production, use proper session management)
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

@app.post("/analyze-job")
async def analyze_job_description(job_description: str = Form(...)):
    """
    Analyze a job description and extract key information
    """
    try:
        if not job_description.strip():
            raise HTTPException(status_code=400, detail="Job description cannot be empty")
        
        # Get Job Parser instance
        job_parser_instance = get_job_parser()
        if not job_parser_instance:
            raise HTTPException(status_code=503, detail="Job Parser service is not available")
        
        # Parse job description
        result = job_parser_instance.parse_job_description(job_description)
        
        if result['status'] == 'error':
            raise HTTPException(status_code=400, detail=result.get('error', 'Failed to parse job description'))
        
        return JobAnalysisResponse(
            keywords=result['keywords'],
            technical_skills=result['technical_skills'],
            soft_skills=result['soft_skills'],
            requirements=result['requirements'],
            experience_level=result['experience_level'],
            status=result['status']
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing job description: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/tailor-resume/{session_id}")
async def tailor_resume(session_id: str, request: TailorRequest):
    """
    Tailor a resume based on job description using AI
    """
    try:
        # Get AI Tailor instance
        ai_tailor_instance = get_ai_tailor()
        if not ai_tailor_instance:
            raise HTTPException(
                status_code=503,
                detail="AI service not available. Please configure Groq API key."
            )
        
        # Get resume data from session
        if session_id not in session_data:
            raise HTTPException(status_code=404, detail="Session not found. Please upload resume first.")
        
        resume_data = session_data[session_id]['resume_data']
        resume_text = resume_data['formatted_text']
        
        if not resume_text.strip():
            raise HTTPException(status_code=400, detail="Resume text is empty")
        
        if not request.job_description.strip():
            raise HTTPException(status_code=400, detail="Job description cannot be empty")
        
        # Get AI Tailor instance
        ai_tailor_instance = get_ai_tailor()
        if not ai_tailor_instance:
            raise HTTPException(status_code=503, detail="AI Tailor service is not available")
        
        # Tailor the resume
        result = ai_tailor_instance.tailor_resume(
            resume_text=resume_text,
            job_description=request.job_description,
            user_preferences=request.preferences
        )
        
        if result['status'] == 'error':
            raise HTTPException(status_code=500, detail=result.get('error', 'Failed to tailor resume'))
        
        # Store tailored resume in session
        session_data[session_id]['tailored_resume'] = result
        session_data[session_id]['job_description'] = request.job_description
        
        return TailorResponse(
            tailored_resume=result['tailored_resume'],
            original_resume=result['original_resume'],
            improvement_metrics=result['improvement_metrics'],
            tokens_used=result['tokens_used'],
            status=result['status']
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error tailoring resume: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/tailor-resume-rag/{session_id}")
async def tailor_resume_with_rag(
    session_id: str,
    job_description: str = Form(...),
    tone: str = Form("professional"),
    focus_areas: str = Form("")
):
    """
    Tailor resume using RAG (Retrieval-Augmented Generation) for enhanced relevance
    """
    try:
        # Get AI Tailor instance
        ai_tailor_instance = get_ai_tailor()
        if not ai_tailor_instance:
            raise HTTPException(
                status_code=503,
                detail="AI service not available. Please configure Groq API key."
            )
        
        # Get resume data from session
        if session_id not in session_data:
            raise HTTPException(status_code=404, detail="Session not found. Please upload resume first.")
        
        session = session_data[session_id]
        resume_data = session['resume_data']
        
        # Parse focus areas
        focus_list = [area.strip() for area in focus_areas.split(",") if area.strip()] if focus_areas else []
        
        # Get AI Tailor instance
        ai_tailor_instance = get_ai_tailor()
        if not ai_tailor_instance:
            raise HTTPException(status_code=503, detail="AI Tailor service is not available")
        
        # Perform RAG-enhanced tailoring
        logger.info(f"🚀 Starting RAG-enhanced resume tailoring for session {session_id}")
        result = ai_tailor_instance.tailor_resume_with_rag(
            resume_data=resume_data,
            job_description=job_description,
            tone=tone,
            focus_areas=focus_list
        )
        
        if result['status'] == 'error':
            raise HTTPException(status_code=500, detail=result.get('error', 'Failed to tailor resume'))
        
        # Store result in session
        session_data[session_id]['tailored_resume_rag'] = result
        
        return TailoringResponse(
            tailored_resume=result['tailored_resume'],
            improvement_score=result['improvement_metrics'].get('improvement_score', 0),
            keyword_matches=result['improvement_metrics'].get('keyword_matches', 0),
            keyword_percentage=result['improvement_metrics'].get('keyword_percentage', 0),
            readability_score=result['improvement_metrics'].get('readability_score', 0),
            ats_score=result['improvement_metrics'].get('ats_score', 0),
            tokens_used=result.get('tokens_used', 0),
            method=result.get('method', 'rag_enhanced'),
            rag_context_summary=result.get('rag_context', {}).get('context_summary', ''),
            status=result['status']
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in RAG-enhanced tailoring: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/tailor-resume-agents/{session_id}")
async def tailor_resume_with_agents(session_id: str, request: TailorRequest):
    """
    🤖 PREMIUM: Tailor resume using Multi-Agent System for PERFECT formatting
    This endpoint solves the text jamming issue using specialized agents!
    """
    try:
        # Get AI Tailor instance  
        ai_tailor_instance = get_ai_tailor()
        if not ai_tailor_instance:
            raise HTTPException(
                status_code=503,
                detail="AI service not available. Please configure Groq API key."
            )
        
        # Get resume data from session
        if session_id not in session_data:
            raise HTTPException(status_code=404, detail="Session not found. Please upload resume first.")
        
        session = session_data[session_id]
        original_resume = session['resume_data']['formatted_text']
        
        # Use the multi-agent system
        result = ai_tailor_instance.tailor_resume_with_agents(
            resume_text=original_resume,
            job_description=request.job_description
        )
        
        if result['status'] != 'success':
            raise HTTPException(status_code=500, detail=result.get('error', 'Failed to tailor resume with agents'))

        # Store result
        session_data[session_id]['tailored_resume_agents'] = result
        
        return TailorResponse(
            tailored_resume=result['tailored_resume'],
            improvement_notes=result.get('improvement_notes', []),
            tokens_used=result.get('tokens_used', 3),
            method=result.get('method', 'multi_agent_langraph'),
            agents_used=result.get('agents_used', []),
            processing_messages=result.get('processing_messages', []),
            status=result['status']
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in multi-agent tailoring: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analyze-ats/{session_id}")
async def analyze_ats_score(session_id: str, job_description: str = Form(...)):
    """
    Analyze ATS compatibility score for a resume against job description
    """
    try:
        # Get AI Tailor instance
        ai_tailor_instance = get_ai_tailor()
        if not ai_tailor_instance:
            raise HTTPException(
                status_code=503,
                detail="AI service not available. Please configure Groq API key."
            )
        
        # Get resume data from session
        if session_id not in session_data:
            raise HTTPException(status_code=404, detail="Session not found. Please upload resume first.")
        
        # Use tailored resume if available, otherwise use original
        session = session_data[session_id]
        if 'tailored_resume' in session:
            resume_text = session['tailored_resume']['tailored_resume']
        else:
            resume_text = session['resume_data']['formatted_text']
        
        # Get AI Tailor instance
        ai_tailor_instance = get_ai_tailor()
        if not ai_tailor_instance:
            raise HTTPException(status_code=503, detail="AI Tailor service is not available")
        
        # Analyze ATS score
        result = ai_tailor_instance.analyze_ats_score(resume_text, job_description)
        
        if result['status'] == 'error':
            raise HTTPException(status_code=500, detail=result.get('error', 'Failed to analyze ATS score'))
        
        return AnalysisResponse(
            overall_score=result.get('overall_score', 0),
            keyword_score=result.get('keyword_score', 0),
            structure_score=result.get('structure_score', 0),
            skills_score=result.get('skills_score', 0),
            experience_score=result.get('experience_score', 0),
            matched_keywords=result.get('matched_keywords', []),
            missing_keywords=result.get('missing_keywords', []),
            recommendations=result.get('recommendations', []),
            status=result['status']
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing ATS score: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate-files/{session_id}")
async def generate_resume_files(
    session_id: str,
    format: str = Form(..., regex="^(pdf|docx|both)$"),
    style: str = Form(default="modern", regex="^(modern|classic|minimal)$")
):
    """
    Generate downloadable resume files in specified format(s)
    """
    try:
        # Get session data
        if session_id not in session_data:
            raise HTTPException(status_code=404, detail="Session not found. Please upload resume first.")
        
        session = session_data[session_id]
        
        # Use tailored resume if available, otherwise use original
        if 'tailored_resume' in session:
            resume_text = session['tailored_resume']['tailored_resume']
            base_filename = f"tailored_resume_{session_id}"
        else:
            resume_text = session['resume_data']['formatted_text']
            base_filename = f"resume_{session_id}"
        
        # Generate files
        if format == "both":
            result = file_generator.generate_both_formats(resume_text, base_filename, style)
        elif format == "pdf":
            result = file_generator.generate_pdf(resume_text, f"{base_filename}.pdf", style)
        elif format == "docx":
            result = file_generator.generate_docx(resume_text, f"{base_filename}.docx", style)
        
        # Store file info in session
        session_data[session_id]['generated_files'] = result
        
        return {
            "session_id": session_id,
            "generated_files": result,
            "download_links": {
                "pdf": f"/download/{session_id}/pdf" if format in ["pdf", "both"] else None,
                "docx": f"/download/{session_id}/docx" if format in ["docx", "both"] else None
            },
            "status": "success"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating files: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/download/{session_id}/{file_format}")
async def download_resume(session_id: str, file_format: str):
    """
    Download generated resume file
    """
    try:
        if session_id not in session_data:
            raise HTTPException(status_code=404, detail="Session not found")
        
        session = session_data[session_id]
        if 'generated_files' not in session:
            raise HTTPException(status_code=404, detail="No generated files found")
        
        generated_files = session['generated_files']
        
        # Handle both single format and both formats responses
        if file_format in generated_files:
            file_info = generated_files[file_format]
        elif file_format == "pdf" and 'pdf' in generated_files:
            file_info = generated_files['pdf']
        elif file_format == "docx" and 'docx' in generated_files:
            file_info = generated_files['docx']
        else:
            raise HTTPException(status_code=404, detail=f"File format {file_format} not found")
        
        if file_info['status'] != 'success':
            raise HTTPException(status_code=500, detail="File generation failed")
        
        file_path = file_info['file_path']
        filename = file_info['filename']
        
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="File not found")
        
        return FileResponse(
            path=file_path,
            filename=filename,
            media_type='application/octet-stream'
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading file: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/cover-letter/{session_id}")
async def generate_cover_letter(
    session_id: str,
    job_description: str = Form(...),
    company_name: str = Form(default=""),
    position_title: str = Form(default="")
):
    """
    Generate a tailored cover letter
    """
    try:
        # Get AI Tailor instance
        ai_tailor_instance = get_ai_tailor()
        if not ai_tailor_instance:
            raise HTTPException(
                status_code=503,
                detail="AI service not available. Please configure Groq API key."
            )
        
        # Get resume data from session
        if session_id not in session_data:
            raise HTTPException(status_code=404, detail="Session not found. Please upload resume first.")
        
        session = session_data[session_id]
        
        # Use tailored resume if available, otherwise use original
        if 'tailored_resume' in session:
            resume_text = session['tailored_resume']['tailored_resume']
        else:
            resume_text = session['resume_data']['formatted_text']
        
        # Generate cover letter
        result = ai_tailor_instance.generate_cover_letter(
            resume_text=resume_text,
            job_description=job_description,
            company_name=company_name,
            position_title=position_title
        )
        
        if result['status'] == 'error':
            raise HTTPException(status_code=500, detail=result.get('error', 'Failed to generate cover letter'))
        
        return {
            "cover_letter": result['cover_letter'],
            "company_name": company_name,
            "position_title": position_title,
            "tokens_used": result['tokens_used'],
            "status": result['status']
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating cover letter: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/cleanup")
async def cleanup_files(background_tasks: BackgroundTasks):
    """
    Clean up old files and sessions
    """
    try:
        background_tasks.add_task(file_generator.cleanup_old_files, 24)  # Clean files older than 24 hours
        
        # Clean up old sessions (older than 1 hour)
        current_time = datetime.now().timestamp()
        sessions_to_remove = []
        
        for session_id, session_info in session_data.items():
            if 'uploaded_at' in session_info:
                upload_time = datetime.fromisoformat(session_info['uploaded_at']).timestamp()
                if current_time - upload_time > 3600:  # 1 hour
                    sessions_to_remove.append(session_id)
        
        for session_id in sessions_to_remove:
            del session_data[session_id]
        
        return {
            "message": "Cleanup initiated",
            "sessions_removed": len(sessions_to_remove),
            "status": "success"
        }
        
    except Exception as e:
        logger.error(f"Error during cleanup: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/configure-api-key")
async def configure_api_key(api_key: str = Form(...)):
    """
    Configure Groq API key for AI features
    """
    try:
        try:
            from .ai_tailor import AITailor
        except ImportError:
            from ai_tailor import AITailor
        global ai_tailor
        ai_tailor = AITailor(api_key=api_key)
        
        return {
            "message": "AI features enabled successfully with Groq",
            "status": "success"
        }
        
    except Exception as e:
        logger.error(f"Error configuring API key: {str(e)}")
        raise HTTPException(status_code=400, detail="Invalid API key or configuration failed")

if __name__ == "__main__":
    # Commented out to prevent conflicts when running with uvicorn directly
    # uvicorn.run(
    #     "app:app",
    #     host="0.0.0.0",
    #     port=8001,
    #     reload=True,
    #     log_level="info"
    # )
    print("⚠️ Please use: uvicorn backend.app:app --host 0.0.0.0 --port 8001")
    print("🚀 Starting SmartResume AI API server...")