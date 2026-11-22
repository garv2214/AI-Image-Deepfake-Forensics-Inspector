"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import {
  SlidersHorizontal,
  LayoutGrid,
  Activity,
  FileSearch,
  Scale,
  Cpu,
  Fingerprint,
  Waves,
  ScanEye,
} from "lucide-react";
import type {
  AnalysisResponse,
  DemoSampleItem,
  HealthResponse,
} from "@/types/forensics";
import {
  analyzeDemoSample,
  analyzeUploadedFile,
  fetchDemoSamples,
  fetchHealth,
} from "@/lib/api";
import { Header } from "@/components/Header";
import { UploadDropzone } from "@/components/UploadDropzone";
import { VerdictBanner } from "@/components/VerdictBanner";
import { SplitSliderViewer } from "@/components/SplitSliderViewer";
import { FourLayerGallery } from "@/components/FourLayerGallery";
import { FrequencyChart } from "@/components/FrequencyChart";
import { MetadataAuditTable } from "@/components/MetadataAuditTable";
import { SignalFusionPanel } from "@/components/SignalFusionPanel";

type TabId = "slider" | "gallery" | "fft" | "metadata" | "fusion";

const TABS: { id: TabId; label: string; icon: typeof SlidersHorizontal }[] = [
  { id: "slider", label: "Interactive Split-Slider", icon: SlidersHorizontal },
  { id: "gallery", label: "4-Layer Visual Board", icon: LayoutGrid },
  { id: "fft", label: "2D FFT Frequency", icon: Activity },
  { id: "metadata", label: "EXIF & C2PA Audit", icon: FileSearch },
  { id: "fusion", label: "Fusion Engine & Limits", icon: Scale },
];

