"""Generate a curated live-demo sample suite in demo_samples/ showcasing all 4 forensic layers.

Creates 6 realistic test images:
  1. authentic_dslr_landscape.jpg      - Uniform compression + full Canon EOS R5 EXIF telemetry
  2. authentic_c2pa_street.jpg         - Natural scene + C2PA JUMBF provenance marker + Nikon EXIF
  3. spliced_photoshop_evidence.jpg    - Q72 base photo + Q99 spliced object patch + Photoshop EXIF (ELA showcase!)
  4. spliced_cloning_document.jpg      - Forged ID/receipt patch pasted at mismatched JPEG quality (ELA showcase!)
  5. ai_synthetic_diffusion_grid.png   - Synthetic smooth diffusion-style render + periodic FFT upsampling peaks + SD PNG prompt metadata
  6. edge_whatsapp_recompressed.jpg    - Authentic photo stripped of EXIF & double-compressed at Q56 (viva limitations showcase!)
"""

from __future__ import annotations

import io
import json
import os
from pathlib import Path

import cv2
import numpy as np
import piexif
from PIL import Image, ImageDraw, PngImagePlugin

ROOT = Path(__file__).resolve().parent.parent.parent
OUT_DIR = Path(os.environ.get("FORENSICS_DEMO_SAMPLES_DIR", str(ROOT / "demo_samples")))


def _make_natural_scene(width: int = 768, height: int = 512, seed: int = 42) -> np.ndarray:
    """Synthesize a rich multi-scale natural photograph-like scene with realistic 1/f texture & sensor grain."""
    rng = np.random.default_rng(seed)
    yy, xx = np.mgrid[0:height, 0:width].astype(np.float32)
    yn = yy / height
    xn = xx / width

    img = np.zeros((height, width, 3), dtype=np.float32)

    # Sky gradient (top 55%)
    sky_r = 78 + 95 * yn
    sky_g = 128 + 75 * yn
    sky_b = 198 + 38 * (1.0 - yn)
    img[:, :, 0] = sky_r
    img[:, :, 1] = sky_g
    img[:, :, 2] = sky_b

    # Rolling mountain silhouettes using multi-octave waves
    ridge1 = (
        0.48
        + 0.06 * np.sin(xn * 6.5 + seed)
        + 0.03 * np.sin(xn * 17.0 + 1.2)
        + 0.015 * np.cos(xn * 37.0)
    )
    ridge2 = (
        0.62
        + 0.05 * np.cos(xn * 5.2 + 0.7)
        + 0.025 * np.sin(xn * 13.0)
        + 0.01 * np.sin(xn * 29.0)
    )
    water_line = 0.74 + 0.008 * np.sin(xn * 20.0)

    mask_m1 = yn >= ridge1
    mask_m2 = yn >= ridge2
    mask_water = yn >= water_line

    # Distant atmospheric haze mountains
    img[mask_m1] = np.stack(
        [
            65 + 25 * (yn[mask_m1] - 0.45),
            82 + 28 * (yn[mask_m1] - 0.45),
            106 + 22 * (yn[mask_m1] - 0.45),
        ],
        axis=-1,
    )

    # Foreground pine hills
    img[mask_m2] = np.stack(
        [
            44 + 28 * np.sin(xn[mask_m2] * 40) * 0.3,
            78 + 30 * (yn[mask_m2] - 0.6),
            52 + 18 * (yn[mask_m2] - 0.6),
        ],
        axis=-1,
    )

    # Lake reflection with gentle ripples
    ripple = 8.0 * np.sin(yy[mask_water] * 0.55 + np.sin(xx[mask_water] * 0.08) * 3.0)
    img[mask_water, 0] = 56 + ripple
    img[mask_water, 1] = 92 + ripple
    img[mask_water, 2] = 128 + ripple

    # Add realistic pink (1/f) natural texture + fine CMOS sensor photon shot noise
    f_noise = rng.normal(0, 1, (height, width)).astype(np.float32)
    f_fft = np.fft.fft2(f_noise)
    fy = np.fft.fftfreq(height)[:, None]
    fx = np.fft.fftfreq(width)[None, :]
    freq_mag = np.sqrt(fx**2 + fy**2) + 1e-3
    pink = np.fft.ifft2(f_fft / np.power(freq_mag, 0.95)).real
    pink = (pink - pink.mean()) / (pink.std() + 1e-5)

    for ch in range(3):
        img[:, :, ch] += pink * 10.0 + rng.normal(0, 3.2, (height, width))

    # Soft golden sun glow
    sun_d = np.sqrt((xn - 0.76) ** 2 + (yn - 0.24) ** 2)
    glow = np.exp(-(sun_d**2) / 0.018) * 90.0
    img[:, :, 0] += glow * 1.05
    img[:, :, 1] += glow * 0.85
    img[:, :, 2] += glow * 0.45

    return np.clip(img, 0, 255).astype(np.uint8)


