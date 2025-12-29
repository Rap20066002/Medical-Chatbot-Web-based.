"""
Patient Routes - COMPLETE VERSION
All CLI features restored (without chat)
"""

from fastapi import APIRouter, HTTPException, Depends, status, Response
from typing import List, Dict, Optional
from bson import ObjectId
from pydantic import BaseModel, Field, field_validator

from models.patient import (
    PatientResponse,
    SymptomAnalysisRequest,
    SymptomAnalysisResponse,
    TokenData,
    PatientDemographic,
    SymptomDetail
)
from api.middleware.auth import get_current_patient, get_current_doctor, hash_password, verify_password
from core.database import db_manager
from core.llm import llm_manager
from utils.pdf_generator import generate_patient_pdf

router = APIRouter()

# Password change model
class PasswordChange(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=6)
    
    @field_validator('new_password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 6:
            raise ValueError('Password must be at least 6 characters long')
        return v

# Update models for individual sections
class DemographicUpdate(BaseModel):
    demographic: PatientDemographic

class SymptomUpdate(BaseModel):
    per_symptom: Dict[str, SymptomDetail]

class HealthQuestionsUpdate(BaseModel):
    gen_questions: Dict[str, str]

@router.get("/me", response_model=PatientResponse)
async def get_my_profile(token_data: TokenData = Depends(get_current_patient)):
    """Get current patient's profile"""
    found_patient = None
    for patient in db_manager.patients.find():
        try:
            decrypted_demo = db_manager.decrypt_dict(patient.get("demographic", {}))
            if decrypted_demo.get("email", "").lower() == token_data.email.lower():
                found_patient = patient
                break
        except:
            continue
    
    if not found_patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found"
        )
    
    decrypted_data = {
        "id": str(found_patient["_id"]),
        "demographic": db_manager.decrypt_dict(found_patient["demographic"]),
        "per_symptom": db_manager.decrypt_dict(found_patient["per_symptom"]),
        "gen_questions": db_manager.decrypt_dict(found_patient.get("Gen_questions", {})),
        "created_at": found_patient.get("created_at")
    }
    
    if "summary" in found_patient:
        try:
            decrypted_data["summary"] = db_manager.decrypt_data(found_patient["summary"])
        except:
            decrypted_data["summary"] = None
    
    return PatientResponse(**decrypted_data)

@router.get("/me/pdf")
async def download_my_pdf(token_data: TokenData = Depends(get_current_patient)):
    """Download patient's health report as PDF"""
    found_patient = None
    for patient in db_manager.patients.find():
        try:
            decrypted_demo = db_manager.decrypt_dict(patient.get("demographic", {}))
            if decrypted_demo.get("email", "").lower() == token_data.email.lower():
                found_patient = patient
                break
        except:
            continue
    
    if not found_patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found"
        )
    
    decrypted_data = {
        "demographic": db_manager.decrypt_dict(found_patient["demographic"]),
        "per_symptom": db_manager.decrypt_dict(found_patient["per_symptom"]),
        "Gen_questions": db_manager.decrypt_dict(found_patient.get("Gen_questions", {}))
    }
    
    if "summary" in found_patient:
        try:
            decrypted_data["summary"] = db_manager.decrypt_data(found_patient["summary"])
        except:
            decrypted_data["summary"] = None
    
    pdf_buffer = generate_patient_pdf(decrypted_data)
    patient_name = decrypted_data["demographic"].get("name", "patient").replace(" ", "_")
    filename = f"{patient_name}_Health_Report.pdf"
    
    return Response(
        content=pdf_buffer.getvalue(),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@router.put("/me/demographic")
async def update_demographic(
    update_data: DemographicUpdate,
    token_data: TokenData = Depends(get_current_patient)
):
    """Update only demographic information"""
    found_patient = None
    for patient in db_manager.patients.find():
        try:
            decrypted_demo = db_manager.decrypt_dict(patient.get("demographic", {}))
            if decrypted_demo.get("email", "").lower() == token_data.email.lower():
                found_patient = patient
                break
        except:
            continue
    
    if not found_patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found"
        )
    
    db_manager.patients.update_one(
        {"_id": found_patient["_id"]},
        {"$set": {"demographic": db_manager.encrypt_dict(update_data.demographic.dict())}}
    )
    
    return {"message": "Demographic information updated successfully"}

@router.put("/me/symptoms")
async def update_symptoms(
    update_data: SymptomUpdate,
    token_data: TokenData = Depends(get_current_patient)
):
    """Update only symptom details and regenerate summary"""
    found_patient = None
    for patient in db_manager.patients.find():
        try:
            decrypted_demo = db_manager.decrypt_dict(patient.get("demographic", {}))
            if decrypted_demo.get("email", "").lower() == token_data.email.lower():
                found_patient = patient
                break
        except:
            continue
    
    if not found_patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found"
        )
    
    # Convert SymptomDetail objects to dict
    per_symptom_dict = {}
    for symptom_name, symptom_detail in update_data.per_symptom.items():
        per_symptom_dict[symptom_name] = {
            "Duration": symptom_detail.Duration or "",
            "Severity": symptom_detail.Severity or "",
            "Frequency": symptom_detail.Frequency or "",
            "Factors": symptom_detail.Factors or "",
            "Additional Notes": symptom_detail.additional_notes or ""
        }
    
    update_dict = {"per_symptom": db_manager.encrypt_dict(per_symptom_dict)}
    
    # Regenerate summary
    current_data = {
        "demographic": db_manager.decrypt_dict(found_patient["demographic"]),
        "per_symptom": per_symptom_dict,
        "Gen_questions": db_manager.decrypt_dict(found_patient.get("Gen_questions", {}))
    }
    
    new_summary = llm_manager.summarize_patient_condition(current_data)
    if new_summary:
        update_dict["summary"] = db_manager.encrypt_data(new_summary)
    
    db_manager.patients.update_one(
        {"_id": found_patient["_id"]},
        {"$set": update_dict}
    )
    
    return {"message": "Symptoms updated and summary regenerated successfully"}

