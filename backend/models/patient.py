"""
Pydantic models for API request/response validation
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Dict, List
from datetime import datetime

# Patient Models
class PatientDemographic(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    age: int = Field(..., ge=0, le=150)
    gender: str = Field(..., min_length=1)
    email: EmailStr
    phone: str = Field(..., min_length=10)

class SymptomDetail(BaseModel):
    Duration: Optional[str] = None
    Severity: Optional[str] = None
    Frequency: Optional[str] = None
    Factors: Optional[str] = None
    additional_notes: Optional[str] = Field(None, alias="Additional Notes")

class PatientCreate(BaseModel):
    demographic: PatientDemographic
    per_symptom: Dict[str, SymptomDetail]
    gen_questions: Dict[str, str] = Field(alias="Gen_questions")
    password: str = Field(..., min_length=6)
    summary: Optional[str] = None

class PatientLogin(BaseModel):
    email: EmailStr
    password: str

class PatientResponse(BaseModel):
    id: str
    demographic: PatientDemographic
    per_symptom: Dict[str, SymptomDetail]
    gen_questions: Dict[str, str]
    summary: Optional[str] = None
    created_at: Optional[float] = None

class PatientUpdate(BaseModel):
    demographic: Optional[PatientDemographic] = None
    per_symptom: Optional[Dict[str, SymptomDetail]] = None
    gen_questions: Optional[Dict[str, str]] = None

# Symptom Analysis
class SymptomAnalysisRequest(BaseModel):
    description: str = Field(..., min_length=10)

class SymptomAnalysisResponse(BaseModel):
    symptoms: List[str]
    questions: List[str]

# Chat Models
class ChatMessage(BaseModel):
    role: str = Field(..., pattern="^(user|assistant|system)$")
    content: str

class ChatRequest(BaseModel):
    message: str
    conversation_history: Optional[List[ChatMessage]] = []
    language: Optional[str] = "en"

class ChatResponse(BaseModel):
    response: str
    detected_symptoms: Optional[List[str]] = None
    follow_up_questions: Optional[List[str]] = None

# Token Response
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_type: str  # "patient", "doctor", "admin"
    user_id: str

class TokenData(BaseModel):
    email: Optional[str] = None
    user_type: Optional[str] = None