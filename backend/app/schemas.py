"""Pydantic schemas for the 4-layer forensic inspection API."""

from typing import Literal, Optional
from pydantic import BaseModel, Field


class ImageMetadataInfo(BaseModel):
    filename: str
    mime_type: str
    format: str
    width: int
    height: int
    file_size_bytes: int
    color_mode: str
    sha256_prefix: str


class MetadataEntry(BaseModel):
    tag: str
    value: str
    category: Literal["camera", "software", "provenance", "capture", "technical"]
    significance: Literal["authentic_signal", "editing_flag", "ai_signature", "neutral"]


class MetadataReport(BaseModel):
    has_exif: bool
    has_camera_signature: bool
    has_c2pa_credentials: bool
    editing_software_detected: Optional[str] = None
    ai_generator_detected: Optional[str] = None
    camera_make_model: Optional[str] = None
    capture_timestamp: Optional[str] = None
    color_profile: Optional[str] = None
    provenance_status: Literal[
        "verified_provenance",
        "camera_signature_present",
        "editing_software_flagged",
        "ai_metadata_found",
        "metadata_stripped",
    ]
    provenance_summary: str
    risk_contribution: float = Field(..., ge=0.0, le=1.0)
    entries: list[MetadataEntry]
    latency_ms: float


class HotspotRegion(BaseModel):
    x_pct: float
    y_pct: float
    w_pct: float
    h_pct: float
    z_score: float


class ELAResult(BaseModel):
    quality_used: int
    amplification_factor: float
    mean_error: float
    max_error: float
    std_error: float
    hotspot_z_score: float
    localized_tampering_score: float = Field(..., ge=0.0, le=1.0)
    is_lossless_source: bool
    hotspots: list[HotspotRegion]
    interpretation: str
    ela_map_b64: str
    ela_heatmap_b64: str
    latency_ms: float


class RadialFrequencyPoint(BaseModel):
    radius_norm: float
    observed_power: float
    natural_reference: float


class FFTResult(BaseModel):
    high_freq_energy_ratio: float
    spectral_slope: float
    periodic_peak_score: float = Field(..., ge=0.0, le=1.0)
    frequency_anomaly_score: float = Field(..., ge=0.0, le=1.0)
    radial_profile: list[RadialFrequencyPoint]
    interpretation: str
    fft_spectrum_b64: str
    latency_ms: float


class DeepLearningResult(BaseModel):
    model_id: str
    backend_mode: Literal["huggingface_transformer", "local_cnn_fallback"]
    device: str
    predicted_label: str
    synthetic_probability: float = Field(..., ge=0.0, le=1.0)
    authentic_probability: float = Field(..., ge=0.0, le=1.0)
    gradcam_method: str
    gradcam_peak_region: str
    gradcam_overlay_b64: str
    gradcam_heatmap_b64: str
    interpretation: str
    latency_ms: float


class ChannelContribution(BaseModel):
    channel: str
    layer: str
    raw_score: float
    weight: float
    role: str
    status: Literal["clean", "caution", "alert", "neutral"]
    finding: str


class VerdictResult(BaseModel):
    verdict_code: Literal[
        "likely_authentic",
        "localized_manipulation_suspected",
        "high_probability_ai",
        "inconclusive_recompressed",
    ]
    verdict_label: str
    severity: Literal["low", "medium", "high", "neutral"]
    confidence_percent: float = Field(..., ge=0.0, le=100.0)
    full_frame_synthetic_score: float = Field(..., ge=0.0, le=100.0)
    localized_tampering_score: float = Field(..., ge=0.0, le=100.0)
    executive_summary: str
    key_findings: list[str]
    limitations_note: str
    channel_breakdown: list[ChannelContribution]


class AnalysisResponse(BaseModel):
    analysis_id: str
    analyzed_at_utc: str
    total_latency_ms: float
    ephemeral_notice: str
    image_info: ImageMetadataInfo
    original_image_b64: str
    layer1_metadata: MetadataReport
    layer2_ela: ELAResult
    layer2_fft: FFTResult
    layer3_deep_learning: DeepLearningResult
    layer4_verdict: VerdictResult


class HealthResponse(BaseModel):
    status: str
    version: str
    model_id: str
    model_loaded: bool
    backend_mode: str
    device: str
    offline_ready: bool


class DemoSampleItem(BaseModel):
    id: str
    title: str
    category: Literal["authentic", "spliced", "ai_generated", "edge_case"]
    description: str
    expected_signal: str
    filename: str
    thumbnail_b64: str
