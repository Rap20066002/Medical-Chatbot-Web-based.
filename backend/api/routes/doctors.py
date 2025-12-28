"""
Doctor Routes
Doctor registration and management
"""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr, field_validator
import time

from api.middleware.auth import hash_password
from core.database import db_manager

router = APIRouter()

class DoctorRegister(BaseModel):
    name: str
    email: str
    specialization: str
    license_number: str
    password: str
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v: str) -> str:
        """Validate email format"""
        if '@' not in v:
            raise ValueError('Email must contain @ symbol')
        parts = v.split('@')
        if len(parts) != 2 or not parts[0] or not parts[1]:
            raise ValueError('Invalid email format. Use: user@example.com')
        if '.' not in parts[1]:
            raise ValueError('Email domain must have extension (e.g., .com, .org)')
        return v.lower()
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Ensure password meets requirements"""
        if len(v) < 6:
            raise ValueError('Password must be at least 6 characters long')
        return v


@router.post("/register")
async def register_doctor(doctor_data: DoctorRegister):
    """Register a new doctor (pending approval)"""
    try:
        # Check if doctor already exists
        existing = db_manager.doctors.find_one({"email": doctor_data.email.lower()})
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Doctor with this email already exists"
            )
        
        # Create doctor record
        doctor_record = {
            "name": doctor_data.name,
            "email": doctor_data.email.lower(),
            "specialization": doctor_data.specialization,
            "license_number": doctor_data.license_number,
            "password": hash_password(doctor_data.password),
            "status": "pending",
            "created_at": time.time()
        }
        
        db_manager.doctors.insert_one(doctor_record)
        
        return {
            "message": "Registration submitted for admin approval",
            "status": "pending"
        }
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )