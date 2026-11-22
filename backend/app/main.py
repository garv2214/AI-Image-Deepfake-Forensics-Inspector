"""FastAPI entrypoint for the AI-Image & Deepfake Forensics Inspector."""

from contextlib import asynccontextmanager
import json
import logging
from pathlib import Path
from PIL import Image

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.forensics.deep_model import deep_model_engine
from app.forensics.pipeline import run_forensic_pipeline
from app.forensics.validator import ValidationError
from app.schemas import AnalysisResponse, DemoSampleItem, HealthResponse
from app.utils.image_io import pil_to_base64_data_uri

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("forensics.api")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Warm up the deep learning classifier on startup so live demos respond in <2s."""
    logger.info("Initializing forensic deep vision backbone (%s)...", settings.hf_model_id)
    try:
        deep_model_engine.load()
        # Run a tiny dummy warmup forward pass on MPS/CPU to eliminate cold-start jitter
        dummy = Image.new("RGB", (224, 224), color=(128, 128, 128))
        deep_model_engine.analyze(dummy)
        logger.info("Forensic model warmup complete.")
    except Exception as exc:
        logger.warning("Startup warmup warning: %s", exc)
    yield


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "4-Layer AI-Image & Deepfake Forensics API combining EXIF/C2PA provenance auditing, "
        "Error Level Analysis (ELA), 2D FFT spectral forensics, and Deep Vision Grad-CAM explainability."
    ),
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins + ["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


@app.exception_handler(ValidationError)
async def validation_error_handler(_request, exc: ValidationError):
    return JSONResponse(status_code=exc.status_code, content={"detail": str(exc)})


@app.get("/", tags=["System"])
async def root_status():
    """Root endpoint used by Hugging Face Spaces / cloud health probes."""
    return {
        "service": settings.app_name,
        "version": settings.app_version,
        "status": "running",
        "docs": "/docs",
        "health": "/api/health",
    }


@app.get("/api/health", response_model=HealthResponse, tags=["System"])
async def health_check() -> HealthResponse:
    """Return engine readiness, hardware accelerator, and offline cache status."""
    return HealthResponse(
        status="ok",
        version=settings.app_version,
        model_id=(
            deep_model_engine.model_id
            if deep_model_engine.backend_mode == "huggingface_transformer"
            else "resnet18-offline-fallback"
        ),
        model_loaded=deep_model_engine.is_loaded,
        backend_mode=deep_model_engine.backend_mode,
        device=str(deep_model_engine.device),
        offline_ready=deep_model_engine.offline_ready,
    )


@app.post("/api/analyze", response_model=AnalysisResponse, tags=["Forensics"])
async def analyze_image(file: UploadFile = File(...)) -> AnalysisResponse:
    """Run parallel 4-layer forensic inspection strictly in memory (zero disk persistence)."""
    raw_bytes = await file.read()
    return run_forensic_pipeline(
        raw_bytes=raw_bytes,
        filename=file.filename or "upload.jpg",
        declared_content_type=file.content_type,
    )


def _load_sample_manifest() -> list[dict]:
    samples_dir = Path(settings.demo_samples_dir)
    manifest_path = samples_dir / "manifest.json"
    if not manifest_path.exists():
        return []
    try:
        return json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception:
        return []


@app.get("/api/samples", response_model=list[DemoSampleItem], tags=["Live Demo"])
async def list_demo_samples() -> list[DemoSampleItem]:
    """List curated live-demo samples (authentic, spliced, AI-generated, re-compressed edge case)."""
    samples_dir = Path(settings.demo_samples_dir)
    manifest = _load_sample_manifest()
    items: list[DemoSampleItem] = []

    for entry in manifest:
        img_path = samples_dir / entry["filename"]
        if not img_path.exists():
            continue
        try:
            with Image.open(img_path) as im:
                thumb = im.convert("RGB")
                thumb.thumbnail((240, 240))
                thumb_b64 = pil_to_base64_data_uri(thumb, fmt="JPEG", quality=82)
            items.append(
                DemoSampleItem(
                    id=entry["id"],
                    title=entry["title"],
                    category=entry["category"],
                    description=entry["description"],
                    expected_signal=entry["expected_signal"],
                    filename=entry["filename"],
                    thumbnail_b64=thumb_b64,
                )
            )
        except Exception:
            continue

    return items


@app.post("/api/samples/{sample_id}/analyze", response_model=AnalysisResponse, tags=["Live Demo"])
async def analyze_demo_sample(sample_id: str) -> AnalysisResponse:
    """One-click analysis of a bundled live-demo case study."""
    samples_dir = Path(settings.demo_samples_dir)
    manifest = _load_sample_manifest()
    match = next((m for m in manifest if m["id"] == sample_id), None)
    if not match:
        raise HTTPException(status_code=404, detail=f"Demo sample '{sample_id}' not found.")

    img_path = samples_dir / match["filename"]
    if not img_path.exists():
        raise HTTPException(status_code=404, detail="Sample file missing on disk.")

    raw_bytes = img_path.read_bytes()
    return run_forensic_pipeline(
        raw_bytes=raw_bytes,
        filename=match["filename"],
        declared_content_type=None,
    )
