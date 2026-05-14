from ml_engine.translator import TranslationEngine
from .postprocessing import PostProcessor

class ExtendedTranslationPipeline:
    """Wraps Translation Engine to automatically include Post-Processing."""
    def __init__(self, translator: TranslationEngine):
        self.translator = translator
        self.postprocessor = PostProcessor()
        
    def translate_and_romanize(self, text: str, target_lang: str):
        translated = self.translator.translate(text, target_lang)
        return self.postprocessor.add_pronunciation(translated, target_lang)
