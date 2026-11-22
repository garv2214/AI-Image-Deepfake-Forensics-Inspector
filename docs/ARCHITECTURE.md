# System Architecture & Data Flow Diagrams

These diagrams and mathematical formulations are formatted for direct reuse in your project synopsis, SRS report, and viva presentation slides.

---

## 1. High-Level System Architecture

```mermaid
flowchart LR
    User["Investigator / User"] --> UI["Next.js Dark Forensic Dashboard<br/>(Split-Slider, Charts, PDF/JSON Export)"]
    UI -- "POST /api/analyze (multipart/form-data)" --> API["FastAPI Async Gateway<br/>(In-Memory Magic-Byte & Size Validator)"]

    API --> Pool["Parallel ThreadPoolExecutor<br/>(RAM-Only Ephemeral Processing)"]

    Pool --> L1["Layer 1: Provenance & Metadata<br/>(EXIF, XMP, PNG Chunks, C2PA)"]
    Pool --> L2A["Layer 2A: Error Level Analysis<br/>(JPEG Q90 Re-Encode + 16×16 Z-Score)"]
    Pool --> L2B["Layer 2B: 2D FFT Spectrum<br/>(Hann Window + Radial 1/f + Grid Peaks)"]
    Pool --> L3["Layer 3: Deep Vision + Grad-CAM<br/>(Swin Transformer / MPS + Spatial Hooks)"]

    L1 --> L4["Layer 4: Calibrated Hybrid Fusion Engine<br/>(Full-Frame Synthetic vs Localized Tampering)"]
    L2A --> L4
    L2B --> L4
    L3 --> L4

    L4 -- "Verdict JSON + Base64 Proof Maps" --> UI
```

---

## 2. Data Flow Diagram — Level 0 (Context Diagram)

```mermaid
flowchart LR
    U["External Entity:<br/>User / Fact-Checker"] -- "Suspect Image<br/>(.jpg / .png / .webp, ≤10 MB)" --> S(("0.0<br/>AI-Image & Deepfake<br/>Forensics Inspector"))
    S -- "Aggregated Verdict,<br/>Visual Proof Maps (ELA, FFT, Grad-CAM),<br/>PDF / JSON Dossier" --> U
    M[("Local Pretrained<br/>Model Cache<br/>(Offline Weights)")] -- "Swin Transformer<br/>Parameters" --> S
```

---

## 3. Data Flow Diagram — Level 1 (Pipeline Decomposition)

```mermaid
flowchart TD
    Upload["Raw Image Bytes"] --> P1(("1.0<br/>Validate & Decode<br/>in RAM"))
    P1 -->|"Valid Bytes + PIL Image"| P2(("2.0<br/>EXIF / XMP / C2PA<br/>Header Parser"))
    P1 -->|"EXIF-Oriented RGB"| P3(("3.0<br/>ELA Re-Compression<br/>& Hotspot Grid"))
    P1 -->|"512×512 Grayscale"| P4(("4.0<br/>2D FFT Spectrum<br/>& Radial Profile"))
    P1 -->|"Normalized Tensor"| P5(("5.0<br/>Deep Vision Classifier<br/>+ Grad-CAM Backprop"))

    P2 -->|"Provenance Risk & Audit Table"| P6(("6.0<br/>Hybrid Fusion &<br/>Verdict Calibration"))
    P3 -->|"Tampering Score + ELA Maps"| P6
    P4 -->|"Spectral Anomaly + FFT Map"| P6
    P5 -->|"Synthetic Prob + Grad-CAM Overlay"| P6

    P6 -->|"Structured AnalysisResponse"| P7(("7.0<br/>Dashboard Renderer &<br/>PDF/JSON Exporter"))
```

---

## 4. Layer 4 Calibrated Fusion Formulation

Instead of naive equal averaging, the inspector separates two orthogonal forensic axes:

### Axis A: Full-Frame Synthetic Probability ($S_{\text{AI}}$)
$$
S_{\text{AI}} = 0.68 \cdot P_{\text{DL}} + 0.14 \cdot A_{\text{FFT}} + 0.08 \cdot C_{\text{ELA}} + 0.10 \cdot R_{\text{meta}}
$$

- **$P_{\text{DL}}$**: Softmax probability of the synthetic class from the fine-tuned Vision Transformer (`Organika/sdxl-detector`).
- **$A_{\text{FFT}}$**: Weighted combination of off-axis periodic grid peak z-score, radial $1/f^\alpha$ deviation, and high-frequency energy ratio.
- **$C_{\text{ELA}}$**: Secondary calibration signal (since single-pass diffusion renders tend to have uniform compression error).
- **$R_{\text{meta}}$**: Provenance prior (`0.12` for C2PA, `0.18` for camera telemetry, `0.45` neutral for stripped EXIF, `0.90` for explicit AI generator prompt chunks).

### Axis B: Localized Tampering Score ($S_{\text{tamper}}$)
$$
S_{\text{tamper}} = \min\!\left(0.98,\; \sigma\!\big(0.75(\bar{z}_{\text{top6}} - 3.6)\big) + B_{\text{cluster}} + \Delta_{\text{editor}}\right)
$$

- **$\bar{z}_{\text{top6}}$**: Mean robust z-score of the top 6 edge-normalized $16 \times 16$ ELA error blocks.
- **$B_{\text{cluster}}$**: Spatial hotspot cluster boost proportional to blocks exceeding $3.2\sigma$ and $\ge 1.8$ absolute error delta.
- **$\Delta_{\text{editor}}$**: $+0.16$ reinforcement when editing software tags (e.g., *Adobe Photoshop*, *GIMP*) are present in EXIF/XMP.
