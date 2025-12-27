"""
Admin Routes - FIXED VERSION
Admin operations for user management
"""

from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, EmailStr
from bson import ObjectId
from typing import List
import time

from api.middleware.auth import get_current_admin, hash_password
from models.patient import TokenData
from core.database import db_manager

router = APIRouter()

class AdminCreate(BaseModel):
    name: str
    email: EmailStr
    password: str

class DoctorApproval(BaseModel):
    doctor_id: str
    approved: bool

class DoctorToggle(BaseModel):
    doctor_id: str

@router.post("/create")
async def create_admin(admin_data: AdminCreate, token_data: TokenData = Depends(get_current_admin)):
    """Create new admin (requires existing admin authentication)"""
    # Check if admin with this email already exists
    existing = db_manager.admins.find_one({"email": admin_data.email.lower()})
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Admin with this email already exists"
        )
    
    admin_record = {
        "name": admin_data.name,
        "email": admin_data.email.lower(),
        "password": hash_password(admin_data.password),
        "created_by": token_data.email,
        "created_at": time.time()
    }
    
    db_manager.admins.insert_one(admin_record)
    
    return {"message": "Admin created successfully"}

@router.post("/create-first")
async def create_first_admin(admin_data: AdminCreate):
    """Create first admin (only works if no admins exist)"""
    # Check if any admin exists
    if db_manager.admins.count_documents({}) > 0:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin already exists. Please login to create more admins."
        )
    
    admin_record = {
        "name": admin_data.name,
        "email": admin_data.email.lower(),
        "password": hash_password(admin_data.password),
        "created_at": time.time()
    }
    
    db_manager.admins.insert_one(admin_record)
    
    return {"message": "First admin created successfully"}

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

@router.get("/doctors/all")
async def get_all_doctors(token_data: TokenData = Depends(get_current_admin)):
    """Get all doctors (approved and pending)"""
    all_doctors = list(db_manager.doctors.find({}))
    
    result = []
    for doctor in all_doctors:
        result.append({
            "id": str(doctor["_id"]),
            "name": doctor["name"],
            "email": doctor["email"],
            "specialization": doctor["specialization"],
            "license_number": doctor["license_number"],
            "status": doctor.get("status", "pending"),
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

@router.post("/doctors/toggle")
async def toggle_doctor_status(
    toggle: DoctorToggle,
    token_data: TokenData = Depends(get_current_admin)
):
    """Toggle doctor status between approved and disabled"""
    try:
        doctor_id = ObjectId(toggle.doctor_id)
    except:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid doctor ID"
        )
    
    # Get current doctor
    doctor = db_manager.doctors.find_one({"_id": doctor_id})
    if not doctor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Doctor not found"
        )
    
    # Toggle status
    current_status = doctor.get("status", "pending")
    new_status = "disabled" if current_status == "approved" else "approved"
    
    db_manager.doctors.update_one(
        {"_id": doctor_id},
        {
            "$set": {
                "status": new_status,
                "modified_by": token_data.email,
                "modified_at": time.time()
            }
        }
    )
    
    return {
        "message": f"Doctor {'disabled' if new_status == 'disabled' else 'enabled'} successfully",
        "new_status": new_status
    }

@router.get("/patients/count")
async def get_patient_count(token_data: TokenData = Depends(get_current_admin)):
    """Get total number of patients"""
    count = db_manager.patients.count_documents({})
    return {"count": count}

@router.get("/patients/all")
async def get_all_patients(token_data: TokenData = Depends(get_current_admin)):
    """Get all patients (demographics only)"""
    patients_list = []
    
    for patient in db_manager.patients.find():
        try:
            decrypted_demo = db_manager.decrypt_dict(patient["demographic"])
            patients_list.append({
                "id": str(patient["_id"]),
                "name": decrypted_demo.get("name", "Unknown"),
                "age": decrypted_demo.get("age"),
                "gender": decrypted_demo.get("gender"),
                "email": decrypted_demo.get("email"),
                "phone": decrypted_demo.get("phone"),
                "created_at": patient.get("created_at")
            })
        except Exception as e:
            continue
    
    return patients_list

@router.get("/doctors/count")
async def get_doctor_count(token_data: TokenData = Depends(get_current_admin)):
    """Get total number of doctors"""
    approved = db_manager.doctors.count_documents({"status": "approved"})
    pending = db_manager.doctors.count_documents({"status": "pending"})
    disabled = db_manager.doctors.count_documents({"status": "disabled"})
    
    return {
        "approved": approved,
        "pending": pending,
        "disabled": disabled,
        "total": approved + pending + disabled
    }