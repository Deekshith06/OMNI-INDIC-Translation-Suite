"""
Translation Engine
==================
NLLB-200 based translation engine for English → Indic languages.
Uses the distilled 600M parameter model for CPU-friendly inference.

v2.1.0 Fixes:
  • Reverted primary model to facebook/nllb-200-distilled-600M
    (ai4bharat/indictrans2-en-indic-dist-200M is a gated HF repo requiring login)
  • INT8 dynamic quantization via torch.quantization.quantize_dynamic (CPU only)
  • Pre-flight RAM check with MemoryError + actionable message
  • Tinglish normaliser: NFC, ZWJ/ZWNJ strip, whitespace collapse
  • FP16 on CUDA, FP32 on CPU (avoids bfloat16 fallback issues)

API Contract (UNCHANGED from v1.0.0):
  TranslationEngine().load()
  TranslationEngine().translate(text: str, target_lang: str) -> dict
    Returns: { translated_text, confidence, source_lang, target_lang }
"""

import logging
import os
import re
import unicodedata
from typing import Optional

import psutil
import torch
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

from .language_config import SOURCE_LANG_FLORES, get_flores_code

logger = logging.getLogger(__name__)

__all__ = ["TranslationEngine", "preflight_ram_check"]

# ── Model catalogue ────────────────────────────────────────────────────
#   facebook/nllb-200-distilled-600M  — open, no HF login required
#   facebook/nllb-200-distilled-1.3B  — open, better quality, needs ~6.5 GB FP32
DEFAULT_MODEL = "facebook/nllb-200-distilled-600M"
MAX_INPUT_TOKENS = 512

# Conservative RAM estimates per model × precision (MB)
MODEL_RAM_REQUIREMENTS_MB: dict[str, dict[str, int]] = {
    "facebook/nllb-200-distilled-600M": {"fp32": 3800, "int8": 1900},
    "facebook/nllb-200-distilled-1.3B": {"fp32": 6500, "int8": 3300},
    # IndicTrans2 kept for reference (requires HF login + huggingface-cli login)
    "ai4bharat/indictrans2-en-indic-dist-200M": {"fp32": 1600, "int8": 820},
    "ai4bharat/indictrans2-en-indic-1B":        {"fp32": 5000, "int8": 2600},
}
RAM_HEADROOM_FACTOR = 0.80  # Alert if model needs > 80% of available RAM


# ── Pre-flight RAM check ───────────────────────────────────────────────

def preflight_ram_check(model_name: str, precision: str = "fp32") -> None:
    """
    Validates that sufficient RAM is available before loading a model.

    Args:
        model_name: Hugging Face model ID string.
        precision:  "fp32" or "int8" — determines RAM estimate used.

    Raises:
        MemoryError: If estimated model RAM exceeds 80% of available system RAM.
    """
    available_mb = psutil.virtual_memory().available // (1024 * 1024)
    requirements = MODEL_RAM_REQUIREMENTS_MB.get(model_name, {})
    required_mb = requirements.get(precision.lower(), 4000)  # conservative default
    headroom_mb = int(available_mb * RAM_HEADROOM_FACTOR)

    if required_mb > headroom_mb:
        raise MemoryError(
            f"Insufficient RAM to load {model_name} in {precision.upper()} mode.\n"
            f"  Required:  ~{required_mb} MB\n"
            f"  Available: {available_mb} MB\n"
            f"  Headroom:  {headroom_mb} MB (80% of available)\n"
            f"  Solutions:\n"
            f"    1. Use INT8 quantization: set QUANTIZE=int8 in .env\n"
            f"    2. Upgrade to a VM with ≥{required_mb + 512} MB RAM\n"
            f"    3. Use DEMO_MODE=true and connect Colab GPU backend via ngrok"
        )

    logger.info(
        "RAM preflight PASSED — model: %s [%s], required: %d MB, available: %d MB",
        model_name, precision.upper(), required_mb, available_mb,
    )


