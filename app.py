"""
Omni-Indic Translation Suite — Hugging Face Spaces Deployment
==============================================================
Dual-Mode Server:
1. Gradio Web Interface (for direct browser use on Hugging Face Spaces)
2. FastAPI REST API (mounted at /api for Next.js frontend on Vercel)
"""

# IMPORTANT: spaces must be imported at the very top for Hugging Face ZeroGPU
try:
    import spaces
except ImportError:
    class _MockSpaces:
        @staticmethod
        def GPU(fn=None, duration=None):
            if fn is not None and callable(fn):
                return fn
            def decorator(func):
                return func
            return decorator
    spaces = _MockSpaces()

import io
import os
import sys
import tempfile
from pathlib import Path

# Add project root and api directories to search path
PROJECT_ROOT = Path(__file__).resolve().parent
API_DIR = PROJECT_ROOT / "api"
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(API_DIR) not in sys.path:
    sys.path.insert(0, str(API_DIR))

# Ensure real-world inference mode
os.environ["DEMO_MODE"] = "false"

import gradio as gr
from gtts import gTTS

from ml_engine.language_config import LANGUAGES, get_flores_code, get_gtts_code
from ml_engine.translator import TranslationEngine
from ml_engine.transliterator import TransliterationEngine
from ml_engine.romanization.romanizer import RomanizerEngine
from ml_engine.ocr_processor import OCRProcessor
from ml_engine.pdf_processor import PDFProcessor
from api.main import app as fastapi_app

# ── Preload ML Singletons ──────────────────────────────────────────────────────
print("Initializing Omni-Indic Engines for Hugging Face Space...")
translation_engine = TranslationEngine()
translation_engine.load()

transliteration_engine = TransliterationEngine()
transliteration_engine.load()

romanizer_engine = RomanizerEngine()
ocr_processor = OCRProcessor()
ocr_processor.load()
pdf_processor = PDFProcessor()

# Inject initialized engines into FastAPI app state for API endpoints
fastapi_app.state.translation_engine = translation_engine
fastapi_app.state.transliteration_engine = transliteration_engine
fastapi_app.state.romanizer_engine = romanizer_engine
fastapi_app.state.ocr_processor = ocr_processor
fastapi_app.state.pdf_processor = pdf_processor
fastapi_app.state.demo_mode = False
print("All engines successfully initialized!")

# Language list for Gradio dropdowns
LANG_CHOICES = [
    ("English", "english"),
    ("Telugu (తెలుగు)", "telugu"),
    ("Tamil (தமிழ்)", "tamil"),
    ("Kannada (ಕನ್ನಡ)", "kannada"),
    ("Hindi (हिन्दी)", "hindi"),
    ("Malayalam (മലയാളം)", "malayalam"),
    ("Marathi (मराठी)", "marathi"),
    ("Punjabi (ਪੰਜਾਬੀ)", "punjabi"),
    ("Bengali (বাংলা)", "bengali"),
    ("Gujarati (ગુજરાતી)", "gujarati"),
    ("Odia (ଓଡ଼ିଆ)", "odia"),
    ("Assamese (অসমীয়া)", "assamese"),
]


# ── Internal Core Processing (Undecorated to avoid nesting) ───────────────────

def _run_translation_core(text: str, source_lang: str, target_lang: str, mode: str):
    if not text or not text.strip():
        return "", "", "0.00", None

    text = text.strip()
    romanized = ""
    confidence_str = "1.00"
    audio_path = None

    if mode == "Transliterate":
        translated = transliteration_engine.transliterate(text, target_lang)
    else:
        result = translation_engine.translate(text, target_lang, source_lang=source_lang)
        translated = result["translated_text"]
        confidence_str = f"{result['confidence']:.2f}"
        if target_lang != "english":
            romanized = romanizer_engine.romanize(translated, target_lang)

    # Generate Audio via TTS
    gtts_code = get_gtts_code(target_lang)
    if gtts_code and translated:
        try:
            tts = gTTS(text=translated, lang=gtts_code, slow=False)
            temp_audio = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
            tts.save(temp_audio.name)
            audio_path = temp_audio.name
        except Exception:
            audio_path = None

    return translated, romanized, confidence_str, audio_path


# ── Gradio Handlers (Decorated with @spaces.GPU for ZeroGPU dynamic hardware) ──

@spaces.GPU(duration=60)
def process_text(text: str, source_lang: str, target_lang: str, mode: str):
    return _run_translation_core(text, source_lang, target_lang, mode)


