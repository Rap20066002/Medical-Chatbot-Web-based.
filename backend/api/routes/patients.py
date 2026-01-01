"""
Patient Routes - FIXED CLINICAL INSIGHTS
Clinical insights now generate in background (no timeout!)
"""

from fastapi import APIRouter, HTTPException, Depends, status, Response
from typing import List, Dict, Optional
from bson import ObjectId
from pydantic import BaseModel, Field, field_validator
import threading
import time
from urllib.parse import quote
import re

from models.patient import (
    PatientResponse,
    SymptomAnalysisRequest,
    SymptomAnalysisResponse,
    TokenData,
    PatientDemographic,
    SymptomDetail,
    PatientUpdate
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


def sanitize_filename_ascii(filename: str) -> str:
    """
    Convert Unicode filename to safe ASCII version
    
    Examples:
        "अवनि" -> "Patient"
        "نامان" -> "Patient"
        "José García" -> "Jose_Garcia"
        "李明" -> "Patient"
    """
    # Try to transliterate common characters
    transliterations = {
        'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u',
        'à': 'a', 'è': 'e', 'ì': 'i', 'ò': 'o', 'ù': 'u',
        'ä': 'a', 'ë': 'e', 'ï': 'i', 'ö': 'o', 'ü': 'u',
        'â': 'a', 'ê': 'e', 'î': 'i', 'ô': 'o', 'û': 'u',
        'ñ': 'n', 'ç': 'c', 'ß': 'ss',
        ' ': '_', '-': '_'
    }
    
    # Apply transliterations
    result = filename.lower()
    for char, replacement in transliterations.items():
        result = result.replace(char, replacement)
    
    # Keep only ASCII alphanumeric and underscores
    result = re.sub(r'[^a-z0-9_]', '', result)
    
    # If nothing remains (e.g., all Hindi/Arabic/Chinese), use generic name
    if not result or len(result) < 2:
        result = "Patient"
    
    # Capitalize first letter
    result = result.capitalize()
    
    # Limit length
    if len(result) > 50:
        result = result[:50]
    
    return result

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
        "created_at": found_patient.get("created_at"),
        # ✅ ADD THESE LINES
        "summary_status": found_patient.get("summary_status", "unknown"),
        "summary_generated_at": found_patient.get("summary_generated_at")
    }
    
    if "summary" in found_patient:
        try:
            decrypted_data["summary"] = db_manager.decrypt_data(found_patient["summary"])
        except:
            decrypted_data["summary"] = None
    
    return PatientResponse(**decrypted_data)

@router.post("/me/regenerate-summary")
async def regenerate_summary(token_data: TokenData = Depends(get_current_patient)):
    """Regenerate clinical summary for current patient"""
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
    
    # Mark as generating again
    db_manager.patients.update_one(
        {"_id": found_patient["_id"]},
        {"$set": {"summary_status": "generating"}}
    )
    
    # Start background generation
    import threading
    
    def regenerate_background():
        try:
            patient_data = {
                "demographic": db_manager.decrypt_dict(found_patient["demographic"]),
                "per_symptom": db_manager.decrypt_dict(found_patient["per_symptom"]),
                "Gen_questions": db_manager.decrypt_dict(found_patient.get("Gen_questions", {}))
            }
            
            summary = llm_manager.summarize_patient_condition(patient_data)
            
            if summary:
                db_manager.patients.update_one(
                    {"_id": found_patient["_id"]},
                    {
                        "$set": {
                            "summary": db_manager.encrypt_data(summary),
                            "summary_status": "completed",
                            "summary_generated_at": time.time()
                        }
                    }
                )
            else:
                db_manager.patients.update_one(
                    {"_id": found_patient["_id"]},
                    {"$set": {"summary_status": "failed"}}
                )
        except Exception as e:
            print(f"Regeneration error: {e}")
            db_manager.patients.update_one(
                {"_id": found_patient["_id"]},
                {"$set": {"summary_status": "failed"}}
            )
    
    thread = threading.Thread(target=regenerate_background, daemon=True)
    thread.start()
    
    return {"message": "Summary regeneration started"}

