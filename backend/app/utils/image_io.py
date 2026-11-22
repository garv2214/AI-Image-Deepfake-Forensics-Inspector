"""In-memory image encoding, resizing, and heatmap utility helpers."""

import base64
import io
import cv2
import numpy as np
from PIL import Image


def pil_to_base64_data_uri(image: Image.Image, fmt: str = "PNG", quality: int = 90) -> str:
    """Encode a PIL Image to a base64 data URI completely in memory."""
    buf = io.BytesIO()
    save_kwargs = {}
    if fmt.upper() == "JPEG":
        image = image.convert("RGB")
        save_kwargs["quality"] = quality
        save_kwargs["optimize"] = True
    image.save(buf, format=fmt.upper(), **save_kwargs)
    mime = "image/jpeg" if fmt.upper() == "JPEG" else "image/png"
    b64 = base64.b64encode(buf.getvalue()).decode("ascii")
    return f"data:{mime};base64,{b64}"


def numpy_rgb_to_data_uri(arr: np.ndarray, fmt: str = "PNG", quality: int = 90) -> str:
    """Encode a HxWx3 uint8 RGB numpy array to a base64 data URI."""
    arr_u8 = np.clip(arr, 0, 255).astype(np.uint8)
    img = Image.fromarray(arr_u8, mode="RGB")
    return pil_to_base64_data_uri(img, fmt=fmt, quality=quality)


def resize_for_display(image: Image.Image, max_dim: int = 1024) -> Image.Image:
    """Downscale large images proportionally for snappy UI rendering while preserving aspect."""
    w, h = image.size
    if max(w, h) <= max_dim:
        return image
    scale = max_dim / float(max(w, h))
    new_size = (max(1, int(round(w * scale))), max(1, int(round(h * scale))))
    return image.resize(new_size, Image.Resampling.LANCZOS)


def apply_colormap_rgb(normalized_map: np.ndarray, colormap: int = cv2.COLORMAP_INFERNO) -> np.ndarray:
    """Apply an OpenCV colormap to a float32 [0, 1] 2D map and return RGB uint8."""
    u8 = np.clip(normalized_map * 255.0, 0, 255).astype(np.uint8)
    colored_bgr = cv2.applyColorMap(u8, colormap)
    return cv2.cvtColor(colored_bgr, cv2.COLOR_BGR2RGB)


def blend_heatmap_overlay(
    rgb_image: np.ndarray,
    heatmap_norm: np.ndarray,
    alpha: float = 0.48,
    colormap: int = cv2.COLORMAP_JET,
) -> tuple[np.ndarray, np.ndarray]:
    """Blend a [0, 1] spatial heatmap onto an RGB image using attention-weighted alpha.

    Returns (blended_overlay_rgb, standalone_colored_heatmap_rgb).
    """
    h, w = rgb_image.shape[:2]
    hm_resized = cv2.resize(
        heatmap_norm.astype(np.float32), (w, h), interpolation=cv2.INTER_CUBIC
    )
    hm_resized = np.clip(hm_resized, 0.0, 1.0)
    colored = apply_colormap_rgb(hm_resized, colormap=colormap)

    # Attention-aware blending keeps cool low-activation zones clean and legible
    weight = (0.15 + 0.85 * hm_resized)[..., None] * alpha
    blended = (
        rgb_image.astype(np.float32) * (1.0 - weight)
        + colored.astype(np.float32) * weight
    )
    return np.clip(blended, 0, 255).astype(np.uint8), colored
