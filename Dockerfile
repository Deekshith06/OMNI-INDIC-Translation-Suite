# ==============================================================================
# Omni-Indic Translation Suite — Dockerfile
# v2.0.0 | Multi-stage CPU-optimised build
# Base: python:3.11-slim-bookworm (Ubuntu 22.04 compatible)
#
# ── Option A: Model weights baked into image (self-contained, larger image)
#    Build: docker build --target runtime -t omni-indic .
#    Run:   docker run -p 8000:8000 omni-indic
#
# ── Option B: Model weights via external volume (smaller image, faster push)
#    Build: docker build --build-arg BAKE_MODELS=false --target runtime -t omni-indic .
#    Run:   docker run -v /host/model-cache:/root/.cache/huggingface \
#                      -p 8000:8000 omni-indic
# ==============================================================================

ARG PYTHON_VERSION=3.11
ARG BAKE_MODELS=true

# ─────────────────────────────────────────────────────────────────────────────
# Stage 1: builder — install ALL Python dependencies (includes build tools)
# ─────────────────────────────────────────────────────────────────────────────
FROM python:${PYTHON_VERSION}-slim-bookworm AS builder

# System build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        gcc \
        g++ \
        libgl1-mesa-glx \
        libglib2.0-0 \
        libsm6 \
        libxext6 \
        libxrender-dev \
        libgomp1 \
        curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /install

# Copy only requirements first (layer cache optimisation)
COPY api/requirements.txt .

# Install CPU-only PyTorch to save ~2 GB vs the default CUDA build
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir \
        torch==2.3.0+cpu \
        torchvision==0.18.0+cpu \
        --index-url https://download.pytorch.org/whl/cpu && \
    pip install --no-cache-dir -r requirements.txt

# ─────────────────────────────────────────────────────────────────────────────
# Stage 2: model-downloader — pre-fetch model weights into the image
# Only runs when BAKE_MODELS=true
# ─────────────────────────────────────────────────────────────────────────────
FROM builder AS model-downloader

ARG BAKE_MODELS
ENV HF_HUB_DISABLE_PROGRESS_BARS=1 \
    TRANSFORMERS_OFFLINE=0

# Download NLLB-200-distilled-600M weights into the HF cache
# Enables fully offline, high-accuracy inference across Indian languages
RUN if [ "$BAKE_MODELS" = "true" ]; then \
      python -c "\
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer; \
model_id = 'facebook/nllb-200-distilled-600M'; \
print('Downloading tokenizer...'); \
AutoTokenizer.from_pretrained(model_id); \
print('Downloading model weights...'); \
AutoModelForSeq2SeqLM.from_pretrained(model_id); \
print('Download complete.')"; \
    fi

# ─────────────────────────────────────────────────────────────────────────────
# Stage 3: runtime — lean image, non-root user, HEALTHCHECK
# ─────────────────────────────────────────────────────────────────────────────
FROM python:${PYTHON_VERSION}-slim-bookworm AS runtime

LABEL maintainer="Deekshith Sai Kiran" \
      version="2.0.0" \
      description="Omni-Indic Translation Suite — CPU-optimised production image"

# Runtime system libraries (no build tools)
RUN apt-get update && apt-get install -y --no-install-recommends \
        libgl1-mesa-glx \
        libglib2.0-0 \
        libsm6 \
        libxext6 \
        libxrender-dev \
        libgomp1 \
        curl \
    && rm -rf /var/lib/apt/lists/*

# ── Non-root user (security best practice) ────────────────────────────────────
RUN groupadd -r omniindic && useradd -r -g omniindic -d /app omniindic

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.11 /usr/local/lib/python3.11
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy model weights from downloader (only if baked)
COPY --from=model-downloader /root/.cache/huggingface /home/omniindic/.cache/huggingface

# Copy application code
WORKDIR /app
COPY --chown=omniindic:omniindic . .

# Switch to non-root user
USER omniindic

# ── Environment defaults (override with -e or .env) ───────────────────────────
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DEMO_MODE=false \
    TRANSLATION_MODEL=facebook/nllb-200-distilled-600M \
    QUANTIZE=int8 \
    HOST=0.0.0.0 \
    PORT=8000 \
    CORS_ORIGINS="http://localhost:3000" \
    HF_HOME=/home/omniindic/.cache/huggingface \
    TRANSFORMERS_OFFLINE=1

# Expose API port
EXPOSE 8000

# ── Health check — polls /api/status every 30 s ───────────────────────────────
HEALTHCHECK --interval=30s --timeout=10s --start-period=120s --retries=3 \
    CMD curl -f http://localhost:8000/api/status | python3 -c \
        "import sys, json; d=json.load(sys.stdin); sys.exit(0 if d.get('pdf_processor') else 1)" \
    || exit 1

# ── Start the API server ──────────────────────────────────────────────────────
CMD ["sh", "-c", "cd /app/api && uvicorn main:app --host $HOST --port $PORT --workers 1"]