@router.get("/me/pdf")
async def download_my_pdf(token_data: TokenData = Depends(get_current_patient)):
    """Download patient's health report as PDF - FIXED for Unicode names"""
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
    
    # Generate PDF
    pdf_buffer = generate_patient_pdf(decrypted_data)
    
    # ✅ FIX: Handle Unicode characters in filename
    patient_name = decrypted_data["demographic"].get("name", "patient")
    
    # Create safe ASCII filename (fallback)
    safe_filename = sanitize_filename_ascii(patient_name)
    
    # Create RFC 5987 encoded filename (supports Unicode)
    unicode_filename = f"{patient_name}_Health_Report.pdf"
    encoded_filename = quote(unicode_filename.encode('utf-8'))
    
    # Use Content-Disposition with both ASCII and UTF-8 filenames
    # Modern browsers will use the UTF-8 version, older ones use ASCII
    headers = {
        "Content-Disposition": (
            f"attachment; "
            f"filename=\"{safe_filename}_Health_Report.pdf\"; "
            f"filename*=UTF-8''{encoded_filename}"
        )
    }
    
    return Response(
        content=pdf_buffer.getvalue(),
        media_type="application/pdf",
        headers=headers
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

@router.put("/me")
async def update_patient(
    update_data: PatientUpdate,
    token_data: TokenData = Depends(get_current_patient)
):
    """Update patient's complete information"""
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
    
    update_dict = {}
    
    if update_data.demographic:
        update_dict["demographic"] = db_manager.encrypt_dict(update_data.demographic.dict())
    
    if update_data.per_symptom:
        per_symptom_dict = {}
        for symptom_name, symptom_detail in update_data.per_symptom.items():
            if isinstance(symptom_detail, SymptomDetail):
                per_symptom_dict[symptom_name] = {
                    "Duration": symptom_detail.Duration or "",
                    "Severity": symptom_detail.Severity or "",
                    "Frequency": symptom_detail.Frequency or "",
                    "Factors": symptom_detail.Factors or "",
                    "Additional Notes": symptom_detail.additional_notes or ""
                }
            else:
                per_symptom_dict[symptom_name] = symptom_detail
        
        update_dict["per_symptom"] = db_manager.encrypt_dict(per_symptom_dict)
    
    if update_data.gen_questions:
        update_dict["Gen_questions"] = db_manager.encrypt_dict(update_data.gen_questions)
    
    if update_data.per_symptom or update_data.gen_questions:
        current_data = {
            "demographic": db_manager.decrypt_dict(
                update_dict.get("demographic", found_patient["demographic"])
            ),
            "per_symptom": db_manager.decrypt_dict(
                update_dict.get("per_symptom", found_patient["per_symptom"])
            ),
            "Gen_questions": db_manager.decrypt_dict(
                update_dict.get("Gen_questions", found_patient.get("Gen_questions", {}))
            )
        }
        
        new_summary = llm_manager.summarize_patient_condition(current_data)
        if new_summary:
            update_dict["summary"] = db_manager.encrypt_data(new_summary)
    
    if update_dict:
        db_manager.patients.update_one(
            {"_id": found_patient["_id"]},
            {"$set": update_dict}
        )
    
    return {"message": "Patient information updated successfully"}

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
    
    if not verify_password(password_data.current_password, found_patient.get("password", "")):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Current password is incorrect"
        )
    
    db_manager.patients.update_one(
        {"_id": found_patient["_id"]},
        {"$set": {"password": hash_password(password_data.new_password)}}
    )
    
    return {"message": "Password changed successfully"}

@router.post("/analyze-symptoms", response_model=SymptomAnalysisResponse)
async def analyze_symptoms(request: SymptomAnalysisRequest):
    """
    FIXED: Analyze symptoms with COMPLETE LLM integration
    - Detects symptoms
    - Extracts ALL details (duration, severity, frequency, factors)
    - Generates intelligent follow-up questions
    """
    print(f"\n🔍 ANALYZING SYMPTOMS: {request.description}")
    
    # STEP 1: Identify symptoms using LLM
    symptoms = llm_manager.identify_symptoms(request.description)
    print(f"✅ Identified symptoms: {symptoms}")
    
    # STEP 2: Extract details for EACH symptom using LLM
    extracted_details = llm_manager.extract_symptom_details(request.description)
    print(f"✅ Extracted details: {extracted_details}")
    
    # STEP 3: Generate intelligent follow-up questions
    questions = []
    if symptoms:
        # Generate questions for the primary symptom
        questions = llm_manager.generate_questions(symptoms[0], extracted_details)
        print(f"✅ Generated {len(questions)} follow-up questions")
    
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
    """Download patient's PDF report (doctors only) - FIXED for Unicode names"""
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
    
    # Generate PDF
    pdf_buffer = generate_patient_pdf(decrypted_data)
    
    # ✅ FIX: Handle Unicode characters in filename
    patient_name = decrypted_data["demographic"].get("name", "patient")
    
    # Create safe ASCII filename (fallback)
    safe_filename = sanitize_filename_ascii(patient_name)
    
    # Create RFC 5987 encoded filename (supports Unicode)
    unicode_filename = f"{patient_name}_Health_Report.pdf"
    encoded_filename = quote(unicode_filename.encode('utf-8'))
    
    # Use Content-Disposition with both ASCII and UTF-8 filenames
    headers = {
        "Content-Disposition": (
            f"attachment; "
            f"filename=\"{safe_filename}_Health_Report.pdf\"; "
            f"filename*=UTF-8''{encoded_filename}"
        )
    }
    
    return Response(
        content=pdf_buffer.getvalue(),
        media_type="application/pdf",
        headers=headers
    )

