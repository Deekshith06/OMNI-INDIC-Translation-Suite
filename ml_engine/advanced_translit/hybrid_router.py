from .language_detector import LanguageDetector
from .transliteration import TransliterationEngineV3

class HybridRouter:
    """Intelligently routes requests to either Translation or Transliteration."""
    def __init__(self, translation_engine, transliteration_engine: TransliterationEngineV3):
        self.detector = LanguageDetector()
        self.translation_engine = translation_engine
        self.transliteration_engine = transliteration_engine

    def process(self, text: str, target_lang: str, mode: str = "auto") -> dict:
        """
        Process the text based on mode: 'translate', 'transliterate', or 'auto'
        """
        analysis = self.detector.analyze_mixed_content(text)
        
        selected_mode = mode
        if mode == "auto":
            if analysis["is_likely_english_sentence"]:
                selected_mode = "translate"
            else:
                selected_mode = "transliterate"
                
        if selected_mode == "translate":
            result = self.translation_engine.translate(text, target_lang)
            confidence = analysis["confidence"] if analysis["confidence"] > 0 else 0.85
            return {"result": result, "mode_used": "translate", "confidence": confidence}
        else:
            result = self.transliteration_engine.transliterate_sentence(text, target_lang)
            confidence = 1.0 - analysis["confidence"] if analysis["confidence"] < 1.0 else 0.90
            return {"result": result, "mode_used": "transliterate", "confidence": confidence}
