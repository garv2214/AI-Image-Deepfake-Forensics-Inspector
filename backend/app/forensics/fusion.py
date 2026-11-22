"""Layer 4: Calibrated Hybrid Fusion & Verdict Engine."""

import numpy as np

from app.config import settings
from app.schemas import (
    ChannelContribution,
    DeepLearningResult,
    ELAResult,
    FFTResult,
    MetadataReport,
    VerdictResult,
)


def compute_fused_verdict(
    meta: MetadataReport,
    ela: ELAResult,
    fft: FFTResult,
    dl: DeepLearningResult,
) -> VerdictResult:
    """Fuse independent forensic signals into dual axes (Synthetic vs Localized Tampering) and a transparent verdict."""

    # Axis 1: Full-Frame Synthetic Probability (0–100)
    # Heaviest weight on Deep Vision Model, supported by 2D FFT spectral anomalies and metadata provenance.
    w_dl = settings.weight_deep_model
    w_fft = settings.weight_fft
    w_ela_s = settings.weight_ela_synthetic
    w_meta = settings.weight_metadata

    # If explicit generative AI metadata (e.g. Stable Diffusion prompt params or IPTC trainedAlgorithmicMedia)
    # is embedded in the file header, boost synthetic floor while still showing neural probability transparently.
    meta_synth_signal = meta.risk_contribution
    if meta.provenance_status == "editing_software_flagged":
        # Photoshop tag suggests manual manipulation rather than pure full-frame AI generation
        meta_synth_signal = 0.42

    full_frame_prob = (
        w_dl * dl.synthetic_probability
        + w_fft * fft.frequency_anomaly_score
        + w_ela_s * (1.0 - abs(0.5 - ela.localized_tampering_score)) * 0.5
        + w_meta * meta_synth_signal
    )

    if meta.ai_generator_detected:
        full_frame_prob = max(full_frame_prob, 0.78)
    elif meta.has_c2pa_credentials and dl.synthetic_probability < 0.55:
        full_frame_prob *= 0.75

    full_frame_score = round(float(np.clip(full_frame_prob * 100.0, 1.0, 99.4)), 1)

    # Axis 2: Localized Tampering Score (0–100)
    # Driven primarily by ELA spatial hotspot variance, reinforced by editing-suite software tags.
    tamper_prob = ela.localized_tampering_score
    if meta.editing_software_detected:
        tamper_prob = min(0.98, tamper_prob + 0.16)
    localized_tamper_score = round(float(np.clip(tamper_prob * 100.0, 1.0, 99.0)), 1)

    # Detect heavy social-media re-compression edge case (stripped EXIF + flat low ELA + borderline DL)
    is_heavily_recompressed = (
        not meta.has_exif
        and not ela.is_lossless_source
        and ela.mean_error < 2.2
        and 36.0 <= full_frame_score <= 60.0
        and localized_tamper_score < 48.0
    )

    # Decision Matrix: Separate Full-Frame AI Generation from Localized Splicing/Retouching
    if full_frame_score >= 62.0 or (dl.synthetic_probability >= 0.75 and full_frame_score >= 56.0):
        verdict_code = "high_probability_ai"
        verdict_label = "High Probability AI-Generated"
        severity = "high"
        confidence = round(float(np.clip(full_frame_score, 62.0, 98.5)), 1)
        exec_summary = (
            "Multiple forensic indicators—led by the deep vision classifier and Grad-CAM spatial attribution—point "
            "strongly toward full-frame synthetic image generation."
        )
    elif localized_tamper_score >= 60.0 or (
        localized_tamper_score >= 52.0 and meta.editing_software_detected is not None
    ):
        verdict_code = "localized_manipulation_suspected"
        verdict_label = "Localized Manipulation Suspected"
        severity = "medium"
        confidence = round(float(np.clip(localized_tamper_score, 58.0, 96.0)), 1)
        exec_summary = (
            "Error Level Analysis detected spatially localized compression anomalies consistent with splicing, "
            "copy-move retouching, or compositing rather than uniform camera capture."
        )
    elif is_heavily_recompressed:
        verdict_code = "inconclusive_recompressed"
        verdict_label = "Inconclusive (Heavy Re-Compression)"
        severity = "neutral"
        confidence = round(float(100.0 - abs(full_frame_score - 50.0) * 1.1), 1)
        exec_summary = (
            "Metadata has been stripped and compression residuals are attenuated—typical of WhatsApp or social-media "
            "re-encoding. Forensic signals are inconclusive; request the original camera file for verification."
        )
    else:
        verdict_code = "likely_authentic"
        verdict_label = "Likely Camera-Authentic"
        severity = "low"
        confidence = round(
            float(np.clip(100.0 - max(full_frame_score, localized_tamper_score * 0.75), 55.0, 97.5)),
            1,
        )
        exec_summary = (
            "No decisive synthetic generation or localized splicing signatures were detected across the deep vision, "
            "frequency-domain, and error-level channels."
        )

    # Build transparent per-channel audit rows
    dl_status = (
        "alert"
        if dl.synthetic_probability >= 0.65
        else ("caution" if dl.synthetic_probability >= 0.42 else "clean")
    )
    ela_status = (
        "alert"
        if ela.localized_tampering_score >= 0.65
        else ("caution" if ela.localized_tampering_score >= 0.42 else "clean")
    )
    fft_status = (
        "alert"
        if fft.frequency_anomaly_score >= 0.65
        else ("caution" if fft.frequency_anomaly_score >= 0.42 else "clean")
    )
    meta_status = (
        "alert"
        if meta.provenance_status == "ai_metadata_found"
        else (
            "caution"
            if meta.provenance_status == "editing_software_flagged"
            else (
                "clean"
                if meta.provenance_status in ("verified_provenance", "camera_signature_present")
                else "neutral"
            )
        )
    )

    channel_breakdown = [
        ChannelContribution(
            channel="Deep Vision Model + Grad-CAM",
            layer="Layer 3",
            raw_score=round(dl.synthetic_probability * 100.0, 1),
            weight=round(w_dl * 100.0, 0),
            role="Primary full-frame synthetic authenticity driver",
            status=dl_status,
            finding=dl.interpretation,
        ),
        ChannelContribution(
            channel="Error Level Analysis (ELA)",
            layer="Layer 2A",
            raw_score=round(ela.localized_tampering_score * 100.0, 1),
            weight=round(w_ela_s * 100.0, 0),
            role="Localized Photoshop splicing & copy-move trigger",
            status=ela_status,
            finding=ela.interpretation,
        ),
        ChannelContribution(
            channel="2D FFT Frequency Spectrum",
            layer="Layer 2B",
            raw_score=round(fft.frequency_anomaly_score * 100.0, 1),
            weight=round(w_fft * 100.0, 0),
            role="Periodic upsampling grid & spectral roll-off detector",
            status=fft_status,
            finding=fft.interpretation,
        ),
        ChannelContribution(
            channel="EXIF / XMP / C2PA Provenance",
            layer="Layer 1",
            raw_score=round(meta.risk_contribution * 100.0, 1),
            weight=round(w_meta * 100.0, 0),
            role="Digital chain-of-custody & software footprint audit",
            status=meta_status,
            finding=meta.provenance_summary,
        ),
    ]

    key_findings: list[str] = []
    if dl.synthetic_probability >= 0.65:
        key_findings.append(
            f"Deep Vision classifier flagged {dl.synthetic_probability * 100:.1f}% synthetic probability, focused on the {dl.gradcam_peak_region}."
        )
    else:
        key_findings.append(
            f"Deep Vision classifier scored {dl.authentic_probability * 100:.1f}% authentic ({dl.synthetic_probability * 100:.1f}% synthetic)."
        )

    if ela.localized_tampering_score >= 0.55:
        key_findings.append(
            f"ELA identified {len(ela.hotspots)} high-variance compression hotspot(s) (peak {ela.hotspot_z_score:.1f}σ)."
        )
    else:
        key_findings.append(
            f"ELA shows uniform compression error distribution (mean {ela.mean_error:.2f}, peak {ela.hotspot_z_score:.1f}σ)."
        )

    if fft.periodic_peak_score >= 0.50:
        key_findings.append(
            f"2D FFT detected periodic off-axis spectral peaks (score {fft.periodic_peak_score:.2f}), typical of synthetic upsampling."
        )
    else:
        key_findings.append(
            f"2D FFT radial power spectrum follows slope {fft.spectral_slope:.2f} with HF/LF ratio {fft.high_freq_energy_ratio:.2f}."
        )

    key_findings.append(meta.provenance_summary)

    limitations_note = (
        "Decision-support signal only—not standalone legal proof. Heavy messaging-app re-compression (WhatsApp/Instagram) "
        "attenuates high-frequency and ELA cues, and unseen generative architectures can lower classifier confidence."
    )

    return VerdictResult(
        verdict_code=verdict_code,
        verdict_label=verdict_label,
        severity=severity,
        confidence_percent=confidence,
        full_frame_synthetic_score=full_frame_score,
        localized_tampering_score=localized_tamper_score,
        executive_summary=exec_summary,
        key_findings=key_findings,
        limitations_note=limitations_note,
        channel_breakdown=channel_breakdown,
    )
