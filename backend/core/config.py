"""
Configuration settings for the application
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    # Application
    APP_NAME: str = "Medical Health Assessment"
    APP_VERSION: str = "2.0.0"
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    
    # API
    API_V1_PREFIX: str = "/api"
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    
    # Database
    MONGODB_URI: str = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
    MONGODB_DB: str = os.getenv("MONGODB_DB", "health_chatbot_db")
    
    # Encryption
    ENCRYPTION_KEY: Optional[str] = os.getenv("ENCRYPTION_KEY")
    
    # LLM
    HUGGING_FACE_TOKEN: str = os.getenv("HUGGING_FACE_TOKEN", "")
    LLM_MODEL_NAME: str = "TheBloke/Mistral-7B-Instruct-v0.2-GGUF"
    USE_LLM: bool = os.getenv("USE_LLM", "True").lower() == "true"
    
    # CORS
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:8501")
    
    # File Upload
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()