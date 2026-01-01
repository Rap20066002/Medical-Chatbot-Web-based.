"""
Authentication Routes - FIXED VERSION
Login and registration endpoints with better error handling
"""

from fastapi import APIRouter, HTTPException, status
from datetime import timedelta
import traceback

from models.patient import PatientLogin, Token, PatientCreate
from api.middleware.auth import (
    create_access_token,
    hash_password,
    verify_password
)
from core.database import db_manager
from core.config import settings
from core.llm import llm_manager

router = APIRouter()

@router.post("/patient/register", response_model=Token)
async def register_patient(patient_data: PatientCreate):
    """
    FIXED: Register patient immediately, generate summary in background
    No timeout issues!
    """
    try:
        print(f"📝 Registration attempt for: {patient_data.demographic.email}")
        
        # Check if patient already exists
        for patient in db_manager.patients.find():
            try:
                decrypted_demo = db_manager.decrypt_dict(patient.get("demographic", {}))
                if decrypted_demo.get("email", "").lower() == patient_data.demographic.email.lower():
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Patient with this email already exists"
                    )
            except Exception as e:
                continue
        
        # Hash password
        hashed_password = hash_password(patient_data.password)
        print("✅ Password hashed")
        
        # Convert per_symptom to dict
        per_symptom_dict = {}
        for symptom_name, symptom_detail in patient_data.per_symptom.items():
            per_symptom_dict[symptom_name] = {
                "Duration": symptom_detail.Duration or "",
                "Severity": symptom_detail.Severity or "",
                "Frequency": symptom_detail.Frequency or "",
                "Factors": symptom_detail.Factors or "",
                "Additional Notes": symptom_detail.additional_notes or ""
            }
        
        print("✅ Symptom data converted")
        
        # ⚡ CRITICAL: Save patient IMMEDIATELY without summary
        encrypted_data = {
            "demographic": db_manager.encrypt_dict(patient_data.demographic.dict()),
            "per_symptom": db_manager.encrypt_dict(per_symptom_dict),
            "Gen_questions": db_manager.encrypt_dict(patient_data.gen_questions),
            "password": hashed_password,
            "created_at": __import__('time').time(),
            "summary_status": "generating"  # Track summary status
        }
        
        print("✅ Data encrypted")
        
        # Save to database FIRST (fast operation)
        result = db_manager.patients.insert_one(encrypted_data)
        print(f"✅ Patient saved with ID: {result.inserted_id}")
        
        # Create access token immediately
        access_token = create_access_token(
            data={
                "sub": patient_data.demographic.email,
                "user_type": "patient"
            },
            expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        
        print("✅ Token created - User can login now!")
        
        # ============================================================
        # 🔧 FIX: Smart summary generation based on LLM availability
        # ============================================================
        if settings.USE_LLM and llm_manager.is_available():
            # LLM MODE: Generate in background (takes 5-10 minutes)
            print("🤖 LLM Mode: Starting background summary generation")
            
            import threading
            
            def generate_summary_background():
                """Background thread to generate summary"""
                try:
                    print(f"🤖 [BACKGROUND] Starting summary generation for {result.inserted_id}")
                    
                    patient_dict_for_summary = {
                        "demographic": patient_data.demographic.dict(),
                        "per_symptom": per_symptom_dict,
                        "Gen_questions": patient_data.gen_questions
                    }
                    
                    # This takes 5-7 minutes with LLM
                    summary = llm_manager.summarize_patient_condition(patient_dict_for_summary)
                    
                    if summary:
                        db_manager.patients.update_one(
                            {"_id": result.inserted_id},
                            {
                                "$set": {
                                    "summary": db_manager.encrypt_data(summary),
                                    "summary_status": "completed",
                                    "summary_generated_at": __import__('time').time()
                                }
                            }
                        )
                        print(f"✅ [BACKGROUND] Summary completed for {result.inserted_id}")
                    else:
                        db_manager.patients.update_one(
                            {"_id": result.inserted_id},
                            {"$set": {"summary_status": "failed"}}
                        )
                        print(f"⚠️ [BACKGROUND] Summary generation failed for {result.inserted_id}")
                        
                except Exception as e:
                    print(f"❌ [BACKGROUND] Error generating summary: {str(e)}")
                    db_manager.patients.update_one(
                        {"_id": result.inserted_id},
                        {"$set": {"summary_status": "failed"}}
                    )
            
            # Start background thread
            summary_thread = threading.Thread(target=generate_summary_background, daemon=True)
            summary_thread.start()
            print("✅ Summary generation started in background thread")
        
        else:
            # NON-LLM MODE: Generate template summary immediately (instant)
            print("📝 Non-LLM Mode: Generating template summary instantly")
            
            try:
                patient_dict_for_summary = {
                    "demographic": patient_data.demographic.dict(),
                    "per_symptom": per_symptom_dict,
                    "Gen_questions": patient_data.gen_questions
                }
                
                # Template summary (instant, no LLM needed)
                template_summary = llm_manager.summarize_patient_condition(patient_dict_for_summary)
                
                # Update immediately (no background thread needed)
                db_manager.patients.update_one(
                    {"_id": result.inserted_id},
                    {
                        "$set": {
                            "summary": db_manager.encrypt_data(template_summary),
                            "summary_status": "completed",
                            "summary_generated_at": __import__('time').time()
                        }
                    }
                )
                print(f"✅ Template summary created instantly for {result.inserted_id}")
            
            except Exception as e:
                print(f"❌ Template summary generation error: {str(e)}")
                db_manager.patients.update_one(
                    {"_id": result.inserted_id},
                    {"$set": {"summary_status": "failed"}}
                )
        
        # Return immediately - user gets logged in!
        return Token(
            access_token=access_token,
            user_type="patient",
            user_id=str(result.inserted_id),
            token_type="bearer"
        )
    
    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"❌ Registration error: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )

@router.post("/patient/login", response_model=Token)
async def login_patient(credentials: PatientLogin):
    """Patient login"""
    try:
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
            user_id=str(found_patient["_id"]),
            token_type="bearer"
        )
    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"❌ Login error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}"
        )

@router.post("/doctor/login", response_model=Token)
async def login_doctor(credentials: PatientLogin):
    """Doctor login"""
    try:
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
            user_id=str(doctor["_id"]),
            token_type="bearer"
        )
    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"❌ Doctor login error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}"
        )

@router.post("/admin/login", response_model=Token)
async def login_admin(credentials: PatientLogin):
    """Admin login"""
    try:
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
            user_id=str(admin["_id"]),
            token_type="bearer"
        )
    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"❌ Admin login error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}"
        )