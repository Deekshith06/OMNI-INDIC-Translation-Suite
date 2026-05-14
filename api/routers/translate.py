"""
Translation Router
==================
Endpoints for text translation, document translation (OCR + PDF),
and transliteration. Supports demo mode for UI testing.
"""

import logging
from typing import Literal, Optional

from fastapi import APIRouter, File, Form, Request, UploadFile, HTTPException
from pydantic import BaseModel
from starlette.concurrency import run_in_threadpool

logger = logging.getLogger(__name__)

router = APIRouter()

# ─── Request / Response Models ────────────────────────────────────────

class TextTranslateRequest(BaseModel):
    text: str
    target_lang: str
    mode: Literal["translate", "transliterate"] = "translate"


class TranslationResponse(BaseModel):
    original_text: str
    translated_text: str
    target_language: str
    mode: str
    confidence: float
    extracted_text: Optional[str] = None
    romanized_text: Optional[str] = None


# ─── Demo translations for UI testing ────────────────────────────────

DEMO_TRANSLATIONS = {
    # Original 7 languages
    "telugu": "ఇది ఒక డెమో అనువాదం. వాస్తవ అనువాదం కోసం Colab GPU బ్యాక్‌ఎండ్‌ను కనెక్ట్ చేయండి.",
    "tamil": "இது ஒரு டெமோ மொழிபெயர்ப்பு. உண்மையான மொழிபெயர்ப்புக்கு Colab GPU பின்நிலையை இணைக்கவும்.",
    "kannada": "ಇದು ಡೆಮೊ ಅನುವಾದ. ನೈಜ ಅನುವಾದಕ್ಕಾಗಿ Colab GPU ಬ್ಯಾಕೆಂಡ್ ಅನ್ನು ಸಂಪರ್ಕಿಸಿ.",
    "malayalam": "ഇതൊരു ഡെമോ വിവർത്തനമാണ്. യഥാർത്ഥ വിവർത്തനത്തിനായി Colab GPU ബാക്കെൻഡ് ബന്ധിപ്പിക്കുക.",
    "marathi": "हे एक डेमो भाषांतर आहे. वास्तविक भाषांतरासाठी Colab GPU बॅकएंड कनेक्ट करा.",
    "punjabi": "ਇਹ ਇੱਕ ਡੈਮੋ ਅਨੁਵਾਦ ਹੈ। ਅਸਲ ਅਨੁਵਾਦ ਲਈ Colab GPU ਬੈਕਐਂਡ ਕਨੈਕਟ ਕਰੋ।",
    "hindi": "यह एक डेमो अनुवाद है। वास्तविक अनुवाद के लिए Colab GPU बैकएंड कनेक्ट करें।",
    # New 4 languages (v2.0.0)
    "bengali": "এটি একটি ডেমো অনুবাদ। প্রকৃত অনুবাদের জন্য Colab GPU ব্যাকএন্ড সংযুক্ত করুন।",
    "gujarati": "આ એક ડેમો અનુવાદ છે. વાસ્તવિક અનુવાદ માટે Colab GPU બૅકઍન્ડ જોડો.",
    "odia": "ଏହା ଏକ ଡେମୋ ଅନୁବାଦ। ପ୍ରକୃତ ଅନୁବାଦ ପାଇଁ Colab GPU ବ୍ୟାକଏଣ୍ଡ ସଂଯୋଗ କରନ୍ତୁ।",
    "assamese": "এইটো এটা ডেমো অনুবাদ। প্ৰকৃত অনুবাদৰ বাবে Colab GPU বেকএণ্ড সংযোগ কৰক।",
}

DEMO_TRANSLITERATIONS = {
    # Original 7 languages
    "telugu": "నమస్తే, ఇది డెమో మోడ్‌లో ట్రాన్స్‌లిటరేషన్",
    "tamil": "நமஸ்தே, இது டெமோ மோடில் டிரான்ஸ்லிட்ரேஷன்",
    "kannada": "ನಮಸ್ತೆ, ಇದು ಡೆಮೊ ಮೋಡ್‌ನಲ್ಲಿ ಟ್ರಾನ್ಸ್‌ಲಿಟರೇಶನ್",
    "malayalam": "നമസ്തേ, ഇതൊരു ഡെമോ മോഡിലുള്ള ട്രാൻസ്‌ലിറ്ററേഷൻ",
    "marathi": "नमस्ते, हे डेमो मोडमध्ये ट्रान्सलिटरेशन",
    "punjabi": "ਨਮਸਤੇ, ਇਹ ਡੈਮੋ ਮੋਡ ਵਿੱਚ ਟ੍ਰਾਂਸਲਿਟਰੇਸ਼ਨ",
    "hindi": "नमस्ते, यह डेमो मोड में ट्रांसलिटरेशन",
    # New 4 languages (v2.0.0)
    "bengali": "নমস্তে, এটি ডেমো মোডে ট্রান্সলিটারেশন",
    "gujarati": "નમસ્તે, આ ડેમો મોડમાં ટ્રાન્સલિટ્રેશન",
    "odia": "ନମସ୍ତେ, ଏହା ଡେମୋ ମୋଡ୍‌ରେ ଟ୍ରାନ୍ସଲିଟ୍ରେସନ",
    "assamese": "নমস্তে, এইটো ডেমো মোডত ট্ৰান্সলিটাৰেচন",
}

