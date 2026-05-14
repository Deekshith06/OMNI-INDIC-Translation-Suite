"""
Omni-Indic ML Engine
====================
Core machine learning components for translation, transliteration,
OCR processing, and PDF text extraction.

v2.0.0: 11 languages, IndicTrans2-200M, INT8 quantization, health checks.
"""

from .language_config import LANGUAGES, get_language, get_flores_code, get_gtts_code, get_xlit_code
from .translator import TranslationEngine, preflight_ram_check
from .transliterator import TransliterationEngine
from .ocr_processor import OCRProcessor
from .pdf_processor import PDFProcessor

__all__ = [
    "LANGUAGES",
    "get_language",
    "get_flores_code",
    "get_gtts_code",
    "get_xlit_code",
    "TranslationEngine",
    "preflight_ram_check",
    "TransliterationEngine",
    "OCRProcessor",
    "PDFProcessor",
]
