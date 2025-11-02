"""
Resume Parser Module
Extracts text content from various file formats (PDF, DOCX, TXT)
Uses pdfplumber for enhanced PDF text extraction
"""

import io
import os
import re
from typing import Dict, Optional
import fitz  # PyMuPDF
import pdfplumber
from docx import Document
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ResumeParser:
    """Class to parse resumes from different file formats"""
    
    def __init__(self):
        self.supported_formats = ['.pdf', '.docx', '.txt']
    
    def extract_text(self, file_path: str = None, file_content: bytes = None, filename: str = None) -> Dict[str, str]:
        """
        Extract text from uploaded file or file path
        
        Args:
            file_path (str): Path to the file
            file_content (bytes): File content as bytes
            filename (str): Original filename to determine format
            
        Returns:
            Dict containing extracted text and metadata
        """
        try:
            if file_path:
                file_extension = os.path.splitext(file_path)[1].lower()
                with open(file_path, 'rb') as f:
                    content = f.read()
            elif file_content and filename:
                file_extension = os.path.splitext(filename)[1].lower()
                content = file_content
            else:
                raise ValueError("Either file_path or (file_content + filename) must be provided")
            
            if file_extension not in self.supported_formats:
                raise ValueError(f"Unsupported file format: {file_extension}")
            
            # Extract text based on file type
            if file_extension == '.pdf':
                text = self._extract_from_pdf(content)
            elif file_extension == '.docx':
                text = self._extract_from_docx(content)
            elif file_extension == '.txt':
                text = self._extract_from_txt(content)
            else:
                raise ValueError(f"Unsupported file format: {file_extension}")
            
            # Parse sections
            parsed_sections = self._parse_sections(text)
            
            return {
                'raw_text': text,
                'formatted_text': self._clean_text(text),
                'sections': parsed_sections,
                'file_type': file_extension,
                'status': 'success',
                'word_count': len(text.split()),
                'char_count': len(text)
            }
            
        except Exception as e:
            logger.error(f"Error extracting text: {str(e)}")
            return {
                'raw_text': '',
                'formatted_text': '',
                'sections': {},
                'file_type': '',
                'status': 'error',
                'error': str(e),
                'word_count': 0,
                'char_count': 0
            }
    
    def _extract_from_pdf(self, content: bytes) -> str:
        """Extract text from PDF content using pdfplumber for better accuracy"""
        try:
            # First try with pdfplumber for better text extraction
            with pdfplumber.open(io.BytesIO(content)) as pdf:
                text = ""
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
                
                if text.strip():
                    logger.info("✅ Successfully extracted text using pdfplumber")
                    return text
            
            # Fallback to PyMuPDF if pdfplumber fails
            logger.info("🔄 Falling back to PyMuPDF extraction")
            doc = fitz.open(stream=content, filetype="pdf")
            text = ""
            for page in doc:
                text += page.get_text()
            doc.close()
            return text
            
        except Exception as e:
            logger.error(f"Error extracting from PDF: {str(e)}")
            raise
    
    def _extract_from_docx(self, content: bytes) -> str:
        """Extract text from DOCX content"""
        try:
            doc = Document(io.BytesIO(content))
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text
        except Exception as e:
            logger.error(f"Error extracting from DOCX: {str(e)}")
            raise
    
    def _extract_from_txt(self, content: bytes) -> str:
        """Extract text from TXT content"""
        try:
            return content.decode('utf-8')
        except UnicodeDecodeError:
            try:
                return content.decode('latin-1')
            except Exception as e:
                logger.error(f"Error extracting from TXT: {str(e)}")
                raise
    
    def _clean_text(self, text: str) -> str:
        """Clean and format extracted text"""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove special characters but keep basic punctuation
        text = re.sub(r'[^\w\s\.\,\-\(\)\@\+\#]', '', text)
        # Remove multiple spaces
        text = re.sub(r' +', ' ', text)
        return text.strip()
    
    def _parse_sections(self, text: str) -> Dict[str, str]:
        """
        Parse resume into common sections
        Returns a dictionary with identified sections
        """
        sections = {
            'contact_info': '',
            'summary': '',
            'skills': '',
            'experience': '',
            'education': '',
            'other': ''
        }
        
        try:
            # Convert to lowercase for pattern matching
            text_lower = text.lower()
            
            # Define section patterns
            patterns = {
                'contact_info': self._extract_contact_info(text),
                'summary': self._extract_section(text, ['summary', 'objective', 'profile']),
                'skills': self._extract_section(text, ['skills', 'technical skills', 'core competencies']),
                'experience': self._extract_section(text, ['experience', 'work experience', 'employment', 'professional experience']),
                'education': self._extract_section(text, ['education', 'academic background', 'qualifications'])
            }
            
            for section, content in patterns.items():
                sections[section] = content
                
        except Exception as e:
            logger.error(f"Error parsing sections: {str(e)}")
        
        return sections
    
    def _extract_contact_info(self, text: str) -> str:
        """Extract contact information (email, phone, etc.)"""
        contact_patterns = [
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # Email
            r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',  # Phone
            r'\b\(\d{3}\)\s*\d{3}[-.]?\d{4}\b'  # Phone with area code
        ]
        
        contact_info = []
        for pattern in contact_patterns:
            matches = re.findall(pattern, text)
            contact_info.extend(matches)
        
        return ' | '.join(contact_info)
    
    def _extract_section(self, text: str, keywords: list) -> str:
        """Extract content for a specific section based on keywords"""
        text_lines = text.split('\n')
        section_content = []
        capturing = False
        
        for i, line in enumerate(text_lines):
            line_lower = line.lower().strip()
            
            # Check if this line starts a section we're looking for
            for keyword in keywords:
                if keyword.lower() in line_lower and len(line_lower) < 50:  # Section headers are usually short
                    capturing = True
                    break
            
            # Stop capturing if we hit another section header
            if capturing and i > 0:
                next_section_keywords = ['summary', 'objective', 'skills', 'experience', 'education', 'projects', 'certifications']
                if any(kw in line_lower for kw in next_section_keywords) and len(line_lower) < 50 and not any(kw in keywords for kw in next_section_keywords if kw in line_lower):
                    break
            
            if capturing and line.strip():
                section_content.append(line.strip())
        
        return '\n'.join(section_content[:20])  # Limit to first 20 lines to avoid too much content

def test_parser():
    """Test function for the resume parser"""
    parser = ResumeParser()
    
    # Test with a sample text
    sample_text = """
    John Doe
    john.doe@email.com
    (555) 123-4567
    
    SUMMARY
    Experienced software developer with 5 years of experience
    
    SKILLS
    Python, JavaScript, React, Node.js
    
    EXPERIENCE
    Software Developer at Tech Corp
    2020-2023
    - Developed web applications
    - Led team of 3 developers
    """
    
    # Save as temp file for testing
    with open('temp_resume.txt', 'w') as f:
        f.write(sample_text)
    
    result = parser.extract_text('temp_resume.txt')
    print("Parsed Resume:")
    print(f"Status: {result['status']}")
    print(f"Word Count: {result['word_count']}")
    print(f"Sections: {list(result['sections'].keys())}")
    
    # Clean up
    os.remove('temp_resume.txt')

if __name__ == "__main__":
    test_parser()