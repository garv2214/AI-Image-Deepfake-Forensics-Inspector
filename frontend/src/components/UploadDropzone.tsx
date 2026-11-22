"use client";

import { useRef, useState } from "react";
import {
  UploadCloud,
  FileImage,
  Lock,
  Sparkles,
  Loader2,
  AlertTriangle,
  FlaskConical,
} from "lucide-react";
import type { DemoSampleItem } from "@/types/forensics";

interface UploadDropzoneProps {
  onFileSelected: (file: File) => void;
  onSampleSelected: (sampleId: string) => void;
  samples: DemoSampleItem[];
  isLoading: boolean;
  error: string | null;
}

const ACCEPTED_TYPES = ["image/jpeg", "image/png", "image/webp"];
const MAX_BYTES = 10 * 1024 * 1024;

const CATEGORY_STYLES: Record<
  DemoSampleItem["category"],
  { label: string; badgeClass: string }
> = {
  authentic: {
    label: "Authentic",
    badgeClass: "border-emerald-500/35 bg-emerald-500/10 text-emerald-300",
  },
  spliced: {
    label: "Spliced / Edited",
    badgeClass: "border-amber-500/35 bg-amber-500/10 text-amber-300",
  },
  ai_generated: {
    label: "AI Synthetic",
    badgeClass: "border-rose-500/35 bg-rose-500/10 text-rose-300",
  },
  edge_case: {
    label: "Edge Case",
    badgeClass: "border-slate-500/40 bg-slate-500/15 text-slate-300",
  },
};

