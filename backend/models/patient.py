"""
Pydantic models for API request/response validation
ENHANCED VERSION - Supports flexible symptom updates
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, List, Union, Any
from datetime import datetime

# Patient Models
class PatientDemographic(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    age: int = Field(..., ge=0, le=150)
    gender: str = Field(..., min_length=1)
    email: str
    phone: str = Field(..., min_length=10)
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v: str) -> str:
        """Validate email format"""
        if '@' not in v:
            raise ValueError('Email must contain @ symbol')
        parts = v.split('@')
        if len(parts) != 2 or not parts[0] or not parts[1]:
            raise ValueError('Invalid email format')
        return v.lower()

class SymptomDetail(BaseModel):
    Duration: Optional[str] = None
    Severity: Optional[str] = None
    Frequency: Optional[str] = None
    Factors: Optional[str] = None
    additional_notes: Optional[str] = Field(None, alias="Additional Notes")
    
    class Config:
        populate_by_name = True  # Allow both 'additional_notes' and 'Additional Notes'

class PatientCreate(BaseModel):
    demographic: PatientDemographic
    per_symptom: Dict[str, SymptomDetail]
    gen_questions: Dict[str, str] = Field(alias="Gen_questions")
    password: str = Field(..., min_length=6)
    summary: Optional[str] = None
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Ensure password meets requirements"""
        if len(v) < 6:
            raise ValueError('Password must be at least 6 characters long')
        return v

class PatientLogin(BaseModel):
    email: str
    password: str
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v: str) -> str:
        """Validate email format"""
        if '@' not in v:
            raise ValueError('Email must contain @ symbol')
        return v.lower()

class PatientResponse(BaseModel):
    id: str
    demographic: PatientDemographic
    per_symptom: Dict[str, SymptomDetail]
    gen_questions: Dict[str, str]
    summary: Optional[str] = None
    created_at: Optional[float] = None

# ENHANCED PatientUpdate - Supports flexible symptom format
class PatientUpdate(BaseModel):
    demographic: Optional[PatientDemographic] = None
    per_symptom: Optional[Dict[str, Union[SymptomDetail, Dict[str, Any]]]] = None
    gen_questions: Optional[Dict[str, str]] = None
    
    class Config:
        # Allow both Pydantic models and plain dicts for symptoms
        arbitrary_types_allowed = True

# Symptom Analysis
class SymptomAnalysisRequest(BaseModel):
    description: str = Field(..., min_length=10)

class SymptomAnalysisResponse(BaseModel):
    symptoms: List[str]
    questions: List[str]
    extracted_info: Optional[Dict[str, str]] = None

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
    user_type: str
    user_id: str

class TokenData(BaseModel):
    email: Optional[str] = None
    user_type: Optional[str] = None