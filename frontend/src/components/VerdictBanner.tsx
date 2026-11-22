"use client";

import type { CSSProperties } from "react";
import {
  ShieldAlert,
  ShieldCheck,
  ScanSearch,
  HelpCircle,
  Clock,
  Download,
  FileJson,
  RotateCcw,
} from "lucide-react";
import type { AnalysisResponse } from "@/types/forensics";
import { downloadJsonDossier, downloadPdfDossier } from "@/lib/reportExport";

interface VerdictBannerProps {
  report: AnalysisResponse;
  onReset: () => void;
}

const SEVERITY_THEME = {
  high: {
    border: "border-rose-500/45",
    bg: "bg-gradient-to-br from-rose-950/40 via-[#0c1220] to-[#0c1220]",
    badge: "border-rose-500/45 bg-rose-500/15 text-rose-200",
    ringColor: "#f43f5e",
    icon: ShieldAlert,
  },
  medium: {
    border: "border-amber-500/45",
    bg: "bg-gradient-to-br from-amber-950/35 via-[#0c1220] to-[#0c1220]",
    badge: "border-amber-500/45 bg-amber-500/15 text-amber-200",
    ringColor: "#f59e0b",
    icon: ScanSearch,
  },
  low: {
    border: "border-emerald-500/45",
    bg: "bg-gradient-to-br from-emerald-950/35 via-[#0c1220] to-[#0c1220]",
    badge: "border-emerald-500/45 bg-emerald-500/15 text-emerald-200",
    ringColor: "#10b981",
    icon: ShieldCheck,
  },
  neutral: {
    border: "border-slate-500/45",
    bg: "bg-gradient-to-br from-slate-800/40 via-[#0c1220] to-[#0c1220]",
    badge: "border-slate-500/45 bg-slate-500/15 text-slate-200",
    ringColor: "#94a3b8",
    icon: HelpCircle,
  },
};

function ConfidenceRing({
  value,
  label,
  fillColor,
  size = 112,
}: {
  value: number;
  label: string;
  fillColor: string;
  size?: number;
}) {
  const clamped = Math.max(0, Math.min(100, value));
  const ringVars = {
    "--value": clamped,
    "--ring-fill": fillColor,
    "--ring-size": `${size}px`,
  } as CSSProperties;

  return (
    <div className="flex flex-col items-center gap-1.5">
      <div className="progress-ring-wrapper" style={ringVars}>
        <progress
          className="progress-ring"
          value={clamped}
          max={100}
          aria-label={label}
          aria-valuetext={`${clamped.toFixed(1)} percent`}
        />
        <div className="progress-ring-content" aria-hidden="true">
          <span className="font-mono text-xl font-bold text-slate-100">
            {clamped.toFixed(0)}%
          </span>
          <span className="text-[10px] font-medium tracking-wider text-slate-400 uppercase">
            {label}
          </span>
        </div>
      </div>
    </div>
  );
}

