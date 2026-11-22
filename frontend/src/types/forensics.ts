export interface ImageMetadataInfo {
  filename: string;
  mime_type: string;
  format: string;
  width: number;
  height: number;
  file_size_bytes: number;
  color_mode: string;
  sha256_prefix: string;
}

export interface MetadataEntry {
  tag: string;
  value: string;
  category: "camera" | "software" | "provenance" | "capture" | "technical";
  significance: "authentic_signal" | "editing_flag" | "ai_signature" | "neutral";
}

export interface MetadataReport {
  has_exif: boolean;
  has_camera_signature: boolean;
  has_c2pa_credentials: boolean;
  editing_software_detected: string | null;
  ai_generator_detected: string | null;
  camera_make_model: string | null;
  capture_timestamp: string | null;
  color_profile: string | null;
  provenance_status:
    | "verified_provenance"
    | "camera_signature_present"
    | "editing_software_flagged"
    | "ai_metadata_found"
    | "metadata_stripped";
  provenance_summary: string;
  risk_contribution: number;
  entries: MetadataEntry[];
  latency_ms: number;
}

export interface HotspotRegion {
  x_pct: number;
  y_pct: number;
  w_pct: number;
  h_pct: number;
  z_score: number;
}

export interface ELAResult {
  quality_used: number;
  amplification_factor: number;
  mean_error: number;
  max_error: number;
  std_error: number;
  hotspot_z_score: number;
  localized_tampering_score: number;
  is_lossless_source: boolean;
  hotspots: HotspotRegion[];
  interpretation: string;
  ela_map_b64: string;
  ela_heatmap_b64: string;
  latency_ms: number;
}

export interface RadialFrequencyPoint {
  radius_norm: number;
  observed_power: number;
  natural_reference: number;
}

export interface FFTResult {
  high_freq_energy_ratio: number;
  spectral_slope: number;
  periodic_peak_score: number;
  frequency_anomaly_score: number;
  radial_profile: RadialFrequencyPoint[];
  interpretation: string;
  fft_spectrum_b64: string;
  latency_ms: number;
}

export interface DeepLearningResult {
  model_id: string;
  backend_mode: "huggingface_transformer" | "local_cnn_fallback";
  device: string;
  predicted_label: string;
  synthetic_probability: number;
  authentic_probability: number;
  gradcam_method: string;
  gradcam_peak_region: string;
  gradcam_overlay_b64: string;
  gradcam_heatmap_b64: string;
  interpretation: string;
  latency_ms: number;
}

export interface ChannelContribution {
  channel: string;
  layer: string;
  raw_score: number;
  weight: number;
  role: string;
  status: "clean" | "caution" | "alert" | "neutral";
  finding: string;
}

export interface VerdictResult {
  verdict_code:
    | "likely_authentic"
    | "localized_manipulation_suspected"
    | "high_probability_ai"
    | "inconclusive_recompressed";
  verdict_label: string;
  severity: "low" | "medium" | "high" | "neutral";
  confidence_percent: number;
  full_frame_synthetic_score: number;
  localized_tampering_score: number;
  executive_summary: string;
  key_findings: string[];
  limitations_note: string;
  channel_breakdown: ChannelContribution[];
}

export interface AnalysisResponse {
  analysis_id: string;
  analyzed_at_utc: string;
  total_latency_ms: number;
  ephemeral_notice: string;
  image_info: ImageMetadataInfo;
  original_image_b64: string;
  layer1_metadata: MetadataReport;
  layer2_ela: ELAResult;
  layer2_fft: FFTResult;
  layer3_deep_learning: DeepLearningResult;
  layer4_verdict: VerdictResult;
}

export interface HealthResponse {
  status: string;
  version: string;
  model_id: string;
  model_loaded: boolean;
  backend_mode: string;
  device: string;
  offline_ready: boolean;
}

export interface DemoSampleItem {
  id: string;
  title: string;
  category: "authentic" | "spliced" | "ai_generated" | "edge_case";
  description: string;
  expected_signal: string;
  filename: string;
  thumbnail_b64: string;
}
