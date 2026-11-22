# Production Backend Container for Hugging Face Spaces (Docker SDK, 16 GB RAM free tier)
# Also compatible with Google Cloud Run, Railway, and Render (respects $PORT, defaults to 7860).

FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    HF_HOME=/app/model_cache \
    FORENSICS_MODEL_CACHE_DIR=/app/model_cache \
    FORENSICS_DEMO_SAMPLES_DIR=/app/demo_samples \
    FORENSICS_LOCAL_FILES_ONLY=true \
    PORT=7860

# Minimal native runtime libraries for OpenCV & Pillow
RUN apt-get update && apt-get install -y --no-install-recommends \
    libglib2.0-0 \
    libgl1 \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Hugging Face Spaces runs containers as non-root UID 1000
RUN useradd -m -u 1000 user
WORKDIR /app

# Install lean CPU-only PyTorch wheels first (saves ~2.5 GB vs CUDA wheels on CPU Spaces)
COPY backend/requirements.txt /app/requirements.txt
RUN pip install --upgrade pip && \
    pip install --index-url https://download.pytorch.org/whl/cpu torch torchvision && \
    pip install -r /app/requirements.txt

# Copy backend code and curated live-demo samples
COPY backend/app /app/app
COPY backend/scripts /app/scripts
COPY demo_samples /app/demo_samples

# Pre-download & cache Organika/sdxl-detector during image build for instant cold starts & offline reliability
RUN mkdir -p /app/model_cache && \
    FORENSICS_LOCAL_FILES_ONLY=false python /app/scripts/download_model.py && \
    chown -R user:user /app

USER user

EXPOSE 7860

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-7860}"]
