"""Quantitative Benchmark Evaluator for Viva Presentation & Project Report.

Usage:
    python backend/scripts/evaluate_benchmark.py --dataset-dir /path/to/val_set --max-per-class 250

Expected folder structure inside --dataset-dir:
    real/   (authentic photographs: .jpg, .jpeg, .png, .webp)
    fake/   (AI-generated or forged images: .jpg, .jpeg, .png, .webp)

Outputs:
    evaluation_results/evaluation_report.json
    evaluation_results/evaluation_report.md
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path

from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.forensics.deep_model import deep_model_engine
from app.forensics.pipeline import run_forensic_pipeline

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp"}


def collect_images(folder: Path, limit: int) -> list[Path]:
    if not folder.exists():
        return []
    files = sorted(
        [p for p in folder.rglob("*") if p.is_file() and p.suffix.lower() in IMAGE_EXTS]
    )
    return files[:limit] if limit > 0 else files


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate AI-Image Forensics Inspector on a labeled dataset.")
    parser.add_argument("--dataset-dir", type=Path, required=True, help="Directory with real/ and fake/ subfolders")
    parser.add_argument("--max-per-class", type=int, default=250, help="Maximum images per class (0 = all)")
    parser.add_argument("--threshold", type=float, default=50.0, help="Decision threshold on full_frame_synthetic_score (0-100)")
    parser.add_argument("--output-dir", type=Path, default=Path("evaluation_results"))
    args = parser.parse_args()

    real_imgs = collect_images(args.dataset_dir / "real", args.max_per_class)
    fake_imgs = collect_images(args.dataset_dir / "fake", args.max_per_class)

    if not real_imgs or not fake_imgs:
        print(
            f"[ERROR] Need images in both {args.dataset_dir / 'real'} and {args.dataset_dir / 'fake'}.\n"
            f"Found: {len(real_imgs)} real, {len(fake_imgs)} fake."
        )
        sys.exit(1)

    deep_model_engine.load()
    print(f"Evaluating {len(real_imgs)} real + {len(fake_imgs)} fake images on {deep_model_engine.device}...")

    y_true: list[int] = []
    y_score: list[float] = []
    y_pred: list[int] = []
    latencies: list[float] = []

    samples = [(p, 0) for p in real_imgs] + [(p, 1) for p in fake_imgs]

    for idx, (img_path, label) in enumerate(samples, start=1):
        try:
            res = run_forensic_pipeline(img_path.read_bytes(), filename=img_path.name)
            score = res.layer4_verdict.full_frame_synthetic_score
            y_true.append(label)
            y_score.append(score / 100.0)
            y_pred.append(1 if score >= args.threshold else 0)
            latencies.append(res.total_latency_ms)
            if idx % 25 == 0 or idx == len(samples):
                print(f"  Processed {idx}/{len(samples)} (avg latency: {statistics.mean(latencies):.0f} ms)")
        except Exception as exc:
            print(f"  Skipped {img_path.name}: {exc}")

    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()
    metrics = {
        "total_evaluated": len(y_true),
        "real_count": sum(1 for y in y_true if y == 0),
        "fake_count": sum(1 for y in y_true if y == 1),
        "model_id": deep_model_engine.model_id,
        "device": str(deep_model_engine.device),
        "threshold": args.threshold,
        "accuracy": round(float(accuracy_score(y_true, y_pred)), 4),
        "precision": round(float(precision_score(y_true, y_pred, zero_division=0)), 4),
        "recall": round(float(recall_score(y_true, y_pred, zero_division=0)), 4),
        "f1_score": round(float(f1_score(y_true, y_pred, zero_division=0)), 4),
        "roc_auc": round(float(roc_auc_score(y_true, y_score)), 4),
        "confusion_matrix": {"tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp)},
        "latency_ms": {
            "mean": round(statistics.mean(latencies), 2),
            "median": round(statistics.median(latencies), 2),
            "p95": round(sorted(latencies)[int(0.95 * (len(latencies) - 1))], 2),
        },
    }

    args.output_dir.mkdir(parents=True, exist_ok=True)
    json_path = args.output_dir / "evaluation_report.json"
    md_path = args.output_dir / "evaluation_report.md"

    json_path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    md_report = f"""# Quantitative Evaluation Sheet — AI-Image & Deepfake Forensics Inspector

- **Model Backbone:** `{metrics['model_id']}` on `{metrics['device']}`
- **Sample Size:** {metrics['total_evaluated']} unseen images ({metrics['real_count']} Real, {metrics['fake_count']} Fake)
- **Decision Threshold:** {metrics['threshold']}%

## Classification Metrics

| Metric | Value |
| --- | --- |
| **Accuracy** | {metrics['accuracy'] * 100:.2f}% |
| **Precision** | {metrics['precision'] * 100:.2f}% |
| **Recall** | {metrics['recall'] * 100:.2f}% |
| **F1-Score** | {metrics['f1_score'] * 100:.2f}% |
| **ROC-AUC** | {metrics['roc_auc']:.4f} |

## Confusion Matrix

| | Predicted Authentic | Predicted Synthetic |
| --- | --- | --- |
| **Actual Authentic** | TN = {tn} | FP = {fp} |
| **Actual Synthetic** | FN = {fn} | TP = {tp} |

## End-to-End Inference Latency (All 4 Layers + Grad-CAM)

| Statistic | Latency (ms) |
| --- | --- |
| **Mean** | {metrics['latency_ms']['mean']} ms |
| **Median** | {metrics['latency_ms']['median']} ms |
| **P95** | {metrics['latency_ms']['p95']} ms |
"""
    md_path.write_text(md_report, encoding="utf-8")
    print(f"\nSaved quantitative reports to {json_path} and {md_path}")


if __name__ == "__main__":
    main()
