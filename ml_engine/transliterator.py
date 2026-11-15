"""
Transliteration Engine
======================
Handles Roman (English/Tinglish) → Indic script conversion
using AI4Bharat's IndicXlit engine, with Aksharamukha as offline fallback.

v2.0.0 Upgrades:
  • Added Aksharamukha rule-based fallback (zero-dependency, works offline)
  • Added libindic-transliteration as secondary fallback layer
  • Preserved all existing method signatures for backward compatibility

API Contract (UNCHANGED):
  TransliterationEngine().load()
  TransliterationEngine().transliterate(text: str, target_lang: str) -> str
  TransliterationEngine().get_candidates(word: str, target_lang: str) -> list[str]
"""

import logging
from typing import Optional

from .language_config import get_xlit_code

logger = logging.getLogger(__name__)

__all__ = ["TransliterationEngine"]

# ── Script → Aksharamukha scheme map (rule-based fallback) ────────────
#   Maps our language key to Aksharamukha's scheme identifier.
#   Reference: https://aksharamukha.appspot.com/about
AKSHARAMUKHA_SCHEME = {
    "hi":  "Devanagari",
    "mr":  "Devanagari",
    "te":  "Telugu",
    "ta":  "Tamil",
    "kn":  "Kannada",
    "ml":  "Malayalam",
    "pa":  "Gurmukhi",
    "bn":  "Bengali",
    "gu":  "Gujarati",
    "or":  "Oriya",
    "as":  "Assamese",
}


