"""
FastAPI Backend Entry Point - FIXED VERSION
Handles all API routes and middleware
"""

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from utils.pdf_generator import generate_patient_pdf
from api.routes import auth, patients, doctors, admin, language
import os
from dotenv import load_dotenv
import traceback
from fastapi.exceptions import RequestValidationError

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

# CORS middleware - MORE PERMISSIVE FOR DEVELOPMENT
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins in development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Enhanced global exception handler with user-friendly messages"""
    print(f"❌ ERROR: {str(exc)}")
    print(traceback.format_exc())
    
    # Map exception types to user-friendly messages
    error_message = str(exc)
    
    # Check for common error patterns
    if "validation" in error_message.lower():
        error_message = "❌ Invalid input data. Please check your form and try again."
    elif "timeout" in error_message.lower():
        error_message = "⏱️ Request timed out. Please try again."
    elif "connection" in error_message.lower():
        error_message = "🔌 Cannot connect to database. Please contact support."
    elif "duplicate" in error_message.lower() or "already exists" in error_message.lower():
        error_message = "❌ This record already exists. Please use different values."
    elif "not found" in error_message.lower():
        error_message = "❌ Record not found. Please check your input."
    elif "unauthorized" in error_message.lower() or "forbidden" in error_message.lower():
        error_message = "🔒 Access denied. Please login again."
    
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": error_message,
            "error_type": type(exc).__name__
        }
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    """Handle Pydantic validation errors with user-friendly messages"""
    errors = exc.errors()
    
    # Extract the most relevant error messages
    if errors:
        first_error = errors[0]
        field = first_error.get('loc', [''])[-1]
        msg = first_error.get('msg', 'Invalid input')
        
        # Create user-friendly message
        if 'email' in field.lower():
            user_message = "❌ Invalid email format. Please use: user@example.com"
        elif 'password' in field.lower():
            user_message = "❌ Password must be at least 6 characters long"
        elif 'phone' in field.lower():
            user_message = "❌ Phone number must contain at least 10 digits"
        elif 'age' in field.lower():
            user_message = "❌ Age must be between 0 and 150"
        else:
            user_message = f"❌ Invalid {field}: {msg}"
    else:
        user_message = "❌ Invalid input data. Please check your form."
    
    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "message": user_message,
            "field": field if errors else None
        }
    )

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(patients.router, prefix="/api/patients", tags=["Patients"])
app.include_router(doctors.router, prefix="/api/doctors", tags=["Doctors"])
app.include_router(admin.router, prefix="/api/admin", tags=["Admin"])
app.include_router(language.router, prefix="/api/language", tags=["Language"])

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