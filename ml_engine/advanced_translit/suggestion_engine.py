from .transliteration import TransliterationEngineV3

class SuggestionEngine:
    def __init__(self, translit_engine: TransliterationEngineV3):
        self.engine = translit_engine
        
    def get_live_suggestions(self, word_prefix: str, lang_code: str, limit: int = 5) -> list:
        """
        Provides live transliteration suggestions for a typed word/prefix.
        Uses the transliteration engine's top-k beam search candidates.
        """
        if not word_prefix.strip():
            return []
        return self.engine.transliterate_word(word_prefix, lang_code, topk=limit)
