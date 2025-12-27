"""
Patient Routes - COMPLETE FIXED VERSION
With PDF generation, smart question skipping, and chat
"""

from fastapi import APIRouter, HTTPException, Depends, status, Response
from typing import List
from bson import ObjectId
from io import BytesIO

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
from utils.pdf_generator import generate_patient_pdf

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

@router.get("/me/pdf")
async def download_my_pdf(token_data: TokenData = Depends(get_current_patient)):
    """Download patient's health report as PDF"""
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
    
    # Decrypt all data
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
    
    # Generate PDF
    pdf_buffer = generate_patient_pdf(decrypted_data)
    
    # Create filename
    patient_name = decrypted_data["demographic"].get("name", "patient").replace(" ", "_")
    filename = f"{patient_name}_Health_Report.pdf"
    
    # Return PDF
    return Response(
        content=pdf_buffer.getvalue(),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )

@router.put("/me", response_model=PatientResponse)
async def update_my_profile(
    update_data: PatientUpdate,
    token_data: TokenData = Depends(get_current_patient)
):
    """Update current patient's profile and regenerate summary"""
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
    
    # Regenerate summary if data changed
    if update_data.per_symptom or update_data.gen_questions:
        # Get current decrypted data
        current_data = {
            "demographic": db_manager.decrypt_dict(found_patient["demographic"]),
            "per_symptom": update_data.per_symptom if update_data.per_symptom else db_manager.decrypt_dict(found_patient["per_symptom"]),
            "Gen_questions": update_data.gen_questions if update_data.gen_questions else db_manager.decrypt_dict(found_patient.get("Gen_questions", {}))
        }
        
        # Generate new summary
        new_summary = llm_manager.summarize_patient_condition(current_data)
        if new_summary:
            update_dict["summary"] = db_manager.encrypt_data(new_summary)
    
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
    """
    Analyze patient's symptom description and generate follow-up questions.
    Smart system: extracts duration, severity, frequency from description.
    """
    # Identify symptoms from description
    symptoms = llm_manager.identify_symptoms(request.description)
    
    # Extract details from the description
    extracted_details = llm_manager.extract_symptom_details(request.description)
    
    # Generate questions only for missing information
    questions = []
    if symptoms:
        questions = llm_manager.generate_questions(symptoms[0], extracted_details)
    
    return SymptomAnalysisResponse(
        symptoms=symptoms,
        questions=questions,
        extracted_info=extracted_details  # Send back what we extracted
    )

@router.post("/chat", response_model=ChatResponse)
async def chat_with_assistant(
    request: ChatRequest,
    token_data: TokenData = Depends(get_current_patient)
):
    """
    Chat with health assessment assistant.
    Provides helpful responses based on patient's questions.
    """
    # Find patient to get context
    found_patient = None
    for patient in db_manager.patients.find():
        try:
            decrypted_demo = db_manager.decrypt_dict(patient.get("demographic", {}))
            if decrypted_demo.get("email", "").lower() == token_data.email.lower():
                found_patient = patient
                break
        except:
            continue
    
    # Build response based on question
    message_lower = request.message.lower()
    
    # Health-related keywords
    if any(word in message_lower for word in ["symptom", "symptoms", "feeling", "pain", "sick"]):
        if found_patient:
            symptoms = list(db_manager.decrypt_dict(found_patient["per_symptom"]).keys())
            response = f"Based on your records, you reported: {', '.join(symptoms)}. "
            response += "If you're experiencing new symptoms or changes, please consult with a healthcare provider."
        else:
            response = "I can help you understand your symptoms. Please describe what you're experiencing."
    
    elif any(word in message_lower for word in ["medication", "medicine", "drug"]):
        response = "I can't provide medical advice or prescribe medications. Please consult with a healthcare professional for medication guidance."
    
    elif any(word in message_lower for word in ["report", "pdf", "download", "document"]):
        response = "You can download your health report from your dashboard. Look for the 'Download PDF Report' button."
    
    elif any(word in message_lower for word in ["doctor", "appointment", "visit"]):
        response = "To schedule an appointment or speak with a doctor, please contact your healthcare provider directly."
    
    elif any(word in message_lower for word in ["update", "change", "modify"]):
        response = "You can update your information from the 'Update Information' tab in your dashboard."
    
    elif any(word in message_lower for word in ["help", "how", "what can"]):
        response = "I can help you:\n"
        response += "• View your health records\n"
        response += "• Download your PDF report\n"
        response += "• Understand your symptoms\n"
        response += "• Update your information\n"
        response += "What would you like to know more about?"
    
    else:
        response = "I'm here to help with your health records. You can ask me about your symptoms, how to download your report, or how to update your information."
    
    # Try to detect symptoms in the message
    detected_symptoms = llm_manager.identify_symptoms(request.message)
    detected_symptoms = [s for s in detected_symptoms if s != "general health concern"]
    
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
    
    # Decrypt all data
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
    
    # Generate PDF
    pdf_buffer = generate_patient_pdf(decrypted_data)
    
    # Create filename
    patient_name = decrypted_data["demographic"].get("name", "patient").replace(" ", "_")
    filename = f"{patient_name}_Health_Report.pdf"
    
    # Return PDF
    return Response(
        content=pdf_buffer.getvalue(),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )

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