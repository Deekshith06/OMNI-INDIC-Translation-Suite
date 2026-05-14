from .romanizer import RomanizerEngine

class PostProcessor:
    """Handles all post-translation text enhancements like Romanization."""
    def __init__(self):
        self.romanizer = RomanizerEngine()
        
    def add_pronunciation(self, text: str, lang_key: str) -> dict:
        """Takes translated native text and attaches a romanized version."""
        romanized = self.romanizer.romanize(text, lang_key)
        return {
            "native_text": text,
            "romanized_text": romanized
        }
