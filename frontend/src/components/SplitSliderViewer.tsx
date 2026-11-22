"use client";

import { useState } from "react";
import {
  ReactCompareSlider,
  ReactCompareSliderImage,
  ReactCompareSliderHandle,
} from "react-compare-slider";
import { Layers, Eye, Info } from "lucide-react";
import type { AnalysisResponse } from "@/types/forensics";

interface SplitSliderViewerProps {
  report: AnalysisResponse;
}

type OverlayMode = "gradcam" | "ela_heat" | "ela_raw" | "fft";

const OVERLAY_META: Record<
  OverlayMode,
  {
    label: string;
    shortBadge: string;
    legendTitle: string;
    legendBody: string;
    gradientClass: string;
    lowLabel: string;
    highLabel: string;
  }
> = {
  gradcam: {
    label: "Grad-CAM Attribution",
    shortBadge: "Layer 3 • Deep Vision",
    legendTitle: "How to read Grad-CAM",
    legendBody:
      "Warm red/yellow zones mark the exact spatial pixels driving the neural network's authenticity prediction (e.g., synthetic skin textures, warped boundaries, or background artifacts). Cool blue zones had minimal impact.",
    gradientClass: "from-blue-600 via-emerald-400 via-yellow-400 to-rose-600",
    lowLabel: "Ignored / Low Weight",
    highLabel: "High Decision Impact",
  },
  ela_heat: {
    label: "ELA Splicing Heatmap",
    shortBadge: "Layer 2A • Q90 Inferno",
    legendTitle: "How to read Error Level Analysis",
    legendBody:
      "Authentic photos re-compressed at JPEG Q90 glow uniformly at similar contrast edges. Spliced or Photoshopped regions pasted from a different compression history light up sharply brighter (yellow/white) against darker surroundings.",
    gradientClass: "from-[#0a0720] via-purple-700 via-orange-500 to-yellow-200",
    lowLabel: "Uniform Compression",
    highLabel: "Mismatched / Spliced",
  },
  ela_raw: {
    label: "ELA Amplified RGB",
    shortBadge: "Layer 2A • Raw Residual",
    legendTitle: "Raw Amplified Compression Residual",
    legendBody:
      "Direct pixel-wise |Original − JPEG(Q90)| difference multiplied by the adaptive gain factor. Useful for spotting color-channel chrominance anomalies and pasted rectangular boundaries.",
    gradientClass: "from-black via-slate-500 to-white",
    lowLabel: "Zero Residual",
    highLabel: "Peak Residual",
  },
  fft: {
    label: "2D FFT Spectrum",
    shortBadge: "Layer 2B • Frequency Domain",
    legendTitle: "How to read the 2D FFT Spectrum",
    legendBody:
      "Low frequencies sit at the center (DC) and fine details radiate outward. Natural photographs decay smoothly; bright symmetric star-like dots off the center axes expose periodic neural upsampling grids (GANs/decoders).",
    gradientClass: "from-[#07061a] via-fuchsia-700 via-amber-500 to-yellow-100",
    lowLabel: "Low Spectral Power",
    highLabel: "Strong Frequency Peak",
  },
};