class TransliterationEngine:
    """
    Transliterates English/Tinglish text into Indic scripts.

    Fallback chain (in order):
      1. AI4Bharat IndicXlit (neural, highest quality)
      2. Aksharamukha rule-based (offline, zero-RAM, good coverage)
      3. libindic-transliteration (pure Python, lightweight)
      4. Passthrough (return original text unchanged)

    Usage:
        engine = TransliterationEngine()
        engine.load()
        result = engine.transliterate("namaste", "hindi")
        # → "नमस्ते"
    """

    def __init__(self, beam_width: int = 10, rescore: bool = False):
        self.beam_width = beam_width
        self.rescore = rescore
        self._engine: Optional[object] = None
        self._loaded: bool = False
        self._fallback_mode: str = "passthrough"

    # ── Lifecycle ──────────────────────────────────────────────────────

    def load(self) -> None:
        """
        Load the IndicXlit engine. Falls back gracefully if unavailable.
        Call once at startup.
        """
        if self._loaded:
            logger.info("Transliteration engine already loaded.")
            return

        # Layer 1: IndicXlit (neural)
        try:
            from ai4bharat.transliteration import XlitEngine
            import torch
            import argparse
            if hasattr(torch.serialization, 'add_safe_globals'):
                torch.serialization.add_safe_globals([argparse.Namespace])

            logger.info("Loading IndicXlit transliteration engine...")
            self._engine = XlitEngine(
                beam_width=self.beam_width,
                rescore=self.rescore,
            )
            self._loaded = True
            self._fallback_mode = "indic_xlit"
            logger.info("IndicXlit loaded successfully.")
            return
        except ImportError:
            logger.warning(
                "ai4bharat-transliteration not installed — trying Aksharamukha fallback."
            )
        except Exception as e:
            logger.error("IndicXlit load failed: %s — trying Aksharamukha fallback.", e)

        # Layer 2: Aksharamukha rule-based (offline)
        try:
            import aksharamukha  # type: ignore # noqa: F401
            self._fallback_mode = "aksharamukha"
            self._loaded = True
            logger.info("Aksharamukha fallback loaded successfully.")
            return
        except ImportError:
            logger.warning("aksharamukha not installed — trying libindic fallback.")

        # Layer 3: libindic-transliteration
        try:
            from libindic.transliteration import Transliterator  # type: ignore # noqa: F401
            self._fallback_mode = "libindic"
            self._loaded = True
            logger.info("libindic fallback loaded successfully.")
            return
        except ImportError:
            logger.warning(
                "No transliteration library available. "
                "Transliteration will pass through original text."
            )
            self._fallback_mode = "passthrough"
            self._loaded = False

    # ── Core transliteration ───────────────────────────────────────────

    def transliterate(self, text: str, target_lang: str, topk: int = 1) -> str:
        """
        Transliterate English/Tinglish text to Indic script.

        Args:
            text:        Input text in Roman script.
            target_lang: Target language key (e.g., "telugu", "hindi").
            topk:        Number of candidate transliterations per word
                         (only meaningful for IndicXlit backend).

        Returns:
            Transliterated text in the target Indic script,
            or original text if no engine is available.
        """
        lang_code = get_xlit_code(target_lang)
        if not lang_code:
            raise ValueError(f"Unsupported target language: {target_lang}")

        if self._fallback_mode == "indic_xlit" and self._engine is not None:
            return self._transliterate_indic_xlit(text, lang_code, topk)

        if self._fallback_mode == "aksharamukha":
            return self._transliterate_aksharamukha(text, lang_code)

        if self._fallback_mode == "libindic":
            return self._transliterate_libindic(text, lang_code)

        # Passthrough
        logger.warning("No transliteration engine available. Returning original text.")
        return text

    # ── Backend implementations ────────────────────────────────────────

    def _transliterate_indic_xlit(
        self, text: str, lang_code: str, topk: int
    ) -> str:
        """Use AI4Bharat IndicXlit (neural beam-search)."""
        try:
            result = self._engine.translit_sentence(text, lang_code=lang_code)
            return result
        except Exception as e:
            logger.error("IndicXlit sentence transliteration failed: %s", e)
            return self._word_by_word_fallback(text, lang_code, topk)

    def _transliterate_aksharamukha(self, text: str, lang_code: str) -> str:
        """Use Aksharamukha rule-based transliteration (offline, zero-RAM)."""
        try:
            from aksharamukha import transliterate as aksh_translit  # type: ignore
            target_scheme = AKSHARAMUKHA_SCHEME.get(lang_code, "Devanagari")
            return aksh_translit.process("ITRANS", target_scheme, text)
        except Exception as e:
            logger.error("Aksharamukha transliteration failed: %s", e)
            return text

    def _transliterate_libindic(self, text: str, lang_code: str) -> str:
        """Use libindic-transliteration as tertiary fallback."""
        try:
            from libindic.transliteration import Transliterator  # type: ignore
            t = Transliterator()
            # libindic maps ISO 639-1 code → its internal name
            return t.transliterate(text, "en", lang_code)
        except Exception as e:
            logger.error("libindic transliteration failed: %s", e)
            return text

    def _word_by_word_fallback(
        self, text: str, lang_code: str, topk: int
    ) -> str:
        """Fallback: transliterate word by word using IndicXlit."""
        words = text.split()
        transliterated_words: list[str] = []

        for word in words:
            try:
                candidates = self._engine.translit_word(
                    word, lang_code=lang_code, topk=topk
                )
                if isinstance(candidates, dict) and lang_code in candidates:
                    transliterated_words.append(candidates[lang_code][0])
                elif isinstance(candidates, list) and candidates:
                    transliterated_words.append(candidates[0])
                else:
                    transliterated_words.append(word)
            except Exception:
                transliterated_words.append(word)

        return " ".join(transliterated_words)

    # ── Utility ────────────────────────────────────────────────────────

    def get_candidates(
        self, word: str, target_lang: str, topk: int = 5
    ) -> list[str]:
        """
        Get top-k transliteration candidates for a single word.

        Returns:
            List of candidate transliterations.
        """
        lang_code = get_xlit_code(target_lang)
        if not lang_code or self._fallback_mode != "indic_xlit" or self._engine is None:
            return [word]

        try:
            candidates = self._engine.translit_word(
                word, lang_code=lang_code, topk=topk
            )
            if isinstance(candidates, dict) and lang_code in candidates:
                return candidates[lang_code]
            elif isinstance(candidates, list):
                return candidates
            return [word]
        except Exception as e:
            logger.error("Candidate generation failed: %s", e)
            return [word]

    @property
    def is_loaded(self) -> bool:
        """True if any transliteration backend was successfully loaded."""
        return self._loaded

    @property
    def backend(self) -> str:
        """Name of the active transliteration backend."""
        return self._fallback_mode
