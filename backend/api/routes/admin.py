"""
Admin Routes
Admin operations for user management
"""

from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel
from bson import ObjectId
from typing import List
import time

from api.middleware.auth import get_current_admin, hash_password
from models.patient import TokenData
from core.database import db_manager

router = APIRouter()

class AdminCreate(BaseModel):
    name: str
    email: str
    password: str

class DoctorApproval(BaseModel):
    doctor_id: str
    approved: bool

@router.post("/create")
async def create_admin(admin_data: AdminCreate):
    """Create first admin (only works if no admins exist)"""
    # Check if any admin exists
    if db_manager.admins.count_documents({}) > 0:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin already exists. Use admin login to create more admins."
        )
    
    admin_record = {
        "name": admin_data.name,
        "email": admin_data.email.lower(),
        "password": hash_password(admin_data.password),
        "created_at": time.time()
    }
    
    db_manager.admins.insert_one(admin_record)
    
    return {"message": "Admin created successfully"}

@router.get("/doctors/pending")
async def get_pending_doctors(token_data: TokenData = Depends(get_current_admin)):
    """Get all pending doctor applications"""
    pending_doctors = list(db_manager.doctors.find({"status": "pending"}))
    
    result = []
    for doctor in pending_doctors:
        result.append({
            "id": str(doctor["_id"]),
            "name": doctor["name"],
            "email": doctor["email"],
            "specialization": doctor["specialization"],
            "license_number": doctor["license_number"],
            "created_at": doctor.get("created_at")
        })
    
    return result

@router.post("/doctors/approve")
async def approve_doctor(
    approval: DoctorApproval,
    token_data: TokenData = Depends(get_current_admin)
):
    """Approve or reject doctor application"""
    try:
        doctor_id = ObjectId(approval.doctor_id)
    except:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid doctor ID"
        )
    
    new_status = "approved" if approval.approved else "rejected"
    
    result = db_manager.doctors.update_one(
        {"_id": doctor_id},
        {
            "$set": {
                "status": new_status,
                "approved_by": token_data.email,
                "approved_at": time.time()
            }
        }
    )
    
    if result.modified_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Doctor not found"
        )
    
    return {
        "message": f"Doctor {'approved' if approval.approved else 'rejected'} successfully"
    }

@router.get("/patients/count")
async def get_patient_count(token_data: TokenData = Depends(get_current_admin)):
    """Get total number of patients"""
    count = db_manager.patients.count_documents({})
    return {"count": count}

@router.get("/doctors/count")
async def get_doctor_count(token_data: TokenData = Depends(get_current_admin)):
    """Get total number of doctors"""
    approved = db_manager.doctors.count_documents({"status": "approved"})
    pending = db_manager.doctors.count_documents({"status": "pending"})
    
    return {
        "approved": approved,
        "pending": pending,
        "total": approved + pending
    }