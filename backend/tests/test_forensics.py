"""Unit and API integration tests for the 4-layer forensic pipeline."""

import io
from pathlib import Path
import sys

import numpy as np
import piexif
import pytest
from fastapi.testclient import TestClient
from PIL import Image, PngImagePlugin

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.forensics.ela import analyze_ela
from app.forensics.fft import analyze_fft
from app.forensics.metadata import analyze_metadata
from app.forensics.validator import ValidationError, validate_and_load_image
from app.main import app


def _make_jpeg_bytes(arr: np.ndarray, quality: int = 92, exif: bytes | None = None) -> bytes:
    buf = io.BytesIO()
    img = Image.fromarray(arr.astype(np.uint8), mode="RGB")
    kwargs = {"format": "JPEG", "quality": quality}
    if exif:
        kwargs["exif"] = exif
    img.save(buf, **kwargs)
    return buf.getvalue()


def test_validator_rejects_corrupt_and_non_image():
    with pytest.raises(ValidationError) as exc_empty:
        validate_and_load_image(b"", "empty.jpg")
    assert exc_empty.value.status_code == 400

    with pytest.raises(ValidationError) as exc_txt:
        validate_and_load_image(b"not an image at all", "fake.jpg", "image/jpeg")
    assert exc_txt.value.status_code == 415

    with pytest.raises(ValidationError) as exc_size:
        validate_and_load_image(b"\xff\xd8\xff" + b"0" * (11 * 1024 * 1024), "huge.jpg")
    assert exc_size.value.status_code == 413


def test_layer1_metadata_camera_vs_photoshop_vs_sd():
    arr = np.full((128, 128, 3), 120, dtype=np.uint8)

    # 1. Camera EXIF
    cam_exif = piexif.dump(
        {
            "0th": {
                piexif.ImageIFD.Make: b"Canon",
                piexif.ImageIFD.Model: b"Canon EOS R5",
            },
            "Exif": {
                piexif.ExifIFD.ISOSpeedRatings: 100,
                piexif.ExifIFD.FocalLength: (50, 1),
            },
        }
    )
    raw_cam = _make_jpeg_bytes(arr, exif=cam_exif)
    pil_cam = Image.open(io.BytesIO(raw_cam))
    rep_cam = analyze_metadata(raw_cam, pil_cam)
    assert rep_cam.has_camera_signature is True
    assert rep_cam.provenance_status == "camera_signature_present"

    # 2. Photoshop Editing Footprint
    ps_exif = piexif.dump({"0th": {piexif.ImageIFD.Software: b"Adobe Photoshop 25.0"}})
    raw_ps = _make_jpeg_bytes(arr, exif=ps_exif)
    pil_ps = Image.open(io.BytesIO(raw_ps))
    rep_ps = analyze_metadata(raw_ps, pil_ps)
    assert rep_ps.editing_software_detected == "Adobe Photoshop"
    assert rep_ps.provenance_status == "editing_software_flagged"

    # 3. Stable Diffusion PNG Parameters
    buf = io.BytesIO()
    pnginfo = PngImagePlugin.PngInfo()
    pnginfo.add_text("parameters", "a cat in space, Steps: 20, Model: sd_xl_base_1.0")
    Image.fromarray(arr).save(buf, format="PNG", pnginfo=pnginfo)
    raw_sd = buf.getvalue()
    pil_sd = Image.open(io.BytesIO(raw_sd))
    rep_sd = analyze_metadata(raw_sd, pil_sd)
    assert rep_sd.ai_generator_detected is not None
    assert rep_sd.provenance_status == "ai_metadata_found"


def test_layer2_ela_distinguishes_spliced_hotspot():
    rng = np.random.default_rng(7)
    base = np.full((384, 384, 3), 130, dtype=np.float32) + rng.normal(0, 4, (384, 384, 3))
    raw_base = _make_jpeg_bytes(np.clip(base, 0, 255), quality=65)
    img_base = Image.open(io.BytesIO(raw_base)).convert("RGB")

    # Uniform baseline
    res_uniform = analyze_ela(img_base, "JPEG")

    # Splice a high-variance fresh patch into center
    spliced = img_base.copy()
    patch = np.clip(180 + rng.normal(0, 22, (96, 96, 3)), 0, 255).astype(np.uint8)
    spliced.paste(Image.fromarray(patch), (144, 144))
    res_spliced = analyze_ela(spliced, "JPEG")

    assert res_spliced.localized_tampering_score > res_uniform.localized_tampering_score
    assert res_spliced.hotspot_z_score > 3.0
    assert res_spliced.ela_map_b64.startswith("data:image/png;base64,")


def test_layer2_fft_detects_periodic_grid_spikes():
    yy, xx = np.mgrid[0:256, 0:256].astype(np.float32)
    grid = 128 + 30 * np.cos(2 * np.pi * xx / 8.0) * np.cos(2 * np.pi * yy / 8.0)
    rgb = np.stack([grid, grid, grid], axis=-1).astype(np.uint8)
    res = analyze_fft(Image.fromarray(rgb, mode="RGB"))
    assert res.periodic_peak_score > 0.5
    assert len(res.radial_profile) == 28
    assert res.fft_spectrum_b64.startswith("data:image/png;base64,")


def test_fastapi_endpoints_end_to_end():
    client = TestClient(app)

    health = client.get("/api/health")
    assert health.status_code == 200
    assert health.json()["status"] == "ok"

    rng = np.random.default_rng(42)
    sample = np.clip(120 + rng.normal(0, 12, (256, 256, 3)), 0, 255).astype(np.uint8)
    jpg_bytes = _make_jpeg_bytes(sample, quality=90)

    resp = client.post(
        "/api/analyze",
        files={"file": ("test_capture.jpg", jpg_bytes, "image/jpeg")},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["analysis_id"].startswith("FNS-")
    assert data["layer2_ela"]["ela_map_b64"].startswith("data:image/png;base64,")
    assert data["layer2_fft"]["fft_spectrum_b64"].startswith("data:image/png;base64,")
    assert data["layer3_deep_learning"]["gradcam_overlay_b64"].startswith("data:image/png;base64,")
    assert 0.0 <= data["layer4_verdict"]["confidence_percent"] <= 100.0
    assert len(data["layer4_verdict"]["channel_breakdown"]) == 4
