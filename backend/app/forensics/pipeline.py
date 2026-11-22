"""Parallel 4-layer forensic pipeline orchestrator."""

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import time
import uuid

from app.config import settings
from app.forensics.deep_model import deep_model_engine
from app.forensics.ela import analyze_ela
from app.forensics.fft import analyze_fft
from app.forensics.fusion import compute_fused_verdict
from app.forensics.metadata import analyze_metadata
from app.forensics.validator import validate_and_load_image
from app.schemas import AnalysisResponse
from app.utils.image_io import pil_to_base64_data_uri, resize_for_display

_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="forensics")


def run_forensic_pipeline(
    raw_bytes: bytes,
    filename: str = "upload.jpg",
    declared_content_type: str | None = None,
) -> AnalysisResponse:
    """Validate an uploaded image in memory and execute Layers 1-4 concurrently."""
    t_start = time.perf_counter()

    validated = validate_and_load_image(
        raw_bytes=raw_bytes,
        filename=filename,
        declared_content_type=declared_content_type,
    )

    # Dispatch Layers 1, 2A, 2B, and 3 concurrently across worker threads
    f_meta = _executor.submit(analyze_metadata, validated.raw_bytes, validated.pil_image)
    f_ela = _executor.submit(analyze_ela, validated.rgb_image, validated.info.format)
    f_fft = _executor.submit(analyze_fft, validated.rgb_image)
    f_dl = _executor.submit(deep_model_engine.analyze, validated.rgb_image)

    # Prepare normalized display copy of original image in parallel with compute
    display_orig = resize_for_display(
        validated.rgb_image, max_dim=settings.max_display_dimension
    )
    original_b64 = pil_to_base64_data_uri(display_orig, fmt="JPEG", quality=92)

    meta_res = f_meta.result()
    ela_res = f_ela.result()
    fft_res = f_fft.result()
    dl_res = f_dl.result()

    # Layer 4: Calibrated Hybrid Fusion & Verdict Engine
    verdict = compute_fused_verdict(
        meta=meta_res,
        ela=ela_res,
        fft=fft_res,
        dl=dl_res,
    )

    total_ms = round((time.perf_counter() - t_start) * 1000.0, 2)

    return AnalysisResponse(
        analysis_id=f"FNS-{uuid.uuid4().hex[:10].upper()}",
        analyzed_at_utc=datetime.now(timezone.utc).isoformat(),
        total_latency_ms=total_ms,
        ephemeral_notice="Processed strictly in RAM — zero image persistence on disk.",
        image_info=validated.info,
        original_image_b64=original_b64,
        layer1_metadata=meta_res,
        layer2_ela=ela_res,
        layer2_fft=fft_res,
        layer3_deep_learning=dl_res,
        layer4_verdict=verdict,
    )
