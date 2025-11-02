"""
Job Description Parser Module
Extracts keywords, skills, and requirements from job descriptions
"""

import re
import logging
from typing import Dict, List, Set
from keybert import KeyBERT
from collections import Counter

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class JobParser:
    """Class to parse and analyze job descriptions"""
    
    def __init__(self):
        try:
            # Initialize KeyBERT for keyword extraction
            self.kw_model = KeyBERT()
            
            # Use basic text processing instead of spaCy
            logger.info("Using basic text processing for job parsing")
            self.nlp = None
            
            # Common skill categories and keywords
            self.tech_skills = {
                'programming_languages': [
                    'python', 'java', 'javascript', 'c++', 'c#', 'ruby', 'php', 'swift', 'kotlin', 
                    'go', 'rust', 'scala', 'r', 'matlab', 'sql', 'html', 'css', 'typescript'
                ],
                'frameworks': [
                    'react', 'angular', 'vue', 'node.js', 'express', 'django', 'flask', 'spring',
                    'laravel', 'rails', '.net', 'bootstrap', 'jquery', 'tensorflow', 'pytorch'
                ],
                'databases': [
                    'mysql', 'postgresql', 'mongodb', 'redis', 'elasticsearch', 'sqlite',
                    'oracle', 'sql server', 'dynamodb', 'cassandra'
                ],
                'cloud_platforms': [
                    'aws', 'azure', 'gcp', 'google cloud', 'docker', 'kubernetes', 'terraform',
                    'jenkins', 'git', 'github', 'gitlab', 'bitbucket'
                ],
                'tools': [
                    'git', 'jira', 'confluence', 'slack', 'trello', 'asana', 'figma', 'sketch',
                    'photoshop', 'illustrator', 'tableau', 'power bi', 'excel', 'powerpoint'
                ]
            }
            
            # Soft skills keywords
            self.soft_skills = [
                'leadership', 'communication', 'teamwork', 'problem solving', 'analytical',
                'creative', 'collaborative', 'adaptable', 'detail-oriented', 'organized',
                'time management', 'project management', 'critical thinking', 'innovation'
            ]
            
            # Experience level indicators
            self.experience_levels = {
                'entry': ['entry level', 'junior', '0-2 years', 'graduate', 'intern'],
                'mid': ['mid level', 'intermediate', '2-5 years', '3-5 years'],
                'senior': ['senior', 'lead', '5+ years', '7+ years', 'expert', 'principal']
            }
            
        except Exception as e:
            logger.error(f"Error initializing JobParser: {str(e)}")
            self.kw_model = None
            self.nlp = None
    
    def parse_job_description(self, job_text: str) -> Dict:
        """
        Parse job description and extract key information
        
        Args:
            job_text (str): The job description text
            
        Returns:
            Dict containing parsed information
        """
        try:
            # Clean the text
            cleaned_text = self._clean_text(job_text)
            
            # Extract various components
            keywords = self._extract_keywords(cleaned_text)
            skills = self._extract_skills(cleaned_text)
            requirements = self._extract_requirements(cleaned_text)
            experience_level = self._determine_experience_level(cleaned_text)
            
            return {
                'original_text': job_text,
                'cleaned_text': cleaned_text,
                'keywords': keywords,
                'technical_skills': skills['technical'],
                'soft_skills': skills['soft'],
                'requirements': requirements,
                'experience_level': experience_level,
                'word_count': len(cleaned_text.split()),
                'status': 'success'
            }
            
        except Exception as e:
            logger.error(f"Error parsing job description: {str(e)}")
            return {
                'original_text': job_text,
                'cleaned_text': '',
                'keywords': [],
                'technical_skills': [],
                'soft_skills': [],
                'requirements': [],
                'experience_level': 'unknown',
                'word_count': 0,
                'status': 'error',
                'error': str(e)
            }
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        # Remove extra whitespace and normalize
        text = re.sub(r'\s+', ' ', text)
        # Remove special formatting but keep essential punctuation
        text = re.sub(r'[^\w\s\.\,\-\(\)\+\#\&]', ' ', text)
        # Convert to lowercase for processing
        return text.lower().strip()
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract important keywords using KeyBERT"""
        try:
            if self.kw_model:
                # Extract keywords using KeyBERT
                keywords = self.kw_model.extract_keywords(
                    text, 
                    keyphrase_ngram_range=(1, 3), 
                    stop_words='english',
                    top_n=20,
                    use_mmr=True,
                    diversity=0.5
                )
                return [kw[0] for kw in keywords]
            else:
                # Fallback: simple frequency-based extraction
                return self._extract_keywords_fallback(text)
        except Exception as e:
            logger.error(f"Error extracting keywords: {str(e)}")
            return self._extract_keywords_fallback(text)
    
    def _extract_keywords_fallback(self, text: str) -> List[str]:
        """Fallback keyword extraction using frequency analysis"""
        # Remove common stop words
        stop_words = {'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'a', 'an'}
        words = [word for word in text.split() if word not in stop_words and len(word) > 2]
        
        # Get most common words
        word_freq = Counter(words)
        return [word for word, count in word_freq.most_common(20)]
    
    def _extract_skills(self, text: str) -> Dict[str, List[str]]:
        """Extract technical and soft skills from text"""
        technical_skills = []
        soft_skills = []
        
        try:
            # Extract technical skills
            for category, skills in self.tech_skills.items():
                for skill in skills:
                    if skill.lower() in text.lower():
                        technical_skills.append(skill)
            
            # Extract soft skills
            for skill in self.soft_skills:
                if skill.lower() in text.lower():
                    soft_skills.append(skill)
            
            # Remove duplicates while preserving order
            technical_skills = list(dict.fromkeys(technical_skills))
            soft_skills = list(dict.fromkeys(soft_skills))
            
            return {
                'technical': technical_skills,
                'soft': soft_skills
            }
            
        except Exception as e:
            logger.error(f"Error extracting skills: {str(e)}")
            return {'technical': [], 'soft': []}
    
    def _extract_requirements(self, text: str) -> List[str]:
        """Extract job requirements and qualifications"""
        requirements = []
        
        try:
            # Common requirement patterns
            requirement_patterns = [
                r'(?:required|must have|essential)[:\s]+([^.]+)',
                r'(?:bachelor|master|phd|degree)[^.]+',
                r'(?:\d+\+?\s*years?)[^.]+',
                r'(?:experience with|proficient in|knowledge of)[^.]+',
                r'(?:certification|certified)[^.]+'
            ]
            
            for pattern in requirement_patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                requirements.extend([match.strip() for match in matches if len(match.strip()) > 10])
            
            # Also look for bullet points or numbered lists
            bullet_pattern = r'(?:•|[*-]|\d+\.)\s*([^•*\n-]+)'
            bullet_matches = re.findall(bullet_pattern, text)
            
            # Filter for requirement-like bullet points
            for match in bullet_matches:
                if any(keyword in match.lower() for keyword in ['experience', 'skill', 'knowledge', 'ability', 'proficient']):
                    requirements.append(match.strip())
            
            # Remove duplicates and limit length
            requirements = list(dict.fromkeys(requirements))[:15]
            
            return requirements
            
        except Exception as e:
            logger.error(f"Error extracting requirements: {str(e)}")
            return []
    
    def _determine_experience_level(self, text: str) -> str:
        """Determine the experience level required for the job"""
        text_lower = text.lower()
        
        # Count mentions of different experience levels
        level_counts = {}
        for level, keywords in self.experience_levels.items():
            count = sum(1 for keyword in keywords if keyword in text_lower)
            level_counts[level] = count
        
        # Return the level with the highest count
        if level_counts:
            max_level = max(level_counts, key=level_counts.get)
            if level_counts[max_level] > 0:
                return max_level
        
        # Try to extract years of experience
        years_pattern = r'(\d+)\+?\s*(?:years?|yrs?)'
        years_matches = re.findall(years_pattern, text_lower)
        
        if years_matches:
            max_years = max(int(year) for year in years_matches)
            if max_years <= 2:
                return 'entry'
            elif max_years <= 5:
                return 'mid'
            else:
                return 'senior'
        
        return 'unknown'
    
    def calculate_match_score(self, resume_text: str, job_requirements: Dict) -> Dict:
        """
        Calculate how well a resume matches job requirements
        
        Args:
            resume_text (str): The resume text
            job_requirements (Dict): Parsed job requirements
            
        Returns:
            Dict with match scores and analysis
        """
        try:
            resume_lower = resume_text.lower()
            
            # Technical skills match
            tech_skills_found = []
            for skill in job_requirements.get('technical_skills', []):
                if skill.lower() in resume_lower:
                    tech_skills_found.append(skill)
            
            tech_match_score = len(tech_skills_found) / max(len(job_requirements.get('technical_skills', [])), 1) * 100
            
            # Keyword match
            keywords_found = []
            for keyword in job_requirements.get('keywords', []):
                if keyword.lower() in resume_lower:
                    keywords_found.append(keyword)
            
            keyword_match_score = len(keywords_found) / max(len(job_requirements.get('keywords', [])), 1) * 100
            
            # Overall match score (weighted average)
            overall_score = (tech_match_score * 0.6 + keyword_match_score * 0.4)
            
            return {
                'overall_score': round(overall_score, 2),
                'technical_skills_score': round(tech_match_score, 2),
                'keyword_score': round(keyword_match_score, 2),
                'matched_technical_skills': tech_skills_found,
                'matched_keywords': keywords_found,
                'missing_technical_skills': [skill for skill in job_requirements.get('technical_skills', []) if skill not in tech_skills_found],
                'status': 'success'
            }
            
        except Exception as e:
            logger.error(f"Error calculating match score: {str(e)}")
            return {
                'overall_score': 0,
                'technical_skills_score': 0,
                'keyword_score': 0,
                'matched_technical_skills': [],
                'matched_keywords': [],
                'missing_technical_skills': [],
                'status': 'error',
                'error': str(e)
            }

def test_job_parser():
    """Test function for the job parser"""
    parser = JobParser()
    
    sample_job_description = """
    Software Engineer - Full Stack Developer
    
    We are looking for a skilled Full Stack Developer to join our team.
    
    Requirements:
    • 3-5 years of experience in web development
    • Proficiency in Python, JavaScript, and React
    • Experience with databases (MySQL, PostgreSQL)
    • Knowledge of cloud platforms (AWS, Azure)
    • Strong problem-solving skills
    • Excellent communication and teamwork abilities
    
    Preferred:
    • Bachelor's degree in Computer Science
    • Experience with Docker and Kubernetes
    • Knowledge of machine learning
    """
    
    result = parser.parse_job_description(sample_job_description)
    
    print("Job Description Analysis:")
    print(f"Status: {result['status']}")
    print(f"Experience Level: {result['experience_level']}")
    print(f"Technical Skills: {result['technical_skills']}")
    print(f"Soft Skills: {result['soft_skills']}")
    print(f"Top Keywords: {result['keywords'][:5]}")

if __name__ == "__main__":
    test_job_parser()