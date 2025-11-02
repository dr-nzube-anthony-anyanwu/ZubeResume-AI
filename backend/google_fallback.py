"""
Google Gemini API Fallback System
Provides hybrid Gemini 1.5 Flash and Pro model support with smart selection
"""

import os
import logging
import time
import json
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GoogleGeminiFallback:
    """
    Google Gemini API fallback service with smart model selection
    - Gemini 1.5 Flash: Fast, efficient for standard tasks
    - Gemini 1.5 Pro: High quality for complex tasks
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('GOOGLE_API_KEY')
        self.initialized = False
        self.models = {}
        
        # Model configurations
        self.flash_model = "gemini-2.5-flash"
        self.pro_model = "gemini-2.5-pro-preview-03-25"
        
        # Safety settings - allow creative content generation
        self.safety_settings = {
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        }
        
        # Generation configuration
        self.generation_config = {
            "temperature": 0.7,
            "top_p": 0.8,
            "top_k": 40,
            "max_output_tokens": 8192,
        }
        
        if self.api_key:
            self.initialize()
    
    def initialize(self) -> bool:
        """Initialize Google Gemini API"""
        try:
            if not self.api_key:
                logger.error("Google API key not provided")
                return False
            
            genai.configure(api_key=self.api_key)
            
            # Initialize models
            self.models['flash'] = genai.GenerativeModel(
                model_name=self.flash_model,
                generation_config=self.generation_config,
                safety_settings=self.safety_settings
            )
            
            self.models['pro'] = genai.GenerativeModel(
                model_name=self.pro_model,
                generation_config=self.generation_config,
                safety_settings=self.safety_settings
            )
            
            self.initialized = True
            logger.info("Google Gemini models initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Google Gemini: {str(e)}")
            return False
    
    def _select_model(self, job_title: str, company: str, content_length: int) -> str:
        """
        Smart model selection based on job complexity and content length
        """
        # Use Pro for complex/senior roles or long content
        complex_keywords = [
            'senior', 'lead', 'principal', 'director', 'manager', 'architect',
            'head of', 'chief', 'vp', 'vice president', 'executive',
            'ai', 'machine learning', 'data science', 'research',
            'consulting', 'strategy', 'product'
        ]
        
        job_lower = job_title.lower()
        company_lower = company.lower()
        
        # Check for complex role indicators
        is_complex_role = any(keyword in job_lower for keyword in complex_keywords)
        is_large_company = any(company in company_lower for company in [
            'google', 'microsoft', 'amazon', 'apple', 'meta', 'netflix',
            'tesla', 'nvidia', 'openai', 'anthropic', 'deepmind'
        ])
        
        # Use Pro for complex roles, large companies, or long content
        if is_complex_role or is_large_company or content_length > 2000:
            return 'pro'
        else:
            return 'flash'
    
    def generate_content(self, prompt: str, job_title: str = "", company: str = "") -> Optional[str]:
        """Generate content using selected Gemini model"""
        if not self.initialized:
            logger.error("Google Gemini not initialized")
            return None
        
        try:
            # Select appropriate model
            model_type = self._select_model(job_title, company, len(prompt))
            model = self.models[model_type]
            
            logger.info(f"Using Gemini {model_type.title()} for {company} - {job_title}")
            
            # Generate content
            response = model.generate_content(prompt)
            
            if response and response.text:
                return response.text.strip()
            else:
                logger.warning(f"Empty response from Gemini {model_type}")
                return None
                
        except Exception as e:
            logger.error(f"Error generating content with Google Gemini: {str(e)}")
            
            # Try fallback to Flash if Pro failed
            if model_type == 'pro':
                try:
                    logger.info("Falling back to Gemini Flash")
                    response = self.models['flash'].generate_content(prompt)
                    if response and response.text:
                        return response.text.strip()
                except Exception as fallback_e:
                    logger.error(f"Fallback to Flash also failed: {str(fallback_e)}")
            
            return None
    
    def tailor_resume_content(self, resume_content: str, job_description: str, 
                            job_title: str, company: str) -> Optional[str]:
        """
        Tailor resume content using Google Gemini with specialized prompt
        """
        prompt = f"""You are an expert resume writer and career counselor. Your task is to tailor a resume for a specific job application.

JOB DETAILS:
Company: {company}
Position: {job_title}

JOB DESCRIPTION:
{job_description}

ORIGINAL RESUME:
{resume_content}

INSTRUCTIONS:
1. Analyze the job description to identify key requirements, skills, and qualifications
2. Tailor the resume content to highlight relevant experience and skills
3. Optimize keywords for ATS (Applicant Tracking Systems)
4. Maintain professional tone and formatting
5. Ensure all information remains truthful and accurate
6. Focus on quantifiable achievements and results

IMPORTANT FORMATTING REQUIREMENTS:
- Keep the exact same structure and sections as the original resume
- Maintain all contact information unchanged
- Use the same formatting style (headings, bullet points, etc.)
- Do not add fake information or experiences
- Enhance existing content rather than creating new experiences

Please provide the tailored resume content:"""

        return self.generate_content(prompt, job_title, company)
    
    def get_status(self) -> Dict[str, Any]:
        """Get current status of Google Gemini service"""
        return {
            "service": "Google Gemini",
            "initialized": self.initialized,
            "has_api_key": bool(self.api_key),
            "models_available": list(self.models.keys()) if self.initialized else [],
            "flash_model": self.flash_model,
            "pro_model": self.pro_model
        }

def test_google_fallback():
    """Test function for Google Gemini fallback"""
    fallback = GoogleGeminiFallback()
    
    if not fallback.initialized:
        print("❌ Google Gemini not initialized - check API key")
        return False
    
    # Test simple generation
    test_prompt = "Write a brief professional summary for a software engineer with 3 years of experience."
    result = fallback.generate_content(test_prompt, "Software Engineer", "Tech Company")
    
    if result:
        print("✅ Google Gemini fallback working correctly")
        print(f"Sample output: {result[:100]}...")
        return True
    else:
        print("❌ Google Gemini test failed")
        return False

if __name__ == "__main__":
    test_google_fallback()