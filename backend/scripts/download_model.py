"""Pre-download and cache the HuggingFace AI-image detector for 100% offline viva demos."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import settings
from app.forensics.deep_model import deep_model_engine


def main() -> None:
    print(f"[download_model] Target model : {settings.hf_model_id}")
    print(f"[download_model] Cache folder : {settings.model_cache_dir}")
    deep_model_engine.load()
    print(f"[download_model] Mode         : {deep_model_engine.backend_mode}")
    print(f"[download_model] Device       : {deep_model_engine.device}")
    print(f"[download_model] Offline ready: {deep_model_engine.offline_ready}")


if __name__ == "__main__":
    main()
