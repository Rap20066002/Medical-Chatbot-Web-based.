"""
Doctor Routes - COMPLETE VERSION
With password change functionality
"""

from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, field_validator
from typing import Optional
import time

from api.middleware.auth import hash_password, verify_password, get_current_doctor
from models.patient import TokenData
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
        if len(v) < 6:
            raise ValueError('Password must be at least 6 characters long')
        return v

class PasswordChange(BaseModel):
    current_password: str
    new_password: str
    
    @field_validator('new_password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 6:
            raise ValueError('Password must be at least 6 characters long')
        return v

@router.post("/register")
async def register_doctor(doctor_data: DoctorRegister):
    """Register a new doctor (pending approval)"""
    try:
        existing = db_manager.doctors.find_one({"email": doctor_data.email.lower()})
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Doctor with this email already exists"
            )
        
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

@router.post("/change-password")
async def change_password(
    password_data: PasswordChange,
    token_data: TokenData = Depends(get_current_doctor)
):
    """Change doctor password"""
    doctor = db_manager.doctors.find_one({"email": token_data.email.lower()})
    
    if not doctor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Doctor account not found"
        )
    
    # Verify current password
    if not verify_password(password_data.current_password, doctor.get("password", "")):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Current password is incorrect"
        )
    
    # Update password
    db_manager.doctors.update_one(
        {"email": token_data.email.lower()},
        {"$set": {"password": hash_password(password_data.new_password)}}
    )
    
    return {"message": "Password changed successfully"}

@router.get("/me")
async def get_doctor_profile(token_data: TokenData = Depends(get_current_doctor)):
    """Get current doctor's profile"""
    doctor = db_manager.doctors.find_one({"email": token_data.email.lower()})
    
    if not doctor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Doctor account not found"
        )
    
    return {
        "id": str(doctor["_id"]),
        "name": doctor["name"],
        "email": doctor["email"],
        "specialization": doctor["specialization"],
        "license_number": doctor["license_number"],
        "status": doctor.get("status", "pending"),
        "created_at": doctor.get("created_at")
    }