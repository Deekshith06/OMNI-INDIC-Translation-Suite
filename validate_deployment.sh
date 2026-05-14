#!/bin/bash
# ==============================================================================
# validate_deployment.sh — Pre-deployment validation for Omni-Indic v2.0.0
#
# Usage:
#   chmod +x validate_deployment.sh
#   ./validate_deployment.sh
#
# Exit code 0 only if ALL checks pass.
# ==============================================================================

set -euo pipefail

PASS=0
FAIL=1
OVERALL=0

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_pass() { echo -e "  ${GREEN}✓ PASS${NC}  $1"; }
log_fail() { echo -e "  ${RED}✗ FAIL${NC}  $1"; OVERALL=1; }
log_info() { echo -e "  ${YELLOW}ℹ INFO${NC}  $1"; }
section()  { echo -e "\n${YELLOW}══ $1 ══${NC}"; }

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║     Omni-Indic v2.0.0 — Pre-Deployment Validation           ║"
echo "╚══════════════════════════════════════════════════════════════╝"


# ── Python version ────────────────────────────────────────────────────────────
section "Python Environment"
PY_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
PY_MAJOR=$(echo "$PY_VERSION" | cut -d. -f1)
PY_MINOR=$(echo "$PY_VERSION" | cut -d. -f2)
if [ "$PY_MAJOR" -eq 3 ] && [ "$PY_MINOR" -ge 10 ]; then
    log_pass "Python $PY_VERSION (3.10+ required)"
else
    log_fail "Python $PY_VERSION — need 3.10+. Install from python.org"
fi


# ── Required pip packages ─────────────────────────────────────────────────────
section "Python Packages"
REQUIRED_PACKAGES=(
    "fastapi"
    "uvicorn"
    "torch"
    "transformers"
    "sentencepiece"
    "easyocr"
    "fitz"         # PyMuPDF
    "gtts"
    "psutil"
    "numpy"
    "PIL"          # Pillow
)

for pkg in "${REQUIRED_PACKAGES[@]}"; do
    if python3 -c "import $pkg" 2>/dev/null; then
        VERSION=$(python3 -c "import importlib.metadata; print(importlib.metadata.version('$pkg'))" 2>/dev/null || echo "?")
        log_pass "$pkg ($VERSION)"
    else
        log_fail "$pkg not installed — run: pip install -r api/requirements.txt"
    fi
done


# ── RAM check ─────────────────────────────────────────────────────────────────
section "System Resources"
AVAILABLE_MB=$(python3 -c "import psutil; print(psutil.virtual_memory().available // (1024*1024))" 2>/dev/null || echo "0")
TOTAL_MB=$(python3 -c "import psutil; print(psutil.virtual_memory().total // (1024*1024))" 2>/dev/null || echo "0")

if [ "$AVAILABLE_MB" -ge 1200 ]; then
    log_pass "RAM: ${AVAILABLE_MB} MB available / ${TOTAL_MB} MB total (need ≥1200 MB for INT8)"
elif [ "$AVAILABLE_MB" -ge 820 ]; then
    log_info "RAM: ${AVAILABLE_MB} MB — marginal; use QUANTIZE=int8 and DEMO_MODE carefully"
else
    log_fail "RAM: only ${AVAILABLE_MB} MB available — need ≥820 MB for INT8 mode"
fi


# ── Disk space ────────────────────────────────────────────────────────────────
FREE_GB=$(df -BG . | awk 'NR==2 {gsub("G",""); print $4}')
if [ "${FREE_GB:-0}" -ge 2 ]; then
    log_pass "Disk: ${FREE_GB} GB free (need ≥2 GB)"
else
    log_fail "Disk: only ${FREE_GB:-?} GB free — need ≥2 GB for model weights"
fi


# ── Port availability ─────────────────────────────────────────────────────────
section "Network"
PORT=${PORT:-8000}
if lsof -Pi :"$PORT" -sTCP:LISTEN -t >/dev/null 2>&1; then
    log_fail "Port $PORT is already in use — stop the conflicting process first"
else
    log_pass "Port $PORT is available"
fi


# ── Environment file ──────────────────────────────────────────────────────────
section "Configuration"
if [ -f "api/.env" ]; then
    log_pass ".env file found at api/.env"
elif [ -f ".env" ]; then
    log_pass ".env file found at .env"
else
    log_fail ".env file not found — copy api/.env.example to api/.env and configure"
fi


# ── Critical source files ─────────────────────────────────────────────────────
section "Source Files"
REQUIRED_FILES=(
    "ml_engine/__init__.py"
    "ml_engine/language_config.py"
    "ml_engine/translator.py"
    "ml_engine/transliterator.py"
    "ml_engine/ocr_processor.py"
    "ml_engine/pdf_processor.py"
    "ml_engine/health_check.py"
    "api/main.py"
    "api/requirements.txt"
    "api/routers/translate.py"
    "api/routers/tts.py"
)

for f in "${REQUIRED_FILES[@]}"; do
    if [ -f "$f" ]; then
        SIZE=$(wc -c < "$f")
        log_pass "$f (${SIZE} bytes)"
    else
        log_fail "$f — MISSING"
    fi
done


# ── Language config check (11 languages) ──────────────────────────────────────
section "Language Configuration"
LANG_COUNT=$(python3 -c "
from ml_engine.language_config import LANGUAGES
print(len(LANGUAGES))
" 2>/dev/null || echo "0")

if [ "$LANG_COUNT" -ge 11 ]; then
    log_pass "Language config has $LANG_COUNT languages (≥11 required)"
else
    log_fail "Language config only has $LANG_COUNT languages — expected 11"
fi


# ── Model import smoke test ───────────────────────────────────────────────────
section "Module Import Test"
if python3 -c "
from ml_engine.translator import TranslationEngine, preflight_ram_check
from ml_engine.transliterator import TransliterationEngine
from ml_engine.ocr_processor import OCRProcessor
from ml_engine.pdf_processor import PDFProcessor
print('All modules imported successfully')
" 2>/dev/null; then
    log_pass "All ml_engine modules importable"
else
    log_fail "ml_engine import failed — check PYTHONPATH and dependencies"
fi


# ── Summary ───────────────────────────────────────────────────────────────────
echo ""
echo "══════════════════════════════════════════════════════════════"
if [ "$OVERALL" -eq 0 ]; then
    echo -e "  ${GREEN}ALL CHECKS PASSED${NC} — safe to deploy"
else
    echo -e "  ${RED}SOME CHECKS FAILED${NC} — fix issues above before deploying"
fi
echo "══════════════════════════════════════════════════════════════"
echo ""

exit $OVERALL