@spaces.GPU(duration=60)
def process_document(file, source_lang: str, target_lang: str, mode: str):
    if file is None:
        return "No file uploaded.", "", "", None

    file_path = file.name if hasattr(file, "name") else str(file)
    extracted_text = ""

    try:
        with open(file_path, "rb") as f:
            file_bytes = f.read()

        if file_path.lower().endswith(".pdf"):
            extracted_text = pdf_processor.extract_text(file_bytes)
        else:
            extracted_text = ocr_processor.extract_text(file_bytes, target_lang)

        if not extracted_text.strip():
            return "No readable text found in document.", "", "", None

        translated, romanized, conf, audio = _run_translation_core(
            extracted_text, source_lang, target_lang, mode
        )
        return translated, romanized, extracted_text, audio
    except Exception as e:
        return f"Document processing error: {e}", "", "", None


# ── Gradio Interface ───────────────────────────────────────────────────────────

custom_css = """
.gradio-container { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
#title { text-align: center; margin-bottom: 8px; }
"""

with gr.Blocks(title="Omni-Indic Translation Suite") as demo:
    gr.Markdown(
        """
        # 🕉️ Omni-Indic Translation Suite
        ### Production Multimodal Neural Translation & Transliteration across 11 Indian Languages
        *Powered by NLLB-200 (600M) + Aksharamukha + gTTS + EasyOCR + PyMuPDF*
        """
    )

    with gr.Tabs():
        # Tab 1: Text Translation & Transliteration
        with gr.TabItem("📝 Text Translation"):
            with gr.Row():
                src_dropdown = gr.Dropdown(
                    choices=LANG_CHOICES, value="english", label="Source Language"
                )
                tgt_dropdown = gr.Dropdown(
                    choices=LANG_CHOICES, value="telugu", label="Target Language"
                )
                mode_radio = gr.Radio(
                    choices=["Translate", "Transliterate"],
                    value="Translate",
                    label="Mode",
                )

            with gr.Row():
                with gr.Column():
                    text_input = gr.Textbox(
                        placeholder="Enter text in English or any Indian language...",
                        lines=5,
                        label="Input Text",
                    )
                    translate_btn = gr.Button("Translate / Transliterate", variant="primary")

                with gr.Column():
                    text_output = gr.Textbox(lines=5, label="Translated Output", interactive=False)
                    romanized_output = gr.Textbox(lines=2, label="Phonetic Romanization", interactive=False)
                    confidence_output = gr.Textbox(label="Model Confidence", interactive=False)
                    audio_output = gr.Audio(label="Voice Pronunciation (TTS)", type="filepath")

            translate_btn.click(
                fn=process_text,
                inputs=[text_input, src_dropdown, tgt_dropdown, mode_radio],
                outputs=[text_output, romanized_output, confidence_output, audio_output],
            )

        # Tab 2: Document & Image Translation
        with gr.TabItem("📄 Document & Image Translation (OCR / PDF)"):
            with gr.Row():
                doc_src_dropdown = gr.Dropdown(
                    choices=LANG_CHOICES, value="english", label="Source Language"
                )
                doc_tgt_dropdown = gr.Dropdown(
                    choices=LANG_CHOICES, value="hindi", label="Target Language"
                )
                doc_mode_radio = gr.Radio(
                    choices=["Translate", "Transliterate"],
                    value="Translate",
                    label="Mode",
                )

            with gr.Row():
                with gr.Column():
                    file_input = gr.File(label="Upload Document (PDF or PNG/JPEG Image)")
                    doc_translate_btn = gr.Button("Extract & Translate", variant="primary")

                with gr.Column():
                    doc_output = gr.Textbox(lines=5, label="Translated Document Content", interactive=False)
                    doc_extracted = gr.Textbox(lines=4, label="Extracted Source Text", interactive=False)
                    doc_romanized = gr.Textbox(lines=2, label="Phonetic Pronunciation", interactive=False)
                    doc_audio = gr.Audio(label="Audio Output", type="filepath")

            doc_translate_btn.click(
                fn=process_document,
                inputs=[file_input, doc_src_dropdown, doc_tgt_dropdown, doc_mode_radio],
                outputs=[doc_output, doc_romanized, doc_extracted, doc_audio],
            )

    gr.Markdown(
        """
        ---
        **API Endpoint:** This Space also serves as the REST API backend for the Next.js frontend.
        `POST /api/translate-text` • `POST /api/translate-doc` • `POST /api/generate-tts` • `GET /healthz`
        """
    )

# Mount FastAPI onto Gradio's internal FastAPI app
demo.app.mount("/api", fastapi_app)

@demo.app.get("/healthz")
def root_healthz():
    return {"status": "ok", "service": "omni-indic", "version": "2.1.0"}

app = demo.app

if __name__ == "__main__":
    demo.queue().launch(server_name="0.0.0.0", server_port=7860)