@router.put("/me/health-questions")
async def update_health_questions(
    update_data: HealthQuestionsUpdate,
    token_data: TokenData = Depends(get_current_patient)
):
    """Update only general health questions and regenerate summary"""
    found_patient = None
    for patient in db_manager.patients.find():
        try:
            decrypted_demo = db_manager.decrypt_dict(patient.get("demographic", {}))
            if decrypted_demo.get("email", "").lower() == token_data.email.lower():
                found_patient = patient
                break
        except:
            continue
    
    if not found_patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found"
        )
    
    update_dict = {"Gen_questions": db_manager.encrypt_dict(update_data.gen_questions)}
    
    # Regenerate summary
    current_data = {
        "demographic": db_manager.decrypt_dict(found_patient["demographic"]),
        "per_symptom": db_manager.decrypt_dict(found_patient["per_symptom"]),
        "Gen_questions": update_data.gen_questions
    }
    
    new_summary = llm_manager.summarize_patient_condition(current_data)
    if new_summary:
        update_dict["summary"] = db_manager.encrypt_data(new_summary)
    
    db_manager.patients.update_one(
        {"_id": found_patient["_id"]},
        {"$set": update_dict}
    )
    
    return {"message": "Health questions updated and summary regenerated successfully"}

@router.post("/me/change-password")
async def change_password(
    password_data: PasswordChange,
    token_data: TokenData = Depends(get_current_patient)
):
    """Change patient password"""
    found_patient = None
    for patient in db_manager.patients.find():
        try:
            decrypted_demo = db_manager.decrypt_dict(patient.get("demographic", {}))
            if decrypted_demo.get("email", "").lower() == token_data.email.lower():
                found_patient = patient
                break
        except:
            continue
    
    if not found_patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found"
        )
    
    # Verify current password
    if not verify_password(password_data.current_password, found_patient.get("password", "")):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Current password is incorrect"
        )
    
    # Update password
    db_manager.patients.update_one(
        {"_id": found_patient["_id"]},
        {"$set": {"password": hash_password(password_data.new_password)}}
    )
    
    return {"message": "Password changed successfully"}

@router.post("/analyze-symptoms", response_model=SymptomAnalysisResponse)
async def analyze_symptoms(request: SymptomAnalysisRequest):
    """Analyze symptoms - NO AUTH REQUIRED (for registration)"""
    symptoms = llm_manager.identify_symptoms(request.description)
    extracted_details = llm_manager.extract_symptom_details(request.description)
    
    questions = []
    if symptoms:
        questions = llm_manager.generate_questions(symptoms[0], extracted_details)
    
    return SymptomAnalysisResponse(
        symptoms=symptoms,
        questions=questions,
        extracted_info=extracted_details
    )

@router.get("/{patient_id}", response_model=PatientResponse)
async def get_patient_by_id(
    patient_id: str,
    token_data: TokenData = Depends(get_current_doctor)
):
    """Get patient by ID (doctors only)"""
    try:
        patient = db_manager.patients.find_one({"_id": ObjectId(patient_id)})
    except:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid patient ID"
        )
    
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found"
        )
    
    decrypted_data = {
        "id": str(patient["_id"]),
        "demographic": db_manager.decrypt_dict(patient["demographic"]),
        "per_symptom": db_manager.decrypt_dict(patient["per_symptom"]),
        "gen_questions": db_manager.decrypt_dict(patient.get("Gen_questions", {})),
        "created_at": patient.get("created_at")
    }
    
    if "summary" in patient:
        try:
            decrypted_data["summary"] = db_manager.decrypt_data(patient["summary"])
        except:
            decrypted_data["summary"] = None
    
    return PatientResponse(**decrypted_data)

@router.get("/{patient_id}/pdf")
async def download_patient_pdf(
    patient_id: str,
    token_data: TokenData = Depends(get_current_doctor)
):
    """Download patient's PDF report (doctors only)"""
    try:
        patient = db_manager.patients.find_one({"_id": ObjectId(patient_id)})
    except:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid patient ID"
        )
    
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found"
        )
    
    decrypted_data = {
        "demographic": db_manager.decrypt_dict(patient["demographic"]),
        "per_symptom": db_manager.decrypt_dict(patient["per_symptom"]),
        "Gen_questions": db_manager.decrypt_dict(patient.get("Gen_questions", {}))
    }
    
    if "summary" in patient:
        try:
            decrypted_data["summary"] = db_manager.decrypt_data(patient["summary"])
        except:
            decrypted_data["summary"] = None
    
    pdf_buffer = generate_patient_pdf(decrypted_data)
    patient_name = decrypted_data["demographic"].get("name", "patient").replace(" ", "_")
    filename = f"{patient_name}_Health_Report.pdf"
    
    return Response(
        content=pdf_buffer.getvalue(),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@router.get("/", response_model=List[dict])
async def list_patients(
    search_name: Optional[str] = None,
    search_email: Optional[str] = None,
    token_data: TokenData = Depends(get_current_doctor)
):
    """List all patients with optional search (doctors only)"""
    patients_list = []
    
    for patient in db_manager.patients.find():
        try:
            decrypted_demo = db_manager.decrypt_dict(patient["demographic"])
            
            # Apply filters if provided
            if search_name and search_name.lower() not in decrypted_demo.get("name", "").lower():
                continue
            if search_email and search_email.lower() not in decrypted_demo.get("email", "").lower():
                continue
            
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