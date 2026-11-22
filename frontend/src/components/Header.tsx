"use client";

import { Cpu, ShieldCheck, WifiOff, Activity } from "lucide-react";
import type { HealthResponse } from "@/types/forensics";

interface HeaderProps {
  health: HealthResponse | null;
  apiError: string | null;
}

export function Header({ health, apiError }: HeaderProps) {
  return (
    <header className="sticky top-0 z-30 border-b border-slate-800/80 bg-[#060911]/90 backdrop-blur-md">
      <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-4 px-4 py-3.5 sm:px-6">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl border border-cyan-500/35 bg-cyan-500/10 text-cyan-400 shadow-[0_0_24px_rgba(34,211,238,0.18)]">
            <ShieldCheck className="h-5 w-5" aria-hidden="true" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-base font-bold tracking-tight text-slate-100 sm:text-lg">
                AI-Image &amp; Deepfake Forensics Inspector
              </h1>
              <span className="hidden rounded-md border border-cyan-500/30 bg-cyan-500/10 px-2 py-0.5 font-mono text-[11px] font-medium text-cyan-300 sm:inline-block">
                4-LAYER PIPELINE
              </span>
            </div>
            <p className="text-xs text-slate-400">
              Provenance Audit &bull; Error Level Analysis &bull; 2D FFT Spectrum &bull; Deep Vision + Grad-CAM
            </p>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-2 text-xs">
          {health ? (
            <>
              <span className="inline-flex items-center gap-1.5 rounded-full border border-emerald-500/30 bg-emerald-500/10 px-2.5 py-1 font-mono text-emerald-300">
                <Activity className="h-3.5 w-3.5" aria-hidden="true" />
                API Online
              </span>
              <span
                className="inline-flex items-center gap-1.5 rounded-full border border-slate-700 bg-slate-900/80 px-2.5 py-1 font-mono text-slate-300"
                title={`Active vision backbone: ${health.model_id}`}
              >
                <Cpu className="h-3.5 w-3.5 text-cyan-400" aria-hidden="true" />
                {health.device.toUpperCase()} &bull;{" "}
                <span className="max-w-[165px] truncate">{health.model_id}</span>
              </span>
              {health.offline_ready && (
                <span className="hidden items-center gap-1.5 rounded-full border border-slate-700/80 bg-slate-900/70 px-2.5 py-1 font-mono text-slate-300 md:inline-flex">
                  <WifiOff className="h-3.5 w-3.5 text-emerald-400" aria-hidden="true" />
                  Offline Ready
                </span>
              )}
            </>
          ) : (
            <span className="inline-flex items-center gap-1.5 rounded-full border border-amber-500/35 bg-amber-500/10 px-2.5 py-1 font-mono text-amber-300">
              {apiError ? "Backend Disconnected" : "Connecting to Engine..."}
            </span>
          )}
        </div>
      </div>
    </header>
  );
}
