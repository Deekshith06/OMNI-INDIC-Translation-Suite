"""
Comprehensive Test Suite for Omni-Indic Translation Suite
==========================================================
Tests API endpoints, middleware, bidirectional translation, TTS,
magic-byte upload safety, and NLP sentence splitting.
"""

import io
import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

# Ensure repo root and api directory are on path
ROOT_DIR = Path(__file__).resolve().parent.parent
API_DIR = ROOT_DIR / "api"
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))
if str(API_DIR) not in sys.path:
    sys.path.insert(0, str(API_DIR))

from api.main import app
from ml_engine.language_config import LANGUAGES, get_flores_code, get_gtts_code
from ml_engine.translator import TranslationEngine
from ml_engine.romanization.romanizer import RomanizerEngine


@pytest.fixture(scope="module")
def client():
    """TestClient instance that triggers FastAPI lifespan."""
    with TestClient(app) as test_client:
        yield test_client


# ─── 1. Health Probes & Observability ──────────────────────────────────────────

def test_healthz_liveness_probe(client: TestClient):
    """Test standard Kubernetes liveness probe /healthz."""
    res = client.get("/healthz")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert data["service"] == "omni-indic"
    assert "version" in data


def test_live_probe(client: TestClient):
    """Test /live endpoint."""
    res = client.get("/live")
    assert res.status_code == 200
    assert res.json() == {"status": "alive"}


def test_ready_probe(client: TestClient):
    """Test /ready readiness probe."""
    res = client.get("/ready")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] in ("ready", "degraded")
    assert data["traffic_ready"] is True


def test_root_status(client: TestClient):
    """Test root endpoint / returns system info."""
    res = client.get("/")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "running"
    assert "demo_mode" in data


def test_engine_status_endpoint(client: TestClient):
    """Test /api/status endpoint."""
    res = client.get("/api/status")
    assert res.status_code == 200
    data = res.json()
    assert "translation_engine" in data
    assert "transliteration_engine" in data
    assert "ocr_processor" in data
    assert data["pdf_processor"] is True


def test_telemetry_headers(client: TestClient):
    """Test X-Request-ID and X-Process-Time-Ms headers are present and valid."""
    custom_id = "test-custom-uuid-12345"
    res = client.get("/healthz", headers={"X-Request-ID": custom_id})
    assert res.status_code == 200
    assert res.headers.get("X-Request-ID") == custom_id
    assert "X-Process-Time-Ms" in res.headers
    latency = float(res.headers["X-Process-Time-Ms"])
    assert latency >= 0.0


# ─── 2. Language Registry & Config ────────────────────────────────────────────

def test_language_choices_endpoint(client: TestClient):
    """Test /api/languages returns all 12 supported languages (English + 11 Indic)."""
    res = client.get("/api/languages")
    assert res.status_code == 200
    data = res.json()
    assert "languages" in data
    langs = {item["key"]: item for item in data["languages"]}
    
    assert "english" in langs
    assert "telugu" in langs
    assert "hindi" in langs
    assert "tamil" in langs
    assert "kannada" in langs
    assert "bengali" in langs
    assert len(langs) == 12


def test_language_config_helpers():
    """Test FLORES and gTTS code lookups."""
    assert get_flores_code("english") == "eng_Latn"
    assert get_flores_code("telugu") == "tel_Telu"
    assert get_flores_code("hindi") == "hin_Deva"
    assert get_gtts_code("english") == "en"
    assert get_gtts_code("telugu") == "te"


# ─── 3. Translation & Transliteration Endpoints ───────────────────────────────

