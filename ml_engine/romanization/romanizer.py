import logging
from .pronunciation_mapper import PronunciationMapper
from ml_engine.language_config import get_language

logger = logging.getLogger(__name__)

class RomanizerEngine:
    """Core engine to convert native Indic script to Romanized pronunciation."""
    def __init__(self):
        self.mapper = PronunciationMapper()
        # Map Omni-Indic internal codes to Aksharamukha scheme names
        self.aksh_scheme_map = {
            "te": "Telugu",
            "ta": "Tamil",
            "hi": "Devanagari",
            "kn": "Kannada",
            "ml": "Malayalam",
            "bn": "Bengali",
            "mr": "Devanagari",
            "gu": "Gujarati",
            "pa": "Gurmukhi",
            "or": "Oriya",
            "as": "Assamese"
        }
        try:
            from aksharamukha import transliterate # type: ignore
            self.transliterate = transliterate.process
            self._loaded = True
        except ImportError:
            logger.warning("Aksharamukha not installed. Romanizer will return empty.")
            self._loaded = False

    def romanize(self, text: str, source_lang_key: str) -> str:
        """Convert native text to romanized pronunciation."""
        if not self._loaded or not text:
            return ""
        
        lang_info = get_language(source_lang_key)
        if not lang_info:
            return ""
            
        xlit_code = lang_info["xlit"]
        scheme = self.aksh_scheme_map.get(xlit_code, "Devanagari")
        
        try:
            iso_text = self.transliterate(scheme, "ISO", text)
            return self.mapper.map_to_human(iso_text)
        except Exception as e:
            logger.error(f"Romanization failed: {e}")
            return ""
