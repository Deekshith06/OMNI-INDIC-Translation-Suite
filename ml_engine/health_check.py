"""
Health Check
============
Standalone pre-deployment validation script for Omni-Indic.

Run with:
    python -m ml_engine.health_check

Exit code 0 = all checks passed.
Exit code 1 = one or more checks failed.

Output: JSON report to stdout.
"""

import json
import os
import sys
import time
from pathlib import Path
from typing import Any

# ── Add project root to path so ml_engine is importable standalone ────
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def _check(name: str, fn) -> dict[str, Any]:
    """Run a single check function, capture pass/fail/error."""
    start = time.monotonic()
    try:
        detail = fn()
        elapsed = round(time.monotonic() - start, 3)
        return {"name": name, "status": "pass", "detail": detail, "elapsed_s": elapsed}
    except Exception as e:
        elapsed = round(time.monotonic() - start, 3)
        return {"name": name, "status": "fail", "detail": str(e), "elapsed_s": elapsed}


# ── Individual checks ──────────────────────────────────────────────────

def check_python_version() -> str:
    v = sys.version_info
    if v.major != 3 or v.minor < 9:
        raise RuntimeError(f"Python 3.9+ required, got {v.major}.{v.minor}.{v.micro}")
    return f"Python {v.major}.{v.minor}.{v.micro} ✓"


def check_torch() -> str:
    import torch
    device = "CUDA" if torch.cuda.is_available() else "CPU"
    return f"PyTorch {torch.__version__}, device={device} ✓"


def check_transformers() -> str:
    import transformers
    return f"transformers {transformers.__version__} ✓"


def check_ram() -> str:
    import psutil
    vm = psutil.virtual_memory()
    available_mb = vm.available // (1024 * 1024)
    total_mb = vm.total // (1024 * 1024)
    if available_mb < 1200:
        raise RuntimeError(
            f"Only {available_mb} MB available. "
            "IndicTrans2-200M INT8 requires ~820 MB; FP32 requires ~1600 MB."
        )
    return f"RAM: {available_mb} MB available / {total_mb} MB total ✓"


def check_disk_space() -> str:
    import shutil
    stat = shutil.disk_usage(PROJECT_ROOT)
    free_gb = stat.free / (1024 ** 3)
    if free_gb < 2.0:
        raise RuntimeError(
            f"Only {free_gb:.1f} GB disk free. "
            "IndicTrans2-200M needs ~820 MB; recommend ≥2 GB free."
        )
    return f"Disk: {free_gb:.1f} GB free ✓"


def check_language_config() -> str:
    from ml_engine.language_config import LANGUAGES, get_flores_code, get_gtts_code, get_xlit_code
    EXPECTED_LANGUAGES = [
        "telugu", "tamil", "kannada", "malayalam",
        "marathi", "punjabi", "hindi",
        "bengali", "gujarati", "odia", "assamese",
    ]
    missing = [l for l in EXPECTED_LANGUAGES if l not in LANGUAGES]
    if missing:
        raise RuntimeError(f"Missing language entries: {missing}")
    # Validate each language has required keys
    for lang in EXPECTED_LANGUAGES:
        flores = get_flores_code(lang)
        gtts = get_gtts_code(lang)
        xlit = get_xlit_code(lang)
        if not all([flores, gtts, xlit]):
            raise RuntimeError(
                f"Language '{lang}' has incomplete config: "
                f"flores={flores}, gtts={gtts}, xlit={xlit}"
            )
    return f"All {len(EXPECTED_LANGUAGES)} languages configured ✓"


def check_fastapi() -> str:
    import fastapi
    import uvicorn
    return f"FastAPI {fastapi.__version__}, uvicorn {uvicorn.__version__} ✓"


def check_easyocr() -> str:
    try:
        import easyocr  # noqa: F401
        return "EasyOCR importable ✓"
    except ImportError:
        raise RuntimeError("easyocr not installed — run: pip install easyocr")


def check_pymupdf() -> str:
    try:
        import fitz
        return f"PyMuPDF {fitz.__version__} ✓"
    except ImportError:
        raise RuntimeError("PyMuPDF not installed — run: pip install PyMuPDF")


def check_gtts() -> str:
    try:
        import gtts  # noqa: F401
        return "gTTS importable ✓"
    except ImportError:
        raise RuntimeError("gTTS not installed — run: pip install gTTS")


def check_psutil() -> str:
    import psutil
    return f"psutil {psutil.__version__} ✓"


def check_demo_mode_env() -> str:
    demo = os.environ.get("DEMO_MODE", "true").lower()
    model = os.environ.get("TRANSLATION_MODEL", "ai4bharat/indictrans2-en-indic-dist-200M")
    quantize = os.environ.get("QUANTIZE", "fp32")
    return f"DEMO_MODE={demo}, MODEL={model}, QUANTIZE={quantize} ✓"


def check_model_ram_estimate() -> str:
    """Verify the selected model's RAM fits within 80% of available RAM."""
    from ml_engine.translator import MODEL_RAM_REQUIREMENTS_MB, RAM_HEADROOM_FACTOR
    import psutil

    model_name = os.environ.get(
        "TRANSLATION_MODEL", "ai4bharat/indictrans2-en-indic-dist-200M"
    )
    quantize = os.environ.get("QUANTIZE", "fp32").lower()
    precision = "int8" if quantize == "int8" else "fp32"

    available_mb = psutil.virtual_memory().available // (1024 * 1024)
    requirements = MODEL_RAM_REQUIREMENTS_MB.get(model_name, {})
    required_mb = requirements.get(precision, 4000)
    headroom_mb = int(available_mb * RAM_HEADROOM_FACTOR)

    if required_mb > headroom_mb:
        raise RuntimeError(
            f"Model {model_name} [{precision.upper()}] needs ~{required_mb} MB "
            f"but only {headroom_mb} MB headroom available. "
            f"Enable INT8 (QUANTIZE=int8) or reduce load."
        )
    return (
        f"Model RAM estimate: {required_mb} MB [{precision.upper()}] "
        f"fits within {headroom_mb} MB headroom ✓"
    )


# ── Main entry point ───────────────────────────────────────────────────

def run_health_check() -> int:
    """Run all checks and return exit code (0=pass, 1=fail)."""
    checks = [
        _check("python_version",       check_python_version),
        _check("torch_device",         check_torch),
        _check("transformers",         check_transformers),
        _check("psutil",               check_psutil),
        _check("ram_available",        check_ram),
        _check("disk_space",           check_disk_space),
        _check("language_config_11",   check_language_config),
        _check("fastapi_uvicorn",      check_fastapi),
        _check("easyocr",              check_easyocr),
        _check("pymupdf",              check_pymupdf),
        _check("gtts",                 check_gtts),
        _check("env_variables",        check_demo_mode_env),
        _check("model_ram_estimate",   check_model_ram_estimate),
    ]

    all_pass = all(c["status"] == "pass" for c in checks)
    report = {
        "status": "pass" if all_pass else "fail",
        "total_checks": len(checks),
        "passed": sum(1 for c in checks if c["status"] == "pass"),
        "failed": sum(1 for c in checks if c["status"] == "fail"),
        "checks": checks,
    }

    print(json.dumps(report, indent=2))
    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(run_health_check())
