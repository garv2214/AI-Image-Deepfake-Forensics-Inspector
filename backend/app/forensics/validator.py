"""Strict in-memory image validation & ingestion (zero disk persistence)."""

import hashlib
import io
from dataclasses import dataclass
from PIL import Image, ImageOps, UnidentifiedImageError

from app.config import settings
from app.schemas import ImageMetadataInfo


class ValidationError(ValueError):
    """Raised when an uploaded payload fails forensic ingestion validation."""

    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.status_code = status_code


MAGIC_SIGNATURES = (
    (b"\xff\xd8\xff", "image/jpeg"),
    (b"\x89PNG\r\n\x1a\n", "image/png"),
    (b"RIFF", "image/webp"),
)


def _detect_magic_mime(raw_bytes: bytes) -> str | None:
    for sig, mime in MAGIC_SIGNATURES:
        if raw_bytes.startswith(sig):
            if mime == "image/webp":
                if len(raw_bytes) >= 12 and raw_bytes[8:12] == b"WEBP":
                    return "image/webp"
                return None
            return mime
    return None


@dataclass
class ValidatedImage:
    raw_bytes: bytes
    pil_image: Image.Image
    rgb_image: Image.Image
    info: ImageMetadataInfo


def validate_and_load_image(
    raw_bytes: bytes,
    filename: str = "upload.jpg",
    declared_content_type: str | None = None,
) -> ValidatedImage:
    """Validate file size, magic bytes, MIME type, and decode image strictly in memory."""
    if not raw_bytes:
        raise ValidationError("Uploaded file is empty.", status_code=400)

    if len(raw_bytes) > settings.max_file_size_bytes:
        max_mb = settings.max_file_size_bytes / (1024 * 1024)
        raise ValidationError(
            f"File size ({len(raw_bytes) / (1024 * 1024):.2f} MB) exceeds the {max_mb:.0f} MB limit.",
            status_code=413,
        )

    detected_mime = _detect_magic_mime(raw_bytes)
    if detected_mime not in settings.allowed_mime_types:
        raise ValidationError(
            "Unsupported or invalid image signature. Accepted formats: JPEG (.jpg, .jpeg), PNG (.png), and WebP (.webp).",
            status_code=415,
        )

    if declared_content_type and declared_content_type != "application/octet-stream":
        norm_ct = declared_content_type.lower().split(";")[0].strip()
        if norm_ct == "image/jpg":
            norm_ct = "image/jpeg"
        if norm_ct not in settings.allowed_mime_types:
            raise ValidationError(
                f"Rejected MIME type '{declared_content_type}'. Only JPEG, PNG, and WebP images are permitted.",
                status_code=415,
            )

    try:
        # First pass: verify structural integrity without full decode
        with Image.open(io.BytesIO(raw_bytes)) as probe:
            probe.verify()

        # Second pass: open cleanly and load pixels into RAM
        img = Image.open(io.BytesIO(raw_bytes))
        img.load()
    except (UnidentifiedImageError, OSError, SyntaxError, ValueError) as exc:
        raise ValidationError(
            f"Image file is corrupted or unreadable: {exc}", status_code=400
        ) from exc

    img_format = (img.format or "").upper()
    if img_format not in settings.allowed_formats:
        raise ValidationError(
            f"Unsupported decoded image format '{img_format}'. Allowed: JPEG, PNG, WEBP.",
            status_code=415,
        )

    if img.width < 32 or img.height < 32:
        raise ValidationError(
            f"Image dimensions ({img.width}x{img.height}) are too small for reliable forensic analysis (minimum 32x32).",
            status_code=400,
        )

    # Apply EXIF orientation on the working RGB copy so visual maps align with display orientation
    rgb_oriented = ImageOps.exif_transpose(img).convert("RGB")
    sha256_prefix = hashlib.sha256(raw_bytes).hexdigest()[:16]

    info = ImageMetadataInfo(
        filename=filename or "uploaded_image",
        mime_type=detected_mime,
        format=img_format,
        width=rgb_oriented.width,
        height=rgb_oriented.height,
        file_size_bytes=len(raw_bytes),
        color_mode=img.mode,
        sha256_prefix=sha256_prefix,
    )

    return ValidatedImage(
        raw_bytes=raw_bytes,
        pil_image=img,
        rgb_image=rgb_oriented,
        info=info,
    )
