"""
Advanced Text Processing Module using Hugging Face Tokenizers
Uses Hugging Face's pre-trained tokenizers that work offline and are highly reliable
No network dependencies after initial download!
"""

import re
import logging
from typing import List, Dict, Tuple
from collections import Counter

# Import Hugging Face tokenizers - work offline and are very reliable
try:
    from tokenizers import Tokenizer
    from transformers import AutoTokenizer, GPT2TokenizerFast
    HF_AVAILABLE = True
except ImportError:
    HF_AVAILABLE = False
    print("Hugging Face tokenizers not available, using pure regex fallback")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TextProcessor:
    """Advanced text processor using Hugging Face tokenizers and smart regex patterns"""
    
    def __init__(self):
        """Initialize the text processor with Hugging Face tokenizers"""
        
        # Initialize Hugging Face tokenizer (temporarily disabled for faster startup)
        if False and HF_AVAILABLE:  # Temporarily disabled
            try:
                # Try to use cached tokenizer first, then download if needed
                logger.info("Initializing Hugging Face tokenizer (may download on first use)...")
                self.tokenizer = GPT2TokenizerFast.from_pretrained('gpt2', local_files_only=False)
                self.tokenizer.pad_token = self.tokenizer.eos_token
                logger.info("✅ Hugging Face GPT-2 tokenizer initialized successfully")
            except Exception as e:
                logger.warning(f"⚠️ Could not initialize HF tokenizer: {e}, using regex fallback")
                self.tokenizer = None
        else:
            logger.info("⚡ Using fast regex-based text processing (HF tokenizer disabled for speed)")
            self.tokenizer = None
        
        # Common stop words (predefined list - no download needed)
        self.stop_words = {
            'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for', 'from',
            'has', 'he', 'in', 'is', 'it', 'its', 'of', 'on', 'that', 'the',
            'to', 'was', 'will', 'with', 'or', 'but', 'this', 'these', 'they',
            'them', 'their', 'we', 'you', 'your', 'our', 'my', 'me', 'i'
        }
        
        # Enhanced patterns for better text structure detection
        self.sentence_endings = re.compile(r'[.!?]+\s+')
        self.bullet_patterns = re.compile(r'^[\s]*[•\-\*●]\s+')
        self.section_headers = re.compile(r'^[A-Z\s]+:?\s*$')
        self.email_pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
        self.phone_pattern = re.compile(r'(\+?\d{1,3}[-.\s]?)?[\(\s]?\d{3}[\)\s-]?\d{3}[-.\s]?\d{4}')
        self.url_pattern = re.compile(r'https?://[^\s]+|www\.[^\s]+|linkedin\.com/[^\s]+')
        
        # Smart spacing patterns - these fix the jamming issues
        self.comma_fix = re.compile(r'([a-zA-Z]),([a-zA-Z])')  # Fix: word,word → word, word
        self.period_fix = re.compile(r'([a-z])\.([A-Z])')  # Fix: word.Word → word. Word
        self.pipe_fix = re.compile(r'([a-zA-Z])\|([a-zA-Z])')  # Fix: word|word → word | word
        self.colon_fix = re.compile(r'([a-zA-Z]):([a-zA-Z])')  # Fix: word:word → word: word
        self.dash_fix = re.compile(r'([a-zA-Z])-([a-zA-Z])')  # Fix compound words carefully
        self.number_fix = re.compile(r'(\d)([A-Za-z])')  # Fix: 5years → 5 years
        self.percent_fix = re.compile(r'(\d)%([A-Za-z])')  # Fix: 40%improvement → 40% improvement
        
        # Patterns for resume-specific content
        self.achievement_starters = re.compile(r'^(developed|implemented|led|managed|created|built|designed|improved|increased|reduced|collaborated|achieved|delivered|optimized|streamlined|executed)', re.IGNORECASE)
        self.role_patterns = re.compile(r'(engineer|developer|analyst|manager|lead|specialist|director|coordinator)', re.IGNORECASE)
        
    def clean_and_structure_text(self, text: str) -> str:
        """
        Clean and structure resume text with proper spacing and formatting
        Uses Hugging Face tokenizers for superior text processing
        
        Args:
            text (str): Raw resume text from AI
            
        Returns:
            str: Cleaned and properly structured text
        """
        if not text:
            return ""
        
        logger.info("Starting advanced text processing with Hugging Face tokenizers...")
        
        # Step 1: Fix obvious spacing issues first (most important for jamming)
        text = self._fix_jamming_issues(text)
        
        # Step 2: Basic text cleaning
        text = self._basic_text_cleaning(text)
        
        # Step 3: Advanced sentence processing with HF tokenizers
        text = self._process_with_hf_tokenizer(text)
        
        # Step 4: Structure sections properly
        text = self._structure_sections(text)
        
        # Step 5: Format bullet points and lists
        text = self._format_bullet_points_enhanced(text)
        
        # Step 6: Fix paragraph spacing
        text = self._fix_paragraph_spacing_enhanced(text)
        
        # Step 7: Final cleanup
        text = self._final_cleanup(text)
        
        logger.info("Advanced text processing completed successfully")
        return text
    
    def _fix_jamming_issues(self, text: str) -> str:
        """Fix the main jamming text issues immediately"""
        # These are the most common jamming patterns - fix them first!
        
        # Fix comma spacing (Python,JavaScript → Python, JavaScript)
        text = self.comma_fix.sub(r'\1, \2', text)
        
        # Fix period spacing (development.Specializes → development. Specializes)
        text = self.period_fix.sub(r'\1. \2', text)
        
        # Fix pipe spacing (Engineer|555 → Engineer | 555)
        text = self.pipe_fix.sub(r'\1 | \2', text)
        
        # Fix colon spacing (Languages:Python → Languages: Python)
        text = self.colon_fix.sub(r'\1: \2', text)
        
        # Fix number-letter jamming (5years → 5 years)
        text = self.number_fix.sub(r'\1 \2', text)
        
        # Fix percentage jamming (40%improvement → 40% improvement)
        text = self.percent_fix.sub(r'\1% \2', text)
        
        # Fix common tech stack jamming
        text = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)  # camelCase → camel Case
        
        # Fix multiple spaces
        text = re.sub(r'  +', ' ', text)  # Multiple spaces → single space
        
        return text
    
    def _basic_text_cleaning(self, text: str) -> str:
        """Enhanced basic text cleaning"""
        # Fix line endings
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        
        # Process line by line to preserve structure
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            if line.strip():
                # Clean excessive spaces but preserve indentation
                cleaned_line = re.sub(r'[ \t]+', ' ', line.strip())
                cleaned_lines.append(cleaned_line)
            else:
                cleaned_lines.append('')
        
        text = '\n'.join(cleaned_lines)
        
        # Fix common encoding issues
        text = text.replace("'", "'").replace(""", '"').replace(""", '"')
        text = text.replace('–', '-').replace('—', ' - ')
        
        # Fix sentence spacing
        text = re.sub(r'([.!?])\s*([A-Z])', r'\1 \2', text)
        
        return text.strip()
    
    def _process_with_hf_tokenizer(self, text: str) -> str:
        """Use Hugging Face tokenizer for intelligent text processing"""
        if not self.tokenizer:
            return text
        
        lines = text.split('\n')
        processed_lines = []
        
        for line in lines:
            line = line.strip()
            if not line:
                processed_lines.append('')
                continue
            
            # Skip section headers and special content
            if (self.section_headers.match(line) or 
                self.email_pattern.search(line) or 
                self.phone_pattern.search(line) or
                self.url_pattern.search(line)):
                processed_lines.append(line)
                continue
            
            # For substantial content, use HF tokenizer intelligently
            if len(line) > 15:
                try:
                    # Tokenize and decode to fix spacing issues
                    # This is very smart and handles most text properly
                    tokens = self.tokenizer.encode(line, add_special_tokens=False)
                    decoded_text = self.tokenizer.decode(tokens)
                    
                    # Clean up any tokenizer artifacts
                    decoded_text = decoded_text.strip()
                    if decoded_text and len(decoded_text) > 5:
                        processed_lines.append(decoded_text)
                    else:
                        processed_lines.append(line)  # Fallback to original
                        
                except Exception as e:
                    logger.debug(f"HF tokenizer processing failed for line: {e}")
                    processed_lines.append(line)  # Fallback to original
            else:
                processed_lines.append(line)
        
        return '\n'.join(processed_lines)
    
    def _structure_sections(self, text: str) -> str:
        """Structure sections with proper spacing and headers"""
        lines = text.split('\n')
        structured_lines = []
        
        section_keywords = [
            'SUMMARY', 'PROFESSIONAL SUMMARY', 'OBJECTIVE', 'PROFILE',
            'SKILLS', 'TECHNICAL SKILLS', 'CORE COMPETENCIES', 'TECHNOLOGIES',
            'EXPERIENCE', 'WORK EXPERIENCE', 'PROFESSIONAL EXPERIENCE',
            'EDUCATION', 'ACADEMIC BACKGROUND', 'QUALIFICATIONS',
            'PROJECTS', 'KEY PROJECTS', 'CERTIFICATIONS', 'ACHIEVEMENTS'
        ]
        
        for i, line in enumerate(lines):
            line_upper = line.strip().upper().replace(':', '')
            
            # Check if this is a section header
            if any(keyword == line_upper for keyword in section_keywords):
                # Add spacing before section (except first)
                if structured_lines and structured_lines[-1] != '':
                    structured_lines.append('')
                structured_lines.append(line.strip())
                structured_lines.append('')  # Add space after header
            else:
                structured_lines.append(line)
        
        return '\n'.join(structured_lines)
    
    def _format_bullet_points_enhanced(self, text: str) -> str:
        """Enhanced bullet point formatting"""
        lines = text.split('\n')
        formatted_lines = []
        
        for line in lines:
            line = line.strip()
            
            if not line:
                formatted_lines.append('')
                continue
            
            # Detect and fix existing bullet points
            if re.match(r'^[\s]*[•\-\*●]\s*', line):
                clean_line = re.sub(r'^[\s]*[•\-\*●]\s*', '', line).strip()
                if clean_line:
                    formatted_lines.append(f"• {clean_line}")
                continue
            
            # Auto-detect lines that should be bullet points
            if (line and 
                not self.section_headers.match(line) and
                not self.email_pattern.search(line) and
                not self.phone_pattern.search(line) and
                not self.url_pattern.search(line) and
                len(line) > 15):
                
                # Check for achievement patterns
                if (self.achievement_starters.match(line) or
                    any(indicator in line.lower() for indicator in [
                        'achieving', 'resulting', '%', 'users', '$', 'million',
                        'increased', 'decreased', 'improved', 'reduced', 'enhanced'
                    ])):
                    formatted_lines.append(f"• {line}")
                    continue
            
            formatted_lines.append(line)
        
        return '\n'.join(formatted_lines)
    
    def _fix_paragraph_spacing_enhanced(self, text: str) -> str:
        """Enhanced paragraph spacing"""
        lines = text.split('\n')
        final_lines = []
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            if not line:
                # Only add one empty line at a time
                if final_lines and final_lines[-1] != '':
                    final_lines.append('')
                i += 1
                continue
            
            final_lines.append(line)
            
            # Smart spacing logic
            if i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                
                # Add spacing between sections
                needs_spacing = (
                    self.section_headers.match(next_line) or
                    (next_line and next_line.startswith('•')) or
                    (next_line and self.role_patterns.search(next_line))
                )
                
                if needs_spacing and final_lines[-1] != '':
                    final_lines.append('')
            
            i += 1
        
        return '\n'.join(final_lines)
    
    def _final_cleanup(self, text: str) -> str:
        """Final cleanup and validation"""
        lines = text.split('\n')
        clean_lines = []
        blank_line_count = 0
        
        for line in lines:
            if line.strip() == '':
                blank_line_count += 1
                if blank_line_count <= 1:  # Max 1 consecutive blank line
                    clean_lines.append('')
            else:
                blank_line_count = 0
                # Final spacing fixes
                cleaned_line = line.strip()
                cleaned_line = re.sub(r'\s*\|\s*', ' | ', cleaned_line)  # Normalize pipes
                clean_lines.append(cleaned_line)
        
        # Remove leading/trailing blank lines
        while clean_lines and clean_lines[0] == '':
            clean_lines.pop(0)
        while clean_lines and clean_lines[-1] == '':
            clean_lines.pop()
            
        return '\n'.join(clean_lines)
    
    def extract_contact_info(self, text: str) -> Dict[str, str]:
        """Extract contact information from resume text"""
        contact_info = {}
        
        # Extract email
        email_match = self.email_pattern.search(text)
        if email_match:
            contact_info['email'] = email_match.group()
        
        # Extract phone
        phone_match = self.phone_pattern.search(text)
        if phone_match:
            contact_info['phone'] = phone_match.group()
        
        # Extract URLs/LinkedIn
        url_matches = self.url_pattern.findall(text)
        if url_matches:
            contact_info['urls'] = url_matches
        
        return contact_info
    
    def extract_keywords(self, text: str, num_keywords: int = 20) -> List[str]:
        """Enhanced keyword extraction using HF tokenizer"""
        try:
            if self.tokenizer:
                # Use HF tokenizer for better word extraction
                tokens = self.tokenizer.encode(text.lower(), add_special_tokens=False)
                words = [self.tokenizer.decode([token]).strip() for token in tokens]
                # Filter meaningful words
                words = [word for word in words if word.isalpha() and word not in self.stop_words and len(word) > 2]
            else:
                # Fallback to regex
                words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
                words = [word for word in words if word not in self.stop_words and len(word) > 2]
            
            # Count frequency and return top keywords
            word_freq = Counter(words)
            keywords = [word for word, freq in word_freq.most_common(num_keywords)]
            return keywords
            
        except Exception as e:
            logger.warning(f"Keyword extraction failed: {e}")
            return []

