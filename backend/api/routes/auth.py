"""
Authentication Routes
Login and registration endpoints
"""

from fastapi import APIRouter, HTTPException, status
from datetime import timedelta

from models.patient import PatientLogin, Token, PatientCreate
from api.middleware.auth import (
    create_access_token,
    hash_password,
    verify_password
)
from core.database import db_manager
from core.config import settings

router = APIRouter()

@router.post("/patient/register", response_model=Token)
async def register_patient(patient_data: PatientCreate):
    """Register a new patient"""
    # Check if patient already exists
    for patient in db_manager.patients.find():
        try:
            decrypted_demo = db_manager.decrypt_dict(patient.get("demographic", {}))
            if decrypted_demo.get("email", "").lower() == patient_data.demographic.email.lower():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Patient with this email already exists"
                )
        except:
            continue
    
    # Hash password
    hashed_password = hash_password(patient_data.password)
    
    # Encrypt patient data
    encrypted_data = {
        "demographic": db_manager.encrypt_dict(patient_data.demographic.dict()),
        "per_symptom": db_manager.encrypt_dict(patient_data.per_symptom),
        "Gen_questions": db_manager.encrypt_dict(patient_data.gen_questions),
        "password": hashed_password,
        "created_at": __import__('time').time()
    }
    
    if patient_data.summary:
        encrypted_data["summary"] = db_manager.encrypt_data(patient_data.summary)
    
    # Save to database
    result = db_manager.patients.insert_one(encrypted_data)
    
    # Create access token
    access_token = create_access_token(
        data={
            "sub": patient_data.demographic.email,
            "user_type": "patient"
        },
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    return Token(
        access_token=access_token,
        user_type="patient",
        user_id=str(result.inserted_id)
    )

@router.post("/patient/login", response_model=Token)
async def login_patient(credentials: PatientLogin):
    """Patient login"""
    # Find patient by email
    found_patient = None
    for patient in db_manager.patients.find():
        try:
            decrypted_demo = db_manager.decrypt_dict(patient.get("demographic", {}))
            if decrypted_demo.get("email", "").lower() == credentials.email.lower():
                found_patient = patient
                break
        except:
            continue
    
    if not found_patient:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Verify password
    if not verify_password(credentials.password, found_patient.get("password", "")):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Create access token
    access_token = create_access_token(
        data={
            "sub": credentials.email,
            "user_type": "patient"
        },
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    return Token(
        access_token=access_token,
        user_type="patient",
        user_id=str(found_patient["_id"])
    )

@router.post("/doctor/login", response_model=Token)
async def login_doctor(credentials: PatientLogin):
    """Doctor login"""
    doctor = db_manager.doctors.find_one({"email": credentials.email.lower()})
    
    if not doctor:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Check if approved
    if doctor.get("status") != "approved":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account is pending approval"
        )
    
    # Verify password
    if not verify_password(credentials.password, doctor.get("password", "")):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Create access token
    access_token = create_access_token(
        data={
            "sub": credentials.email,
            "user_type": "doctor"
        },
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    return Token(
        access_token=access_token,
        user_type="doctor",
        user_id=str(doctor["_id"])
    )

@router.post("/admin/login", response_model=Token)
async def login_admin(credentials: PatientLogin):
    """Admin login"""
    admin = db_manager.admins.find_one({"email": credentials.email.lower()})
    
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Verify password
    if not verify_password(credentials.password, admin.get("password", "")):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Create access token
    access_token = create_access_token(
        data={
            "sub": credentials.email,
            "user_type": "admin"
        },
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    return Token(
        access_token=access_token,
        user_type="admin",
        user_id=str(admin["_id"])
    )