export function SplitSliderViewer({ report }: SplitSliderViewerProps) {
  const [mode, setMode] = useState<OverlayMode>(() =>
    report.layer4_verdict.verdict_code === "localized_manipulation_suspected"
      ? "ela_heat"
      : "gradcam"
  );
  const [showHotspots, setShowHotspots] = useState(true);

  const meta = OVERLAY_META[mode];

  const overlaySrc =
    mode === "gradcam"
      ? report.layer3_deep_learning.gradcam_overlay_b64
      : mode === "ela_heat"
        ? report.layer2_ela.ela_heatmap_b64
        : mode === "ela_raw"
          ? report.layer2_ela.ela_map_b64
          : report.layer2_fft.fft_spectrum_b64;

  const isElaMode = mode === "ela_heat" || mode === "ela_raw";

  return (
    <div className="space-y-4">
      {/* Layer Switcher Controls */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex flex-wrap items-center gap-2" role="group" aria-label="Select forensic overlay map">
          {(Object.keys(OVERLAY_META) as OverlayMode[]).map((key) => {
            const active = mode === key;
            return (
              <button
                key={key}
                type="button"
                onClick={() => setMode(key)}
                aria-pressed={active}
                className={`cursor-pointer rounded-xl border px-3 py-1.5 text-xs font-semibold transition focus-visible:outline-2 focus-visible:outline-cyan-400 ${
                  active
                    ? "border-cyan-400 bg-cyan-400/15 text-cyan-200 shadow-[0_0_16px_rgba(34,211,238,0.16)]"
                    : "border-slate-700/80 bg-slate-900/70 text-slate-300 hover:border-slate-600 hover:text-white"
                }`}
              >
                {OVERLAY_META[key].label}
              </button>
            );
          })}
        </div>

        {isElaMode && report.layer2_ela.hotspots.length > 0 && (
          <label className="inline-flex cursor-pointer items-center gap-2 rounded-lg border border-amber-500/35 bg-amber-500/10 px-3 py-1.5 text-xs font-medium text-amber-200">
            <input
              type="checkbox"
              checked={showHotspots}
              onChange={(e) => setShowHotspots(e.target.checked)}
              className="h-3.5 w-3.5"
            />
            Highlight {report.layer2_ela.hotspots.length} ELA Hotspot Zone(s)
          </label>
        )}
      </div>

      {/* Interactive Split-Slider Stage */}
      <div className="relative overflow-hidden rounded-2xl border border-slate-700/80 bg-[#05080f]">
        {/* Corner labels */}
        <div className="pointer-events-none absolute top-3 left-3 z-20 rounded-lg border border-slate-700/80 bg-slate-950/85 px-2.5 py-1 font-mono text-[11px] font-semibold text-slate-200 backdrop-blur-sm">
          ORIGINAL IMAGE
        </div>
        <div className="pointer-events-none absolute top-3 right-3 z-20 rounded-lg border border-cyan-500/40 bg-slate-950/85 px-2.5 py-1 font-mono text-[11px] font-semibold text-cyan-200 backdrop-blur-sm">
          {meta.label.toUpperCase()} &bull; {meta.shortBadge}
        </div>

        <div className="relative mx-auto max-h-[540px] w-full overflow-hidden">
          <ReactCompareSlider
            position={52}
            handle={
              <ReactCompareSliderHandle
                buttonStyle={{
                  backdropFilter: "blur(6px)",
                  background: "rgba(6, 9, 17, 0.9)",
                  border: "2px solid #22d3ee",
                  color: "#22d3ee",
                  boxShadow: "0 0 18px rgba(34,211,238,0.45)",
                }}
                linesStyle={{ background: "#22d3ee", width: 2 }}
              />
            }
            itemOne={
              <ReactCompareSliderImage
                src={report.original_image_b64}
                alt="Original uploaded image"
                style={{ objectFit: "contain", maxHeight: "540px", background: "#05080f" }}
              />
            }
            itemTwo={
              <div className="relative flex h-full w-full items-center justify-center bg-[#05080f]">
                <ReactCompareSliderImage
                  src={overlaySrc}
                  alt={meta.label}
                  style={{ objectFit: "contain", maxHeight: "540px", background: "#05080f" }}
                />
                {isElaMode && showHotspots && report.layer2_ela.hotspots.length > 0 && (
                  <div className="pointer-events-none absolute inset-0">
                    {report.layer2_ela.hotspots.map((spot, idx) => (
                      <div
                        key={idx}
                        style={{
                          left: `${spot.x_pct}%`,
                          top: `${spot.y_pct}%`,
                          width: `${spot.w_pct}%`,
                          height: `${spot.h_pct}%`,
                        }}
                        className="absolute border border-amber-400/90 bg-amber-400/15 shadow-[0_0_10px_rgba(245,158,11,0.5)]"
                        title={`ELA anomaly z-score: ${spot.z_score}σ`}
                      />
                    ))}
                  </div>
                )}
              </div>
            }
          />
        </div>
      </div>

      {/* Non-Technical Visual Legend for Viva Panelists */}
      <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4">
        <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
          <div className="flex items-start gap-2.5">
            <Info className="mt-0.5 h-4 w-4 shrink-0 text-cyan-400" aria-hidden="true" />
            <div>
              <h4 className="text-xs font-semibold tracking-wide text-slate-100 uppercase">
                {meta.legendTitle}
              </h4>
              <p className="mt-1 text-xs leading-relaxed text-slate-300">
                {meta.legendBody}
              </p>
            </div>
          </div>

          <div className="shrink-0 md:w-56">
            <div className={`h-2.5 w-full rounded-full bg-gradient-to-r ${meta.gradientClass}`} />
            <div className="mt-1 flex justify-between font-mono text-[10px] text-slate-400">
              <span>{meta.lowLabel}</span>
              <span>{meta.highLabel}</span>
            </div>
          </div>
        </div>

        <div className="mt-3 flex flex-wrap items-center gap-4 border-t border-slate-800/80 pt-2.5 font-mono text-[11px] text-slate-400">
          <span className="inline-flex items-center gap-1.5">
            <Eye className="h-3.5 w-3.5 text-cyan-400" aria-hidden="true" />
            Drag center divider left/right to align proof map over suspect anatomy or spliced objects
          </span>
          <span className="inline-flex items-center gap-1.5">
            <Layers className="h-3.5 w-3.5 text-emerald-400" aria-hidden="true" />
            Grad-CAM Peak: <strong className="text-slate-200">{report.layer3_deep_learning.gradcam_peak_region}</strong>
          </span>
        </div>
      </div>
    </div>
  );
}
