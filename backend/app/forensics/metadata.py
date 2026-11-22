"""Layer 1: Provenance & Metadata Inspection (EXIF, XMP, PNG chunks, C2PA)."""

import io
import re
import time
import exifread
from PIL import Image

from app.schemas import MetadataEntry, MetadataReport

EDITING_SOFTWARE_KEYWORDS = {
    "photoshop": "Adobe Photoshop",
    "adobe photoshop": "Adobe Photoshop",
    "lightroom": "Adobe Lightroom",
    "gimp": "GIMP",
    "affinity photo": "Affinity Photo",
    "pixelmator": "Pixelmator",
    "canva": "Canva",
    "snapseed": "Snapseed",
    "facetune": "Facetune",
    "picsart": "PicsArt",
    "paint.net": "Paint.NET",
    "krita": "Krita",
    "corel": "Corel PaintShop / CorelDRAW",
}

AI_GENERATOR_KEYWORDS = {
    "midjourney": "Midjourney",
    "stable diffusion": "Stable Diffusion",
    "automatic1111": "Stable Diffusion (AUTOMATIC1111)",
    "comfyui": "ComfyUI / Stable Diffusion",
    "dall-e": "OpenAI DALL-E",
    "dall·e": "OpenAI DALL-E",
    "chatgpt": "OpenAI Image Generation",
    "openai": "OpenAI Generative Model",
    "firefly": "Adobe Firefly",
    "ideogram": "Ideogram",
    "flux": "Black Forest Labs FLUX",
    "leonardo": "Leonardo.ai",
    "imagen": "Google Imagen",
    "novelai": "NovelAI Diffusion",
    "invokeai": "InvokeAI",
    "diffusers": "HuggingFace Diffusers",
}

CURATED_EXIF_MAP = {
    "Image Make": ("Camera Make", "camera"),
    "Image Model": ("Camera Model", "camera"),
    "EXIF LensModel": ("Lens Model", "camera"),
    "EXIF ExposureTime": ("Shutter Speed", "capture"),
    "EXIF FNumber": ("Aperture (f-stop)", "capture"),
    "EXIF ISOSpeedRatings": ("ISO Sensitivity", "capture"),
    "EXIF FocalLength": ("Focal Length", "capture"),
    "EXIF DateTimeOriginal": ("Capture Timestamp", "capture"),
    "Image DateTime": ("File Modified Timestamp", "capture"),
    "Image Software": ("Software / Encoder", "software"),
    "EXIF ColorSpace": ("Color Space", "technical"),
    "GPS GPSLatitude": ("GPS Latitude", "capture"),
    "GPS GPSLongitude": ("GPS Longitude", "capture"),
}


def _clean_text(val: object, max_len: int = 180) -> str:
    text = str(val).strip().replace("\x00", "")
    text = re.sub(r"\s+", " ", text)
    if len(text) > max_len:
        return text[: max_len - 3] + "..."
    return text


def _detect_c2pa_markers(raw_bytes: bytes) -> tuple[bool, str | None]:
    """Inspect binary container segments for C2PA JUMBF Content Credentials markers."""
    lower = raw_bytes.lower()
    has_c2pa = (
        b"c2pa" in lower
        and (b"jumb" in lower or b"c2pa.claim" in lower or b"urn:uuid:c2pa" in lower)
    )
    if not has_c2pa:
        return False, None

    # Attempt to extract claim generator string near c2pa marker
    match = re.search(rb"claim_generator.{0,60}([A-Za-z0-9_.\-/ ]{3,45})", raw_bytes)
    if match:
        try:
            gen = match.group(1).decode("utf-8", errors="ignore").strip()
            return True, gen or "C2PA Manifest Embedded"
        except Exception:
            pass
    return True, "C2PA JUMBF Manifest Detected"


def _extract_xmp_snippet(raw_bytes: bytes) -> str:
    start = raw_bytes.find(b"<x:xmpmeta")
    if start == -1:
        start = raw_bytes.find(b"<rdf:RDF")
    if start == -1:
        return ""
    end = raw_bytes.find(b"</x:xmpmeta>", start)
    if end == -1:
        end = raw_bytes.find(b"</rdf:RDF>", start)
    if end == -1:
        end = min(len(raw_bytes), start + 16384)
    return raw_bytes[start : end + 16].decode("utf-8", errors="ignore")


