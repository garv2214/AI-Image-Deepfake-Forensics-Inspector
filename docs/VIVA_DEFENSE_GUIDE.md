# Viva Defense & Presentation Guide

## 1. Live Demo Flow (Recommended 3-Minute Script)

1. **System Readiness Check (15 sec):** Point out the header bar showing `API Online`, `MPS` (Apple Silicon GPU acceleration) or `CPU`, the local HuggingFace Swin Transformer backbone (`Organika/sdxl-detector`), and `Offline Ready`—proving the entire pipeline runs 100% locally without campus Wi-Fi.
2. **Case 1 — Authentic DSLR Photo (30 sec):** Click **Authentic DSLR Capture** in the demo tray. Show the green *Likely Camera-Authentic* badge, intact Canon EOS R5 EXIF table, flat/uniform ELA map, and smooth $1/f$ radial FFT decay.
3. **Case 2 — Photoshop Spliced Forgery (45 sec):** Click **Photoshop Spliced Object**. Immediately switch to the **Interactive Split-Slider** with **ELA Splicing Heatmap** enabled. Drag the divider over the pasted patch so the panel sees the bright yellow/orange hotspot box + `Adobe Photoshop` EXIF flag—demonstrating why classical ELA catches localized edits that full-frame AI detectors can miss.
4. **Case 3 — AI-Generated Synthetic Image (45 sec):** Click **AI Synthetic Render + FFT Peaks** (or upload a real Midjourney/FLUX/SDXL portrait). Show the **Grad-CAM Attribution Overlay** highlighting the exact pixels driving the network's score, switch to the **2D FFT Frequency** tab to show off-axis periodic upsampling peaks and radial curve deviation, and inspect the embedded Stable Diffusion prompt chunk in Layer 1.
5. **Case 4 — Honest Engineering Edge Case + Export (45 sec):** Click **WhatsApp Re-Compressed Edge Case**. Explain how missing EXIF is intentionally treated as *weak/neutral* (never auto-flagged as fake) and how repeated social-media compression attenuates ELA/FFT signals. Finally, click **Export PDF Dossier** to generate a multi-page courtroom-style forensic summary in one click.

---

## 2. Anticipated Viva Questions & Strong Answers

### Q1: Why not just use a single neural network classifier?
- **Answer:** A single classifier has two blind spots: (1) localized Photoshop splicing on an otherwise authentic camera photo often looks mostly real to a full-frame AI detector, whereas ELA immediately exposes the mismatched JPEG compression boundary; (2) a bare probability number ("89% Fake") cannot be audited by a human investigator. Combining four orthogonal layers + Grad-CAM + ELA visual maps solves both single-point fragility and the black-box trust gap.

### Q2: Why don't you flag images with missing EXIF metadata as fake?
- **Answer:** Messaging apps (WhatsApp, Telegram, iMessage) and social platforms (Instagram, X, Facebook) automatically strip EXIF headers on upload to protect user privacy and reduce bandwidth. Flagging missing EXIF as fake would cause catastrophic false positives on genuine photos. Therefore, Layer 1 treats stripped EXIF strictly as a weak/neutral signal (`0.45` prior, `10%` weight).

### Q3: Why does ELA sometimes look completely uniform on an AI-generated image?
- **Answer:** ELA measures *differences in JPEG compression history* across regions of the same image. A freshly generated Midjourney or FLUX image saved once has uniform compression across all pixels, so ELA looks clean. That is precisely why our Layer 4 Fusion Engine separates **Full-Frame Synthetic Probability** (driven primarily by the Deep Vision Transformer + 2D FFT) from **Localized Tampering Score** (driven by ELA).

### Q4: How does Grad-CAM work on a Swin Transformer instead of a classic CNN?
- **Answer:** In `backend/app/forensics/deep_model.py`, we attach forward and full-backward PyTorch hooks to the final Swin spatial stage (`swin.layernorm`). The spatial patch tokens `(B, H*W, C)` are reshaped into a 2D feature grid `(B, C, H, W)`, channel-weighted by global-average-pooled gradients ($\alpha_k = \frac{1}{Z}\sum_{i,j} \frac{\partial y^c}{\partial A^k_{i,j}}$), passed through ReLU, and bicubically upsampled onto the original photograph.

### Q5: How do you guarantee user privacy?
- **Answer:** Uploaded files are read into a Python `bytes` buffer in RAM, validated by magic bytes and Pillow in `io.BytesIO()`, processed in memory across all 4 layers, and returned as transient Base64 visual maps. Zero uploaded images are ever written to disk.

### Q6: How do you quantitatively evaluate the system?
- **Answer:** Use `backend/scripts/evaluate_benchmark.py` on an unseen split of **CIFAKE** (Real vs. Stable Diffusion), **140k Real & Fake Faces** (StyleGAN), or **CASIA v2.0** (splicing):
  ```bash
  ./backend/.venv/bin/python backend/scripts/evaluate_benchmark.py \
      --dataset-dir /path/to/cifake_test \
      --max-per-class 500
  ```
  This automatically produces `evaluation_results/evaluation_report.md` with Confusion Matrix, Accuracy, Precision, Recall, F1-Score, ROC-AUC, and Mean/Median/P95 latency in milliseconds.
