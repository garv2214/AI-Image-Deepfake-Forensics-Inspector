"""Configuration settings for the AI-Image & Deepfake Forensics Inspector backend."""

from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="FORENSICS_")

    app_name: str = "AI-Image & Deepfake Forensics Inspector"
    app_version: str = "1.0.0"

    # Ingestion & Ephemeral Security
    max_file_size_bytes: int = 10 * 1024 * 1024  # 10 MB
    allowed_mime_types: tuple[str, ...] = (
        "image/jpeg",
        "image/png",
        "image/webp",
    )
    allowed_formats: tuple[str, ...] = ("JPEG", "PNG", "WEBP")
    max_display_dimension: int = 1024

    # Layer 2: Signal Processing
    ela_quality: int = 90
    ela_scale_cap: float = 24.0
    ela_grid_size: int = 16  # 16x16 grid for localized tampering variance detection

    # Layer 3: Deep Learning Model
    # Organika/sdxl-detector is a compact Swin Transformer (~110MB) fine-tuned
    # on real photography vs modern diffusion outputs; runs locally offline once cached.
    hf_model_id: str = "Organika/sdxl-detector"
    model_cache_dir: str = str(
        Path(__file__).resolve().parent.parent / "model_cache"
    )
    local_files_only: bool = False
    prefer_mps: bool = True

    # Layer 4: Calibrated Fusion Weights (Full-Frame Synthetic Axis)
    weight_deep_model: float = 0.68
    weight_fft: float = 0.14
    weight_ela_synthetic: float = 0.08
    weight_metadata: float = 0.10

    # Demo Samples Directory
    demo_samples_dir: str = str(
        Path(__file__).resolve().parent.parent.parent / "demo_samples"
    )

    # CORS
    cors_origins: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]


settings = Settings()
