"""
OCR Processor
=============
Extracts text from images using EasyOCR.
"""

import logging
from typing import Optional

import numpy as np

logger = logging.getLogger(__name__)


EASYOCR_LANG_MAP = {
    "hindi": "hi",
    "marathi": "mr",
    "tamil": "ta",
    "telugu": "te",
    "kannada": "kn",
    "bengali": "bn",
    "english": "en",
}


class OCRProcessor:
    """
    Extracts text from images using EasyOCR.

    Usage:
        ocr = OCRProcessor()
        ocr.load()
        text = ocr.extract_text(image_bytes)
    """

    def __init__(self, languages: list[str] = None):
        self.languages = languages or ["en"]
        self._readers: dict[tuple[str, ...], any] = {}
        self._reader = None
        self._loaded = False

    def load(self) -> None:
        """Mark OCR processor ready (readers initialized on first OCR request)."""
        self._loaded = True
        logger.info("OCR processor ready (lazy initialization on first request).")

    def _get_reader_for_lang(self, target_lang: Optional[str] = None):
        """Get or initialize reader for specific language."""
        if not self._loaded:
            return None
        ocr_lang = EASYOCR_LANG_MAP.get(target_lang.lower()) if target_lang else "en"
        langs_tuple = tuple(sorted(set(["en", ocr_lang])))
        if langs_tuple in self._readers:
            return self._readers[langs_tuple]
        try:
            import easyocr
            logger.info(f"Initializing EasyOCR reader for {langs_tuple}...")
            reader = easyocr.Reader(list(langs_tuple), gpu=False)
            self._readers[langs_tuple] = reader
            if self._reader is None:
                self._reader = reader
            return reader
        except Exception as e:
            logger.warning(f"Failed to load reader for {langs_tuple}, falling back: {e}")
            return self._reader

    def extract_text(self, image_bytes: bytes, target_lang: Optional[str] = None) -> str:
        """
        Extract text from an image.

        Args:
            image_bytes: Raw bytes of the image file.
            target_lang: Optional language hint for OCR optimization.

        Returns:
            Extracted text as a single string with lines joined.
        """
        if not self._loaded:
            raise RuntimeError("OCR reader not loaded. Call .load() first.")

        reader = self._get_reader_for_lang(target_lang) or self._reader
        if reader is None:
            raise RuntimeError("OCR reader is unavailable.")

        try:
            # Convert bytes to numpy array
            nparr = np.frombuffer(image_bytes, np.uint8)

            # Use OpenCV if available, otherwise PIL
            try:
                import cv2
                img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            except ImportError:
                from PIL import Image
                import io
                img = Image.open(io.BytesIO(image_bytes))
                img = np.array(img)

            # Run OCR — detail=0 returns just the text strings
            results = self._reader.readtext(img, detail=0)

            # Join all detected text lines
            extracted_text = "\n".join(results)
            logger.info(f"OCR extracted {len(results)} text segments.")
            return extracted_text.strip()

        except Exception as e:
            logger.error(f"OCR text extraction failed: {e}")
            raise RuntimeError(f"Failed to extract text from image: {e}")

    def extract_text_with_confidence(
        self, image_bytes: bytes
    ) -> list[dict]:
        """
        Extract text with bounding boxes and confidence scores.

        Returns:
            List of dicts with keys: text, confidence, bbox
        """
        if not self._loaded or self._reader is None:
            raise RuntimeError("OCR reader not loaded. Call .load() first.")

        try:
            nparr = np.frombuffer(image_bytes, np.uint8)

            try:
                import cv2
                img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            except ImportError:
                from PIL import Image
                import io
                img = Image.open(io.BytesIO(image_bytes))
                img = np.array(img)

            results = self._reader.readtext(img, detail=1)

            return [
                {
                    "text": result[1],
                    "confidence": float(result[2]),
                    "bbox": result[0],
                }
                for result in results
            ]

        except Exception as e:
            logger.error(f"OCR extraction with confidence failed: {e}")
            raise RuntimeError(f"Failed to extract text from image: {e}")

    @property
    def is_loaded(self) -> bool:
        return self._loaded