export default function ForensicsDashboardPage() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [apiError, setApiError] = useState<string | null>(null);
  const [samples, setSamples] = useState<DemoSampleItem[]>([]);
  const [report, setReport] = useState<AnalysisResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<TabId>("slider");

  const tabRefs = useRef<Record<TabId, HTMLButtonElement | null>>({
    slider: null,
    gallery: null,
    fft: null,
    metadata: null,
    fusion: null,
  });

  useEffect(() => {
    let active = true;
    async function init() {
      try {
        const [h, s] = await Promise.all([fetchHealth(), fetchDemoSamples()]);
        if (!active) return;
        setHealth(h);
        setSamples(s);
        setApiError(null);
      } catch (err) {
        if (!active) return;
        setApiError(
          err instanceof Error
            ? err.message
            : "Could not reach FastAPI backend on http://127.0.0.1:8000"
        );
      }
    }
    init();
    return () => {
      active = false;
    };
  }, []);

  const handleFileSelected = useCallback(async (file: File) => {
    setIsLoading(true);
    setError(null);
    try {
      const result = await analyzeUploadedFile(file);
      setReport(result);
      setActiveTab("slider");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Analysis failed.");
    } finally {
      setIsLoading(false);
    }
  }, []);

  const handleSampleSelected = useCallback(async (sampleId: string) => {
    setIsLoading(true);
    setError(null);
    try {
      const result = await analyzeDemoSample(sampleId);
      setReport(result);
      setActiveTab("slider");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Demo analysis failed.");
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Accessible keyboard navigation (selection follows focus, Home/End/ArrowLeft/ArrowRight)
  const handleTabKeyDown = (
    e: React.KeyboardEvent<HTMLButtonElement>,
    idx: number
  ) => {
    let nextIdx: number | null = null;
    if (e.key === "ArrowRight") nextIdx = (idx + 1) % TABS.length;
    else if (e.key === "ArrowLeft")
      nextIdx = (idx - 1 + TABS.length) % TABS.length;
    else if (e.key === "Home") nextIdx = 0;
    else if (e.key === "End") nextIdx = TABS.length - 1;

    if (nextIdx !== null) {
      e.preventDefault();
      const nextTab = TABS[nextIdx];
      setActiveTab(nextTab.id);
      const btn = tabRefs.current[nextTab.id];
      btn?.focus();
      btn?.scrollIntoView({ block: "nearest", inline: "nearest" });
    }
  };

  return (
    <div className="flex min-h-screen flex-col">
      <Header health={health} apiError={apiError} />

      <main className="mx-auto w-full max-w-7xl flex-1 space-y-6 px-4 py-6 sm:px-6 lg:py-8">
        {apiError && (
          <div
            role="alert"
            className="rounded-xl border border-amber-500/40 bg-amber-500/10 px-4 py-3 text-sm text-amber-200"
          >
            <strong>Backend offline:</strong> {apiError}. Start the FastAPI server with{" "}
            <code className="rounded bg-slate-900 px-1.5 py-0.5 font-mono text-xs text-cyan-300">
              ./start_dev.sh
            </code>{" "}
            or{" "}
            <code className="rounded bg-slate-900 px-1.5 py-0.5 font-mono text-xs text-cyan-300">
              uvicorn app.main:app --port 8000
            </code>
            .
          </div>
        )}

        {/* Ingestion & Demo Samples (collapsible when inspecting a report) */}
        {!report ? (
          <>
            <UploadDropzone
              onFileSelected={handleFileSelected}
              onSampleSelected={handleSampleSelected}
              samples={samples}
              isLoading={isLoading}
              error={error}
            />

            {/* 4-Layer Architecture Overview Cards */}
            <section
              aria-label="4-layer forensic methodology"
              className="grid grid-cols-1 gap-4 pt-2 sm:grid-cols-2 lg:grid-cols-4"
            >
              {[
                {
                  layer: "LAYER 1",
                  title: "EXIF & C2PA Provenance",
                  icon: Fingerprint,
                  desc: "Audits camera hardware telemetry, editing software footprints (Photoshop/GIMP), SD prompt chunks, and C2PA manifests—treating missing EXIF as weak/neutral.",
                },
                {
                  layer: "LAYER 2A",
                  title: "Error Level Analysis (ELA)",
                  icon: ScanEye,
                  desc: "Re-encodes in RAM at JPEG Q90 and maps spatial block-variance z-scores to spotlight spliced objects and localized copy-move edits.",
                },
                {
                  layer: "LAYER 2B",
                  title: "2D FFT Frequency Domain",
                  icon: Waves,
                  desc: "Computes Hann-windowed 2D Fourier magnitude spectra and radial power decay curves to catch periodic GAN/decoder upsampling grids.",
                },
                {
                  layer: "LAYER 3 & 4",
                  title: "Deep Vision + Grad-CAM",
                  icon: Cpu,
                  desc: "Runs a local Swin Transformer AI detector with spatial Grad-CAM overlays, fused via calibrated weights separating full-frame AI vs. localized tampering.",
                },
              ].map((card) => {
                const Icon = card.icon;
                return (
                  <div
                    key={card.layer}
                    className="rounded-2xl border border-slate-800/80 bg-[#0c1220]/70 p-4"
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-mono text-[11px] font-semibold tracking-wider text-cyan-400">
                        {card.layer}
                      </span>
                      <Icon className="h-4 w-4 text-slate-400" aria-hidden="true" />
                    </div>
                    <h3 className="mt-2 text-sm font-semibold text-slate-100">
                      {card.title}
                    </h3>
                    <p className="mt-1.5 text-xs leading-relaxed text-slate-400">
                      {card.desc}
                    </p>
                  </div>
                );
              })}
            </section>
          </>
        ) : (
          <div className="space-y-6">
            <VerdictBanner
              report={report}
              onReset={() => {
                setReport(null);
                setError(null);
              }}
            />

            {/* Accessible Tabbed Forensics Workspace */}
            <section className="rounded-2xl border border-slate-800/90 bg-[#0c1220]/85 shadow-2xl">
              <div
                role="tablist"
                aria-label="Forensic inspection views"
                className="forensic-tablist px-3 pt-1"
              >
                {TABS.map((tab, idx) => {
                  const Icon = tab.icon;
                  const selected = activeTab === tab.id;
                  return (
                    <button
                      key={tab.id}
                      ref={(el) => {
                        tabRefs.current[tab.id] = el;
                      }}
                      id={`tab-${tab.id}`}
                      type="button"
                      role="tab"
                      aria-selected={selected}
                      tabIndex={selected ? 0 : -1}
                      onClick={(e) => {
                        setActiveTab(tab.id);
                        e.currentTarget.scrollIntoView({
                          block: "nearest",
                          inline: "nearest",
                        });
                      }}
                      onKeyDown={(e) => handleTabKeyDown(e, idx)}
                      className="forensic-tab inline-flex items-center gap-2"
                    >
                      <Icon className="h-4 w-4" aria-hidden="true" />
                      <span>{tab.label}</span>
                    </button>
                  );
                })}
              </div>

              {/* Panels have no padding/border directly so hidden panels render zero strip */}
              <div className="forensic-tabpanel-stack">
                <div
                  role="tabpanel"
                  aria-labelledby="tab-slider"
                  hidden={activeTab !== "slider"}
                >
                  <div className="p-4 sm:p-6">
                    <SplitSliderViewer report={report} />
                  </div>
                </div>

                <div
                  role="tabpanel"
                  aria-labelledby="tab-gallery"
                  hidden={activeTab !== "gallery"}
                >
                  <div className="p-4 sm:p-6">
                    <FourLayerGallery report={report} />
                  </div>
                </div>

                <div
                  role="tabpanel"
                  aria-labelledby="tab-fft"
                  hidden={activeTab !== "fft"}
                >
                  <div className="p-4 sm:p-6">
                    <FrequencyChart fft={report.layer2_fft} />
                  </div>
                </div>

                <div
                  role="tabpanel"
                  aria-labelledby="tab-metadata"
                  hidden={activeTab !== "metadata"}
                >
                  <div className="p-4 sm:p-6">
                    <MetadataAuditTable metadata={report.layer1_metadata} />
                  </div>
                </div>

                <div
                  role="tabpanel"
                  aria-labelledby="tab-fusion"
                  hidden={activeTab !== "fusion"}
                >
                  <div className="p-4 sm:p-6">
                    <SignalFusionPanel report={report} />
                  </div>
                </div>
              </div>
            </section>
          </div>
        )}
      </main>

      <footer className="border-t border-slate-800/70 bg-[#060911]/90 py-4 text-center text-xs text-slate-500">
        AI-Image &amp; Deepfake Forensics Inspector &bull; Layered Decision-Support Pipeline (EXIF/C2PA + ELA + 2D FFT + Deep Vision Grad-CAM) &bull; Local Offline Execution
      </footer>
    </div>
  );
}