def test_translate_text_english_to_telugu(client: TestClient):
    """Test forward translation from English to Telugu."""
    payload = {
        "text": "Hello, welcome to our university.",
        "target_lang": "telugu",
        "source_lang": "english",
        "mode": "translate",
    }
    res = client.post("/api/translate-text", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["target_language"] == "telugu"
    assert data["source_language"] == "english"
    assert data["mode"] == "translate"
    assert len(data["translated_text"]) > 0
    assert data["confidence"] > 0.0


def test_translate_text_bidirectional_indic_to_english(client: TestClient):
    """Test reverse/bidirectional translation from Telugu to English."""
    payload = {
        "text": "నమస్కారం, మా విశ్వవిద్యాలయానికి స్వాగతం.",
        "target_lang": "english",
        "source_lang": "telugu",
        "mode": "translate",
    }
    res = client.post("/api/translate-text", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["target_language"] == "english"
    assert data["source_language"] == "telugu"
    assert len(data["translated_text"]) > 0


def test_transliteration_mode(client: TestClient):
    """Test transliteration mode."""
    payload = {
        "text": "namaste",
        "target_lang": "hindi",
        "mode": "transliterate",
    }
    res = client.post("/api/translate-text", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["mode"] == "transliterate"
    assert len(data["translated_text"]) > 0


def test_translate_text_empty_error(client: TestClient):
    """Test translation with empty text returns 400."""
    res = client.post("/api/translate-text", json={"text": "   ", "target_lang": "telugu"})
    assert res.status_code == 400
    assert "empty" in res.json()["detail"].lower()


# ─── 4. Text-to-Speech (TTS) ──────────────────────────────────────────────────

def test_generate_tts_endpoint(client: TestClient, monkeypatch):
    """Test audio synthesis via /api/generate-tts returns audio/mpeg stream."""
    from gtts import gTTS

    def mock_write_to_fp(self, fp):
        # Mock valid MP3 frame payload for hermetic unit testing
        fp.write(b"ID3\x03\x00\x00\x00\x00\x00#TSSE\x00\x00\x00\x0f\x00\x00\x01Lavf58.29.100\x00" + b"\xff\xfb\x90\x44" * 20)

    monkeypatch.setattr(gTTS, "write_to_fp", mock_write_to_fp)

    payload = {
        "text": "Hello world",
        "lang": "english",
    }
    res = client.post("/api/generate-tts", json=payload)
    assert res.status_code == 200
    assert "audio/mpeg" in res.headers.get("content-type", "")
    assert len(res.content) > 50


def test_generate_tts_empty_validation(client: TestClient):
    """Test TTS empty text validation returns 400."""
    res = client.post("/api/generate-tts", json={"text": "", "lang": "english"})
    assert res.status_code == 400


def test_generate_tts_invalid_lang(client: TestClient):
    """Test TTS invalid language returns 400."""
    res = client.post("/api/generate-tts", json={"text": "hello", "lang": "klingon"})
    assert res.status_code == 400


# ─── 5. Document Translation & Magic Byte Security ────────────────────────────

def test_document_translation_valid_png(client: TestClient, monkeypatch):
    """Test document upload with authentic PNG magic bytes and OCR extraction."""
    from ml_engine.ocr_processor import OCRProcessor
    monkeypatch.setattr(OCRProcessor, "extract_text", lambda self, b, target_lang=None: "Welcome to India")

    # 1x1 transparent PNG file bytes
    png_bytes = (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06"
        b"\x00\x00\x00\x1f\x15c4\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01"
        b"\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
    )
    files = {"file": ("test.png", io.BytesIO(png_bytes), "image/png")}
    data = {"target_lang": "telugu", "source_lang": "english", "mode": "translate"}
    res = client.post("/api/translate-doc", files=files, data=data)
    assert res.status_code == 200
    assert res.json()["target_language"] == "telugu"
    assert len(res.json()["translated_text"]) > 0


def test_document_translation_valid_pdf(client: TestClient):
    """Test document upload with authentic PDF containing readable text."""
    import fitz
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 72), "Welcome to our university.")
    pdf_bytes = doc.tobytes()
    doc.close()

    files = {"file": ("document.pdf", io.BytesIO(pdf_bytes), "application/pdf")}
    data = {"target_lang": "hindi", "source_lang": "english", "mode": "translate"}
    res = client.post("/api/translate-doc", files=files, data=data)
    assert res.status_code == 200
    assert res.json()["target_language"] == "hindi"
    assert len(res.json()["translated_text"]) > 0


def test_document_translation_spoofed_magic_bytes(client: TestClient):
    """Test MIME spoofing protection (fake PNG with executable/garbage bytes)."""
    fake_png_bytes = b"MZ\x90\x00This is an executable disguised as a PNG image"
    files = {"file": ("fake.png", io.BytesIO(fake_png_bytes), "image/png")}
    data = {"target_lang": "telugu", "mode": "translate"}
    res = client.post("/api/translate-doc", files=files, data=data)
    assert res.status_code == 400
    assert "invalid png header" in res.json()["detail"].lower()


def test_document_translation_unsupported_mimetype(client: TestClient):
    """Test unsupported MIME type returns 400."""
    files = {"file": ("script.sh", io.BytesIO(b"#!/bin/bash\necho 1"), "text/x-shellscript")}
    data = {"target_lang": "telugu", "mode": "translate"}
    res = client.post("/api/translate-doc", files=files, data=data)
    assert res.status_code == 400


# ─── 6. NLP & Unit Algorithm Tests ────────────────────────────────────────────

def test_indic_sentence_splitter():
    """Verify sentence splitting handles English punctuation, Indic Danda (।), and Double Danda (॥)."""
    engine = TranslationEngine()
    text = "Sentence one. Sentence two! Sentence three? హిందీ వాక్యం ఒకటి। రెండవ వాక్యం॥ Final one."
    splits = engine._split_sentences(text)
    assert len(splits) == 6
    assert splits[0] == "Sentence one."
    assert splits[1] == "Sentence two!"
    assert splits[2] == "Sentence three?"
    assert splits[3] == "హిందీ వాక్యం ఒకటి।"
    assert splits[4] == "రెండవ వాక్యం॥"
    assert splits[5] == "Final one."


def test_romanizer_engine_singleton():
    """Verify Romanizer produces correct human-readable phonetic pronunciation."""
    romanizer = RomanizerEngine()
    assert romanizer._loaded is True
    # Test Telugu romanization
    romanized = romanizer.romanize("నమస్కారం", "telugu")
    assert len(romanized) > 0
    assert "namask" in romanized.lower()
