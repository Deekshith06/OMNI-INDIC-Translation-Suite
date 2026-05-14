"""
Language Configuration
======================
Central registry of supported Indian languages with their
FLORES-200 codes, gTTS codes, and transliteration codes.

v2.0.0 — Extended to 11 languages:
  Original (7): Telugu, Tamil, Kannada, Malayalam, Marathi, Punjabi, Hindi
  Added   (4):  Bengali, Gujarati, Odia, Assamese
"""

from typing import Optional


LANGUAGES = {
    # ── Original 7 languages ──────────────────────────────────────────
    "telugu": {
        "flores": "tel_Telu",
        "gtts": "te",
        "xlit": "te",
        "label": "Telugu",
        "script": "తెలుగు",
    },
    "tamil": {
        "flores": "tam_Taml",
        "gtts": "ta",
        "xlit": "ta",
        "label": "Tamil",
        "script": "தமிழ்",
    },
    "kannada": {
        "flores": "kan_Knda",
        "gtts": "kn",
        "xlit": "kn",
        "label": "Kannada",
        "script": "ಕನ್ನಡ",
    },
    "malayalam": {
        "flores": "mal_Mlym",
        "gtts": "ml",
        "xlit": "ml",
        "label": "Malayalam",
        "script": "മലയാളം",
    },
    "marathi": {
        "flores": "mar_Deva",
        "gtts": "mr",
        "xlit": "mr",
        "label": "Marathi",
        "script": "मराठी",
    },
    "punjabi": {
        "flores": "pan_Guru",
        "gtts": "pa",
        "xlit": "pa",
        "label": "Punjabi",
        "script": "ਪੰਜਾਬੀ",
    },
    "hindi": {
        "flores": "hin_Deva",
        "gtts": "hi",
        "xlit": "hi",
        "label": "Hindi",
        "script": "हिन्दी",
    },
    # ── New 4 languages (v2.0.0) ──────────────────────────────────────
    "bengali": {
        "flores": "ben_Beng",
        "gtts": "bn",
        "xlit": "bn",
        "label": "Bengali",
        "script": "বাংলা",
    },
    "gujarati": {
        "flores": "guj_Gujr",
        "gtts": "gu",
        "xlit": "gu",
        "label": "Gujarati",
        "script": "ગુજરાતી",
    },
    "odia": {
        "flores": "ory_Orya",
        "gtts": "or",
        "xlit": "or",
        "label": "Odia",
        "script": "ଓଡ଼ିଆ",
    },
    "assamese": {
        "flores": "asm_Beng",
        "gtts": "as",
        "xlit": "as",
        "label": "Assamese",
        "script": "অসমীয়া",
    },
}

# Source language (English)
SOURCE_LANG_FLORES = "eng_Latn"


def get_language(lang_key: str) -> Optional[dict]:
    """Get language config by key (lowercase name)."""
    return LANGUAGES.get(lang_key.lower())


def get_flores_code(lang_key: str) -> Optional[str]:
    """Get FLORES-200 language code for NLLB / IndicTrans2 model."""
    lang = get_language(lang_key)
    return lang["flores"] if lang else None


def get_gtts_code(lang_key: str) -> Optional[str]:
    """Get gTTS language code for text-to-speech."""
    lang = get_language(lang_key)
    return lang["gtts"] if lang else None


def get_xlit_code(lang_key: str) -> Optional[str]:
    """Get transliteration engine language code."""
    lang = get_language(lang_key)
    return lang["xlit"] if lang else None


def get_all_language_keys() -> list[str]:
    """Return all supported language keys."""
    return list(LANGUAGES.keys())


def get_language_choices() -> list[dict]:
    """Return language list suitable for frontend dropdown."""
    return [
        {
            "key": key,
            "label": info["label"],
            "script": info["script"],
        }
        for key, info in LANGUAGES.items()
    ]
