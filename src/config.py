# src/config.py
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    # Flask settings
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-change-in-production')
    DEBUG = os.getenv('DEBUG', 'True') == 'True'
    
    # Database settings
    DATABASE_PATH = os.getenv('DATABASE_PATH', 'database/resume_screener.db')
    
    # Upload settings
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    ALLOWED_EXTENSIONS = {'pdf', 'docx'}
    
    # LLM settings
    USE_GEMINI = os.getenv('USE_GEMINI', 'False') == 'True'
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', None)
    OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'llama3.2:3b')
    
    # Server settings
    HOST = os.getenv('HOST', '0.0.0.0')
    PORT = int(os.getenv('PORT', 5000))

# Example .env file content:
"""
SECRET_KEY=your-super-secret-key-here
DEBUG=True
DATABASE_PATH=database/resume_screener.db
UPLOAD_FOLDER=uploads
USE_GEMINI=False
GEMINI_API_KEY=your-gemini-api-key-here
OLLAMA_MODEL=llama3.2:3b
HOST=0.0.0.0
PORT=5000
"""