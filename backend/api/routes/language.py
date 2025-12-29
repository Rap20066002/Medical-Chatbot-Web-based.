"""
Language detection and translation routes
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

router = APIRouter()

LANGUAGES = {
    "en": "English", "es": "Spanish", "fr": "French",
    "de": "German", "it": "Italian", "pt": "Portuguese",
    "ru": "Russian", "ja": "Japanese", "zh-cn": "Chinese",
    "ko": "Korean", "ar": "Arabic", "hi": "Hindi"
}

class LanguageDetectRequest(BaseModel):
    text: str

class TranslateRequest(BaseModel):
    text: str
    source: Optional[str] = "auto"
    target: str = "en"

@router.post("/detect")
async def detect_language(request: LanguageDetectRequest):
    """Detect language from text (min 10 chars)"""
    text = request.text.strip()
    
    if len(text) < 10:
        return {
            "detected": "en",
            "language_name": "English",
            "confidence": "low"
        }
    
    try:
        from langdetect import detect, DetectorFactory
        DetectorFactory.seed = 0
        
        detected = detect(text)
        return {
            "detected": detected,
            "language_name": LANGUAGES.get(detected, detected),
            "confidence": "high"
        }
    except:
        return {"detected": "en", "language_name": "English", "confidence": "low"}

@router.post("/translate")
async def translate_text(request: TranslateRequest):
    """Translate text"""
    try:
        from deep_translator import GoogleTranslator
        
        translated = GoogleTranslator(
            source=request.source,
            target=request.target
        ).translate(request.text)
        
        return {
            "translated": translated,
            "source": request.source,
            "target": request.target
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/supported")
async def get_supported_languages():
    """List supported languages"""
    return {"languages": [{"code": k, "name": v} for k, v in LANGUAGES.items()]}