# ============================================================================
# 🚀 FIXED: CLINICAL INSIGHTS - NOW GENERATES IN BACKGROUND (NO TIMEOUT!)
# ============================================================================

@router.post("/{patient_id}/clinical-insights")
async def request_clinical_insights(
    patient_id: str,
    token_data: TokenData = Depends(get_current_doctor)
):
    """
    ⚡ FIXED: Request clinical insights generation (immediate response)
    Insights generate in background, doctor can check status
    """
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
    
    # Check if insights already exist and are recent (< 1 hour)
    if "clinical_insights" in patient:
        insights_time = patient.get("insights_generated_at", 0)
        current_time = time.time()
        
        # If insights exist and are less than 1 hour old, return them
        if (current_time - insights_time) < 3600:
            try:
                existing_insights = db_manager.decrypt_data(patient["clinical_insights"])
                return {
                    "status": "completed",
                    "insights": existing_insights,
                    "generated_at": insights_time,
                    "message": "Using cached insights (generated < 1 hour ago)"
                }
            except:
                pass
    
    # Mark insights as generating
    db_manager.patients.update_one(
        {"_id": ObjectId(patient_id)},
        {
            "$set": {
                "insights_status": "generating",
                "insights_requested_at": time.time(),
                "insights_requested_by": token_data.email
            }
        }
    )
    
    print(f"🧠 Starting clinical insights generation for patient {patient_id}")
    
    # 🚀 Generate insights in BACKGROUND thread
    def generate_insights_background():
        """Background thread to generate clinical insights"""
        try:
            print(f"🤖 [BACKGROUND] Generating insights for {patient_id}")
            
            # Decrypt patient data
            patient_data = {
                "demographic": db_manager.decrypt_dict(patient["demographic"]),
                "per_symptom": db_manager.decrypt_dict(patient["per_symptom"]),
                "Gen_questions": db_manager.decrypt_dict(patient.get("Gen_questions", {}))
            }
            
            # Generate insights (this takes 5-7 minutes with LLM)
            insights = llm_manager.get_clinical_insights(patient_data)
            
            if insights:
                # Update patient with insights when ready
                db_manager.patients.update_one(
                    {"_id": ObjectId(patient_id)},
                    {
                        "$set": {
                            "clinical_insights": db_manager.encrypt_data(insights),
                            "insights_status": "completed",
                            "insights_generated_at": time.time()
                        }
                    }
                )
                print(f"✅ [BACKGROUND] Insights completed for {patient_id}")
            else:
                db_manager.patients.update_one(
                    {"_id": ObjectId(patient_id)},
                    {"$set": {"insights_status": "failed"}}
                )
                print(f"⚠️ [BACKGROUND] Insights generation failed for {patient_id}")
                
        except Exception as e:
            print(f"❌ [BACKGROUND] Error generating insights: {str(e)}")
            db_manager.patients.update_one(
                {"_id": ObjectId(patient_id)},
                {"$set": {"insights_status": "failed"}}
            )
    
    # Start background thread (daemon=True means it won't block shutdown)
    insights_thread = threading.Thread(target=generate_insights_background, daemon=True)
    insights_thread.start()
    print("✅ Insights generation started in background thread")
    
    # Return immediately - doctor gets instant response!
    return {
        "status": "generating",
        "message": "Clinical insights are being generated in the background",
        "patient_id": patient_id,
        "estimated_time": "5-7 minutes",
        "tip": "You can close this and check back later - refresh to see results"
    }


@router.get("/{patient_id}/clinical-insights")
async def get_clinical_insights(
    patient_id: str,
    token_data: TokenData = Depends(get_current_doctor)
):
    """
    ✅ Check status and get clinical insights when ready
    """
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
    
    # Check insights status
    insights_status = patient.get("insights_status", "not_requested")
    
    if insights_status == "generating":
        # Still generating
        requested_at = patient.get("insights_requested_at", time.time())
        elapsed = int(time.time() - requested_at)
        
        return {
            "status": "generating",
            "message": f"Insights are being generated... ({elapsed}s elapsed)",
            "patient_id": patient_id,
            "elapsed_seconds": elapsed,
            "estimated_remaining": max(0, 420 - elapsed)  # 7 minutes = 420 seconds
        }
    
    elif insights_status == "completed":
        # Insights ready!
        try:
            insights = db_manager.decrypt_data(patient["clinical_insights"])
            generated_at = patient.get("insights_generated_at")
            
            return {
                "status": "completed",
                "insights": insights,
                "generated_at": generated_at,
                "patient_id": patient_id
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error decrypting insights: {str(e)}"
            )
    
    elif insights_status == "failed":
        return {
            "status": "failed",
            "message": "Clinical insights generation failed. Please try again.",
            "patient_id": patient_id
        }
    
    else:
        # Not requested yet
        return {
            "status": "not_requested",
            "message": "Clinical insights have not been requested yet",
            "patient_id": patient_id
        }


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