def _build_camera_exif(make: str, model: str, software: str, dt: str) -> bytes:
    exif_dict = {
        "0th": {
            piexif.ImageIFD.Make: make.encode("utf-8"),
            piexif.ImageIFD.Model: model.encode("utf-8"),
            piexif.ImageIFD.Software: software.encode("utf-8"),
            piexif.ImageIFD.DateTime: dt.encode("utf-8"),
        },
        "Exif": {
            piexif.ExifIFD.DateTimeOriginal: dt.encode("utf-8"),
            piexif.ExifIFD.ExposureTime: (1, 500),
            piexif.ExifIFD.FNumber: (28, 10),
            piexif.ExifIFD.ISOSpeedRatings: 200,
            piexif.ExifIFD.FocalLength: (50, 1),
            piexif.ExifIFD.LensModel: b"RF 50mm F1.8 STM",
            piexif.ExifIFD.ColorSpace: 1,
        },
        "GPS": {},
        "1st": {},
        "thumbnail": None,
    }
    return piexif.dump(exif_dict)


def _save_authentic_dslr(out_path: Path) -> None:
    arr = _make_natural_scene(768, 512, seed=11)
    img = Image.fromarray(arr, mode="RGB")
    exif_bytes = _build_camera_exif(
        make="Canon",
        model="Canon EOS R5",
        software="Canon Digital Photo Professional 4",
        dt="2026:03:14 17:42:18",
    )
    img.save(out_path, format="JPEG", quality=92, exif=exif_bytes)


def _save_authentic_c2pa(out_path: Path) -> None:
    arr = _make_natural_scene(768, 512, seed=77)
    # Add architectural foreground details
    pil = Image.fromarray(arr, mode="RGB")
    draw = ImageDraw.Draw(pil)
    draw.rectangle([90, 290, 210, 440], fill=(70, 68, 72))
    draw.rectangle([110, 315, 145, 360], fill=(195, 185, 150))
    draw.rectangle([160, 315, 195, 360], fill=(195, 185, 150))

    exif_bytes = _build_camera_exif(
        make="Nikon Corporation",
        model="NIKON Z8",
        software="Nikon Firmware 2.01",
        dt="2026:04:02 09:15:44",
    )
    buf = io.BytesIO()
    pil.save(buf, format="JPEG", quality=93, exif=exif_bytes)
    jpeg_bytes = buf.getvalue()

    # Inject a valid JPEG COM (0xFFFE) segment carrying a simulated C2PA JUMBF header marker
    payload = b"jumb\x00\x00c2pa.claim\x00claim_generator:Nikon_Z8_C2PA_Signer_v2.1"
    com_seg = b"\xff\xfe" + (len(payload) + 2).to_bytes(2, "big") + payload
    with_c2pa = jpeg_bytes[:2] + com_seg + jpeg_bytes[2:]
    out_path.write_bytes(with_c2pa)


def _save_spliced_photoshop(out_path: Path) -> None:
    """Create a textbook ELA splicing forgery: Q68 base photo + Q99 freshly pasted object patch."""
    base_arr = _make_natural_scene(768, 512, seed=21)
    base_img = Image.fromarray(base_arr, mode="RGB")

    # Save base at lower JPEG quality (simulating original photo from camera/web)
    base_buf = io.BytesIO()
    base_img.save(base_buf, format="JPEG", quality=65)
    base_buf.seek(0)
    recompressed_base = Image.open(base_buf).convert("RGB")

    # Create a high-frequency spliced object (e.g., pasted vehicle/signboard with crisp noise/detail)
    rng = np.random.default_rng(99)
    patch_h, patch_w = 136, 176
    patch = np.zeros((patch_h, patch_w, 3), dtype=np.float32)
    patch[:, :, 0] = 175
    patch[:, :, 1] = 48
    patch[:, :, 2] = 42
    # Add sharp checkerboard-like fine texture + high-variance detail that differs from Q65 base
    for y in range(0, patch_h, 4):
        patch[y : y + 2, :, :] += 18
    patch += rng.normal(0, 14.0, patch.shape)
    patch_pil = Image.fromarray(np.clip(patch, 0, 255).astype(np.uint8), mode="RGB")
    draw = ImageDraw.Draw(patch_pil)
    draw.rectangle([8, 8, patch_w - 9, patch_h - 9], outline=(245, 240, 230), width=4)
    draw.rectangle([28, 36, 148, 72], fill=(235, 232, 224))
    draw.rectangle([38, 88, 138, 108], fill=(25, 30, 42))

    # Paste onto the lower-quality background and save at high Q98 (classic Photoshop splice artifact!)
    recompressed_base.paste(patch_pil, (460, 240))

    exif_bytes = _build_camera_exif(
        make="Canon",
        model="Canon EOS 90D",
        software="Adobe Photoshop 25.4 (Macintosh)",
        dt="2026:05:19 14:20:05",
    )
    recompressed_base.save(out_path, format="JPEG", quality=98, exif=exif_bytes)


