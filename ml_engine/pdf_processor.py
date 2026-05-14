"""
PDF Processor
=============
Extracts text from PDF documents using PyMuPDF (fitz).
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


class PDFProcessor:
    """
    Extracts text content from PDF files.

    Usage:
        pdf = PDFProcessor()
        text = pdf.extract_text(pdf_bytes)
    """

    def extract_text(self, pdf_bytes: bytes) -> str:
        """
        Extract all text from a PDF document.

        Args:
            pdf_bytes: Raw bytes of the PDF file.

        Returns:
            Concatenated text from all pages.
        """
        try:
            import fitz  # PyMuPDF

            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            text_parts = []

            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                page_text = page.get_text("text")
                if page_text.strip():
                    text_parts.append(page_text.strip())

            doc.close()

            full_text = "\n\n".join(text_parts)
            logger.info(
                f"PDF extracted text from {len(doc)} pages "
                f"({len(full_text)} characters)."
            )
            return full_text

        except ImportError:
            logger.error(
                "PyMuPDF not installed. Install with: pip install PyMuPDF"
            )
            raise RuntimeError("PyMuPDF not installed.")
        except Exception as e:
            logger.error(f"PDF text extraction failed: {e}")
            raise RuntimeError(f"Failed to extract text from PDF: {e}")

    def extract_text_by_page(self, pdf_bytes: bytes) -> list[dict]:
        """
        Extract text from each page separately.

        Returns:
            List of dicts with keys: page_number, text
        """
        try:
            import fitz

            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            pages = []

            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                page_text = page.get_text("text")
                pages.append({
                    "page_number": page_num + 1,
                    "text": page_text.strip(),
                })

            doc.close()
            return pages

        except Exception as e:
            logger.error(f"PDF page extraction failed: {e}")
            raise RuntimeError(f"Failed to extract pages from PDF: {e}")

    def get_page_count(self, pdf_bytes: bytes) -> int:
        """Get the number of pages in a PDF."""
        try:
            import fitz

            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            count = len(doc)
            doc.close()
            return count
        except Exception as e:
            logger.error(f"Failed to count PDF pages: {e}")
            return 0
