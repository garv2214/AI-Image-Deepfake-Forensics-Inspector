import { jsPDF } from "jspdf";
import type { AnalysisResponse } from "@/types/forensics";

export function downloadJsonDossier(report: AnalysisResponse): void {
  // Include full structured audit data; keep Base64 thumbnails compact or omit raw blobs on request
  const exportPayload = {
    schema_version: "1.0",
    generated_by: "AI-Image & Deepfake Forensics Inspector",
    analysis_id: report.analysis_id,
    analyzed_at_utc: report.analyzed_at_utc,
    total_latency_ms: report.total_latency_ms,
    ephemeral_notice: report.ephemeral_notice,
    image_info: report.image_info,
    verdict: report.layer4_verdict,
    layer1_metadata: report.layer1_metadata,
    layer2_ela: {
      ...report.layer2_ela,
      ela_map_b64: "[embedded PNG omitted in compact JSON — see PDF dossier for visual maps]",
      ela_heatmap_b64: "[embedded PNG omitted]",
    },
    layer2_fft: {
      ...report.layer2_fft,
      fft_spectrum_b64: "[embedded PNG omitted]",
    },
    layer3_deep_learning: {
      ...report.layer3_deep_learning,
      gradcam_overlay_b64: "[embedded PNG omitted]",
      gradcam_heatmap_b64: "[embedded PNG omitted]",
    },
  };

  const blob = new Blob([JSON.stringify(exportPayload, null, 2)], {
    type: "application/json",
  });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `forensic-dossier-${report.analysis_id}.json`;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

export function downloadPdfDossier(report: AnalysisResponse): void {
  const doc = new jsPDF({ orientation: "portrait", unit: "mm", format: "a4" });
  const pageW = doc.internal.pageSize.getWidth();
  const margin = 14;
  let y = 16;

  // Header Banner
  doc.setFillColor(12, 18, 30);
  doc.rect(0, 0, pageW, 30, "F");
  doc.setTextColor(240, 246, 255);
  doc.setFont("helvetica", "bold");
  doc.setFontSize(15);
  doc.text("AI-IMAGE & DEEPFAKE FORENSICS DOSSIER", margin, 13);

  doc.setFont("helvetica", "normal");
  doc.setFontSize(8.5);
  doc.setTextColor(148, 163, 184);
  doc.text(
    `Case ID: ${report.analysis_id}   |   UTC: ${report.analyzed_at_utc}   |   Latency: ${report.total_latency_ms} ms`,
    margin,
    21
  );
  doc.text(
    `File: ${report.image_info.filename} (${report.image_info.width}x${report.image_info.height} ${report.image_info.format}, SHA-256: ${report.image_info.sha256_prefix}...)`,
    margin,
    26
  );

  y = 38;

  // Verdict Summary Box
  const v = report.layer4_verdict;
  const accentColor: [number, number, number] =
    v.severity === "high"
      ? [220, 38, 38]
      : v.severity === "medium"
        ? [217, 119, 6]
        : v.severity === "low"
          ? [16, 185, 129]
          : [100, 116, 139];

  doc.setDrawColor(...accentColor);
  doc.setFillColor(248, 250, 252);
  doc.roundedRect(margin, y, pageW - margin * 2, 29, 2, 2, "FD");

  doc.setTextColor(...accentColor);
  doc.setFont("helvetica", "bold");
  doc.setFontSize(13);
  doc.text(`VERDICT: ${v.verdict_label.toUpperCase()}`, margin + 4, y + 8);

  doc.setTextColor(30, 41, 59);
  doc.setFont("helvetica", "bold");
  doc.setFontSize(9.5);
  doc.text(
    `Confidence: ${v.confidence_percent.toFixed(1)}%   |   Full-Frame Synthetic: ${v.full_frame_synthetic_score.toFixed(1)}%   |   Localized Tampering: ${v.localized_tampering_score.toFixed(1)}%`,
    margin + 4,
    y + 15
  );

  doc.setFont("helvetica", "normal");
  doc.setFontSize(8.5);
  const summaryLines = doc.splitTextToSize(v.executive_summary, pageW - margin * 2 - 8);
  doc.text(summaryLines, margin + 4, y + 21);

  y += 35;

  // 4-Panel Visual Evidence Grid (Original, Grad-CAM, ELA, FFT)
  doc.setFont("helvetica", "bold");
  doc.setFontSize(10.5);
  doc.setTextColor(15, 23, 42);
  doc.text("VISUAL FORENSIC EVIDENCE MAPS", margin, y);
  y += 4;

  const boxW = (pageW - margin * 2 - 6) / 2;
  const boxH = 44;

  const panels = [
    { label: "1. Original Uploaded Image", data: report.original_image_b64, fmt: "JPEG" },
    { label: "2. Layer 3: Grad-CAM Attribution Overlay", data: report.layer3_deep_learning.gradcam_overlay_b64, fmt: "PNG" },
    { label: "3. Layer 2A: Error Level Analysis (ELA @ Q90)", data: report.layer2_ela.ela_heatmap_b64, fmt: "PNG" },
    { label: "4. Layer 2B: 2D FFT Log-Magnitude Spectrum", data: report.layer2_fft.fft_spectrum_b64, fmt: "PNG" },
  ];

  panels.forEach((panel, idx) => {
    const col = idx % 2;
    const row = Math.floor(idx / 2);
    const px = margin + col * (boxW + 6);
    const py = y + row * (boxH + 9);

    doc.setFont("helvetica", "bold");
    doc.setFontSize(8);
    doc.setTextColor(51, 65, 85);
    doc.text(panel.label, px, py + 3.5);

    doc.setDrawColor(203, 213, 225);
    doc.rect(px, py + 5, boxW, boxH);
    try {
      doc.addImage(panel.data, panel.fmt, px + 0.5, py + 5.5, boxW - 1, boxH - 1, undefined, "FAST");
    } catch {
      doc.setFontSize(7.5);
      doc.text("[Visual map unavailable]", px + 4, py + 24);
    }
  });

  y += 2 * (boxH + 9) + 6;

  // Key Findings & Channel Breakdown
  doc.setFont("helvetica", "bold");
  doc.setFontSize(10.5);
  doc.setTextColor(15, 23, 42);
  doc.text("MULTI-LAYER FORENSIC SIGNAL BREAKDOWN", margin, y);
  y += 5;

  v.channel_breakdown.forEach((ch) => {
    doc.setFont("helvetica", "bold");
    doc.setFontSize(8.5);
    doc.setTextColor(15, 23, 42);
    doc.text(
      `[${ch.layer}] ${ch.channel} — Score: ${ch.raw_score.toFixed(1)}% (Weight: ${ch.weight}%) [${ch.status.toUpperCase()}]`,
      margin,
      y
    );
    y += 4;
    doc.setFont("helvetica", "normal");
    doc.setFontSize(8);
    doc.setTextColor(71, 85, 105);
    const lines = doc.splitTextToSize(ch.finding, pageW - margin * 2);
    doc.text(lines, margin + 2, y);
    y += lines.length * 3.8 + 2.5;
  });

  // Page 2: Metadata Audit Table + Limitations
  if (y > 245) {
    doc.addPage();
    y = 18;
  } else {
    y += 3;
  }

  doc.setFont("helvetica", "bold");
  doc.setFontSize(10.5);
  doc.setTextColor(15, 23, 42);
  doc.text("LAYER 1: EXIF & PROVENANCE AUDIT TRAIL", margin, y);
  y += 5;

  report.layer1_metadata.entries.slice(0, 14).forEach((entry) => {
    if (y > 270) {
      doc.addPage();
      y = 18;
    }
    doc.setFont("helvetica", "bold");
    doc.setFontSize(8);
    doc.setTextColor(30, 41, 59);
    doc.text(`${entry.tag}:`, margin, y);
    doc.setFont("helvetica", "normal");
    doc.setTextColor(71, 85, 105);
    const valLines = doc.splitTextToSize(entry.value, pageW - margin * 2 - 48);
    doc.text(valLines, margin + 48, y);
    y += Math.max(4.5, valLines.length * 3.8);
  });

  y += 5;
  if (y > 265) {
    doc.addPage();
    y = 18;
  }

  // Honest Limitations Footer
  doc.setFillColor(241, 245, 249);
  doc.roundedRect(margin, y, pageW - margin * 2, 16, 1.5, 1.5, "F");
  doc.setFont("helvetica", "bold");
  doc.setFontSize(7.5);
  doc.setTextColor(51, 65, 85);
  doc.text("ENGINEERING LIMITATIONS & DISCLAIMER", margin + 3, y + 4.5);
  doc.setFont("helvetica", "normal");
  const limLines = doc.splitTextToSize(v.limitations_note, pageW - margin * 2 - 6);
  doc.text(limLines, margin + 3, y + 9);

  doc.save(`forensic-dossier-${report.analysis_id}.pdf`);
}
