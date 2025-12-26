"""
Patient Routes
CRUD operations for patient data
"""

from fastapi import APIRouter, HTTPException, Depends, status
from typing import List
from bson import ObjectId

from models.patient import (
    PatientResponse,
    PatientUpdate,
    SymptomAnalysisRequest,
    SymptomAnalysisResponse,
    ChatRequest,
    ChatResponse,
    TokenData
)
from api.middleware.auth import get_current_patient, get_current_doctor
from core.database import db_manager
from core.llm import llm_manager

router = APIRouter()

@router.get("/me", response_model=PatientResponse)
async def get_my_profile(token_data: TokenData = Depends(get_current_patient)):
    """Get current patient's profile"""
    # Find patient by email
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
    
    # Decrypt data
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

@router.put("/me", response_model=PatientResponse)
async def update_my_profile(
    update_data: PatientUpdate,
    token_data: TokenData = Depends(get_current_patient)
):
    """Update current patient's profile"""
    # Find patient
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
    
    # Prepare update
    update_dict = {}
    
    if update_data.demographic:
        update_dict["demographic"] = db_manager.encrypt_dict(update_data.demographic.dict())
    
    if update_data.per_symptom:
        update_dict["per_symptom"] = db_manager.encrypt_dict(update_data.per_symptom)
    
    if update_data.gen_questions:
        update_dict["Gen_questions"] = db_manager.encrypt_dict(update_data.gen_questions)
    
    # Update in database
    db_manager.patients.update_one(
        {"_id": found_patient["_id"]},
        {"$set": update_dict}
    )
    
    # Return updated profile
    return await get_my_profile(token_data)

@router.post("/analyze-symptoms", response_model=SymptomAnalysisResponse)
async def analyze_symptoms(
    request: SymptomAnalysisRequest,
    token_data: TokenData = Depends(get_current_patient)
):
    """Analyze patient's symptom description and generate follow-up questions"""
    # Identify symptoms
    symptoms = llm_manager.identify_symptoms(request.description)
    
    # Generate questions for first symptom
    questions = []
    if symptoms:
        questions = llm_manager.generate_questions(symptoms[0])
    
    return SymptomAnalysisResponse(
        symptoms=symptoms,
        questions=questions
    )

@router.post("/chat", response_model=ChatResponse)
async def chat_with_assistant(
    request: ChatRequest,
    token_data: TokenData = Depends(get_current_patient)
):
    """Chat with health assessment assistant"""
    # Build conversation context
    context = "\n".join([
        f"{msg.role}: {msg.content}"
        for msg in request.conversation_history
    ])
    
    full_prompt = f"{context}\nuser: {request.message}\nassistant:"
    
    # Get LLM response
    if llm_manager.is_available():
        response = llm_manager.get_response(full_prompt)
    else:
        response = "I'm here to help with your health assessment. Could you describe your symptoms in detail?"
    
    # Try to detect symptoms in message
    detected_symptoms = llm_manager.identify_symptoms(request.message)
    
    return ChatResponse(
        response=response,
        detected_symptoms=detected_symptoms if detected_symptoms else None
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
    
    # Decrypt data
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

@router.get("/", response_model=List[dict])
async def list_patients(
    token_data: TokenData = Depends(get_current_doctor)
):
    """List all patients (doctors only)"""
    patients_list = []
    
    for patient in db_manager.patients.find():
        try:
            decrypted_demo = db_manager.decrypt_dict(patient["demographic"])
            patients_list.append({
                "id": str(patient["_id"]),
                "name": decrypted_demo.get("name", "Unknown"),
                "age": decrypted_demo.get("age"),
                "email": decrypted_demo.get("email"),
                "created_at": patient.get("created_at")
            })
        except Exception as e:
            continue
    
    return patients_list