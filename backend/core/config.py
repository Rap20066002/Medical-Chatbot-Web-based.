"""
Configuration settings for the application
FIXED VERSION - Auto-generates encryption key if missing
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
    DEBUG: bool = os.getenv("DEBUG", "True").lower() == "true"
    
    # API
    API_V1_PREFIX: str = "/api"
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-secret-key-CHANGE-IN-PRODUCTION-12345")
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
    USE_LLM: bool = os.getenv("USE_LLM", "False").lower() == "true"
    
    # CORS
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:8501")
    
    # File Upload
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB
    
    def get_encryption_key(self) -> bytes:
        """Get or generate encryption key"""
        if self.ENCRYPTION_KEY:
            try:
                return self.ENCRYPTION_KEY.encode()
            except:
                pass
        
        # Generate new key
        from cryptography.fernet import Fernet
        key = Fernet.generate_key()
        
        # Try to save to .env file
        try:
            env_path = '.env'
            if os.path.exists(env_path):
                with open(env_path, 'r') as f:
                    content = f.read()
                
                if 'ENCRYPTION_KEY' not in content:
                    with open(env_path, 'a') as f:
                        f.write(f"\nENCRYPTION_KEY={key.decode()}\n")
                    print(f"✅ Generated and saved encryption key to .env")
        except Exception as e:
            print(f"⚠️  Could not save encryption key to .env: {e}")
            print(f"   Add this line to your .env file:")
            print(f"   ENCRYPTION_KEY={key.decode()}")
        
        return key
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()