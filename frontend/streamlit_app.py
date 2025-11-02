"""
Streamlit Frontend for ZubeResume AI
User-friendly interface for resume tailoring
"""

import streamlit as st

# Configure page - MUST BE FIRST STREAMLIT COMMAND
st.set_page_config(
    page_title="ZubeResume AI",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

import requests
import json
import os
import sys
from datetime import datetime
import base64
from io import BytesIO
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
load_dotenv()

# Add parent directory to path for hybrid backend
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import hybrid backend
try:
    from backend.hybrid_backend import get_smart_resume
    HYBRID_MODE = True
    # Backend loaded successfully (no user message needed)
except ImportError as e:
    HYBRID_MODE = False
    st.error(f"⚠️ Hybrid backend not available: {e}")

# If hybrid mode is available, preload heavy backend components so the first
# user action (parse/tailor) isn't delayed by model initializations.
if HYBRID_MODE:
    try:
        # Preload backend components silently in background
        get_smart_resume()
        # Backend preloaded successfully (no user message needed)
    except Exception as _e:
        st.warning(f"Backend initialization encountered an issue: {_e}")

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        text-align: center;
        color: #2C3E50;
        margin-bottom: 2rem;
    }
    .upload-section {
        background-color: #f8f9fa;
        padding: 2rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    .results-section {
        background-color: #ffffff;
        padding: 2rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin: 1rem 0;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 8px;
        text-align: center;
        margin: 0.5rem;
    }
    .success-message {
        background-color: #d4edda;
        color: #155724;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
    .error-message {
        background-color: #f8d7da;
        color: #721c24;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Backend API configuration
API_BASE_URL = "http://localhost:8001"

# Initialize session state
if 'session_id' not in st.session_state:
    st.session_state.session_id = None
if 'resume_uploaded' not in st.session_state:
    st.session_state.resume_uploaded = False
if 'tailored_resume' not in st.session_state:
    st.session_state.tailored_resume = None
if 'job_analysis' not in st.session_state:
    st.session_state.job_analysis = None
if 'ats_analysis' not in st.session_state:
    st.session_state.ats_analysis = None

def check_api_status():
    """Check if the backend API is running"""
    # In hybrid mode, we don't need the API server
    if HYBRID_MODE:
        return True
    
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        return response.status_code == 200
    except:
        return False

def upload_resume(uploaded_file):
    """Upload resume using hybrid backend or API"""
    try:
        if HYBRID_MODE:
            # Use hybrid backend directly
            smart_resume = get_smart_resume()
            result = smart_resume.upload_resume(uploaded_file)
            
            if result['status'] == 'success':
                st.success(f"✅ Resume uploaded successfully: {result['filename']}")
                return result
            else:
                st.error(f"❌ Upload failed: {result.get('error', 'Unknown error')}")
                return None
        else:
            # Fallback to API mode
            files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
            
            # Debug information
            st.info(f"🔄 Uploading {uploaded_file.name} ({uploaded_file.type}) to {API_BASE_URL}/upload-resume")
            
            response = requests.post(f"{API_BASE_URL}/upload-resume", files=files)
            
            st.info(f"📡 Backend response status: {response.status_code}")
            
            if response.status_code == 200:
                return response.json()
            else:
                error_text = response.text
                st.error(f"Upload failed (Status {response.status_code}): {error_text}")
                return None
    except Exception as e:
        st.error(f"Error uploading resume: {str(e)}")
        return None

def analyze_job_description(job_description):
    """Analyze job description"""
    try:
        if HYBRID_MODE:
            # Use hybrid backend directly
            smart_resume = get_smart_resume()
            result = smart_resume.analyze_job_description(job_description)
            
            if result['status'] == 'success':
                return result
            else:
                st.error(f"Job analysis failed: {result.get('error', 'Unknown error')}")
                return None
        else:
            # Use API endpoint
            data = {"job_description": job_description}
            response = requests.post(f"{API_BASE_URL}/analyze-job", data=data)
            
            if response.status_code == 200:
                return response.json()
            else:
                st.error(f"Job analysis failed: {response.text}")
                return None
    except Exception as e:
        st.error(f"Error analyzing job description: {str(e)}")
        return None

def tailor_resume(session_id, job_description, preferences=None):
    """Tailor resume using AI"""
    try:
        if HYBRID_MODE:
            # Use hybrid backend directly
            smart_resume = get_smart_resume()
            result = smart_resume.tailor_resume_standard(session_id, job_description, preferences)
            
            if result['status'] == 'success':
                st.success("✅ Resume tailoring completed!")
                return result
            else:
                st.error(f"❌ Resume tailoring failed: {result.get('error', 'Unknown error')}")
                return None
        else:
            # Use API endpoint
            data = {
                "job_description": job_description,
                "preferences": preferences or {}
            }
            response = requests.post(
                f"{API_BASE_URL}/tailor-resume/{session_id}",
                json=data
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                error_detail = response.json().get('detail', 'Unknown error')
                st.error(f"Resume tailoring failed: {error_detail}")
                return None
    except Exception as e:
        st.error(f"Error tailoring resume: {str(e)}")
        return None

def tailor_resume_with_rag(session_id, job_description, tone="professional", focus_areas=""):
    """Tailor resume using RAG (Retrieval-Augmented Generation) for enhanced relevance"""
    try:
        if HYBRID_MODE:
            # Use hybrid backend directly
            smart_resume = get_smart_resume()
            focus_list = [area.strip() for area in focus_areas.split(",") if area.strip()] if focus_areas else []
            result = smart_resume.tailor_resume_with_rag(session_id, job_description, tone, focus_list)
            
            if result['status'] == 'success':
                st.success("🔍 RAG-enhanced tailoring completed!")
                return result
            else:
                st.error(f"❌ RAG-enhanced tailoring failed: {result.get('error', 'Unknown error')}")
                return None
        else:
            # Use API endpoint
            data = {
                "job_description": job_description,
                "tone": tone,
                "focus_areas": focus_areas
            }
            response = requests.post(
                f"{API_BASE_URL}/tailor-resume-rag/{session_id}",
                data=data
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                error_detail = response.json().get('detail', 'Unknown error')
                st.error(f"RAG-enhanced tailoring failed: {error_detail}")
                return None
    except Exception as e:
        st.error(f"Error in RAG-enhanced tailoring: {str(e)}")
        return None

def tailor_resume_with_agents(session_id, job_description):
    """🤖 PREMIUM: Tailor resume using Multi-Agent System for PERFECT formatting"""
    try:
        if HYBRID_MODE:
            # Use hybrid backend directly
            smart_resume = get_smart_resume()
            result = smart_resume.tailor_resume_with_agents(session_id, job_description)
            
            if result['status'] == 'success':
                st.success("🎉 Multi-agent tailoring completed! Text jamming issues resolved!")
                return result
            else:
                st.error(f"❌ Multi-agent tailoring failed: {result.get('error', 'Unknown error')}")
                return None
        else:
            # Fallback to API mode
            data = {"job_description": job_description}
            response = requests.post(
                f"{API_BASE_URL}/tailor-resume-agents/{session_id}",
                json=data
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                error_detail = response.text
                try:
                    error_json = response.json()
                    error_detail = error_json.get('detail', response.text)
                except:
                    pass
                st.error(f"Multi-agent tailoring failed: {error_detail}")
                return None
    except Exception as e:
        st.error(f"Error in multi-agent tailoring: {str(e)}")
        return None

def analyze_ats_score(session_id, job_description):
    """Analyze ATS compatibility score using hybrid backend"""
    try:
        if HYBRID_MODE:
            # Use hybrid backend for ATS analysis
            smart_resume = get_smart_resume()
            return smart_resume.analyze_ats_score(session_id, job_description)
        else:
            # Fallback to API mode (legacy)
            data = {"job_description": job_description}
            response = requests.post(
                f"{API_BASE_URL}/analyze-ats/{session_id}",
                data=data
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                st.error(f"ATS analysis failed: {response.text}")
                return None
    except Exception as e:
        st.error(f"Error analyzing ATS score: {str(e)}")
        return None

def generate_files(session_id, file_format="both", style="modern"):
    """Generate downloadable files"""
    try:
        if HYBRID_MODE:
            # Use hybrid backend directly
            smart_resume = get_smart_resume()
            result = smart_resume.generate_files(session_id, file_format, style)
            
            if result['status'] == 'success':
                st.success("📄 Files generated successfully!")
                return result
            else:
                st.error(f"❌ File generation failed: {result.get('error', 'Unknown error')}")
                return None
        else:
            # Use API endpoint
            data = {
                "format": file_format,
                "style": style
            }
            response = requests.post(
                f"{API_BASE_URL}/generate-files/{session_id}",
                data=data
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                st.error(f"File generation failed: {response.text}")
                return None
    except Exception as e:
        st.error(f"Error generating files: {str(e)}")
        return None

def download_file(session_id, file_format):
    """Download generated file"""
    try:
        if HYBRID_MODE:
            smart_resume = get_smart_resume()
            data = smart_resume.get_generated_file_bytes(session_id, file_format)
            if data:
                return data
            else:
                st.error("Download failed: generated file not found or unavailable")
                return None

        # fallback to API
        response = requests.get(f"{API_BASE_URL}/download/{session_id}/{file_format}")
        
        if response.status_code == 200:
            return response.content
        else:
            st.error(f"Download failed: {response.text}")
            return None
    except Exception as e:
        st.error(f"Error downloading file: {str(e)}")
        return None

def configure_api_key(api_key):
    """Configure Groq API key"""
    try:
        data = {"api_key": api_key}
        response = requests.post(f"{API_BASE_URL}/configure-api-key", data=data)
        
        if response.status_code == 200:
            return True
        else:
            st.error(f"API key configuration failed: {response.text}")
            return False
    except Exception as e:
        st.error(f"Error configuring API key: {str(e)}")
        return False

def check_api_key_configured():
    """Check if Groq API key is already configured"""
    # Check environment variable first
    env_api_key = os.getenv('GROQ_API_KEY')
    if env_api_key:
        return True, env_api_key
    return False, None

def main():
    """Main Streamlit application"""
    
    # Check if API key is configured
    api_key_configured, env_api_key = check_api_key_configured()
    
    # Header
    st.markdown('<h1 class="main-header">🚀 ZubeResume AI</h1>', unsafe_allow_html=True)
    
    # Tagline and Description
    st.markdown(
        '''
        <div style="text-align: center; margin: 20px 0;">
            <h2 style="color: #2E86C1; font-size: 1.8em; margin-bottom: 10px; font-weight: 600;">
                ✨ Smart Resumes, Brighter Futures ✨
            </h2>
            <p style="font-size: 1.2em; color: #34495e; line-height: 1.4; max-width: 800px; margin: 0 auto;">
                <strong>ZubeResume AI</strong> - The intelligent resume tailoring platform from <strong>ZubeVision Technologies</strong>. 
                Transform your career prospects with AI-powered resume optimization.
            </p>
        </div>
        ''', 
        unsafe_allow_html=True
    )
    
    # Check API status
    if not check_api_status():
        st.error("⚠️ Backend API is not running. Please start the FastAPI server first.")
        st.info("Run: `python backend/app.py` to start the backend server.")
        st.stop()
    
    # Sidebar configuration
    with st.sidebar:
        st.header("⚙️ Configuration")
        
    # Sidebar configuration
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # AI Service Status and Configuration
        st.subheader("🤖 AI Service Status")
        
        # Check current API status
        groq_configured = api_key_configured
        google_configured = bool(os.getenv('GOOGLE_API_KEY'))
        
        # Groq Status
        if groq_configured:
            st.success("✅ Groq API Key Configured")
            st.info("Primary AI service active")
        else:
            st.warning("⚠️ Groq API Key Missing")
            api_key = st.text_input(
                "Enter your Groq API key:",
                type="password",
                help="Primary AI service for resume tailoring. Get it free at console.groq.com"
            )
            
            if st.button("Configure Groq API Key"):
                if api_key:
                    if configure_api_key(api_key):
                        st.success("✅ Groq API key configured successfully!")
                        st.rerun()
                else:
                    st.warning("Please enter an API key")
        
        # Google Gemini Status and Configuration
        st.subheader("🔄 Google Gemini Fallback")
        
        if google_configured:
            st.success("✅ Google API Key Configured")
            st.info("Fallback service ready")
            
            # Test Google connection
            if st.button("Test Google Connection"):
                try:
                    from backend.google_fallback import GoogleGeminiFallback
                    google_fallback = GoogleGeminiFallback()
                    if google_fallback.initialized:
                        st.success("🚀 Google Gemini connection successful!")
                        status = google_fallback.get_status()
                        st.json(status)
                    else:
                        st.error("❌ Google Gemini initialization failed")
                except Exception as e:
                    st.error(f"❌ Google connection test failed: {e}")
        else:
            st.warning("⚠️ Google API Key Not Configured")
            st.info("Configure Google Gemini as fallback when Groq tokens are exhausted")
            
            google_key = st.text_input(
                "Enter your Google API key:",
                type="password",
                help="Free backup AI service. Get it at console.cloud.google.com"
            )
            
            if st.button("Configure Google API Key"):
                if google_key:
                    try:
                        # Add to .env file
                        env_path = Path(".env")
                        if env_path.exists():
                            with open(env_path, "a") as f:
                                f.write(f"\nGOOGLE_API_KEY={google_key}\n")
                        else:
                            with open(env_path, "w") as f:
                                f.write(f"GOOGLE_API_KEY={google_key}\n")
                        
                        # Set environment variable for current session
                        os.environ['GOOGLE_API_KEY'] = google_key
                        st.success("✅ Google API key configured successfully!")
                        st.info("Restart the app to fully activate Google fallback")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed to configure Google API key: {e}")
                else:
                    st.warning("Please enter a Google API key")
        
        # Service Priority Display
        st.subheader("🔗 AI Service Chain")
        if groq_configured and google_configured:
            st.success("1️⃣ Groq (Primary) → 2️⃣ Google Gemini (Fallback) → 3️⃣ Local Formatter")
        elif groq_configured:
            st.warning("1️⃣ Groq (Primary) → 2️⃣ Local Formatter ⚠️")
            st.info("💡 Add Google API for better reliability")
        elif google_configured:
            st.warning("1️⃣ Google Gemini (Primary) → 2️⃣ Local Formatter")
            st.info("💡 Add Groq API for faster processing")
        else:
            st.error("❌ No AI services configured - only basic formatting available")
        
        st.markdown("---")
        
        # AI Enhancement Method
        st.subheader("🧠 AI Enhancement")
        use_rag = st.checkbox(
            "Enable RAG Enhancement",
            value=True,
            help="Use Retrieval-Augmented Generation for more relevant resume tailoring"
        )
        
        if use_rag:
            st.info("🔥 RAG will analyze your resume content and find the most relevant experiences for each job!")
        
        st.markdown("---")
        
        # Style preferences
        st.subheader("Resume Style")
        resume_style = st.selectbox(
            "Choose resume style:",
            ["modern", "classic", "minimal"],
            help="Visual style for generated resume files"
        )
        
        # Advanced options
        with st.expander("Advanced Options"):
            focus_areas = st.multiselect(
                "Focus Areas:",
                ["Technical Skills", "Leadership", "Communication", "Problem Solving", "Innovation"],
                help="Areas to emphasize in tailored resume"
            )
            
            tone = st.selectbox(
                "Tone:",
                ["professional", "confident", "friendly"],
                help="Writing tone for the tailored resume"
            )
    
    # Check if API key is configured before showing main functionality
    if not api_key_configured:
        st.markdown('<div class="upload-section">', unsafe_allow_html=True)
        st.error("🔑 **Groq API Key Required**")
        st.markdown("""
        Please configure your Groq API key to use ZubeResume AI:
        
        1. **Get a FREE API key** from [console.groq.com](https://console.groq.com/)
        2. **Add it to your .env file** in the project directory:
           ```
           GROQ_API_KEY=your_api_key_here
           ```
        3. **Restart the application**
        
        Or enter it in the sidebar configuration panel.
        """)
        st.markdown('</div>', unsafe_allow_html=True)
        st.stop()
    
    # Main content area
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown('<div class="upload-section">', unsafe_allow_html=True)
        st.header("📄 Upload Resume")
        
        uploaded_file = st.file_uploader(
            "Choose your resume file:",
            type=['pdf', 'docx', 'txt'],
            help="Supported formats: PDF, DOCX, TXT"
        )
        
        if uploaded_file is not None:
            if st.button("Parse Resume", type="primary"):
                with st.spinner("Parsing resume..."):
                    result = upload_resume(uploaded_file)
                    
                    if result:
                        st.session_state.session_id = result['session_id']
                        st.session_state.resume_uploaded = True
                        
                        st.success("✅ Resume uploaded and parsed successfully!")
                        
                        # Display resume info
                        st.info(f"""
                        **File:** {result['filename']}  
                        **Type:** {result['file_type']}  
                        **Words:** {result['word_count']}  
                        **Sections:** {', '.join(result['sections'])}
                        """)
                        
                        # Preview
                        with st.expander("📖 Resume Preview"):
                            st.text_area("Parsed Content:", result['preview'], height=200, disabled=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="upload-section">', unsafe_allow_html=True)
        st.header("💼 Job Description")
        
        job_description = st.text_area(
            "Paste the job description:",
            height=200,
            placeholder="Paste the job posting description here..."
        )
        
        if st.button("Analyze Job", type="secondary"):
            if job_description:
                with st.spinner("Analyzing job description..."):
                    analysis = analyze_job_description(job_description)
                    
                    if analysis:
                        st.session_state.job_analysis = analysis
                        st.success("✅ Job description analyzed!")
                        
                        # Display analysis
                        st.info(f"""
                        **Experience Level:** {analysis['experience_level']}  
                        **Technical Skills:** {len(analysis['technical_skills'])} found  
                        **Key Requirements:** {len(analysis['requirements'])} identified
                        """)
            else:
                st.warning("Please enter a job description")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Resume Tailoring Section
    if st.session_state.resume_uploaded and job_description:
        st.markdown('<div class="results-section">', unsafe_allow_html=True)
        st.header("🎯 AI Resume Tailoring")
        
        col1, col2, col3 = st.columns([1, 1, 1])
        
        with col1:
            if use_rag:
                button_text = "🧠 RAG-Enhanced Tailoring"
                spinner_text = "RAG is analyzing and tailoring your resume..."
            else:
                button_text = "✨ Standard Tailoring"
                spinner_text = "AI is tailoring your resume..."
                
            if st.button(button_text, type="primary", use_container_width=True):
                with st.spinner(spinner_text):
                    if use_rag:
                        result = tailor_resume_with_rag(
                            st.session_state.session_id, 
                            job_description, 
                            tone, 
                            focus_areas
                        )
                    else:
                        preferences = {
                            "tone": tone,
                            "focus_areas": focus_areas
                        }
                        result = tailor_resume(st.session_state.session_id, job_description, preferences)
                    
                    if result:
                        st.session_state.tailored_resume = result
                        if use_rag and result.get('rag_context_summary'):
                            st.success(f"✅ RAG-Enhanced tailoring completed!")
                            st.info(f"🔍 Context Used: {result['rag_context_summary']}")
                        else:
                            st.success("✅ Resume tailored successfully!")
        
        # 🤖 PREMIUM: Multi-Agent System Row
        st.markdown("---")
        st.markdown("### 🤖 **PREMIUM: Multi-Agent System** - *Eliminates Text Jamming Issues*")
        
        col_agent = st.columns(1)[0]
        with col_agent:
            st.info("🎯 **3 Specialized Agents**: Content Agent, Formatting Agent, Document Agent + Supervisor")
            if st.button("🤖 Multi-Agent Perfect Formatting", type="primary", use_container_width=True, 
                        help="Uses 3 specialized agents to ensure perfect formatting and eliminate text jamming"):
                with st.spinner("🤖 Multi-Agent System is processing your resume..."):
                    agent_result = tailor_resume_with_agents(
                        st.session_state.session_id, 
                        job_description
                    )
                    
                    if agent_result:
                        st.session_state.tailored_resume = agent_result
                        st.success("🎉 Multi-Agent System completed successfully!")
                        st.info(f"🤖 **Agents Used**: {', '.join(agent_result.get('agents_used', []))}")
                        st.info(f"📝 **Processing Steps**: {len(agent_result.get('processing_messages', []))}")
                        
                        # Show improvement notes
                        if agent_result.get('improvement_notes'):
                            st.markdown("**✨ Improvements Applied:**")
                            for note in agent_result['improvement_notes']:
                                st.markdown(f"- {note}")

        with col2:
            if st.button("📊 Analyze ATS Score", type="secondary", use_container_width=True):
                with st.spinner("Analyzing ATS compatibility..."):
                    ats_result = analyze_ats_score(st.session_state.session_id, job_description)
                    
                    if ats_result:
                        st.session_state.ats_analysis = ats_result
                        st.success("✅ ATS analysis completed!")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Results Display
    if st.session_state.tailored_resume:
        st.markdown('<div class="results-section">', unsafe_allow_html=True)
        st.header("📋 Tailored Resume")
        
        # Improvement metrics
        metrics = st.session_state.tailored_resume.get('improvement_metrics', {})
        if metrics:
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    "Original Match",
                    f"{metrics.get('original_keyword_match', 0):.1f}%"
                )
            
            with col2:
                st.metric(
                    "Tailored Match",
                    f"{metrics.get('tailored_keyword_match', 0):.1f}%"
                )
            
            with col3:
                improvement = metrics.get('improvement_percentage', 0)
                st.metric(
                    "Improvement",
                    f"{improvement:+.1f}%",
                    delta=f"{improvement:.1f}%"
                )
            
            with col4:
                word_change = metrics.get('word_count_change', 0)
                tailored_count = metrics.get('tailored_word_count', 0)
                st.metric(
                    "Word Count",
                    tailored_count,
                    delta=f"{word_change:+d} words" if word_change != 0 else None
                )
        
        # Display tailored resume
        st.subheader("✨ Tailored Resume Content")
        st.text_area(
            "Your AI-optimized resume:",
            st.session_state.tailored_resume['tailored_resume'],
            height=400,
            disabled=True
        )
        
        # File Generation Section (after multi-agent output)
        st.subheader("📄 Generate Downloadable Files")
        col1, col2, col3 = st.columns([1, 1, 1])
        
        with col1:
            file_format = st.selectbox(
                "File Format:",
                ["both", "pdf", "docx"],
                format_func=lambda x: {"both": "📄 PDF + DOCX", "pdf": "📄 PDF Only", "docx": "📄 DOCX Only"}[x]
            )
        
        with col2:
            resume_style = st.selectbox(
                "Style:",
                ["modern", "classic", "professional"],
                format_func=lambda x: {"modern": "🔥 Modern", "classic": "📜 Classic", "professional": "💼 Professional"}[x]
            )
        
        with col3:
            if st.button("📥 Generate Files", type="primary", use_container_width=True):
                with st.spinner("Generating downloadable files..."):
                    file_result = generate_files(
                        st.session_state.session_id,
                        file_format,
                        resume_style
                    )
                    
                    if file_result:
                        st.success("✅ Files generated successfully!")
                        st.session_state.files_generated = True
        
        # Download buttons (only show after files are generated)
        if hasattr(st.session_state, 'files_generated') and st.session_state.files_generated:
            st.subheader("💾 Download Your Resume")
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("📄 Download PDF", use_container_width=True):
                    pdf_content = download_file(st.session_state.session_id, "pdf")
                    if pdf_content:
                        st.download_button(
                            label="💾 Download PDF",
                            data=pdf_content,
                            file_name=f"tailored_resume_{datetime.now().strftime('%Y%m%d')}.pdf",
                            mime="application/pdf",
                            use_container_width=True
                        )
            
            with col2:
                if st.button("📄 Download DOCX", use_container_width=True):
                    docx_content = download_file(st.session_state.session_id, "docx")
                    if docx_content:
                        st.download_button(
                            label="💾 Download DOCX",
                            data=docx_content,
                            file_name=f"tailored_resume_{datetime.now().strftime('%Y%m%d')}.docx",
                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                            use_container_width=True
                        )
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # ATS Analysis Results
    if st.session_state.ats_analysis:
        st.markdown('<div class="results-section">', unsafe_allow_html=True)
        st.header("🎯 ATS Compatibility Analysis")
        
        ats = st.session_state.ats_analysis
        
        # Score display
        col1, col2, col3, col4, col5 = st.columns(5)
        
        scores = [
            ("Overall", ats.get('overall_score', 0)),
            ("Keywords", ats.get('keyword_score', 0)),
            ("Structure", ats.get('structure_score', 0)),
            ("Skills", ats.get('skills_score', 0)),
            ("Experience", ats.get('experience_score', 0))
        ]
        
        for i, (label, score) in enumerate(scores):
            with [col1, col2, col3, col4, col5][i]:
                # Color based on score
                if score >= 80:
                    color = "green"
                elif score >= 60:
                    color = "orange"
                else:
                    color = "red"
                
                st.metric(
                    label,
                    f"{score:.0f}%",
                    delta=None
                )
        
        # Detailed analysis
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("✅ Matched Keywords")
            matched = ats.get('matched_keywords', [])
            if matched:
                for keyword in matched[:10]:  # Show top 10
                    st.write(f"• {keyword}")
            else:
                st.write("No matched keywords found")
        
        with col2:
            st.subheader("❌ Missing Keywords")
            missing = ats.get('missing_keywords', [])
            if missing:
                for keyword in missing[:10]:  # Show top 10
                    st.write(f"• {keyword}")
            else:
                st.write("No missing keywords identified")
        
        # Recommendations
        recommendations = ats.get('recommendations', [])
        if recommendations:
            st.subheader("💡 Recommendations")
            for i, rec in enumerate(recommendations[:5], 1):
                st.write(f"{i}. {rec}")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Job Analysis Display
    if st.session_state.job_analysis:
        with st.expander("📊 Job Description Analysis"):
            analysis = st.session_state.job_analysis
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("🔧 Technical Skills Required")
                tech_skills = analysis.get('technical_skills', [])
                if tech_skills:
                    for skill in tech_skills[:15]:
                        st.write(f"• {skill}")
                else:
                    st.write("No technical skills identified")
            
            with col2:
                st.subheader("🤝 Soft Skills Required")
                soft_skills = analysis.get('soft_skills', [])
                if soft_skills:
                    for skill in soft_skills[:10]:
                        st.write(f"• {skill}")
                else:
                    st.write("No soft skills identified")
            
            st.subheader("📋 Key Requirements")
            requirements = analysis.get('requirements', [])
            if requirements:
                for req in requirements[:10]:
                    st.write(f"• {req}")
            else:
                st.write("No specific requirements identified")
    
    # Footer
    st.markdown("---")
    st.markdown(
        '<p style="text-align: center; color: #7f8c8d;">🚀 ZubeResume AI - Powered by Groq (FREE!)</p>',
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()