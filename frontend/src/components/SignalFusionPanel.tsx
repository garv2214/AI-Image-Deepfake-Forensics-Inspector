"use client";

import { AlertCircle, CheckCircle2, ShieldAlert, Scale, Clock } from "lucide-react";
import type { AnalysisResponse, ChannelContribution } from "@/types/forensics";

interface SignalFusionPanelProps {
  report: AnalysisResponse;
}

const STATUS_STYLE: Record<
  ChannelContribution["status"],
  { bar: string; badge: string; label: string }
> = {
  alert: {
    bar: "bg-rose-500",
    badge: "border-rose-500/40 bg-rose-500/15 text-rose-300",
    label: "Anomaly Flagged",
  },
  caution: {
    bar: "bg-amber-400",
    badge: "border-amber-500/40 bg-amber-500/15 text-amber-300",
    label: "Moderate Signal",
  },
  clean: {
    bar: "bg-emerald-400",
    badge: "border-emerald-500/40 bg-emerald-500/15 text-emerald-300",
    label: "Clean / Nominal",
  },
  neutral: {
    bar: "bg-slate-400",
    badge: "border-slate-600 bg-slate-800 text-slate-300",
    label: "Weak / Neutral",
  },
};

export function SignalFusionPanel({ report }: SignalFusionPanelProps) {
  const { layer4_verdict: verdict } = report;

  const timings = [
    { label: "Layer 1: Metadata", ms: report.layer1_metadata.latency_ms },
    { label: "Layer 2A: ELA", ms: report.layer2_ela.latency_ms },
    { label: "Layer 2B: 2D FFT", ms: report.layer2_fft.latency_ms },
    { label: "Layer 3: Deep Vision + Grad-CAM", ms: report.layer3_deep_learning.latency_ms },
  ];

  return (
    <div className="space-y-5">
      {/* Weighted Channel Contribution Cards */}
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        {verdict.channel_breakdown.map((ch) => {
          const st = STATUS_STYLE[ch.status];
          return (
            <div
              key={ch.channel}
              className="rounded-2xl border border-slate-800 bg-[#0a101d] p-4"
            >
              <div className="flex items-start justify-between gap-2">
                <div>
                  <span className="font-mono text-[10px] font-semibold tracking-wider text-cyan-400 uppercase">
                    {ch.layer} &bull; Fusion Weight {ch.weight}%
                  </span>
                  <h4 className="mt-0.5 text-sm font-semibold text-slate-100">
                    {ch.channel}
                  </h4>
                  <p className="text-xs text-slate-400">{ch.role}</p>
                </div>
                <span
                  className={`shrink-0 rounded-md border px-2 py-0.5 font-mono text-[11px] font-medium ${st.badge}`}
                >
                  {st.label}
                </span>
              </div>

              <div className="mt-3">
                <div className="mb-1 flex justify-between font-mono text-xs">
                  <span className="text-slate-400">Channel Signal Score</span>
                  <span className="font-semibold text-slate-100">
                    {ch.raw_score.toFixed(1)}%
                  </span>
                </div>
                <div className="h-2 w-full overflow-hidden rounded-full bg-slate-800">
                  <div
                    className={`h-full rounded-full transition-all duration-500 ${st.bar}`}
                    style={{ width: `${Math.max(4, Math.min(100, ch.raw_score))}%` }}
                  />
                </div>
              </div>

              <p className="mt-3 text-xs leading-relaxed text-slate-300">
                {ch.finding}
              </p>
            </div>
          );
        })}
      </div>

      {/* Parallel Execution Telemetry */}
      <div className="rounded-2xl border border-slate-800 bg-[#0a101d] p-4">
        <div className="mb-3 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Clock className="h-4 w-4 text-cyan-400" aria-hidden="true" />
            <h4 className="text-xs font-semibold tracking-wide text-slate-200 uppercase">
              Parallel Pipeline Latency Breakdown
            </h4>
          </div>
          <span className="font-mono text-xs text-cyan-300">
            Wall-Clock Total: {report.total_latency_ms.toFixed(0)} ms
          </span>
        </div>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          {timings.map((t) => (
            <div key={t.label} className="rounded-xl border border-slate-800/80 bg-slate-900/60 p-3">
              <p className="text-[11px] text-slate-400">{t.label}</p>
              <p className="mt-1 font-mono text-sm font-semibold text-slate-100">
                {t.ms.toFixed(1)} ms
              </p>
            </div>
          ))}
        </div>
      </div>

      {/* Key Findings + Honest Engineering Limitations */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <div className="rounded-2xl border border-slate-800 bg-[#0a101d] p-4">
          <div className="mb-2.5 flex items-center gap-2 text-xs font-semibold tracking-wide text-slate-200 uppercase">
            <CheckCircle2 className="h-4 w-4 text-emerald-400" aria-hidden="true" />
            Auditable Key Findings
          </div>
          <ul className="space-y-2 text-xs leading-relaxed text-slate-300">
            {verdict.key_findings.map((item, idx) => (
              <li key={idx} className="flex items-start gap-2">
                <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-cyan-400" />
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </div>

        <div className="rounded-2xl border border-amber-500/25 bg-amber-950/15 p-4">
          <div className="mb-2.5 flex items-center gap-2 text-xs font-semibold tracking-wide text-amber-200 uppercase">
            <Scale className="h-4 w-4 text-amber-400" aria-hidden="true" />
            Known Forensic Boundaries &amp; Limitations
          </div>
          <p className="text-xs leading-relaxed text-slate-300">
            {verdict.limitations_note}
          </p>
          <ul className="mt-3 space-y-1.5 text-xs text-slate-400">
            <li className="flex items-start gap-2">
              <AlertCircle className="mt-0.5 h-3.5 w-3.5 shrink-0 text-amber-400" aria-hidden="true" />
              <span>
                <strong className="text-slate-200">Social Media Re-Compression:</strong> Repeated WhatsApp/Instagram encoding strips EXIF and attenuates ELA &amp; FFT artifacts.
              </span>
            </li>
            <li className="flex items-start gap-2">
              <ShieldAlert className="mt-0.5 h-3.5 w-3.5 shrink-0 text-amber-400" aria-hidden="true" />
              <span>
                <strong className="text-slate-200">Cross-Generator Generalization:</strong> Unseen generative architectures require periodic model fine-tuning.
              </span>
            </li>
          </ul>
        </div>
      </div>
    </div>
  );
}
