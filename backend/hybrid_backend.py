"""
Hybrid Backend for ZubeResume AI
Handles local processing and AI integration
"""

import os
import json
import tempfile
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List, Any, Union

# Import backend components
from backend.ai_tailor import AITailor
from backend.resume_parser import ResumeParser
from backend.job_parser import JobParser
from backend.file_generator import FileGenerator

class HybridBackend:
    def __init__(self):
        self.ai_tailor = AITailor()
        self.resume_parser = ResumeParser()
        self.job_parser = JobParser()
        self.file_generator = FileGenerator()
        self.sessions = {}

    def get_smart_resume(self):
        """Return instance for direct access"""
        return self

    def upload_resume(self, file) -> Dict[str, Any]:
        """Process uploaded resume file"""
        try:
            # Generate session ID
            session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Parse resume
            parsed_data = self.resume_parser.parse(file)
            
            # Store session data
            self.sessions[session_id] = {
                'original_text': parsed_data['text'],
                'parsed_data': parsed_data,
                'file_type': parsed_data['file_type']
            }
            
            return {
                'status': 'success',
                'session_id': session_id,
                'filename': file.name,
                'file_type': parsed_data['file_type'],
                'word_count': len(parsed_data['text'].split()),
                'sections': parsed_data.get('sections', []),
                'preview': parsed_data['text'][:500] + "..." if len(parsed_data['text']) > 500 else parsed_data['text']
            }
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }

    def analyze_job_description(self, job_description: str) -> Dict[str, Any]:
        """Analyze job description"""
        try:
            analysis = self.job_parser.analyze(job_description)
            return {
                'status': 'success',
                **analysis
            }
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }

    def tailor_resume_standard(self, 
                             session_id: str, 
                             job_description: str, 
                             preferences: Optional[Dict] = None) -> Dict[str, Any]:
        """Standard resume tailoring"""
        try:
            if session_id not in self.sessions:
                raise ValueError("Session not found")
            
            session_data = self.sessions[session_id]
            original_text = session_data['original_text']
            
            # Tailor resume
            result = self.ai_tailor.tailor_resume(
                resume_text=original_text,
                job_description=job_description,
                preferences=preferences or {}
            )
            
            # Store tailored version
            self.sessions[session_id]['tailored_text'] = result['tailored_text']
            
            return {
                'status': 'success',
                'tailored_resume': result['tailored_text'],
                'improvement_metrics': result.get('metrics', {})
            }
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }

    def tailor_resume_with_rag(self, 
                              session_id: str, 
                              job_description: str,
                              tone: str = "professional",
                              focus_areas: Optional[List[str]] = None) -> Dict[str, Any]:
        """RAG-enhanced resume tailoring"""
        try:
            if session_id not in self.sessions:
                raise ValueError("Session not found")
            
            session_data = self.sessions[session_id]
            original_text = session_data['original_text']
            
            # Use RAG-enhanced tailoring
            result = self.ai_tailor.tailor_resume_rag(
                resume_text=original_text,
                job_description=job_description,
                tone=tone,
                focus_areas=focus_areas or []
            )
            
            # Store tailored version
            self.sessions[session_id]['tailored_text'] = result['tailored_text']
            
            return {
                'status': 'success',
                'tailored_resume': result['tailored_text'],
                'improvement_metrics': result.get('metrics', {}),
                'rag_context_summary': result.get('context_summary', '')
            }
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }

    def tailor_resume_with_agents(self, 
                                 session_id: str, 
                                 job_description: str) -> Dict[str, Any]:
        """Multi-agent resume tailoring"""
        try:
            if session_id not in self.sessions:
                raise ValueError("Session not found")
            
            session_data = self.sessions[session_id]
            original_text = session_data['original_text']
            
            # Use multi-agent system
            result = self.ai_tailor.tailor_resume_agents(
                resume_text=original_text,
                job_description=job_description
            )
            
            # Store tailored version
            self.sessions[session_id]['tailored_text'] = result['tailored_text']
            
            return {
                'status': 'success',
                'tailored_resume': result['tailored_text'],
                'improvement_metrics': result.get('metrics', {}),
                'agents_used': result.get('agents_used', []),
                'processing_messages': result.get('processing_messages', []),
                'improvement_notes': result.get('improvement_notes', [])
            }
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }

    def analyze_ats_score(self, 
                         session_id: str, 
                         job_description: str) -> Dict[str, Any]:
        """Analyze ATS compatibility"""
        try:
            if session_id not in self.sessions:
                raise ValueError("Session not found")
            
            session_data = self.sessions[session_id]
            current_text = session_data.get('tailored_text', session_data['original_text'])
            
            # Analyze ATS compatibility
            analysis = self.ai_tailor.analyze_ats(
                resume_text=current_text,
                job_description=job_description
            )
            
            return {
                'status': 'success',
                **analysis
            }
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }

    def generate_files(self, 
                      session_id: str, 
                      file_format: str = "both", 
                      style: str = "modern") -> Dict[str, Any]:
        """Generate downloadable files"""
        try:
            if session_id not in self.sessions:
                raise ValueError("Session not found")
            
            session_data = self.sessions[session_id]
            current_text = session_data.get('tailored_text', session_data['original_text'])
            
            # Generate files
            result = self.file_generator.generate(
                resume_text=current_text,
                formats=[file_format] if file_format != "both" else ["pdf", "docx"],
                style=style
            )
            
            # Store generated files
            self.sessions[session_id]['generated_files'] = result['files']
            
            return {
                'status': 'success',
                'formats_generated': list(result['files'].keys())
            }
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }

    def get_generated_file_bytes(self, 
                               session_id: str, 
                               file_format: str) -> Optional[bytes]:
        """Get generated file content"""
        try:
            if session_id not in self.sessions:
                raise ValueError("Session not found")
            
            files = self.sessions[session_id].get('generated_files', {})
            if file_format not in files:
                raise ValueError(f"No {file_format} file generated for this session")
            
            return files[file_format]
        except Exception:
            return None

# Singleton instance
_instance = None

def get_smart_resume():
    """Get or create singleton instance"""
    global _instance
    if _instance is None:
        _instance = HybridBackend()
    return _instance