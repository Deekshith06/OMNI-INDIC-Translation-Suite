"""
🕉️ Omni-Indic Translation Suite — Standalone Backend
This is the standalone Python version of the Colab notebook.
It runs the full FastAPI backend and optionally exposes it via ngrok.
"""

import io
import re
import os
import torch
import numpy as np
import cv2
import easyocr
import uvicorn
import nest_asyncio
from pyngrok import ngrok
from typing import Literal, Optional
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
from fastapi import FastAPI, File, Form, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

# ─── 1. Configuration ──────────────────────────────────────────────────────────

LANGUAGES = {
    "telugu":    {"flores": "tel_Telu", "gtts": "te", "label": "Telugu",    "script": "తెలుగు"},
    "tamil":     {"flores": "tam_Taml", "gtts": "ta", "label": "Tamil",     "script": "தமிழ்"},
    "kannada":   {"flores": "kan_Knda", "gtts": "kn", "label": "Kannada",   "script": "ಕನ್ನಡ"},
    "malayalam": {"flores": "mal_Mlym", "gtts": "ml", "label": "Malayalam", "script": "മലയാളം"},
    "marathi":   {"flores": "mar_Deva", "gtts": "mr", "label": "Marathi",   "script": "मराठी"},
    "punjabi":   {"flores": "pan_Guru", "gtts": "pa", "label": "Punjabi",   "script": "ਪੰਜਾਬੀ"},
    "hindi":     {"flores": "hin_Deva", "gtts": "hi", "label": "Hindi",     "script": "हिन्दी"},
}

SOURCE_LANG_FLORES = "eng_Latn"

def get_language(key): return LANGUAGES.get(key.lower())
def get_flores_code(key):
    lang = get_language(key)
    return lang["flores"] if lang else None
def get_gtts_code(key):
    lang = get_language(key)
    return lang["gtts"] if lang else None

print(f"✅ {len(LANGUAGES)} languages configured")

# ─── 2. Load Translation Model ────────────────────────────────────────────────

MODEL_NAME = "facebook/nllb-200-distilled-600M"
# Use MPS on Mac if available, otherwise CUDA, otherwise CPU
if torch.backends.mps.is_available():
    DEVICE = "mps"
elif torch.cuda.is_available():
    DEVICE = "cuda"
else:
    DEVICE = "cpu"

print(f"🖥️ Device: {DEVICE}")

print(f"📥 Loading {MODEL_NAME}...")
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, trust_remote_code=True)
model = AutoModelForSeq2SeqLM.from_pretrained(
    MODEL_NAME,
    trust_remote_code=True,
    # Use float16 for CUDA/MPS to save memory, float32 for CPU
    torch_dtype=torch.float16 if DEVICE in ["cuda", "mps"] else torch.float32,
).to(DEVICE)
model.eval()
print(f"✅ Model loaded on {DEVICE}")


def split_sentences(text):
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    return [s.strip() for s in sentences if s.strip()]


def translate(text, target_lang, max_length=256, num_beams=5):
    """Translate English text to an Indian language using NLLB-200."""
    flores_code = get_flores_code(target_lang)
    if not flores_code:
        raise ValueError(f"Unsupported language: {target_lang}")

    tokenizer.src_lang = SOURCE_LANG_FLORES
    sentences = split_sentences(text)
    if not sentences:
        return {"translated_text": "", "confidence": 0.0}

    translated_parts = []
    confidence_scores = []

    for sentence in sentences:
        inputs = tokenizer(
            sentence, return_tensors="pt",
            truncation=True, max_length=512, padding=True
        ).to(DEVICE)

        forced_bos_token_id = tokenizer.convert_tokens_to_ids(flores_code)

        with torch.no_grad():
            output = model.generate(
                **inputs,
                forced_bos_token_id=forced_bos_token_id,
                max_new_tokens=max_length,
                num_beams=num_beams,
                num_return_sequences=1,
                output_scores=True,
                return_dict_in_generate=True,
            )

        translated = tokenizer.batch_decode(output.sequences, skip_special_tokens=True)[0]
        translated_parts.append(translated)

        # Confidence from softmax
        try:
            probs = []
            for score in output.scores:
                softmax = torch.softmax(score, dim=-1)
                max_prob = softmax.max(dim=-1).values.mean().item()
                probs.append(max_prob)
            confidence_scores.append(sum(probs) / len(probs) if probs else 0.0)
        except:
            confidence_scores.append(0.0)

    full_translation = " ".join(translated_parts)
    avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.0

    return {
        "translated_text": full_translation,
        "confidence": round(avg_confidence, 4),
    }

# ─── 3. Load OCR Engine ───────────────────────────────────────────────────────

print("📥 Loading EasyOCR...")
# EasyOCR doesn't fully support MPS yet, so we use cuda if available, otherwise CPU
ocr_reader = easyocr.Reader(['en'], gpu=torch.cuda.is_available())
print("✅ EasyOCR loaded")


