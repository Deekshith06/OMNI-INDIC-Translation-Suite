import logging
from typing import List
from ai4bharat.transliteration import XlitEngine
from .phonetic_mapper import PhoneticMapper
from .config import DEFAULT_BEAM_WIDTH, RESCORE

logger = logging.getLogger(__name__)

class TransliterationEngineV3:
    def __init__(self, beam_width: int = DEFAULT_BEAM_WIDTH, rescore: bool = RESCORE):
        self.beam_width = beam_width
        self.rescore = rescore
        self._engine = None
        self._loaded = False
        self.phonetic_mapper = PhoneticMapper()

    def load(self):
        if self._loaded: return
        try:
            import torch
            import argparse
            if hasattr(torch.serialization, 'add_safe_globals'):
                torch.serialization.add_safe_globals([argparse.Namespace])
                
            self._engine = XlitEngine(beam_width=self.beam_width, rescore=self.rescore)
            self._loaded = True
            logger.info("IndicXlit V3 Engine loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load IndicXlit: {e}")

    def transliterate_word(self, word: str, lang_code: str, topk: int = 5) -> List[str]:
        if not self._loaded:
            return [self.phonetic_mapper.map_word(word, lang_code)]
        try:
            res = self._engine.translit_word(word, lang_code=lang_code, topk=topk)
            if isinstance(res, dict) and lang_code in res:
                return res[lang_code]
            elif isinstance(res, list):
                return res
        except Exception as e:
            logger.error(f"Word translit error: {e}")
        return [self.phonetic_mapper.map_word(word, lang_code)]

    def transliterate_sentence(self, text: str, lang_code: str) -> str:
        if not self._loaded:
            words = text.split()
            return " ".join([self.phonetic_mapper.map_word(w, lang_code) for w in words])
        try:
            return self._engine.translit_sentence(text, lang_code=lang_code)
        except Exception as e:
            logger.error(f"Sentence translit error: {e}")
            words = text.split()
            return " ".join([self.transliterate_word(w, lang_code, 1)[0] for w in words])
