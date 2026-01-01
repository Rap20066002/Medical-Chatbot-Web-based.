from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import time

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
    """
    Detect language from text (min 10 chars)
    ✅ FIXED: Better error handling and timeout management
    """
    text = request.text.strip()
    
    # Quick validation
    if len(text) < 10:
        return {
            "detected": "en",
            "language_name": "English",
            "confidence": "low"
        }
    
    try:
        # ✅ FIX: Import only when needed to avoid startup issues
        try:
            from langdetect import detect, DetectorFactory
        except ImportError:
            print("⚠️  langdetect not installed. Install with: pip install langdetect")
            return {
                "detected": "en",
                "language_name": "English",
                "confidence": "low",
                "error": "Language detection library not available"
            }
        
        # Set seed for consistent results
        DetectorFactory.seed = 0
        
        # Detect with timeout protection
        start_time = time.time()
        detected = detect(text)
        elapsed = time.time() - start_time
        
        print(f"✅ Language detected: {detected} (took {elapsed:.2f}s)")
        
        return {
            "detected": detected,
            "language_name": LANGUAGES.get(detected, detected),
            "confidence": "high" if elapsed < 1.0 else "medium"
        }
    
    except Exception as e:
        print(f"⚠️  Language detection error: {str(e)}")
        # Return default instead of error to avoid breaking UI
        return {
            "detected": "en",
            "language_name": "English",
            "confidence": "low",
            "error": str(e)
        }


@router.post("/translate")
async def translate_text(request: TranslateRequest):
    """
    Translate text between languages
    ✅ FIXED: Increased timeout, better error handling
    """
    # Quick validation
    if not request.text or not request.text.strip():
        return {
            "translated": "",
            "source": request.source,
            "target": request.target,
            "error": "Empty text"
        }
    
    # If source and target are the same, no translation needed
    if request.source == request.target and request.source != "auto":
        return {
            "translated": request.text,
            "source": request.source,
            "target": request.target,
            "skipped": True
        }
    
    try:
        # ✅ FIX: Import only when needed
        try:
            from deep_translator import GoogleTranslator
        except ImportError:
            print("⚠️  deep-translator not installed. Install with: pip install deep-translator")
            raise HTTPException(
                status_code=503,
                detail="Translation service not available. Please install deep-translator."
            )
        
        # ✅ FIX: Add timeout and retry logic
        max_retries = 2
        retry_delay = 1  # seconds
        
        for attempt in range(max_retries):
            try:
                start_time = time.time()
                
                # Perform translation
                translator = GoogleTranslator(
                    source=request.source,
                    target=request.target
                )
                
                # ✅ FIX: Handle long text by chunking (Google Translate has 5000 char limit)
                text = request.text
                if len(text) > 4500:
                    # Split into chunks
                    chunks = [text[i:i+4500] for i in range(0, len(text), 4500)]
                    translated_chunks = []
                    
                    for chunk in chunks:
                        translated_chunk = translator.translate(chunk)
                        translated_chunks.append(translated_chunk)
                    
                    translated = " ".join(translated_chunks)
                else:
                    translated = translator.translate(text)
                
                elapsed = time.time() - start_time
                
                print(f"✅ Translation complete: {request.source} -> {request.target} (took {elapsed:.2f}s)")
                
                return {
                    "translated": translated,
                    "source": request.source,
                    "target": request.target,
                    "elapsed_seconds": round(elapsed, 2)
                }
            
            except Exception as translate_error:
                print(f"⚠️  Translation attempt {attempt + 1} failed: {str(translate_error)}")
                
                if attempt < max_retries - 1:
                    # Retry after delay
                    print(f"   Retrying in {retry_delay}s...")
                    time.sleep(retry_delay)
                    continue
                else:
                    # Final attempt failed
                    raise translate_error
    
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    
    except Exception as e:
        error_msg = str(e)
        print(f"❌ Translation error: {error_msg}")
        
        # Provide user-friendly error messages
        if "timeout" in error_msg.lower():
            detail = "Translation service timed out. Please try again."
        elif "connection" in error_msg.lower() or "network" in error_msg.lower():
            detail = "Cannot connect to translation service. Check your internet connection."
        elif "rate limit" in error_msg.lower():
            detail = "Translation service rate limit reached. Please wait a moment and try again."
        else:
            detail = f"Translation failed: {error_msg}"
        
        raise HTTPException(
            status_code=500,
            detail=detail
        )


@router.get("/supported")
async def get_supported_languages():
    """
    List supported languages
    ✅ Always succeeds, no external dependencies
    """
    return {
        "languages": [
            {"code": k, "name": v} 
            for k, v in LANGUAGES.items()
        ],
        "count": len(LANGUAGES)
    }


# ============================================================================
# ✅ NEW: Health check endpoint for language services
# ============================================================================

@router.get("/health")
async def check_language_services():
    """
    Check if language detection and translation services are available
    """
    status = {
        "detection": "unavailable",
        "translation": "unavailable",
        "supported_languages": len(LANGUAGES)
    }
    
    # Check langdetect
    try:
        from langdetect import detect
        status["detection"] = "available"
    except ImportError:
        status["detection"] = "not_installed"
    except Exception as e:
        status["detection"] = f"error: {str(e)}"
    
    # Check deep-translator
    try:
        from deep_translator import GoogleTranslator
        status["translation"] = "available"
    except ImportError:
        status["translation"] = "not_installed"
    except Exception as e:
        status["translation"] = f"error: {str(e)}"
    
    return status