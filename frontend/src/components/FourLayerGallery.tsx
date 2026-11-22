"use client";

import type { AnalysisResponse } from "@/types/forensics";

interface FourLayerGalleryProps {
  report: AnalysisResponse;
}

export function FourLayerGallery({ report }: FourLayerGalleryProps) {
  const cards = [
    {
      badge: "INPUT",
      title: "Original Photograph",
      metric: `${report.image_info.width}×${report.image_info.height} ${report.image_info.format}`,
      src: report.original_image_b64,
      caption: "EXIF-oriented reference frame held strictly in RAM for visual auditing.",
    },
    {
      badge: "LAYER 3 • GRAD-CAM",
      title: "Deep Vision Attribution Overlay",
      metric: `${(report.layer3_deep_learning.synthetic_probability * 100).toFixed(1)}% AI Prob • ${report.layer3_deep_learning.latency_ms} ms`,
      src: report.layer3_deep_learning.gradcam_overlay_b64,
      caption: report.layer3_deep_learning.interpretation,
    },
    {
      badge: "LAYER 2A • ELA @ Q90",
      title: "Error Level Analysis Heatmap",
      metric: `Peak ${report.layer2_ela.hotspot_z_score}σ • Gain ${report.layer2_ela.amplification_factor}×`,
      src: report.layer2_ela.ela_heatmap_b64,
      caption: report.layer2_ela.interpretation,
    },
    {
      badge: "LAYER 2B • 2D FFT",
      title: "Spatial Frequency Magnitude Spectrum",
      metric: `Periodic Peak ${report.layer2_fft.periodic_peak_score.toFixed(2)} • Slope ${report.layer2_fft.spectral_slope.toFixed(2)}`,
      src: report.layer2_fft.fft_spectrum_b64,
      caption: report.layer2_fft.interpretation,
    },
  ];

  return (
    <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
      {cards.map((card) => (
        <article
          key={card.title}
          className="flex flex-col overflow-hidden rounded-2xl border border-slate-800 bg-[#0a101d]"
        >
          <div className="flex items-center justify-between gap-2 border-b border-slate-800/80 px-4 py-2.5">
            <div>
              <span className="font-mono text-[10px] font-semibold tracking-wider text-cyan-400 uppercase">
                {card.badge}
              </span>
              <h4 className="text-sm font-semibold text-slate-100">{card.title}</h4>
            </div>
            <span className="rounded-md border border-slate-700/80 bg-slate-900 px-2 py-0.5 font-mono text-[11px] text-slate-300">
              {card.metric}
            </span>
          </div>

          <div className="flex h-64 items-center justify-center bg-[#05080f] p-2">
            <img
              src={card.src}
              alt={card.title}
              className="max-h-full max-w-full rounded-lg object-contain"
            />
          </div>

          <p className="border-t border-slate-800/80 bg-slate-900/40 px-4 py-3 text-xs leading-relaxed text-slate-300">
            {card.caption}
          </p>
        </article>
      ))}
    </div>
  );
}
