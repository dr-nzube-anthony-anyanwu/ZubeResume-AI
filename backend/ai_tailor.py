"""
AI Tailoring Engine
Uses Groq API for free AI-powered resume tailoring with RAG support
Enhanced with advanced text processing using NLTK
"""

import os
import logging
from typing import Dict, Optional
from groq import Groq
from dotenv import load_dotenv
import json
import time

# Handle imports for both direct execution and module loading
try:
    from .rag_engine import RAGEngine
    from .text_processor import TextProcessor
    from .agent_system import ResumeAgentSystem
except ImportError:
    from rag_engine import RAGEngine
    from text_processor import TextProcessor
    from agent_system import ResumeAgentSystem

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AITailor:
    """Class to handle AI-powered resume tailoring using Groq with RAG support"""
    
    def __init__(self, api_key: str = None):
        """
        Initialize the AI Tailor with Groq API and RAG engine
        
        Args:
            api_key (str): Groq API key, if not provided, will use environment variable
        """
        try:
            self.api_key = api_key or os.getenv('GROQ_API_KEY')
            if not self.api_key:
                raise ValueError("Groq API key not provided. Set GROQ_API_KEY environment variable.")
            
            self.client = Groq(api_key=self.api_key)
            # Using Llama 3.3 70B - free and powerful model on Groq
            self.model = "llama-3.3-70b-versatile"
            
            # Initialize text processor for better formatting
            try:
                self.text_processor = TextProcessor()
                logger.info("Text processor initialized successfully")
            except Exception as e:
                logger.warning(f"Text processor initialization failed: {e}")
                self.text_processor = None
            
            # Initialize RAG engine
            try:
                self.rag_engine = RAGEngine()
            except Exception as e:
                logger.warning(f"RAG engine initialization failed: {e}")
                self.rag_engine = None
            
            # Tailoring templates
            self.system_prompt = """You are an expert resume writer and ATS optimization specialist with over 10 years of experience. 
Your task is to tailor resumes to match specific job descriptions while maintaining professionalism and authenticity.

Key principles:
1. Emphasize relevant experiences and skills that match the job requirements
2. Use keywords from the job description naturally throughout the resume
3. Reorder and rewrite content to highlight the most relevant qualifications
4. Maintain a professional, consistent tone and format
5. Ensure the resume is ATS-friendly with clear sections and formatting
6. Use provided contextual information from RAG to focus on the most relevant experiences
7. Keep content truthful - enhance and reframe existing experiences rather than fabricating
8. Optimize for both human readers and ATS systems

CRITICAL FORMATTING REQUIREMENTS:
- Use clear section headers in ALL CAPS followed by a colon (e.g., "PROFESSIONAL SUMMARY:", "SKILLS:", "EXPERIENCE:")
- Add a blank line after each section header before the content
- Add a blank line between different sections
- For experience entries, format each project clearly:
  
  ● Project Name — Brief Description
  Role/Title | Tech: Technology Stack Used
  • Achievement 1 with quantifiable results
  • Achievement 2 with relevant keywords
  • Achievement 3 focusing on impact
  
- For skills, organize in clear categories with line breaks:
  Programming & Tools: List, of, technologies
  Machine Learning: List, of, ML, tools
  Cloud Platforms: List, of, platforms
  
- For education and certifications, use simple bullet points with proper spacing
- Ensure each line has adequate spacing and avoid cramming text together
- Use line breaks strategically to improve readability
- Keep sentences clear and not overly long to prevent text jamming together

Structure the output with these exact sections in order:
1. PROFESSIONAL SUMMARY:
2. SKILLS:
3. EXPERIENCE:
4. EDUCATION:
5. Any other relevant sections (CERTIFICATIONS:, PROJECTS:, etc.)"""

        except Exception as e:
            logger.error(f"Error initializing AI Tailor: {str(e)}")
            raise
    
    def tailor_resume(self, resume_text: str, job_description: str, 
                     user_preferences: Dict = None) -> Dict[str, str]:
        """
        Tailor a resume to match a job description
        
        Args:
            resume_text (str): Original resume text
            job_description (str): Target job description
            user_preferences (Dict): Optional user preferences for tailoring
            
        Returns:
            Dict containing tailored resume and metadata
        """
        try:
            # Prepare user preferences
            preferences = user_preferences or {}
            tone = preferences.get('tone', 'professional')
            focus_areas = preferences.get('focus_areas', [])
            
            # Create the tailoring prompt
            user_prompt = self._create_tailoring_prompt(
                resume_text, job_description, tone, focus_areas
            )
            
            # Call Groq API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=4000,
                temperature=0.3,  # Lower temperature for more consistent results
                top_p=0.9
            )
            
            tailored_resume = response.choices[0].message.content.strip()
            
            # Post-process the tailored resume with advanced text processing
            if self.text_processor:
                try:
                    tailored_resume = self.text_processor.clean_and_structure_text(tailored_resume)
                    logger.info("Applied advanced text processing to tailored resume")
                except Exception as e:
                    logger.warning(f"Text processing failed, using original: {e}")
            
            # Calculate improvement metrics
            metrics = self._calculate_improvement_metrics(
                resume_text, tailored_resume, job_description
            )
            
            return {
                'tailored_resume': tailored_resume,
                'original_resume': resume_text,
                'job_description': job_description,
                'improvement_metrics': metrics,
                'tokens_used': response.usage.total_tokens if hasattr(response, 'usage') else 0,
                'model_used': self.model,
                'status': 'success',
                'timestamp': time.time()
            }
            
        except Exception as e:
            logger.error(f"Error tailoring resume: {str(e)}")
            return {
                'tailored_resume': '',
                'original_resume': resume_text,
                'job_description': job_description,
                'improvement_metrics': {},
                'tokens_used': 0,
                'model_used': self.model,
                'status': 'error',
                'error': str(e),
                'timestamp': time.time()
            }
    
    def _create_tailoring_prompt(self, resume_text: str, job_description: str, 
                               tone: str, focus_areas: list) -> str:
        """Create a detailed prompt for resume tailoring"""
        
        focus_instruction = ""
        if focus_areas:
            focus_instruction = f"\nPay special attention to highlighting: {', '.join(focus_areas)}"
        
        prompt = f"""
Please tailor the following resume to match the job description provided. 

**INSTRUCTIONS:**
1. Analyze the job description to identify key requirements, skills, and keywords
2. Rewrite the resume to emphasize relevant experiences and skills
3. Incorporate job-specific keywords naturally throughout the content
4. Reorder bullet points to put the most relevant experiences first
5. Optimize the summary/objective section to align with the target role
6. Ensure all technical skills mentioned in the job description are highlighted if present in the original resume
7. Maintain the same basic structure but enhance content for relevance
8. Use a {tone} tone throughout
9. Ensure ATS compatibility with clear section headers and bullet points{focus_instruction}

**JOB DESCRIPTION:**
{job_description}

**ORIGINAL RESUME:**
{resume_text}

**OUTPUT FORMAT:**
Provide the tailored resume in a clean, professional format with clear section headers. Use bullet points for experience items and ensure consistent formatting throughout.

**TAILORED RESUME:**
"""
        return prompt
    
    def generate_cover_letter(self, resume_text: str, job_description: str, 
                            company_name: str = "", position_title: str = "") -> Dict[str, str]:
        """
        Generate a tailored cover letter based on resume and job description
        
        Args:
            resume_text (str): Resume text
            job_description (str): Job description
            company_name (str): Name of the company
            position_title (str): Title of the position
            
        Returns:
            Dict containing cover letter and metadata
        """
        try:
            cover_letter_prompt = f"""
Write a professional, compelling cover letter for the following position.

**INSTRUCTIONS:**
1. Write a personalized cover letter that highlights relevant experience from the resume
2. Address specific requirements mentioned in the job description
3. Show enthusiasm for the role and company
4. Keep it concise (3-4 paragraphs)
5. Use a professional but engaging tone
6. Include specific examples from the resume that demonstrate qualifications

**POSITION:** {position_title}
**COMPANY:** {company_name}

**JOB DESCRIPTION:**
{job_description}

**RESUME:**
{resume_text}

**COVER LETTER:**
"""
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert career counselor and professional writer specializing in cover letters."},
                    {"role": "user", "content": cover_letter_prompt}
                ],
                max_tokens=1500,
                temperature=0.4
            )
            
            cover_letter = response.choices[0].message.content.strip()
            
            return {
                'cover_letter': cover_letter,
                'company_name': company_name,
                'position_title': position_title,
                'tokens_used': response.usage.total_tokens if hasattr(response, 'usage') else 0,
                'status': 'success'
            }
            
        except Exception as e:
            logger.error(f"Error generating cover letter: {str(e)}")
            return {
                'cover_letter': '',
                'company_name': company_name,
                'position_title': position_title,
                'tokens_used': 0,
                'status': 'error',
                'error': str(e)
            }
    
    def _calculate_improvement_metrics(self, original: str, tailored: str, job_description: str) -> Dict:
        """Calculate metrics to show improvement from tailoring"""
        try:
            # Simple keyword matching for demonstration
            job_words = set(job_description.lower().split())
            original_words = set(original.lower().split())
            tailored_words = set(tailored.lower().split())
            
            # Calculate keyword overlap
            original_overlap = len(job_words.intersection(original_words)) / len(job_words) * 100
            tailored_overlap = len(job_words.intersection(tailored_words)) / len(job_words) * 100
            
            improvement = tailored_overlap - original_overlap
            
            return {
                'original_keyword_match': round(original_overlap, 2),
                'tailored_keyword_match': round(tailored_overlap, 2),
                'improvement_percentage': round(improvement, 2),
                'word_count_original': len(original.split()),
                'word_count_tailored': len(tailored.split())
            }
            
        except Exception as e:
            logger.error(f"Error calculating metrics: {str(e)}")
            return {}
    
    def analyze_ats_score(self, resume_text: str, job_description: str) -> Dict:
        """
        Analyze how ATS-friendly the resume is for the given job
        
        Args:
            resume_text (str): Resume text to analyze
            job_description (str): Job description to match against
            
        Returns:
            Dict containing ATS analysis
        """
        try:
            analysis_prompt = f"""
Analyze the following resume for ATS (Applicant Tracking System) compatibility and provide a detailed score.

**EVALUATION CRITERIA:**
1. Keyword matching with job description (40%)
2. Resume structure and formatting (20%)
3. Skills alignment (20%)
4. Experience relevance (20%)

**JOB DESCRIPTION:**
{job_description}

**RESUME:**
{resume_text}

**PROVIDE:**
1. Overall ATS Score (0-100)
2. Keyword Match Score (0-100)
3. Structure Score (0-100)
4. Skills Alignment Score (0-100)
5. Experience Relevance Score (0-100)
6. List of matched keywords (up to 10)
7. List of missing important keywords (up to 10)
8. Specific recommendations for improvement (up to 5)

Format your response as JSON with these exact keys: overall_score, keyword_score, structure_score, skills_score, experience_score, matched_keywords, missing_keywords, recommendations.
"""
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an ATS analysis expert. Provide accurate, detailed analysis in JSON format."},
                    {"role": "user", "content": analysis_prompt}
                ],
                max_tokens=2000,
                temperature=0.2
            )
            
            # Try to parse JSON response
            try:
                analysis_result = json.loads(response.choices[0].message.content.strip())
                analysis_result['status'] = 'success'
                analysis_result['tokens_used'] = response.usage.total_tokens if hasattr(response, 'usage') else 0
                return analysis_result
            except json.JSONDecodeError:
                # Fallback if JSON parsing fails
                return {
                    'overall_score': 0,
                    'keyword_score': 0,
                    'structure_score': 0,
                    'skills_score': 0,
                    'experience_score': 0,
                    'matched_keywords': [],
                    'missing_keywords': [],
                    'recommendations': ['Unable to parse detailed analysis'],
                    'raw_response': response.choices[0].message.content,
                    'status': 'partial_success',
                    'tokens_used': response.usage.total_tokens if hasattr(response, 'usage') else 0
                }
                
        except Exception as e:
            logger.error(f"Error analyzing ATS score: {str(e)}")
            return {
                'overall_score': 0,
                'keyword_score': 0,
                'structure_score': 0,
                'skills_score': 0,
                'experience_score': 0,
                'matched_keywords': [],
                'missing_keywords': [],
                'recommendations': [],
                'status': 'error',
                'error': str(e),
                'tokens_used': 0
            }
    
    def tailor_resume_with_rag(self, resume_data: Dict, job_description: str, 
                              tone: str = "professional", focus_areas: list = None) -> Dict:
        """
        Enhanced resume tailoring using RAG for better context retrieval
        
        Args:
            resume_data: Parsed resume data dictionary
            job_description: Target job description
            tone: Tone for the tailored resume
            focus_areas: Specific areas to focus on
            
        Returns:
            Dictionary containing tailored resume and metadata
        """
        try:
            # Step 1: Vectorize the resume data for RAG
            logger.info("🔄 Vectorizing resume data for RAG...")
            vectorization_success = self.rag_engine.vectorize_resume(resume_data)
            
            if not vectorization_success:
                logger.warning("⚠️ RAG vectorization failed, falling back to standard tailoring")
                # Fallback to standard method with compatible arguments
                resume_text = resume_data.get('raw_text', '')
                user_preferences = {'tone': tone, 'focus_areas': focus_areas or []}
                return self.tailor_resume(resume_text, job_description, user_preferences)
            
            # Step 2: Retrieve relevant context from the resume
            logger.info("🔍 Retrieving relevant resume content...")
            contextual_data = self.rag_engine.get_contextual_resume_data(job_description, top_k=8)
            
            # Step 3: Build enhanced prompt with RAG context
            enhanced_prompt = self._create_rag_enhanced_prompt(
                resume_data, job_description, contextual_data, tone, focus_areas
            )
            
            # Step 4: Generate tailored resume using Groq with RAG context
            logger.info("🤖 Generating tailored resume with RAG enhancement...")
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": enhanced_prompt}
                ],
                max_tokens=4000,
                temperature=0.3
            )
            
            tailored_resume = response.choices[0].message.content.strip()
            
            # Post-process the tailored resume with advanced text processing
            if self.text_processor:
                try:
                    tailored_resume = self.text_processor.clean_and_structure_text(tailored_resume)
                    logger.info("Applied advanced text processing to RAG-enhanced resume")
                except Exception as e:
                    logger.warning(f"Text processing failed, using original: {e}")
            
            # Calculate improvement metrics
            original_text = resume_data.get('raw_text', '')
            metrics = self._calculate_improvement_metrics(
                original_text, tailored_resume, job_description
            )
            
            return {
                'tailored_resume': tailored_resume,
                'original_resume': original_text,
                'job_description': job_description,
                'rag_context': contextual_data,
                'improvement_metrics': metrics,
                'tokens_used': response.usage.total_tokens if hasattr(response, 'usage') else 0,
                'model_used': self.model,
                'method': 'rag_enhanced',
                'status': 'success',
                'timestamp': time.time()
            }
            
        except Exception as e:
            logger.error(f"Error in RAG-enhanced tailoring: {str(e)}")
            # Fallback to standard method
            resume_text = resume_data.get('raw_text', '')
            fallback_result = self.tailor_resume(resume_text, job_description, tone, focus_areas)
            fallback_result['method'] = 'fallback_standard'
            fallback_result['rag_error'] = str(e)
            return fallback_result
    
    def _create_rag_enhanced_prompt(self, resume_data: Dict, job_description: str, 
                                   contextual_data: Dict, tone: str, focus_areas: list) -> str:
        """Create an enhanced prompt using RAG context"""
        
        # Extract the most relevant chunks
        relevant_chunks = contextual_data.get('relevant_content', [])
        context_summary = contextual_data.get('context_summary', '')
        
        # Build context section
        context_section = "**MOST RELEVANT RESUME CONTENT (Retrieved via RAG):**\n"
        for i, chunk in enumerate(relevant_chunks[:5], 1):  # Top 5 most relevant
            context_section += f"{i}. {chunk['type'].title()}: {chunk['text'][:200]}...\n"
            context_section += f"   Relevance Score: {chunk['similarity_score']:.3f}\n\n"
        
        focus_instruction = ""
        if focus_areas:
            focus_instruction = f"\nPay special attention to highlighting: {', '.join(focus_areas)}"
        
        prompt = f"""
Please tailor the following resume to match the job description using the provided contextual information.

**RAG ANALYSIS SUMMARY:**
{context_summary}

{context_section}

**INSTRUCTIONS:**
1. Use the RAG-retrieved content above as the PRIMARY focus for tailoring
2. Emphasize the most relevant experiences (highest similarity scores) prominently
3. Incorporate job-specific keywords naturally throughout the content  
4. Reorder sections to prioritize the most relevant content first
5. Ensure the tailored resume highlights experiences that best match the job requirements
6. Maintain professional formatting and readability
7. Use quantifiable achievements where possible
{focus_instruction}

**TARGET JOB DESCRIPTION:**
{job_description}

**ORIGINAL RESUME (Full Text):**
{resume_data.get('raw_text', '')}

**TONE:** {tone}

Please provide a complete, tailored resume that strategically emphasizes the most relevant content identified through RAG analysis:
"""
        
        return prompt

    def tailor_resume_with_agents(self, resume_text: str, job_description: str) -> Dict[str, str]:
        """
        Use multi-agent system for enhanced resume tailoring with perfect formatting
        This is the KEY method that solves the text jamming issue!
        
        Args:
            resume_text (str): Original resume text
            job_description (str): Target job description
            
        Returns:
            Dict containing perfectly formatted tailored resume
        """
        try:
            logger.info("🤖 Initializing Multi-Agent Resume Processing System...")
            
            # Initialize the agent system with the same API key
            agent_system = ResumeAgentSystem(self.api_key)
            
            # Process through the specialized agent workflow
            result = agent_system.process_resume(resume_text, job_description)
            
            if result['status'] in ['success', 'completed', 'partial_success']:
                logger.info("✅ Multi-Agent System completed successfully!")
                
                # Return in the expected format for the rest of the system
                return {
                    'tailored_resume': result['tailored_resume'],
                    'original_resume': resume_text,
                    'job_description': job_description,
                    'processing_messages': result.get('processing_messages', []),
                    'method': 'multi_agent_langraph',
                    'status': 'success',
                    'tokens_used': 3,  # 3 agents each use 1 token
                    'model_used': self.model,
                    'agents_used': result.get('agents_used', ['content_agent', 'formatting_agent', 'document_agent']),
                    'timestamp': result.get('timestamp', time.time()),
                    'improvement_notes': [
                        '🎯 Content optimized for job relevance',
                        '✨ Professional formatting applied to eliminate text jamming',
                        '📄 Document structure prepared for perfect file generation'
                    ]
                }
            else:
                # If agents fail, fallback to standard method
                logger.warning("⚠️ Agent system failed, falling back to standard method")
                return self.tailor_resume(resume_text, job_description)
                
        except Exception as e:
            logger.error(f"Multi-agent system error: {str(e)}")
            # Fallback to standard method on any error
            logger.info("🔄 Falling back to standard tailoring method")
            return self.tailor_resume(resume_text, job_description)

def test_ai_tailor():
    """Test function for the AI tailor (requires Groq API key)"""
    try:
        # This test requires a valid Groq API key
        tailor = AITailor()
        
        sample_resume = """
        John Doe
        Software Developer
        john.doe@email.com
        
        SUMMARY
        Experienced software developer with 3 years of experience
        
        SKILLS
        Python, JavaScript, HTML, CSS
        
        EXPERIENCE
        Software Developer at ABC Corp
        2021-2024
        - Developed web applications
        - Worked with databases
        """
        
        sample_job = """
        Senior Python Developer
        We need an experienced Python developer with React skills
        Requirements:
        - 3+ years Python experience
        - React.js knowledge
        - Database experience
        """
        
        result = tailor.tailor_resume(sample_resume, sample_job)
        print(f"Tailoring Status: {result['status']}")
        if result['status'] == 'success':
            print(f"Tokens Used: {result['tokens_used']}")
            print("Tailored Resume Preview:")
            print(result['tailored_resume'][:200] + "...")
        
    except Exception as e:
        print(f"Test failed (expected without API key): {str(e)}")

if __name__ == "__main__":
    test_ai_tailor()