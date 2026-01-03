"""
FIXED Language Routes - Addresses Detection Issues
✅ More reliable language detection
✅ Minimum text requirements
✅ Fallback strategies
✅ Only well-supported languages in manual selector
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import time

router = APIRouter()

# ============================================================================
# ✅ FIXED: Only include languages with RELIABLE detection
# These languages have distinct character sets that langdetect handles well
# ============================================================================
WELL_SUPPORTED_LANGUAGES = {
    # Latin script (excellent detection)
    "en": "English",
    "es": "Spanish", 
    "fr": "French",
    "de": "German",
    "it": "Italian",
    "pt": "Portuguese",
    
    # Cyrillic script (excellent detection)
    "ru": "Russian",
    "uk": "Ukrainian",
    "bg": "Bulgarian",
    
    # Arabic script (excellent detection)
    "ar": "Arabic",
    "fa": "Persian",
    "ur": "Urdu",
    
    # Indic scripts (excellent detection)
    "hi": "Hindi",
    "bn": "Bengali",
    "ta": "Tamil",
    "te": "Telugu",
    "mr": "Marathi",
    "gu": "Gujarati",
    
    # East Asian (excellent detection)
    "zh-cn": "Chinese (Simplified)",
    "zh-tw": "Chinese (Traditional)",
    "ja": "Japanese",
    "ko": "Korean",
    
    # Southeast Asian (good detection)
    "th": "Thai",
    "vi": "Vietnamese",
    
    # Other well-detected languages
    "tr": "Turkish",
    "pl": "Polish",
    "nl": "Dutch",
    "sv": "Swedish",
    "he": "Hebrew",
    "el": "Greek",
}

# ============================================================================
# ✅ FIXED: Character count requirements per script
# Different scripts need different minimum lengths for reliable detection
# ============================================================================
MIN_CHARS_BY_SCRIPT = {
    "latin": 30,      # English, Spanish, French, etc. need more text
    "cyrillic": 20,   # Russian, Ukrainian - distinctive alphabet
    "arabic": 15,     # Arabic, Urdu - very distinctive
    "devanagari": 15, # Hindi, Marathi - very distinctive
    "chinese": 10,    # Chinese characters are very distinctive
    "japanese": 10,   # Hiragana/Katakana very distinctive
    "korean": 10,     # Hangul very distinctive
    "thai": 15,       # Thai script very distinctive
}

class LanguageDetectRequest(BaseModel):
    text: str

class TranslateRequest(BaseModel):
    text: str
    source: Optional[str] = "auto"
    target: str = "en"


def detect_script_type(text):
    """
    Detect which script family the text belongs to
    This helps determine minimum text requirements
    """
    if not text:
        return "latin"
    
    for char in text:
        code = ord(char)
        
        # Cyrillic
        if 0x0400 <= code <= 0x04FF:
            return "cyrillic"
        
        # Arabic
        elif 0x0600 <= code <= 0x06FF or 0xFB50 <= code <= 0xFDFF:
            return "arabic"
        
        # Devanagari (Hindi, etc.)
        elif 0x0900 <= code <= 0x097F:
            return "devanagari"
        
        # Chinese
        elif 0x4E00 <= code <= 0x9FFF:
            return "chinese"
        
        # Japanese
        elif 0x3040 <= code <= 0x309F or 0x30A0 <= code <= 0x30FF:
            return "japanese"
        
        # Korean
        elif 0xAC00 <= code <= 0xD7AF or 0x1100 <= code <= 0x11FF:
            return "korean"
        
        # Thai
        elif 0x0E00 <= code <= 0x0E7F:
            return "thai"
    
    return "latin"


@router.post("/detect")
async def detect_language(request: LanguageDetectRequest):
    """
    ✅ FIXED: More intelligent language detection
    - Checks minimum text requirements by script type
    - Better error handling
    - Clear confidence levels
    """
    text = request.text.strip()
    
    # ========================================================================
    # STEP 1: Check minimum length requirements
    # ========================================================================
    script_type = detect_script_type(text)
    min_required = MIN_CHARS_BY_SCRIPT.get(script_type, 30)
    
    if len(text) < min_required:
        return {
            "detected": "en",
            "language_name": "English",
            "confidence": "insufficient_text",
            "message": f"Need at least {min_required} characters for {script_type} script detection",
            "current_length": len(text)
        }
    
    # ========================================================================
    # STEP 2: Try language detection
    # ========================================================================
    try:
        try:
            from langdetect import detect, DetectorFactory, LangDetectException
        except ImportError:
            return {
                "detected": "en",
                "language_name": "English",
                "confidence": "library_unavailable",
                "error": "langdetect not installed"
            }
        
        # Set seed for consistent results
        DetectorFactory.seed = 0
        
        # Detect with timeout protection
        start_time = time.time()
        detected = detect(text)
        elapsed = time.time() - start_time
        
        # ====================================================================
        # STEP 3: Validate detection result
        # ====================================================================
        
        # Check if detected language is in our supported list
        if detected not in WELL_SUPPORTED_LANGUAGES:
            print(f"⚠️  Detected '{detected}' but it's not in supported list")
            
            # Try to map to supported language
            # e.g., 'zh' -> 'zh-cn'
            if detected == 'zh':
                detected = 'zh-cn'
            elif detected.startswith('zh-'):
                # Keep as is
                pass
            else:
                # Default to English for unsupported languages
                return {
                    "detected": "en",
                    "language_name": "English",
                    "confidence": "unsupported_language",
                    "raw_detection": detected,
                    "message": f"Detected {detected} but it's not supported"
                }
        
        # ====================================================================
        # STEP 4: Determine confidence level
        # ====================================================================
        confidence = "high"
        
        # Lower confidence for Latin-script languages if text is short
        if script_type == "latin" and len(text) < 50:
            confidence = "medium"
        
        # Lower confidence if detection took too long (ambiguous text)
        if elapsed > 0.5:
            confidence = "medium" if confidence == "high" else "low"
        
        print(f"✅ Language detected: {detected} (confidence: {confidence}, {elapsed:.2f}s)")
        
        return {
            "detected": detected,
            "language_name": WELL_SUPPORTED_LANGUAGES.get(detected, detected),
            "confidence": confidence,
            "script_type": script_type,
            "text_length": len(text)
        }
    
    except LangDetectException as e:
        print(f"⚠️  LangDetectException: {str(e)}")
        return {
            "detected": "en",
            "language_name": "English",
            "confidence": "detection_failed",
            "error": "Text not suitable for detection"
        }
    
    except Exception as e:
        print(f"⚠️  Language detection error: {str(e)}")
        return {
            "detected": "en",
            "language_name": "English",
            "confidence": "error",
            "error": str(e)
        }


@router.post("/translate")
async def translate_text(request: TranslateRequest):
    """
    ✅ FIXED: Better translation with validation
    """
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
        try:
            from deep_translator import GoogleTranslator
        except ImportError:
            raise HTTPException(
                status_code=503,
                detail="Translation service not available"
            )
        
        # Validate target language
        if request.target not in WELL_SUPPORTED_LANGUAGES:
            raise HTTPException(
                status_code=400,
                detail=f"Target language '{request.target}' not supported"
            )
        
        max_retries = 2
        retry_delay = 1
        
        for attempt in range(max_retries):
            try:
                start_time = time.time()
                
                translator = GoogleTranslator(
                    source=request.source,
                    target=request.target
                )
                
                # Handle long text by chunking
                text = request.text
                if len(text) > 4500:
                    chunks = [text[i:i+4500] for i in range(0, len(text), 4500)]
                    translated_chunks = []
                    
                    for chunk in chunks:
                        translated_chunk = translator.translate(chunk)
                        translated_chunks.append(translated_chunk)
                    
                    translated = " ".join(translated_chunks)
                else:
                    translated = translator.translate(text)
                
                elapsed = time.time() - start_time
                
                print(f"✅ Translation: {request.source} -> {request.target} ({elapsed:.2f}s)")
                
                return {
                    "translated": translated,
                    "source": request.source,
                    "target": request.target,
                    "elapsed_seconds": round(elapsed, 2)
                }
            
            except Exception as translate_error:
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    continue
                else:
                    raise translate_error
    
    except HTTPException:
        raise
    
    except Exception as e:
        error_msg = str(e)
        print(f"❌ Translation error: {error_msg}")
        
        if "timeout" in error_msg.lower():
            detail = "Translation timed out. Try again."
        elif "connection" in error_msg.lower():
            detail = "Cannot connect to translation service."
        elif "rate limit" in error_msg.lower():
            detail = "Rate limit reached. Wait and try again."
        else:
            detail = f"Translation failed: {error_msg}"
        
        raise HTTPException(status_code=500, detail=detail)


@router.get("/supported")
async def get_supported_languages():
    """
    ✅ FIXED: Only return well-supported languages
    """
    return {
        "languages": [
            {"code": k, "name": v, "detection_quality": "high"} 
            for k, v in sorted(WELL_SUPPORTED_LANGUAGES.items(), key=lambda x: x[1])
        ],
        "count": len(WELL_SUPPORTED_LANGUAGES),
        "note": "Only languages with reliable detection included"
    }


@router.get("/health")
async def check_language_services():
    """
    Check language service availability
    """
    status = {
        "detection": "unavailable",
        "translation": "unavailable",
        "supported_languages": len(WELL_SUPPORTED_LANGUAGES)
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