def _save_spliced_document(out_path: Path) -> None:
    """Create a tampered document / plate crop with localized copy-move/paste ELA anomaly."""
    rng = np.random.default_rng(123)
    h, w = 512, 768
    canvas = np.full((h, w, 3), 232, dtype=np.float32) + rng.normal(0, 4.0, (h, w, 3))
    img = Image.fromarray(np.clip(canvas, 0, 255).astype(np.uint8), mode="RGB")
    draw = ImageDraw.Draw(img)
    draw.rectangle([36, 36, w - 36, h - 36], outline=(40, 52, 72), width=4)
    draw.rectangle([60, 65, w - 60, 120], fill=(32, 48, 82))
    for row in range(160, 430, 44):
        draw.line([(72, row), (w - 72, row)], fill=(180, 188, 198), width=2)
        draw.rectangle([80, row - 24, 240, row - 10], fill=(75, 82, 95))
        draw.rectangle([280, row - 24, 520, row - 10], fill=(105, 112, 125))

    # Save base at Q60
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=60)
    buf.seek(0)
    base = Image.open(buf).convert("RGB")

    # Splice an altered high-detail numerical box at (480, 245)
    patch = np.full((96, 200, 3), 238, dtype=np.float32) + rng.normal(0, 15.0, (96, 200, 3))
    patch_img = Image.fromarray(np.clip(patch, 0, 255).astype(np.uint8), mode="RGB")
    pd = ImageDraw.Draw(patch_img)
    pd.rectangle([6, 6, 194, 90], outline=(190, 40, 40), width=3)
    pd.rectangle([24, 28, 176, 64], fill=(22, 28, 38))
    base.paste(patch_img, (480, 255))

    exif_bytes = _build_camera_exif(
        make="Apple",
        model="iPhone 15 Pro",
        software="GIMP 2.10.36",
        dt="2026:06:11 11:08:30",
    )
    base.save(out_path, format="JPEG", quality=98, exif=exif_bytes)


def _save_ai_synthetic_sample(out_path: Path) -> None:
    """Create a synthetic AI-style render with diffusion smooth gradients, periodic FFT upsampling harmonics, and SD prompt metadata."""
    h, w = 512, 512
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    yn = yy / h
    xn = xx / w

    # Hyper-smooth surreal neon studio lighting portrait-like orb & architectural backdrop
    r = 38 + 165 * np.exp(-((xn - 0.5) ** 2 + (yn - 0.45) ** 2) / 0.14) + 55 * np.sin(xn * 9.0)
    g = 24 + 135 * np.exp(-((xn - 0.46) ** 2 + (yn - 0.42) ** 2) / 0.11) + 45 * np.cos(yn * 7.0)
    b = 88 + 150 * np.exp(-((xn - 0.54) ** 2 + (yn - 0.50) ** 2) / 0.18) + 60 * np.sin((xn + yn) * 8.0)

    # Inject subtle periodic GAN/decoder upsampling grid harmonics (8px & 16px frequency spikes)
    grid_artifact = (
        5.5 * np.cos(2 * np.pi * xx / 8.0) * np.cos(2 * np.pi * yy / 8.0)
        + 4.0 * np.cos(2 * np.pi * xx / 16.0) * np.sin(2 * np.pi * yy / 16.0)
        + 3.0 * np.sin(2 * np.pi * (xx + yy) / 12.0)
    )
    arr = np.stack([r + grid_artifact, g + grid_artifact, b + grid_artifact], axis=-1)
    # Smooth over-denoised surface characteristic of diffusion models
    arr = cv2.GaussianBlur(np.clip(arr, 0, 255).astype(np.uint8), (3, 3), 0.6)

    pil = Image.fromarray(arr, mode="RGB")
    pnginfo = PngImagePlugin.PngInfo()
    pnginfo.add_text(
        "parameters",
        "hyperrealistic cinematic portrait lighting, volumetric fog, 8k uhd, sharp focus\n"
        "Negative prompt: blurry, lowres\n"
        "Steps: 28, Sampler: DPM++ 2M Karras, CFG scale: 7.0, Seed: 381920441, Model: sd_xl_base_1.0",
    )
    pnginfo.add_text("Software", "Stable Diffusion WebUI (AUTOMATIC1111)")
    pil.save(out_path, format="PNG", pnginfo=pnginfo)


