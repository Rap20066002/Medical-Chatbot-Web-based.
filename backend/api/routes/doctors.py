"""
Doctor Routes - IMPROVED VERSION
✅ Handles DuplicateKeyError from database unique constraint
✅ Better error messages for duplicate emails
"""

from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, field_validator
from pymongo.errors import DuplicateKeyError
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
    """
    Register a new doctor (pending approval)
    ✅ MongoDB unique constraint automatically prevents duplicate emails
    ✅ Better error messages
    """
    try:
        target_email = doctor_data.email.lower().strip()
        
        # ============================================================
        # ✅ IMPROVED: Check for duplicates before attempting insert
        # This gives us a chance to provide better error messages
        # ============================================================
        existing = db_manager.doctors.find_one({"email": target_email})
        if existing:
            existing_status = existing.get("status", "pending")
            
            if existing_status == "pending":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Email '{doctor_data.email}' already has a pending registration. Please wait for admin approval or contact support."
                )
            elif existing_status == "approved":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Email '{doctor_data.email}' is already registered as an approved doctor. Please try logging in instead."
                )
            elif existing_status == "rejected":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Email '{doctor_data.email}' was previously rejected. Please contact administration or use a different email."
                )
            elif existing_status == "disabled":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Email '{doctor_data.email}' account is disabled. Please contact administration."
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Email '{doctor_data.email}' is already registered. Please use a different email or try logging in."
                )
        
        # Create doctor record
        doctor_record = {
            "name": doctor_data.name,
            "email": target_email,
            "specialization": doctor_data.specialization,
            "license_number": doctor_data.license_number,
            "password": hash_password(doctor_data.password),
            "status": "pending",
            "created_at": time.time()
        }
        
        # ============================================================
        # ✅ IMPROVED: Try to insert with database constraint handling
        # ============================================================
        try:
            db_manager.doctors.insert_one(doctor_record)
            print(f"✅ Doctor registered: {target_email} (pending approval)")
            
            return {
                "message": "Registration submitted successfully! Your account is pending admin approval.",
                "status": "pending",
                "email": doctor_data.email,
                "next_steps": "You will be notified once your account is approved. This usually takes 24-48 hours."
            }
        
        except DuplicateKeyError:
            # This catches race conditions where two requests happen simultaneously
            print(f"⚠️  Duplicate key error for: {target_email}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Email '{doctor_data.email}' was just registered by another request. Please try logging in or use a different email."
            )
    
    except HTTPException as he:
        raise he
    
    except Exception as e:
        print(f"❌ Doctor registration error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )


@router.post("/change-password")
async def change_password(
    password_data: PasswordChange,
    token_data: TokenData = Depends(get_current_doctor)
):
    """Change doctor password"""
    target_email = token_data.email.lower().strip()
    doctor = db_manager.doctors.find_one({"email": target_email})
    
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
        {"email": target_email},
        {"$set": {"password": hash_password(password_data.new_password)}}
    )
    
    return {"message": "Password changed successfully"}


@router.get("/me")
async def get_doctor_profile(token_data: TokenData = Depends(get_current_doctor)):
    """Get current doctor's profile"""
    target_email = token_data.email.lower().strip()
    doctor = db_manager.doctors.find_one({"email": target_email})
    
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