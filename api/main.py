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
import time
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Add both api dir and project root to path so ml_engine and routers are always importable
API_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = API_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(API_DIR) not in sys.path:
    sys.path.insert(0, str(API_DIR))

# Load .env file before reading os.environ
try:
    from dotenv import load_dotenv
    _env_file = API_DIR / ".env"
    if _env_file.exists():
        load_dotenv(_env_file)
        _loaded = True
    else:
        load_dotenv()  # try cwd .env
        _loaded = False
except ImportError:
    pass  # python-dotenv optional; fall back to system env vars

from ml_engine.language_config import get_language_choices
from ml_engine.romanization.romanizer import RomanizerEngine

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
    """Preload ML models and singletons on startup (graceful fallback in demo mode)."""
    logger.info("═" * 60)
    logger.info("  Omni-Indic Translation Suite — Starting up...")
    logger.info("═" * 60)

    app.state.demo_mode = DEMO_MODE

    # Preload singleton RomanizerEngine for zero per-request allocation
    try:
        app.state.romanizer_engine = RomanizerEngine()
        logger.info("  Romanizer singleton initialized.")
    except Exception as e:
        logger.warning(f"  Romanizer failed to initialize: {e}")
        app.state.romanizer_engine = None

    if DEMO_MODE:
        logger.info("  🎭 DEMO MODE — Deep ML models offline (using demo mocks/Colab GPU backend)")
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
    logger.info("  Server is ready to accept requests!")
    logger.info("═" * 60)

    yield

    logger.info("Shutting down Omni-Indic server...")


# ─── App Creation ─────────────────────────────────────────────────────
app = FastAPI(
    title="Omni-Indic Translation Suite",
    description=(
        "Production-grade enterprise API for bidirectional translation, "
        "transliteration, OCR, PDF extraction, and TTS across Indian languages."
    ),
    version="2.1.0",
    lifespan=lifespan,
)

# ─── Telemetry Middleware ─────────────────────────────────────────────
@app.middleware("http")
async def telemetry_middleware(request: Request, call_next):
    """
    Structured observability middleware:
    - Injects unique X-Request-ID header into request & response.
    - Measures high-resolution request duration (X-Process-Time-Ms).
    - Emits structured telemetry logs.
    """
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    start_time = time.perf_counter()

    try:
        response = await call_next(request)
    except Exception as exc:
        process_time_ms = round((time.perf_counter() - start_time) * 1000, 2)
        logger.error(
            f"ERROR {request.method} {request.url.path} latency={process_time_ms}ms req_id={request_id} err={exc}",
            exc_info=True,
        )
        raise exc

    process_time_ms = round((time.perf_counter() - start_time) * 1000, 2)
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Process-Time-Ms"] = str(process_time_ms)
    logger.info(
        f"HTTP {request.method} {request.url.path} status={response.status_code} latency={process_time_ms}ms req_id={request_id}"
    )
    return response

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


# ─── Cloud-Native Standard Health Probes ───────────────────────────────
@app.get("/healthz", tags=["Health"])
async def healthz():
    """Liveness probe: verifies process is alive and HTTP server responds."""
    return {"status": "ok", "service": "omni-indic", "version": "2.1.0"}


@app.get("/live", tags=["Health"])
async def live():
    """Kubernetes-standard liveness probe."""
    return {"status": "alive"}


@app.get("/ready", tags=["Health"])
async def ready(request: Request):
    """Readiness probe: verifies whether application is ready to handle traffic."""
    if DEMO_MODE:
        return {"status": "ready", "mode": "demo", "traffic_ready": True}

    tx_ready = getattr(getattr(request.app.state, "translation_engine", None), "is_loaded", False)
    return {
        "status": "ready" if tx_ready else "degraded",
        "mode": "production",
        "translation_engine_loaded": tx_ready,
        "traffic_ready": True,
    }


@app.get("/", tags=["Health"])
async def root():
    """Service status and meta info endpoint."""
    return {
        "service": "Omni-Indic Translation Suite",
        "status": "running",
        "version": "2.1.0",
        "demo_mode": DEMO_MODE,
    }


@app.get("/api/languages", tags=["Config"])
async def get_languages():
    """Return the list of supported languages for the frontend dropdown."""
    return {"languages": get_language_choices()}


@app.get("/api/status", tags=["Health"])
async def get_status(request: Request):
    """Return comprehensive engine loading status."""
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
        "pdf_processor": True,
        "demo_mode": DEMO_MODE,
    }
