# SmartResume AI Configuration
"""
Configuration module for SmartResume AI
Handles environment variables and application settings
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Application configuration class"""
    
    # Groq Configuration (FREE!)
    GROQ_API_KEY = os.getenv('GROQ_API_KEY', '')
    DEFAULT_MODEL = os.getenv('DEFAULT_MODEL', 'llama-3.3-70b-versatile')
    MAX_TOKENS = int(os.getenv('MAX_TOKENS', '4000'))
    TEMPERATURE = float(os.getenv('TEMPERATURE', '0.3'))
    
    # API Configuration
    API_HOST = os.getenv('API_HOST', '0.0.0.0')
    API_PORT = int(os.getenv('API_PORT', '8000'))
    DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'
    
    # File Configuration
    UPLOAD_DIR = os.getenv('UPLOAD_DIR', 'uploads')
    OUTPUT_DIR = os.getenv('OUTPUT_DIR', 'outputs')
    MAX_FILE_SIZE = int(os.getenv('MAX_FILE_SIZE', '10485760'))  # 10MB
    ALLOWED_EXTENSIONS = os.getenv('ALLOWED_EXTENSIONS', 'pdf,docx,txt').split(',')
    
    # Session Configuration
    SESSION_TIMEOUT = int(os.getenv('SESSION_TIMEOUT', '3600'))  # 1 hour
    AUTO_CLEANUP = os.getenv('AUTO_CLEANUP', 'True').lower() == 'true'
    CLEANUP_INTERVAL = int(os.getenv('CLEANUP_INTERVAL', '24'))  # hours
    
    # Resume Generation
    DEFAULT_STYLE = os.getenv('DEFAULT_STYLE', 'modern')
    SUPPORTED_STYLES = os.getenv('SUPPORTED_STYLES', 'modern,classic,minimal').split(',')
    
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'smartresume.log')
    
    # Security
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-change-in-production')
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', '*')
    
    @classmethod
    def validate_config(cls):
        """Validate critical configuration settings"""
        errors = []
        
        if not cls.GROQ_API_KEY:
            errors.append("GROQ_API_KEY is not set")
        
        if cls.MAX_FILE_SIZE <= 0:
            errors.append("MAX_FILE_SIZE must be positive")
        
        if cls.SESSION_TIMEOUT <= 0:
            errors.append("SESSION_TIMEOUT must be positive")
        
        return errors
    
    @classmethod
    def get_groq_config(cls):
        """Get Groq specific configuration"""
        return {
            'api_key': cls.GROQ_API_KEY,
            'model': cls.DEFAULT_MODEL,
            'max_tokens': cls.MAX_TOKENS,
            'temperature': cls.TEMPERATURE
        }
    
    @classmethod
    def get_file_config(cls):
        """Get file handling configuration"""
        return {
            'upload_dir': cls.UPLOAD_DIR,
            'output_dir': cls.OUTPUT_DIR,
            'max_file_size': cls.MAX_FILE_SIZE,
            'allowed_extensions': cls.ALLOWED_EXTENSIONS
        }

# Create directories if they don't exist
os.makedirs(Config.UPLOAD_DIR, exist_ok=True)
os.makedirs(Config.OUTPUT_DIR, exist_ok=True)