def analyze_metadata(raw_bytes: bytes, pil_image: Image.Image) -> MetadataReport:
    """Run Layer 1 provenance & metadata inspection completely in memory."""
    t0 = time.perf_counter()

    entries: list[MetadataEntry] = []
    seen_tags: set[str] = set()
    searchable_corpus_parts: list[str] = []

    camera_make = None
    camera_model = None
    capture_ts = None
    color_profile = None
    editing_software = None
    ai_generator = None

    # 1. Deep EXIF extraction via exifread
    try:
        exif_tags = exifread.process_file(
            io.BytesIO(raw_bytes), details=False, strict=False
        )
    except Exception:
        exif_tags = {}

    has_exif = len(exif_tags) > 0

    for raw_key, (display_name, category) in CURATED_EXIF_MAP.items():
        if raw_key in exif_tags:
            val_str = _clean_text(exif_tags[raw_key])
            if not val_str:
                continue
            searchable_corpus_parts.append(f"{display_name}:{val_str}")
            significance = "neutral"
            if raw_key == "Image Make":
                camera_make = val_str
                significance = "authentic_signal"
            elif raw_key == "Image Model":
                camera_model = val_str
                significance = "authentic_signal"
            elif raw_key in ("EXIF LensModel", "EXIF ExposureTime", "EXIF FNumber", "EXIF ISOSpeedRatings", "EXIF FocalLength"):
                significance = "authentic_signal"
            elif raw_key == "EXIF DateTimeOriginal":
                capture_ts = val_str
            elif raw_key == "EXIF ColorSpace":
                color_profile = val_str

            entries.append(
                MetadataEntry(
                    tag=display_name,
                    value=val_str,
                    category=category,
                    significance=significance,
                )
            )
            seen_tags.add(display_name)

    # 2. PIL info dictionary (PNG text chunks, ICC profile, WebP/JPEG comments)
    if isinstance(pil_image.info, dict):
        if "icc_profile" in pil_image.info and not color_profile:
            icc_raw = pil_image.info["icc_profile"]
            if isinstance(icc_raw, (bytes, bytearray)):
                icc_match = re.search(
                    rb"(sRGB|Display P3|Adobe RGB|ProPhoto RGB)", icc_raw, re.IGNORECASE
                )
                color_profile = (
                    icc_match.group(1).decode("ascii", errors="ignore")
                    if icc_match
                    else f"Embedded ICC ({len(icc_raw)} bytes)"
                )
            entries.append(
                MetadataEntry(
                    tag="ICC Color Profile",
                    value=color_profile,
                    category="technical",
                    significance="neutral",
                )
            )
            seen_tags.add("ICC Color Profile")

        # Inspect PNG/JPEG text chunks (Stable Diffusion 'parameters', ComfyUI 'prompt'/'workflow', Software, etc.)
        for k, v in pil_image.info.items():
            if k in ("exif", "icc_profile", "dpi", "jfif", "jfif_version", "jfif_unit", "jfif_density", "progressive"):
                continue
            val_text = _clean_text(v, max_len=240)
            if not val_text:
                continue
            searchable_corpus_parts.append(f"{k}:{val_text}")
            kl = str(k).lower()
            if kl in ("parameters", "prompt", "workflow", "generation_data", "sd-metadata", "comment", "description", "software", "source", "creator"):
                sig = "neutral"
                cat = "technical"
                if kl in ("parameters", "prompt", "workflow", "sd-metadata", "generation_data"):
                    sig = "ai_signature"
                    cat = "provenance"
                    if not ai_generator:
                        ai_generator = "Embedded Diffusion Prompt Parameters"
                elif kl == "software":
                    cat = "software"
                tag_name = f"Chunk: {k}"
                if tag_name not in seen_tags:
                    entries.append(
                        MetadataEntry(
                            tag=tag_name,
                            value=val_text,
                            category=cat,
                            significance=sig,
                        )
                    )
                    seen_tags.add(tag_name)

    # 3. XMP inspection for CreatorTool / DigitalSourceType (IPTC trainedAlgorithmicMedia)
    xmp_text = _extract_xmp_snippet(raw_bytes)
    if xmp_text:
        searchable_corpus_parts.append(xmp_text)
        creator_match = re.search(
            r"xmp:CreatorTool[=>\"\s]+([^<\"]{2,80})", xmp_text, re.IGNORECASE
        )
        if creator_match:
            tool = _clean_text(creator_match.group(1))
            if "XMP Creator Tool" not in seen_tags:
                entries.append(
                    MetadataEntry(
                        tag="XMP Creator Tool",
                        value=tool,
                        category="software",
                        significance="neutral",
                    )
                )
                seen_tags.add("XMP Creator Tool")

        if "trainedalgorithmicmedia" in xmp_text.lower() or "compositewithalgorithmicmedia" in xmp_text.lower():
            ai_generator = ai_generator or "IPTC DigitalSourceType: Trained Algorithmic Media"
            entries.append(
                MetadataEntry(
                    tag="IPTC DigitalSourceType",
                    value="trainedAlgorithmicMedia (Declared AI-Generated)",
                    category="provenance",
                    significance="ai_signature",
                )
            )

    # 4. C2PA Content Credentials check
    has_c2pa, c2pa_detail = _detect_c2pa_markers(raw_bytes)
    if has_c2pa:
        entries.append(
            MetadataEntry(
                tag="C2PA Content Credentials",
                value=c2pa_detail or "Embedded JUMBF Provenance Manifest",
                category="provenance",
                significance="authentic_signal",
            )
        )

    # 5. Match editing software & AI generator signatures across metadata corpus
    corpus_lower = " ".join(searchable_corpus_parts).lower()
    for kw, label in AI_GENERATOR_KEYWORDS.items():
        if kw in corpus_lower:
            ai_generator = label
            break

    for kw, label in EDITING_SOFTWARE_KEYWORDS.items():
        if kw in corpus_lower:
            editing_software = label
            break

    # Upgrade software entry significance if matched
    for entry in entries:
        v_low = entry.value.lower()
        if any(kw in v_low for kw in AI_GENERATOR_KEYWORDS):
            entry.significance = "ai_signature"
        elif any(kw in v_low for kw in EDITING_SOFTWARE_KEYWORDS):
            entry.significance = "editing_flag"

    camera_make_model = None
    if camera_make and camera_model:
        camera_make_model = (
            camera_model
            if camera_make.lower() in camera_model.lower()
            else f"{camera_make} {camera_model}"
        )
    elif camera_model or camera_make:
        camera_make_model = camera_model or camera_make

    has_camera_signature = bool(camera_make_model) and any(
        e.tag in ("Shutter Speed", "Aperture (f-stop)", "ISO Sensitivity", "Focal Length", "Lens Model")
        for e in entries
    )

    # 6. Provenance classification & calibrated risk contribution (metadata alone is never absolute proof)
    if ai_generator:
        status = "ai_metadata_found"
        summary = f"Generative AI metadata signature detected ({ai_generator})."
        risk_contribution = 0.90
    elif editing_software:
        status = "editing_software_flagged"
        summary = f"Post-processing software footprint detected ({editing_software}); inspect ELA map for localized edits."
        risk_contribution = 0.62
    elif has_c2pa:
        status = "verified_provenance"
        summary = "C2PA Content Credentials container present in file header."
        risk_contribution = 0.12
    elif has_camera_signature or camera_make_model:
        status = "camera_signature_present"
        summary = f"Camera hardware telemetry present ({camera_make_model}), consistent with optical capture."
        risk_contribution = 0.18
    else:
        status = "metadata_stripped"
        summary = (
            "No EXIF camera telemetry found. Treated strictly as a weak/neutral signal because "
            "messaging apps (WhatsApp, Telegram) and social platforms strip EXIF automatically."
        )
        risk_contribution = 0.45  # Neutral / weak prior

    if not entries:
        entries.append(
            MetadataEntry(
                tag="EXIF / Header Audit",
                value="Stripped or absent (common on social media, messaging apps, PNG exports, and AI generators)",
                category="provenance",
                significance="neutral",
            )
        )

    latency_ms = round((time.perf_counter() - t0) * 1000.0, 2)

    return MetadataReport(
        has_exif=has_exif,
        has_camera_signature=has_camera_signature or bool(camera_make_model),
        has_c2pa_credentials=has_c2pa,
        editing_software_detected=editing_software,
        ai_generator_detected=ai_generator,
        camera_make_model=camera_make_model,
        capture_timestamp=capture_ts,
        color_profile=color_profile,
        provenance_status=status,
        provenance_summary=summary,
        risk_contribution=round(risk_contribution, 4),
        entries=entries,
        latency_ms=latency_ms,
    )