export function VerdictBanner({ report, onReset }: VerdictBannerProps) {
  const verdict = report.layer4_verdict;
  const theme = SEVERITY_THEME[verdict.severity];
  const Icon = theme.icon;

  return (
    <section
      aria-label="Aggregated forensic verdict"
      className={`rounded-2xl border p-5 shadow-xl sm:p-6 ${theme.border} ${theme.bg}`}
    >
      <div className="flex flex-col gap-6 lg:flex-row lg:items-center lg:justify-between">
        {/* Left: Verdict Identity & Executive Summary */}
        <div className="flex-1 space-y-3">
          <div className="flex flex-wrap items-center gap-2.5">
            <span
              className={`inline-flex items-center gap-2 rounded-full border px-3 py-1 text-xs font-semibold tracking-wide uppercase ${theme.badge}`}
            >
              <Icon className="h-4 w-4" aria-hidden="true" />
              {verdict.verdict_label}
            </span>
            <span className="rounded-md border border-slate-700/80 bg-slate-900/80 px-2.5 py-1 font-mono text-xs text-slate-300">
              {report.analysis_id}
            </span>
            <span className="inline-flex items-center gap-1 rounded-md border border-slate-800 bg-slate-900/70 px-2.5 py-1 font-mono text-xs text-cyan-300">
              <Clock className="h-3.5 w-3.5" aria-hidden="true" />
              {(report.total_latency_ms / 1000).toFixed(2)}s ({report.total_latency_ms.toFixed(0)} ms)
            </span>
          </div>

          <p className="max-w-3xl text-sm leading-relaxed text-slate-200 sm:text-base">
            {verdict.executive_summary}
          </p>

          {/* File telemetry strip */}
          <div className="flex flex-wrap items-center gap-x-4 gap-y-1 font-mono text-xs text-slate-400">
            <span>
              File: <strong className="text-slate-200">{report.image_info.filename}</strong>
            </span>
            <span>
              Dimensions:{" "}
              <strong className="text-slate-200">
                {report.image_info.width}&times;{report.image_info.height}
              </strong>
            </span>
            <span>
              Format: <strong className="text-slate-200">{report.image_info.format}</strong>
            </span>
            <span>
              Size:{" "}
              <strong className="text-slate-200">
                {(report.image_info.file_size_bytes / 1024).toFixed(1)} KB
              </strong>
            </span>
            <span>
              SHA-256: <strong className="text-slate-200">{report.image_info.sha256_prefix}&hellip;</strong>
            </span>
          </div>
        </div>

        {/* Right: Dual Forensic Axis Progress Rings */}
        <div className="flex flex-wrap items-center justify-start gap-5 sm:gap-6 lg:justify-end">
          <ConfidenceRing
            value={verdict.full_frame_synthetic_score}
            label="AI Synthetic"
            fillColor={
              verdict.full_frame_synthetic_score >= 62
                ? "#f43f5e"
                : verdict.full_frame_synthetic_score >= 42
                  ? "#f59e0b"
                  : "#10b981"
            }
          />
          <ConfidenceRing
            value={verdict.localized_tampering_score}
            label="ELA Tamper"
            fillColor={
              verdict.localized_tampering_score >= 60
                ? "#f59e0b"
                : verdict.localized_tampering_score >= 42
                  ? "#38bdf8"
                  : "#10b981"
            }
          />
        </div>
      </div>

      {/* Action Toolbar: Export Dossier & New Inspection */}
      <div className="mt-5 flex flex-wrap items-center justify-between gap-3 border-t border-slate-800/80 pt-4">
        <span className="font-mono text-xs text-slate-400">
          {report.ephemeral_notice}
        </span>

        <div className="flex flex-wrap items-center gap-2.5">
          <button
            type="button"
            onClick={() => downloadPdfDossier(report)}
            className="inline-flex cursor-pointer items-center gap-2 rounded-xl bg-cyan-400 px-3.5 py-2 text-xs font-semibold text-slate-950 transition hover:bg-cyan-300 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-cyan-300"
          >
            <Download className="h-3.5 w-3.5" aria-hidden="true" />
            Export PDF Dossier
          </button>
          <button
            type="button"
            onClick={() => downloadJsonDossier(report)}
            className="inline-flex cursor-pointer items-center gap-2 rounded-xl border border-slate-700 bg-slate-900/90 px-3.5 py-2 text-xs font-semibold text-slate-200 transition hover:border-cyan-500/50 hover:text-cyan-200 focus-visible:outline-2 focus-visible:outline-cyan-400"
          >
            <FileJson className="h-3.5 w-3.5" aria-hidden="true" />
            Export JSON Report
          </button>
          <button
            type="button"
            onClick={onReset}
            className="inline-flex cursor-pointer items-center gap-1.5 rounded-xl border border-slate-700/80 bg-transparent px-3 py-2 text-xs font-medium text-slate-300 transition hover:border-slate-500 hover:text-white focus-visible:outline-2 focus-visible:outline-cyan-400"
          >
            <RotateCcw className="h-3.5 w-3.5" aria-hidden="true" />
            Inspect Another
          </button>
        </div>
      </div>
    </section>
  );
}
