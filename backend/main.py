"""
FastAPI Backend Entry Point
Handles all API routes and middleware
"""

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from contextlib import asynccontextmanager
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import routes
from api.routes import auth, patients, doctors, admin
from core.database import db_manager
from core.llm import llm_manager

# Lifespan context manager for startup/shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("🚀 Starting up application...")
    print("📦 Initializing LLM (this may take a moment)...")
    # LLM is already initialized in llm_manager
    print("✅ Application ready!")
    
    yield
    
    # Shutdown
    print("🔄 Shutting down application...")
    db_manager.close()
    print("✅ Cleanup complete!")

# Create FastAPI app
app = FastAPI(
    title="Medical Health Assessment API",
    description="AI-powered health assessment and patient management system",
    version="2.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:8501",  # Streamlit default
        "https://*.streamlit.app",  # Streamlit Cloud
        os.getenv("FRONTEND_URL", "*")
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(patients.router, prefix="/api/patients", tags=["Patients"])
app.include_router(doctors.router, prefix="/api/doctors", tags=["Doctors"])
app.include_router(admin.router, prefix="/api/admin", tags=["Admin"])

# Health check endpoint
@app.get("/")
async def root():
    return {
        "message": "Medical Health Assessment API",
        "version": "2.0.0",
        "status": "healthy",
        "llm_available": llm_manager.is_available()
    }

@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    try:
        # Test database connection
        db_manager.patients.find_one()
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"
    
    return {
        "status": "healthy",
        "database": db_status,
        "llm": "available" if llm_manager.is_available() else "unavailable"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )