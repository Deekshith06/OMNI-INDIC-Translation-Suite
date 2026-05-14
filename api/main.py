"""
Omni-Indic API — Main Application
==================================
FastAPI application entry point with CORS, router mounting,
and environment-driven configuration.

Set DEMO_MODE=true to run without loading ML models (for UI testing).
When using Colab GPU backend, the frontend connects directly to the
ngrok URL — this local server is not needed.

v2.0.0: IndicTrans2-200M, 11 languages, INT8 quantization, .env support.
"""

import logging
import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

# Add project root to path so ml_engine is importable
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Load .env file before reading os.environ
try:
    from dotenv import load_dotenv
    _env_file = Path(__file__).parent / ".env"
    if _env_file.exists():
        load_dotenv(_env_file)
        _loaded = True
    else:
        load_dotenv()  # try cwd .env
        _loaded = False
except ImportError:
    pass  # python-dotenv optional; fall back to system env vars

from ml_engine.language_config import get_language_choices

from routers import translate, tts
from ml_engine.advanced_translit.transliteration_api import router as v3_translit_router

# ─── Logging ───────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s │ %(name)-20s │ %(levelname)-7s │ %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("omni-indic")

# ─── Demo mode flag ───────────────────────────────────────────────────
DEMO_MODE = os.environ.get("DEMO_MODE", "true").lower() == "true"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Preload ML models on startup (skipped in demo mode)."""
    logger.info("═" * 60)
    logger.info("  Omni-Indic Translation Suite — Starting up...")
    logger.info("═" * 60)

    app.state.demo_mode = DEMO_MODE

    if DEMO_MODE:
        logger.info("  🎭 DEMO MODE — No models loaded (use Colab for real inference)")
        app.state.translation_engine = None
        app.state.transliteration_engine = None
        app.state.ocr_processor = None
        app.state.pdf_processor = None
    else:
        from ml_engine.translator import TranslationEngine
        from ml_engine.transliterator import TransliterationEngine
        from ml_engine.ocr_processor import OCRProcessor
        from ml_engine.pdf_processor import PDFProcessor

        translation_engine = TranslationEngine()
        transliteration_engine = TransliterationEngine()
        ocr_processor = OCRProcessor()
        pdf_processor = PDFProcessor()

        logger.info("Loading translation model (this may take a minute)...")
        translation_engine.load()
        logger.info("Loading transliteration engine...")
        transliteration_engine.load()
        logger.info("Loading OCR processor...")
        ocr_processor.load()

        app.state.translation_engine = translation_engine
        app.state.transliteration_engine = transliteration_engine
        app.state.ocr_processor = ocr_processor
        app.state.pdf_processor = pdf_processor

    logger.info("═" * 60)
    logger.info("  Server is ready!")
    logger.info("═" * 60)

    yield

    logger.info("Shutting down Omni-Indic server...")


# ─── App Creation ─────────────────────────────────────────────────────
app = FastAPI(
    title="Omni-Indic Translation Suite",
    description=(
        "Professional-grade API for translating and transliterating "
        "English/Tinglish to 11 Indian languages with OCR, PDF support, "
        "and TTS. Powered by IndicTrans2-200M + IndicXlit."
    ),
    version="2.0.0",
    lifespan=lifespan,
)

# ─── CORS ─────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "*",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Routers ──────────────────────────────────────────────────────────
app.include_router(translate.router, prefix="/api", tags=["Translation"])
app.include_router(tts.router, prefix="/api", tags=["Text-to-Speech"])
app.include_router(v3_translit_router, prefix="/api")


# ─── Health & Info ────────────────────────────────────────────────────
@app.get("/", tags=["Health"])
async def root():
    """Health check endpoint."""
    return {
        "service": "Omni-Indic Translation Suite",
        "status": "running",
        "version": "2.0.0",
        "demo_mode": DEMO_MODE,
    }


@app.get("/api/languages", tags=["Config"])
async def get_languages():
    """Return the list of supported languages for the frontend dropdown."""
    return {"languages": get_language_choices()}


@app.get("/api/status", tags=["Health"])
async def get_status(request: Request):
    """Return engine loading status."""
    # In real mode, check actual engine state from app.state
    translation_ready = (
        not DEMO_MODE
        and getattr(getattr(request.app.state, "translation_engine", None), "is_loaded", False)
    )
    transliteration_ready = (
        not DEMO_MODE
        and getattr(getattr(request.app.state, "transliteration_engine", None), "is_loaded", False)
    )
    ocr_ready = (
        not DEMO_MODE
        and getattr(getattr(request.app.state, "ocr_processor", None), "is_loaded", False)
    )
    return {
        "translation_engine": translation_ready,
        "transliteration_engine": transliteration_ready,
        "ocr_processor": ocr_ready,
        "pdf_processor": True,  # PDFProcessor is always available (no load() needed)
        "demo_mode": DEMO_MODE,
    }