def _save_whatsapp_recompressed(out_path: Path) -> None:
    """Create the Viva edge-case: authentic photo stripped of EXIF and re-compressed twice at low JPEG quality."""
    arr = _make_natural_scene(768, 512, seed=55)
    img = Image.fromarray(arr, mode="RGB")

    # Simulate WhatsApp / social media pipeline: downscale slightly + strip EXIF + double Q58 compression
    buf1 = io.BytesIO()
    img.resize((640, 426), Image.Resampling.BILINEAR).save(buf1, format="JPEG", quality=62)
    buf1.seek(0)
    img2 = Image.open(buf1).convert("RGB")
    img2.save(out_path, format="JPEG", quality=55)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    _save_authentic_dslr(OUT_DIR / "authentic_dslr_landscape.jpg")
    _save_authentic_c2pa(OUT_DIR / "authentic_c2pa_street.jpg")
    _save_spliced_photoshop(OUT_DIR / "spliced_photoshop_evidence.jpg")
    _save_spliced_document(OUT_DIR / "spliced_cloning_document.jpg")
    _save_ai_synthetic_sample(OUT_DIR / "ai_synthetic_diffusion_grid.png")
    _save_whatsapp_recompressed(OUT_DIR / "edge_whatsapp_recompressed.jpg")

    manifest = [
        {
            "id": "authentic-dslr",
            "title": "Authentic DSLR Capture",
            "category": "authentic",
            "description": "Natural camera-captured scene with uniform Q92 JPEG compression and intact Canon EOS R5 EXIF telemetry.",
            "expected_signal": "Clean camera EXIF, uniform ELA error field, smooth 1/f FFT decay.",
            "filename": "authentic_dslr_landscape.jpg",
        },
        {
            "id": "authentic-c2pa",
            "title": "C2PA Provenance Photo",
            "category": "authentic",
            "description": "Photograph carrying embedded C2PA Content Credentials JUMBF manifest alongside Nikon Z8 hardware metadata.",
            "expected_signal": "Verified C2PA provenance badge + uniform compression profile.",
            "filename": "authentic_c2pa_street.jpg",
        },
        {
            "id": "spliced-photoshop",
            "title": "Photoshop Spliced Object",
            "category": "spliced",
            "description": "Composite forgery where a high-quality patch was pasted onto a lower-quality JPEG background and saved in Adobe Photoshop.",
            "expected_signal": "Bright localized ELA hotspot box + Adobe Photoshop EXIF software flag.",
            "filename": "spliced_photoshop_evidence.jpg",
        },
        {
            "id": "spliced-document",
            "title": "Tampered Document / Claim",
            "category": "spliced",
            "description": "Simulated insurance/KYC document with a localized pasted region edited in GIMP at a mismatched compression level.",
            "expected_signal": "Localized ELA manipulation trigger + GIMP editing footprint.",
            "filename": "spliced_cloning_document.jpg",
        },
        {
            "id": "ai-diffusion-grid",
            "title": "AI Synthetic Render + FFT Peaks",
            "category": "ai_generated",
            "description": "Synthetic smooth diffusion render containing periodic decoder upsampling harmonics and embedded Stable Diffusion prompt chunks.",
            "expected_signal": "2D FFT periodic peaks + AI generator metadata + Grad-CAM attention map.",
            "filename": "ai_synthetic_diffusion_grid.png",
        },
        {
            "id": "edge-whatsapp",
            "title": "WhatsApp Re-Compressed Edge Case",
            "category": "edge_case",
            "description": "Authentic photo stripped of EXIF and double-compressed at low quality to demonstrate real-world platform attenuation during viva Q&A.",
            "expected_signal": "Stripped EXIF treated as neutral + attenuated ELA/FFT limitation callout.",
            "filename": "edge_whatsapp_recompressed.jpg",
        },
    ]

    (OUT_DIR / "manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )
    print(f"[generate_demo_samples] Created {len(manifest)} demo samples in {OUT_DIR}")


if __name__ == "__main__":
    main()