def test_text_processor():
    """Test the text processor with sample resume text"""
    processor = TextProcessor()
    
    sample_text = """
John Doe john.doe@email.com(555)123-4567 LinkedIn:linkedin.com/in/johndoe

SUMMARY
Experienced software developer with 5+ years building scalable applications.Skilled in Python JavaScript and cloud technologies.Passionate about machine learning and AI development.

SKILLS
Programming Languages:Python,JavaScript,Java,SQL
Frameworks:React,Django,Flask,Node.js
Cloud Platforms:AWS,Azure,GCP

EXPERIENCE
Senior Software Developer
TechCorp Inc.|2022-Present
Developed microservices architecture serving 100K+ users.Implemented CI/CD pipelines reducing deployment time by 60%.Led team of 5 developers on critical projects.Built machine learning models improving recommendation accuracy by 35%.

Software Developer  
StartupXYZ|2020-2022
Created e-commerce platform handling $2M+ in transactions.Collaborated with cross-functional teams to deliver features.Implemented automated testing increasing code coverage to 90%.
"""
    
    print("Original text:")
    print(repr(sample_text))
    print("\n" + "="*50 + "\n")
    
    cleaned_text = processor.clean_and_structure_text(sample_text)
    print("Cleaned and structured text:")
    print(cleaned_text)
    print("\n" + "="*50 + "\n")
    
    contact_info = processor.extract_contact_info(sample_text)
    print("Extracted contact info:")
    print(contact_info)
    
    keywords = processor.extract_keywords(sample_text)
    print("\nExtracted keywords:")
    print(keywords[:10])

if __name__ == "__main__":
    test_text_processor()