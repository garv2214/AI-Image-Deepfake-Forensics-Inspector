"use client";

import { Camera, FileWarning, Sparkles, ShieldCheck, Info } from "lucide-react";
import type { MetadataEntry, MetadataReport } from "@/types/forensics";

interface MetadataAuditTableProps {
  metadata: MetadataReport;
}

const SIG_BADGE: Record<
  MetadataEntry["significance"],
  { label: string; classes: string }
> = {
  authentic_signal: {
    label: "Hardware / Auth Signal",
    classes: "border-emerald-500/35 bg-emerald-500/10 text-emerald-300",
  },
  editing_flag: {
    label: "Editing Footprint",
    classes: "border-amber-500/35 bg-amber-500/10 text-amber-300",
  },
  ai_signature: {
    label: "AI Generator Tag",
    classes: "border-rose-500/35 bg-rose-500/10 text-rose-300",
  },
  neutral: {
    label: "Contextual / Neutral",
    classes: "border-slate-700 bg-slate-800/70 text-slate-300",
  },
};

export function MetadataAuditTable({ metadata }: MetadataAuditTableProps) {
  return (
    <div className="space-y-4">
      {/* Top Provenance Badges */}
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-3.5">
          <div className="flex items-center gap-2 text-xs text-slate-400">
            <Camera className="h-3.5 w-3.5 text-cyan-400" aria-hidden="true" />
            Camera Hardware
          </div>
          <p className="mt-1 truncate text-sm font-semibold text-slate-100">
            {metadata.camera_make_model || "None / Stripped"}
          </p>
        </div>

        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-3.5">
          <div className="flex items-center gap-2 text-xs text-slate-400">
            <ShieldCheck className="h-3.5 w-3.5 text-emerald-400" aria-hidden="true" />
            C2PA Credentials
          </div>
          <p className="mt-1 text-sm font-semibold text-slate-100">
            {metadata.has_c2pa_credentials ? "Manifest Detected" : "Not Embedded"}
          </p>
        </div>

        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-3.5">
          <div className="flex items-center gap-2 text-xs text-slate-400">
            <FileWarning className="h-3.5 w-3.5 text-amber-400" aria-hidden="true" />
            Editing Suite Tag
          </div>
          <p className="mt-1 truncate text-sm font-semibold text-slate-100">
            {metadata.editing_software_detected || "None Detected"}
          </p>
        </div>

        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-3.5">
          <div className="flex items-center gap-2 text-xs text-slate-400">
            <Sparkles className="h-3.5 w-3.5 text-rose-400" aria-hidden="true" />
            AI Generator Metadata
          </div>
          <p className="mt-1 truncate text-sm font-semibold text-slate-100">
            {metadata.ai_generator_detected || "None Detected"}
          </p>
        </div>
      </div>

      {/* Provenance Summary Banner */}
      <div className="flex items-start gap-2.5 rounded-xl border border-slate-800 bg-slate-900/50 p-3.5 text-xs text-slate-300">
        <Info className="mt-0.5 h-4 w-4 shrink-0 text-cyan-400" aria-hidden="true" />
        <p>{metadata.provenance_summary}</p>
      </div>

      {/* Accessible Responsive Container-Query Table (modern-web-guidance) */}
      <div
        tabIndex={0}
        role="region"
        aria-labelledby="metadata-audit-caption"
        className="forensic-table-wrapper forensic-scroller"
      >
        <table className="forensic-table">
          <caption id="metadata-audit-caption" className="sr-only">
            Layer 1 EXIF, XMP, PNG chunk, and C2PA provenance audit entries
          </caption>
          <thead>
            <tr>
              <th scope="col">Metadata Tag</th>
              <th scope="col">Extracted Value</th>
              <th scope="col">Category</th>
              <th scope="col">Forensic Signal</th>
            </tr>
          </thead>
          <tbody>
            {metadata.entries.map((entry, idx) => {
              const badge = SIG_BADGE[entry.significance];
              return (
                <tr key={`${entry.tag}-${idx}`}>
                  <th scope="row">{entry.tag}</th>
                  <td className="break-words font-mono text-xs text-slate-200">
                    {entry.value}
                  </td>
                  <td className="capitalize text-slate-400">{entry.category}</td>
                  <td>
                    <span
                      className={`inline-block rounded-md border px-2 py-0.5 font-mono text-[11px] font-medium ${badge.classes}`}
                    >
                      {badge.label}
                    </span>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
