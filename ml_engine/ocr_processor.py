"""
OCR Processor
=============
Extracts text from images using EasyOCR.
"""

import logging
from typing import Optional

import numpy as np

logger = logging.getLogger(__name__)


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
        self._reader = None
        self._loaded = False

    def load(self) -> None:
        """Load EasyOCR reader. Call once at startup."""
        if self._loaded:
            logger.info("OCR reader already loaded.")
            return

        try:
            import easyocr

            logger.info(f"Loading EasyOCR reader for languages: {self.languages}")
            self._reader = easyocr.Reader(self.languages, gpu=False)
            self._loaded = True
            logger.info("OCR reader loaded successfully.")
        except ImportError:
            logger.error(
                "easyocr not installed. Install with: pip install easyocr"
            )
            self._loaded = False
        except Exception as e:
            logger.error(f"Failed to load OCR reader: {e}")
            self._loaded = False

    def extract_text(self, image_bytes: bytes) -> str:
        """
        Extract text from an image.

        Args:
            image_bytes: Raw bytes of the image file.

        Returns:
            Extracted text as a single string with lines joined.
        """
        if not self._loaded or self._reader is None:
            raise RuntimeError("OCR reader not loaded. Call .load() first.")

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
