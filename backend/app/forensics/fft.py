"""Layer 2b: 2D Fast Fourier Transform (FFT) spatial frequency forensics."""

import time
import cv2
import numpy as np
from PIL import Image

from app.schemas import FFTResult, RadialFrequencyPoint
from app.utils.image_io import apply_colormap_rgb, numpy_rgb_to_data_uri


def analyze_fft(rgb_image: Image.Image) -> FFTResult:
    """Compute 2D FFT log-magnitude spectrum, azimuthal radial profile, and spectral anomalies."""
    t0 = time.perf_counter()

    # Resize to canonical 512x512 grayscale for consistent frequency bin resolution & fast FFT
    gray = np.asarray(rgb_image.convert("L").resize((512, 512), Image.Resampling.BICUBIC), dtype=np.float32)

    # Apply 2D Hann window to suppress border discontinuity cross-artifacts in FFT
    h, w = gray.shape
    hann_y = np.hanning(h).astype(np.float32)
    hann_x = np.hanning(w).astype(np.float32)
    windowed = (gray - np.mean(gray)) * np.outer(hann_y, hann_x)

    # 2D FFT + center DC shift
    fft2 = np.fft.fft2(windowed)
    fft_shift = np.fft.fftshift(fft2)
    magnitude = np.abs(fft_shift)
    log_mag = np.log1p(magnitude)

    # Normalize log-magnitude for crisp forensic visualization (Magma colormap)
    p5, p995 = np.percentile(log_mag, [5.0, 99.8])
    norm_spec = np.clip((log_mag - p5) / max(p995 - p5, 1e-5), 0.0, 1.0)
    spec_rgb = apply_colormap_rgb(norm_spec, colormap=cv2.COLORMAP_MAGMA)

    # Compute azimuthal (radial) average power profile from DC center to Nyquist edge
    cy, cx = h // 2, w // 2
    yy, xx = np.ogrid[:h, :w]
    dist = np.sqrt((yy - cy) ** 2 + (xx - cx) ** 2)
    max_r = min(cy, cx)
    num_bins = 28
    bin_edges = np.linspace(1.0, float(max_r), num_bins + 1)

    radial_observed: list[float] = []
    radial_radii: list[float] = []
    for i in range(num_bins):
        mask = (dist >= bin_edges[i]) & (dist < bin_edges[i + 1])
        vals = log_mag[mask]
        radial_observed.append(float(np.mean(vals)) if vals.size else 0.0)
        radial_radii.append(float((bin_edges[i] + bin_edges[i + 1]) / (2.0 * max_r)))

    obs_arr = np.array(radial_observed, dtype=np.float32)
    # Normalize profile to [0, 1] relative to low-frequency energy
    obs_min, obs_max = float(np.min(obs_arr)), float(np.max(obs_arr))
    obs_norm = (obs_arr - obs_min) / max(obs_max - obs_min, 1e-5)

    # Natural camera photography follows a smooth ~1/f^alpha spectral decay (in log-magnitude,
    # approximately linear decay vs log(radius))
    r_arr = np.array(radial_radii, dtype=np.float32)
    log_r = np.log(r_arr + 0.03)
    # Fit linear slope in log-r vs log-magnitude
    slope, intercept = np.polyfit(log_r, obs_arr, 1)
    # Ideal natural reference curve anchored at the image's own low-frequency energy
    natural_ref = np.clip(1.0 - 0.88 * np.power(r_arr, 0.55), 0.05, 1.0)

    radial_profile = [
        RadialFrequencyPoint(
            radius_norm=round(float(r_arr[i]), 3),
            observed_power=round(float(obs_norm[i]), 4),
            natural_reference=round(float(natural_ref[i]), 4),
        )
        for i in range(num_bins)
    ]

    # 1. High-frequency energy ratio (outer 40% radius vs total)
    high_mask = (dist >= 0.60 * max_r) & (dist <= max_r)
    low_mask = (dist >= 2.0) & (dist < 0.25 * max_r)
    high_energy = float(np.mean(log_mag[high_mask]))
    low_energy = float(np.mean(log_mag[low_mask]))
    hf_ratio = high_energy / max(low_energy, 1e-5)

    # 2. Periodic grid spike detector (GAN upsampling / transposed conv checkerboard peaks)
    # Mask out DC center & axial cross (within 6px of center axes) to avoid natural horizontal/vertical edge lines
    mid_high_mask = (dist >= 0.08 * max_r) & (dist <= 0.94 * max_r)
    axis_mask = (np.abs(yy - cy) > 6) & (np.abs(xx - cx) > 6)
    off_axis_mask = mid_high_mask & axis_mask

    # Subtract local 15x15 Gaussian background to isolate sharp periodic Dirac-like spectral peaks
    local_bg = cv2.GaussianBlur(log_mag.astype(np.float32), (15, 15), 0)
    residual = log_mag - local_bg
    off_axis_res = residual[off_axis_mask]

    # Use robust MAD-based scale so strong periodic spikes do not inflate their own denominator
    res_med = float(np.median(off_axis_res))
    res_mad = float(np.median(np.abs(off_axis_res - res_med)))
    robust_std = max(1.4826 * res_mad, float(np.std(off_axis_res)) * 0.5, 1e-3)

    # Average top-8 symmetric off-axis peaks to catch 4-point/8-point periodic upsampling grids cleanly
    top_peaks = np.partition(off_axis_res, -8)[-8:]
    peak_z = float(np.mean(top_peaks) - res_med) / robust_std
    # Natural camera spectra rarely exceed ~6.5σ off-axis narrow peaks; periodic upsampling grids spike > 9σ
    periodic_peak_score = float(np.clip((peak_z - 6.0) / 5.5, 0.0, 1.0))

    # 3. Radial roll-off deviation from smooth natural photography decay
    profile_l1_dev = float(np.mean(np.abs(obs_norm - natural_ref)))
    # Abnormal high-frequency suppression (diffusion over-smoothing) or excess synthetic aliasing
    rolloff_anomaly = float(np.clip((profile_l1_dev - 0.12) / 0.25, 0.0, 1.0))
    hf_anomaly = 0.0
    if hf_ratio < 0.42:
        hf_anomaly = float(np.clip((0.42 - hf_ratio) / 0.22, 0.0, 1.0))
    elif hf_ratio > 0.80:
        hf_anomaly = float(np.clip((hf_ratio - 0.80) / 0.20, 0.0, 1.0))

    frequency_anomaly_score = float(
        np.clip(
            0.50 * periodic_peak_score + 0.30 * rolloff_anomaly + 0.20 * hf_anomaly,
            0.03,
            0.97,
        )
    )

    if periodic_peak_score >= 0.55:
        interpretation = (
            f"Distinct off-axis periodic spectral peaks detected (peak score {periodic_peak_score:.2f}), "
            "a classic signature of neural upsampling grids (GAN / diffusion decoder artifacts) or periodic resampling."
        )
    elif frequency_anomaly_score >= 0.50:
        interpretation = (
            f"Abnormal high-frequency spectral roll-off observed (HF/LF ratio {hf_ratio:.2f}, slope {slope:.2f}). "
            "Deviates from natural optical sensor 1/f decay—consistent with synthetic denoising or heavy post-processing."
        )
    else:
        interpretation = (
            f"2D magnitude spectrum exhibits smooth radial decay (HF/LF ratio {hf_ratio:.2f}, slope {slope:.2f}) "
            "without prominent periodic upsampling grid spikes."
        )

    fft_spectrum_b64 = numpy_rgb_to_data_uri(spec_rgb, fmt="PNG")
    latency_ms = round((time.perf_counter() - t0) * 1000.0, 2)

    return FFTResult(
        high_freq_energy_ratio=round(hf_ratio, 4),
        spectral_slope=round(float(slope), 4),
        periodic_peak_score=round(periodic_peak_score, 4),
        frequency_anomaly_score=round(frequency_anomaly_score, 4),
        radial_profile=radial_profile,
        interpretation=interpretation,
        fft_spectrum_b64=fft_spectrum_b64,
        latency_ms=latency_ms,
    )
