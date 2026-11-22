"""Layer 2a: Error Level Analysis (ELA) for localized splicing & tampering detection."""

import io
import time
import cv2
import numpy as np
from PIL import Image

from app.config import settings
from app.schemas import ELAResult, HotspotRegion
from app.utils.image_io import apply_colormap_rgb, numpy_rgb_to_data_uri, resize_for_display


def analyze_ela(rgb_image: Image.Image, source_format: str) -> ELAResult:
    """Re-compress image at fixed JPEG quality in memory and analyze error-level variance."""
    t0 = time.perf_counter()

    # Work at display resolution (up to 1024px) for consistent sub-second latency & crisp visual maps
    working = resize_for_display(rgb_image, max_dim=settings.max_display_dimension)
    orig_arr = np.asarray(working, dtype=np.float32)

    # Re-compress at known JPEG quality strictly in memory (BytesIO)
    buf = io.BytesIO()
    working.save(buf, format="JPEG", quality=settings.ela_quality)
    buf.seek(0)
    recompressed = Image.open(buf).convert("RGB")
    recomp_arr = np.asarray(recompressed, dtype=np.float32)

    # Pixel-wise absolute error
    diff = np.abs(orig_arr - recomp_arr)
    gray_diff = np.mean(diff, axis=2)  # H x W

    mean_error = float(np.mean(gray_diff))
    std_error = float(np.std(gray_diff))
    max_error = float(np.max(gray_diff))
    p99 = float(np.percentile(gray_diff, 99.5))

    # Dynamic amplification factor so subtle compression discrepancies become clearly visible
    denom = max(p99, 6.0)
    scale = min(settings.ela_scale_cap, 220.0 / denom)
    amplified_rgb = np.clip(diff * scale, 0, 255).astype(np.uint8)

    # Normalized [0, 1] heatmap for false-color Inferno visualization
    heat_norm = np.clip((gray_diff * scale) / 255.0, 0.0, 1.0)
    ela_heatmap_rgb = apply_colormap_rgb(heat_norm, colormap=cv2.COLORMAP_INFERNO)

    # Localized tampering detection via spatial block grid (16x16 blocks)
    # Authentic uniformly compressed photos have consistent error levels across blocks of similar texture;
    # spliced patches from different compression histories create strong spatial outliers (high robust z-score).
    h, w = gray_diff.shape
    grid_n = settings.ela_grid_size
    cell_h = max(1, h // grid_n)
    cell_w = max(1, w // grid_n)

    # Compute edge-normalized block error to avoid false alarms purely on sharp high-contrast edges
    gray_img = cv2.cvtColor(orig_arr.astype(np.uint8), cv2.COLOR_RGB2GRAY).astype(np.float32)
    grad_x = cv2.Sobel(gray_img, cv2.CV_32F, 1, 0, ksize=3)
    grad_y = cv2.Sobel(gray_img, cv2.CV_32F, 0, 1, ksize=3)
    edge_mag = np.sqrt(grad_x**2 + grad_y**2)

    block_means = np.zeros((grid_n, grid_n), dtype=np.float32)
    block_ratios = np.zeros((grid_n, grid_n), dtype=np.float32)

    for r in range(grid_n):
        y0 = r * cell_h
        y1 = h if r == grid_n - 1 else (r + 1) * cell_h
        for c in range(grid_n):
            x0 = c * cell_w
            x1 = w if c == grid_n - 1 else (c + 1) * cell_w
            err_patch = gray_diff[y0:y1, x0:x1]
            edge_patch = edge_mag[y0:y1, x0:x1]
            b_err = float(np.mean(err_patch))
            b_edge = float(np.mean(edge_patch))
            block_means[r, c] = b_err
            # Normalize error slightly by local edge energy + floor so flat spliced patches stand out strongly
            block_ratios[r, c] = b_err / (1.0 + 0.012 * b_edge)

    median_ratio = float(np.median(block_ratios))
    mad_ratio = float(np.median(np.abs(block_ratios - median_ratio)))
    robust_sigma = max(1.4826 * mad_ratio, float(np.std(block_ratios)) * 0.5, 0.25)

    z_grid = (block_ratios - median_ratio) / robust_sigma
    # Also ensure absolute error difference is meaningful (prevents noise amplification on blank images)
    abs_delta_grid = block_means - float(np.median(block_means))

    hotspots: list[HotspotRegion] = []
    max_z = 0.0
    for r in range(grid_n):
        for c in range(grid_n):
            z = float(z_grid[r, c])
            if z > max_z:
                max_z = z
            if z >= 3.2 and float(abs_delta_grid[r, c]) >= 1.8:
                hotspots.append(
                    HotspotRegion(
                        x_pct=round((c / grid_n) * 100.0, 2),
                        y_pct=round((r / grid_n) * 100.0, 2),
                        w_pct=round((1.0 / grid_n) * 100.0, 2),
                        h_pct=round((1.0 / grid_n) * 100.0, 2),
                        z_score=round(z, 2),
                    )
                )

    # Sort strongest hotspots first, cap at top 12 cells
    hotspots.sort(key=lambda item: item.z_score, reverse=True)
    hotspots = hotspots[:12]

    # Calibrate localized tampering score [0, 1]
    is_lossless = source_format.upper() in ("PNG",)
    # Spliced regions typically produce clustered high-z blocks (z > 4.0) with elevated absolute delta
    top_z_mean = float(np.mean(np.sort(z_grid.ravel())[-6:]))
    hotspot_cluster_boost = min(0.25, len(hotspots) * 0.045)
    raw_tamper = float(1.0 / (1.0 + np.exp(-0.75 * (top_z_mean - 3.6)))) + hotspot_cluster_boost

    # Attenuate slightly if the image has negligible absolute ELA signal (e.g., heavily over-compressed)
    if float(np.max(abs_delta_grid)) < 1.5:
        raw_tamper *= 0.35
    elif is_lossless:
        # Pure lossless PNG saved once has uniform first-gen JPEG error unless a JPEG patch was spliced in
        raw_tamper *= 0.78

    localized_tampering_score = float(np.clip(raw_tamper, 0.02, 0.98))

    if localized_tampering_score >= 0.65:
        interpretation = (
            f"Strong localized ELA discrepancy detected ({len(hotspots)} anomalous grid zone(s), "
            f"peak z-score {max_z:.1f}σ). Bright regions indicate mismatched JPEG compression history "
            "consistent with object splicing, cloning, or localized retouching."
        )
    elif localized_tampering_score >= 0.40:
        interpretation = (
            f"Moderate error-level variance observed (peak z-score {max_z:.1f}σ). Could reflect localized "
            "edits, text overlays, or high-contrast texture boundaries—cross-check with the split slider."
        )
    else:
        caveat = (
            " Note: Source is lossless PNG, where single-pass AI renders can exhibit uniform ELA."
            if is_lossless
            else ""
        )
        interpretation = (
            f"Compression error levels appear spatially uniform across the frame (mean error {mean_error:.2f}, "
            f"peak z-score {max_z:.1f}σ), showing no obvious localized JPEG splicing boundary.{caveat}"
        )

    ela_map_b64 = numpy_rgb_to_data_uri(amplified_rgb, fmt="PNG")
    ela_heatmap_b64 = numpy_rgb_to_data_uri(ela_heatmap_rgb, fmt="PNG")
    latency_ms = round((time.perf_counter() - t0) * 1000.0, 2)

    return ELAResult(
        quality_used=settings.ela_quality,
        amplification_factor=round(scale, 2),
        mean_error=round(mean_error, 3),
        max_error=round(max_error, 3),
        std_error=round(std_error, 3),
        hotspot_z_score=round(max_z, 2),
        localized_tampering_score=round(localized_tampering_score, 4),
        is_lossless_source=is_lossless,
        hotspots=hotspots,
        interpretation=interpretation,
        ela_map_b64=ela_map_b64,
        ela_heatmap_b64=ela_heatmap_b64,
        latency_ms=latency_ms,
    )
