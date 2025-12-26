"""
Doctor Routes
Doctor registration and management
"""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr
import time

from api.middleware.auth import hash_password
from core.database import db_manager

router = APIRouter()

class DoctorRegister(BaseModel):
    name: str
    email: EmailStr
    specialization: str
    license_number: str
    password: str

@router.post("/register")
async def register_doctor(doctor_data: DoctorRegister):
    """Register a new doctor (pending approval)"""
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
        "status": "pending",  # Requires admin approval
        "created_at": time.time()
    }
    
    db_manager.doctors.insert_one(doctor_record)
    
    return {
        "message": "Registration submitted for admin approval",
        "status": "pending"
    }