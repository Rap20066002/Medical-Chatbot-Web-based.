"""
Authentication Routes - IMPROVED VERSION
✅ Better duplicate email handling
✅ Database-level uniqueness for doctors/admins
✅ Application-level uniqueness for patients (encrypted emails)
"""

from fastapi import APIRouter, HTTPException, status
from datetime import timedelta
import traceback
from pymongo.errors import DuplicateKeyError

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
    Patient registration with improved duplicate email handling
    ✅ Checks all existing patients (encrypted emails)
    ✅ Case-insensitive email comparison
    ✅ Immediate registration without timeout
    """
    try:
        print(f"📝 Registration attempt for: {patient_data.demographic.email}")
        
        # ============================================================
        # ✅ IMPROVED: Check for duplicate email (case-insensitive)
        # ============================================================
        target_email = patient_data.demographic.email.lower().strip()
        
        for patient in db_manager.patients.find():
            try:
                decrypted_demo = db_manager.decrypt_dict(patient.get("demographic", {}))
                existing_email = decrypted_demo.get("email", "").lower().strip()
                
                if existing_email == target_email:
                    print(f"❌ Duplicate email found: {target_email}")
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Email '{patient_data.demographic.email}' is already registered. Please use a different email or try logging in."
                    )
            except HTTPException:
                raise  # Re-raise HTTP exceptions
            except Exception:
                continue  # Skip patients with decryption errors
        
        print(f"✅ Email is unique: {target_email}")
        
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
        
        # Save patient IMMEDIATELY without summary
        encrypted_data = {
            "demographic": db_manager.encrypt_dict(patient_data.demographic.dict()),
            "per_symptom": db_manager.encrypt_dict(per_symptom_dict),
            "Gen_questions": db_manager.encrypt_dict(patient_data.gen_questions),
            "password": hashed_password,
            "created_at": __import__('time').time(),
            "summary_status": "generating"
        }
        
        print("✅ Data encrypted")
        
        # Save to database
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
        
        # Generate summary in background
        if settings.USE_LLM and llm_manager.is_available():
            print("🤖 LLM Mode: Starting background summary generation")
            
            import threading
            
            def generate_summary_background():
                try:
                    print(f"🤖 [BACKGROUND] Starting summary for {result.inserted_id}")
                    
                    patient_dict_for_summary = {
                        "demographic": patient_data.demographic.dict(),
                        "per_symptom": per_symptom_dict,
                        "Gen_questions": patient_data.gen_questions
                    }
                    
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
                        print(f"⚠️ [BACKGROUND] Summary generation failed")
                        
                except Exception as e:
                    print(f"❌ [BACKGROUND] Error: {str(e)}")
                    db_manager.patients.update_one(
                        {"_id": result.inserted_id},
                        {"$set": {"summary_status": "failed"}}
                    )
            
            summary_thread = threading.Thread(target=generate_summary_background, daemon=True)
            summary_thread.start()
            print("✅ Summary generation started in background")
        
        else:
            print("📝 Non-LLM Mode: Generating template summary instantly")
            
            try:
                patient_dict_for_summary = {
                    "demographic": patient_data.demographic.dict(),
                    "per_symptom": per_symptom_dict,
                    "Gen_questions": patient_data.gen_questions
                }
                
                template_summary = llm_manager.summarize_patient_condition(patient_dict_for_summary)
                
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
                print(f"✅ Template summary created instantly")
            
            except Exception as e:
                print(f"❌ Template summary error: {str(e)}")
                db_manager.patients.update_one(
                    {"_id": result.inserted_id},
                    {"$set": {"summary_status": "failed"}}
                )
        
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
    """Patient login with improved email handling"""
    try:
        target_email = credentials.email.lower().strip()
        
        # Find patient by email
        found_patient = None
        for patient in db_manager.patients.find():
            try:
                decrypted_demo = db_manager.decrypt_dict(patient.get("demographic", {}))
                existing_email = decrypted_demo.get("email", "").lower().strip()
                
                if existing_email == target_email:
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
    """
    Doctor login
    ✅ Database-level unique constraint prevents duplicate emails
    """
    try:
        target_email = credentials.email.lower().strip()
        doctor = db_manager.doctors.find_one({"email": target_email})
        
        if not doctor:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Check if approved
        if doctor.get("status") != "approved":
            status_msg = doctor.get("status", "pending")
            
            if status_msg == "pending":
                detail = "Your account is pending admin approval. Please wait for approval before logging in."
            elif status_msg == "rejected":
                detail = "Your account has been rejected. Please contact administration."
            elif status_msg == "disabled":
                detail = "Your account has been disabled. Please contact administration."
            else:
                detail = f"Your account status is: {status_msg}"
            
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=detail
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
    """
    Admin login
    ✅ Database-level unique constraint prevents duplicate emails
    """
    try:
        target_email = credentials.email.lower().strip()
        admin = db_manager.admins.find_one({"email": target_email})
        
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