def extract_text_from_image(image_bytes):
    """Extract text from image bytes using EasyOCR."""
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    results = ocr_reader.readtext(img, detail=0)
    return "\n".join(results).strip()


def extract_text_from_pdf(pdf_bytes):
    """Extract text from PDF bytes using PyMuPDF."""
    import fitz
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    text_parts = []
    for page in doc:
        page_text = page.get_text("text")
        if page_text.strip():
            text_parts.append(page_text.strip())
    doc.close()
    return "\n\n".join(text_parts)


# ─── 4. Build FastAPI Server ──────────────────────────────────────────────────

app = FastAPI(title="Omni-Indic Translation Suite")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class TextTranslateRequest(BaseModel):
    text: str
    target_lang: str
    mode: Literal["translate", "transliterate"] = "translate"

class TTSRequest(BaseModel):
    text: str
    lang: str

@app.get("/")
async def root():
    return {"service": "Omni-Indic Translation Suite", "status": "running", "device": DEVICE}

@app.get("/api/languages")
async def get_languages():
    return {"languages": [
        {"key": k, "label": v["label"], "script": v["script"]}
        for k, v in LANGUAGES.items()
    ]}

@app.get("/api/status")
async def get_status():
    return {
        "translation_engine": True,
        "transliteration_engine": False,
        "ocr_processor": True,
        "pdf_processor": True,
        "device": DEVICE,
    }

@app.post("/api/translate-text")
async def translate_text_endpoint(body: TextTranslateRequest):
    text = body.text.strip()
    if not text:
        raise HTTPException(400, "Text cannot be empty.")

    target = body.target_lang.lower()

    if body.mode == "transliterate":
        # Return the original text with a note
        return {
            "original_text": text,
            "translated_text": text,
            "target_language": target,
            "mode": "transliterate",
            "confidence": 0.0,
            "extracted_text": None,
        }

    try:
        result = translate(text, target)
        return {
            "original_text": text,
            "translated_text": result["translated_text"],
            "target_language": target,
            "mode": "translate",
            "confidence": result["confidence"],
            "extracted_text": None,
        }
    except Exception as e:
        raise HTTPException(500, f"Translation failed: {e}")

IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/bmp", "image/tiff"}
PDF_TYPES = {"application/pdf"}

@app.post("/api/translate-doc")
async def translate_doc_endpoint(
    file: UploadFile = File(...),
    target_lang: str = Form(...),
    mode: str = Form("translate"),
):
    content_type = file.content_type or ""
    if content_type not in IMAGE_TYPES | PDF_TYPES:
        raise HTTPException(400, f"Unsupported file type: {content_type}")

    file_bytes = await file.read()
    target = target_lang.lower()

    if content_type in IMAGE_TYPES:
        extracted = extract_text_from_image(file_bytes)
    else:
        extracted = extract_text_from_pdf(file_bytes)

    if not extracted.strip():
        raise HTTPException(422, "No text could be extracted from the file.")

    result = translate(extracted, target)

    return {
        "original_text": extracted,
        "translated_text": result["translated_text"],
        "target_language": target,
        "mode": mode,
        "confidence": result["confidence"],
        "extracted_text": extracted,
    }

@app.post("/api/generate-tts")
async def generate_tts_endpoint(body: TTSRequest):
    text = body.text.strip()
    if not text:
        raise HTTPException(400, "Text cannot be empty.")

    gtts_code = get_gtts_code(body.lang.lower())
    from gtts import gTTS
    tts = gTTS(text=text, lang=gtts_code, slow=False)
    audio_buffer = io.BytesIO()
    tts.write_to_fp(audio_buffer)
    audio_buffer.seek(0)

    return StreamingResponse(
        audio_buffer,
        media_type="audio/mpeg",
        headers={"Content-Disposition": f'attachment; filename="tts_{body.lang}.mp3"'},
    )

print("✅ FastAPI app built with all endpoints")

# ─── 5. Start Server ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Run the standalone Omni-Indic backend.")
    parser.add_argument("--ngrok", type=str, help="Your ngrok auth token (optional)", default=os.environ.get("NGROK_AUTH_TOKEN"))
    parser.add_argument("--port", type=int, default=8000, help="Port to run the server on")
    args = parser.parse_args()

    if args.ngrok:
        ngrok.set_auth_token(args.ngrok)
        nest_asyncio.apply()
        public_url = ngrok.connect(args.port)
        print("═" * 60)
        print(f"  🌐 NGROK PUBLIC URL: {public_url.public_url}")
        print("═" * 60)
        print("📋 Copy this into your frontend/.env.local:")
        print(f"   NEXT_PUBLIC_API_URL={public_url.public_url}")
        print("═" * 60)

    print(f"🚀 Starting server on http://0.0.0.0:{args.port}...")
    uvicorn.run(app, host="0.0.0.0", port=args.port)