# ─── Allowed file types ──────────────────────────────────────────────

IMAGE_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
    "image/bmp",
    "image/tiff",
}
PDF_TYPES = {"application/pdf"}
ALLOWED_TYPES = IMAGE_TYPES | PDF_TYPES

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


# ─── Text Translation ────────────────────────────────────────────────

@router.post("/translate-text", response_model=TranslationResponse)
async def translate_text(request: Request, body: TextTranslateRequest):
    """
    Translate or transliterate English/Tinglish text to an Indian language.
    """
    text = body.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="Text cannot be empty.")

    target_lang = body.target_lang.lower()
    is_demo = getattr(request.app.state, "demo_mode", True)

    try:
        if is_demo:
            # Demo mode — return sample translations
            if body.mode == "transliterate":
                demo_text = DEMO_TRANSLITERATIONS.get(target_lang, f"[Demo transliteration of: {text}]")
                return TranslationResponse(
                    original_text=text,
                    translated_text=demo_text,
                    target_language=target_lang,
                    mode="transliterate",
                    confidence=0.92,
                )
            else:
                demo_text = DEMO_TRANSLATIONS.get(target_lang, f"[Demo translation of: {text}]")
                return TranslationResponse(
                    original_text=text,
                    translated_text=demo_text,
                    target_language=target_lang,
                    mode="translate",
                    confidence=0.87,
                )

        # Real mode — use loaded engines
        if body.mode == "transliterate":
            engine = request.app.state.transliteration_engine
            transliterated = await run_in_threadpool(
                engine.transliterate, text, target_lang
            )
            return TranslationResponse(
                original_text=text,
                translated_text=transliterated,
                target_language=target_lang,
                mode="transliterate",
                confidence=1.0,
            )
        else:
            engine = request.app.state.translation_engine
            result = await run_in_threadpool(engine.translate, text, target_lang)
            translated_text = result["translated_text"]
            
            # Post-Translation Romanization
            from ml_engine.romanization.romanizer import RomanizerEngine
            romanizer = RomanizerEngine()
            romanized_text = await run_in_threadpool(romanizer.romanize, translated_text, target_lang)
            
            return TranslationResponse(
                original_text=text,
                translated_text=translated_text,
                romanized_text=romanized_text,
                target_language=target_lang,
                mode="translate",
                confidence=result["confidence"],
            )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"Translation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Translation failed.")


# ─── Document Translation (Image + PDF) ──────────────────────────────

@router.post("/translate-doc", response_model=TranslationResponse)
async def translate_document(
    request: Request,
    file: UploadFile = File(...),
    target_lang: str = Form(...),
    mode: str = Form("translate"),
):
    """
    Upload an image (OCR) or PDF and translate/transliterate its content.
    """
    content_type = file.content_type or ""
    if content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Unsupported file type: {content_type}. "
                f"Accepted: JPEG, PNG, WebP, BMP, TIFF, PDF."
            ),
        )

    file_bytes = await file.read()
    if len(file_bytes) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size is {MAX_FILE_SIZE // (1024*1024)} MB.",
        )

    if not file_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    target_lang = target_lang.lower()
    is_demo = getattr(request.app.state, "demo_mode", True)

    try:
        if is_demo:
            # Demo mode
            extracted_text = "[Demo] Sample extracted text from your document. Connect Colab GPU backend for real OCR."
            demo_text = DEMO_TRANSLATIONS.get(target_lang, f"[Demo translation]")
            return TranslationResponse(
                original_text=extracted_text,
                translated_text=demo_text,
                target_language=target_lang,
                mode=mode,
                confidence=0.85,
                extracted_text=extracted_text,
            )

        # Real mode — extract and translate
        if content_type in IMAGE_TYPES:
            ocr = request.app.state.ocr_processor
            extracted_text = await run_in_threadpool(
                ocr.extract_text, file_bytes
            )
        elif content_type in PDF_TYPES:
            pdf = request.app.state.pdf_processor
            extracted_text = await run_in_threadpool(
                pdf.extract_text, file_bytes
            )
        else:
            raise HTTPException(status_code=400, detail="Unsupported file type.")

        if not extracted_text.strip():
            raise HTTPException(
                status_code=422,
                detail="No text could be extracted from the uploaded file.",
            )

        if mode == "transliterate":
            xlit = request.app.state.transliteration_engine
            translated_text = await run_in_threadpool(
                xlit.transliterate, extracted_text, target_lang
            )
            confidence = 1.0
        else:
            translator = request.app.state.translation_engine
            result = await run_in_threadpool(
                translator.translate, extracted_text, target_lang
            )
            translated_text = result["translated_text"]
            confidence = result["confidence"]

        return TranslationResponse(
            original_text=extracted_text,
            translated_text=translated_text,
            target_language=target_lang,
            mode=mode,
            confidence=confidence,
            extracted_text=extracted_text,
        )

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"Document translation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Document translation failed.")