# ── Tinglish / code-mixed normaliser ──────────────────────────────────

def _normalise_tinglish(text: str) -> str:
    """
    Light normalisation for Tinglish (code-mixed Roman-Indic) input.
    Strips zero-width joiners/non-joiners, normalises Unicode to NFC,
    and collapses repeated whitespace.
    """
    text = unicodedata.normalize("NFC", text)
    # Remove zero-width characters that confuse tokenizers
    text = text.replace("\u200b", "").replace("\u200c", "").replace("\u200d", "")
    # Collapse whitespace
    text = re.sub(r"\s+", " ", text)
    return text.strip()


# ── Translation Engine ─────────────────────────────────────────────────

class TranslationEngine:
    """
    Wrapper around NLLB-200 for English / Tinglish → Indic translation.

    Usage:
        engine = TranslationEngine()
        engine.load()
        result = engine.translate("Hello world", "telugu")
        # → {"translated_text": "హలో వరల్డ్", "confidence": 0.87, ...}

    Environment variables (optional):
        TRANSLATION_MODEL   Override the default HF model ID.
                            Must be an open (non-gated) HF repo, or already cached.
        QUANTIZE            "int8" to enable INT8 quantization (default: "fp32").
                            Recommended on CPU: halves RAM usage.
        DEMO_MODE           "true" to skip model loading entirely.
    """

    def __init__(self, model_name: str = DEFAULT_MODEL):
        env_model = os.environ.get("TRANSLATION_MODEL", "").strip()
        self.model_name = env_model if env_model else model_name
        self.quantize: str = os.environ.get("QUANTIZE", "fp32").lower()

        self.model: Optional[AutoModelForSeq2SeqLM] = None
        self.tokenizer: Optional[AutoTokenizer] = None
        self.device: str = "cuda" if torch.cuda.is_available() else "cpu"
        self._loaded: bool = False

    # ── Lifecycle ──────────────────────────────────────────────────────

    def load(self) -> None:
        """
        Load model and tokenizer into memory.
        Call once at application startup (via FastAPI lifespan).

        Raises:
            MemoryError:   If RAM is insufficient for this model + precision.
            RuntimeError:  If the model cannot be downloaded or loaded.
        """
        if self._loaded:
            logger.info("Translation model already loaded.")
            return

        precision = "int8" if self.quantize == "int8" else "fp32"
        preflight_ram_check(self.model_name, precision)

        logger.info(
            "Loading translation model: %s on %s [%s]",
            self.model_name, self.device, precision.upper(),
        )

        # Load tokenizer (prefer cached files to avoid network overhead)
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name, local_files_only=True)
        except Exception:
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)

        # Load in FP32 on CPU, FP16 on CUDA
        torch_dtype = torch.float16 if self.device == "cuda" else torch.float32
        try:
            raw_model = AutoModelForSeq2SeqLM.from_pretrained(
                self.model_name,
                dtype=torch_dtype,
                local_files_only=True,
            ).to(self.device)
        except Exception:
            raw_model = AutoModelForSeq2SeqLM.from_pretrained(
                self.model_name,
                dtype=torch_dtype,
            ).to(self.device)
        raw_model.eval()

        # Apply INT8 dynamic quantization on CPU (halves RAM, <5% BLEU loss)
        if self.quantize == "int8" and self.device == "cpu":
            try:
                self.model = torch.quantization.quantize_dynamic(
                    raw_model,
                    {torch.nn.Linear},
                    dtype=torch.qint8,
                )
                logger.info("INT8 dynamic quantization applied successfully.")
            except Exception as qe:
                logger.warning(
                    "INT8 quantization failed (%s) — falling back to FP32.", qe
                )
                self.model = raw_model
        else:
            self.model = raw_model

        self._loaded = True
        logger.info("Translation model loaded successfully.")

    # ── Core translation ───────────────────────────────────────────────

    def translate(
        self,
        text: str,
        target_lang: str,
        source_lang: str = "english",
        max_length: int = 256,
        num_beams: int = 4,
    ) -> dict:
        """
        Translate text between English and Indian languages (bidirectional).

        Args:
            text:        Input text in English, code-mixed, or Indic script.
            target_lang: Target language key (e.g., "telugu", "hindi", "english").
            source_lang: Source language key (default: "english").
            max_length:  Maximum output token length.
            num_beams:   Beam search width (4 ≈ +1.5 BLEU vs greedy, +40% latency).

        Returns:
            dict with keys: translated_text, confidence, source_lang, target_lang

        Raises:
            RuntimeError: If .load() was not called.
            ValueError:   If target_lang or source_lang is not in LANGUAGES.
        """
        if not self._loaded:
            raise RuntimeError("Model not loaded. Call .load() first.")

        target_flores = get_flores_code(target_lang)
        if not target_flores:
            raise ValueError(f"Unsupported target language: {target_lang}")

        source_flores = get_flores_code(source_lang)
        if not source_flores:
            source_flores = SOURCE_LANG_FLORES

        text = _normalise_tinglish(text)

        # NLLB-200: set source language on the tokenizer
        self.tokenizer.src_lang = source_flores

        sentences = self._split_sentences(text)
        if not sentences:
            return {
                "translated_text": "",
                "confidence": 0.0,
                "source_lang": source_lang.capitalize(),
                "target_lang": target_lang,
            }

        translated_parts: list[str] = []
        confidence_scores: list[float] = []

        device = "cuda" if torch.cuda.is_available() else self.device
        if self.model is not None and next(self.model.parameters()).device.type != device:
            self.model.to(device)

        for sentence in sentences:
            inputs = self.tokenizer(
                sentence,
                return_tensors="pt",
                truncation=True,
                max_length=MAX_INPUT_TOKENS,
                padding=True,
            ).to(device)

            # NLLB-200: use convert_tokens_to_ids for forced BOS token
            forced_bos_token_id = self.tokenizer.convert_tokens_to_ids(target_flores)

            with torch.no_grad():
                output = self.model.generate(
                    **inputs,
                    forced_bos_token_id=forced_bos_token_id,
                    max_new_tokens=max_length,
                    num_beams=num_beams,
                    num_return_sequences=1,
                    output_scores=True,
                    return_dict_in_generate=True,
                )

            decoded = self.tokenizer.batch_decode(
                output.sequences, skip_special_tokens=True
            )[0]
            translated_parts.append(decoded)
            confidence_scores.append(self._compute_confidence(output))

        full_translation = " ".join(translated_parts)
        avg_confidence = (
            sum(confidence_scores) / len(confidence_scores)
            if confidence_scores else 0.0
        )

        return {
            "translated_text": full_translation,
            "confidence": round(avg_confidence, 4),
            "source_lang": source_lang.capitalize(),
            "target_lang": target_lang,
        }

    # ── Helpers ────────────────────────────────────────────────────────

    def _split_sentences(self, text: str) -> list[str]:
        """Split text into sentences for better translation quality (supports Indic Dandas)."""
        sentences = re.split(r"(?<=[.!?\u0964\u0965])\s+", text.strip())
        return [s.strip() for s in sentences if s.strip()]

    def _compute_confidence(self, output) -> float:
        """
        Compute a confidence score from generation output.
        Uses mean of max softmax probabilities across generated tokens.
        """
        try:
            if hasattr(output, "scores") and output.scores:
                probs = []
                for score in output.scores:
                    softmax = torch.softmax(score, dim=-1)
                    max_prob = softmax.max(dim=-1).values.mean().item()
                    probs.append(max_prob)
                return sum(probs) / len(probs) if probs else 0.0
        except Exception as e:
            logger.warning("Could not compute confidence: %s", e)
        return 0.0

    @property
    def is_loaded(self) -> bool:
        """True if the model has been successfully loaded."""
        return self._loaded