export function UploadDropzone({
  onFileSelected,
  onSampleSelected,
  samples,
  isLoading,
  error,
}: UploadDropzoneProps) {
  const inputRef = useRef<HTMLInputElement | null>(null);
  const [dragActive, setDragActive] = useState(false);
  const [clientError, setClientError] = useState<string | null>(null);

  const validateAndDispatch = (file: File | undefined) => {
    if (!file) return;
    setClientError(null);

    if (!ACCEPTED_TYPES.includes(file.type)) {
      setClientError(
        `Unsupported file type (${file.type || "unknown"}). Upload JPEG, PNG, or WebP images only.`
      );
      return;
    }
    if (file.size > MAX_BYTES) {
      setClientError(
        `File is ${(file.size / (1024 * 1024)).toFixed(2)} MB. Maximum permitted size is 10 MB.`
      );
      return;
    }
    onFileSelected(file);
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setDragActive(false);
    if (isLoading) return;
    validateAndDispatch(e.dataTransfer.files?.[0]);
  };

  const activeError = clientError || error;

  return (
    <section className="space-y-6" aria-label="Image ingestion and live demo samples">
      {/* Main Drag & Drop Zone */}
      <div
        onDragOver={(e) => {
          e.preventDefault();
          if (!isLoading) setDragActive(true);
        }}
        onDragLeave={() => setDragActive(false)}
        onDrop={handleDrop}
        className={`relative overflow-hidden rounded-2xl border-2 border-dashed p-6 transition-all sm:p-8 ${
          dragActive
            ? "border-cyan-400 bg-cyan-500/10 shadow-[0_0_40px_rgba(34,211,238,0.16)]"
            : "border-slate-700/80 bg-[#0c1220]/80 hover:border-slate-600"
        }`}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".jpg,.jpeg,.png,.webp,image/jpeg,image/png,image/webp"
          className="sr-only"
          id="forensic-file-input"
          disabled={isLoading}
          onChange={(e) => {
            validateAndDispatch(e.target.files?.[0]);
            e.target.value = "";
          }}
        />

        <div className="flex flex-col items-center justify-center text-center">
          <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-2xl border border-cyan-500/30 bg-cyan-500/10 text-cyan-300">
            {isLoading ? (
              <Loader2 className="h-7 w-7 animate-spin" aria-hidden="true" />
            ) : (
              <UploadCloud className="h-7 w-7" aria-hidden="true" />
            )}
          </div>

          <h2 className="text-lg font-semibold text-slate-100 sm:text-xl">
            {isLoading
              ? "Running 4-Layer Parallel Forensic Pipeline..."
              : "Drop a suspect photograph to inspect"}
          </h2>
          <p className="mt-1.5 max-w-xl text-sm text-slate-400">
            {isLoading
              ? "Executing EXIF/C2PA header audit, JPEG Error Level Analysis, 2D FFT spectrum, and Deep Vision Grad-CAM concurrently."
              : "Drag and drop any JPG, PNG, or WebP photo (up to 10 MB) to expose AI generation, Photoshop splicing, and frequency anomalies with visual proof maps."}
          </p>

          <div className="mt-5 flex flex-wrap items-center justify-center gap-3">
            <button
              type="button"
              disabled={isLoading}
              onClick={() => inputRef.current?.click()}
              className="inline-flex cursor-pointer items-center gap-2 rounded-xl bg-cyan-400 px-5 py-2.5 text-sm font-semibold text-slate-950 transition hover:bg-cyan-300 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-cyan-300 disabled:cursor-not-allowed disabled:opacity-50"
            >
              <FileImage className="h-4 w-4" aria-hidden="true" />
              Select Image File
            </button>

            <span className="inline-flex items-center gap-1.5 rounded-xl border border-slate-700/70 bg-slate-900/70 px-3 py-2 text-xs text-slate-400">
              <Lock className="h-3.5 w-3.5 text-emerald-400" aria-hidden="true" />
              Ephemeral RAM-only processing &mdash; zero disk storage
            </span>
          </div>
        </div>

        {activeError && (
          <div
            role="alert"
            className="mt-5 flex items-start gap-2.5 rounded-xl border border-rose-500/40 bg-rose-500/10 px-4 py-3 text-left text-sm text-rose-200"
          >
            <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-rose-400" aria-hidden="true" />
            <span>{activeError}</span>
          </div>
        )}
      </div>

      {/* Curated Live-Demo Case Studies Tray */}
      {samples.length > 0 && (
        <div className="rounded-2xl border border-slate-800/80 bg-[#0c1220]/70 p-5">
          <div className="mb-3.5 flex flex-wrap items-center justify-between gap-2">
            <div className="flex items-center gap-2">
              <FlaskConical className="h-4 w-4 text-cyan-400" aria-hidden="true" />
              <h3 className="text-sm font-semibold tracking-wide text-slate-200 uppercase">
                Curated Live-Demo Test Suite
              </h3>
            </div>
            <span className="text-xs text-slate-400">
              Click any case study to run a live 4-layer forensic demo
            </span>
          </div>

          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {samples.map((sample) => {
              const style = CATEGORY_STYLES[sample.category];
              return (
                <button
                  key={sample.id}
                  type="button"
                  disabled={isLoading}
                  onClick={() => {
                    setClientError(null);
                    onSampleSelected(sample.id);
                  }}
                  className="group flex cursor-pointer items-start gap-3 rounded-xl border border-slate-800 bg-slate-900/60 p-3 text-left transition hover:border-cyan-500/45 hover:bg-slate-900 focus-visible:outline-2 focus-visible:outline-cyan-400 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  <img
                    src={sample.thumbnail_b64}
                    alt={sample.title}
                    className="h-16 w-16 shrink-0 rounded-lg border border-slate-700/80 object-cover"
                  />
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center justify-between gap-2">
                      <span
                        className={`inline-block rounded-md border px-1.5 py-0.5 font-mono text-[10px] font-medium ${style.badgeClass}`}
                      >
                        {style.label}
                      </span>
                      <Sparkles
                        className="h-3.5 w-3.5 text-slate-600 transition group-hover:text-cyan-400"
                        aria-hidden="true"
                      />
                    </div>
                    <p className="mt-1 truncate text-sm font-semibold text-slate-100">
                      {sample.title}
                    </p>
                    <p className="mt-0.5 line-clamp-2 text-xs text-slate-400">
                      {sample.expected_signal}
                    </p>
                  </div>
                </button>
              );
            })}
          </div>
        </div>
      )}
    </section>
  );
}
