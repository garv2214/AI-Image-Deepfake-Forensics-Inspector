"use client";

import {
  ResponsiveContainer,
  AreaChart,
  Area,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
} from "recharts";
import type { FFTResult } from "@/types/forensics";

interface FrequencyChartProps {
  fft: FFTResult;
}

export function FrequencyChart({ fft }: FrequencyChartProps) {
  return (
    <div className="grid grid-cols-1 gap-5 lg:grid-cols-5">
      {/* Radial Azimuthal Power Chart */}
      <div className="rounded-2xl border border-slate-800 bg-[#0a101d] p-4 lg:col-span-3">
        <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
          <div>
            <h4 className="text-sm font-semibold text-slate-100">
              Azimuthal Radial Frequency Profile
            </h4>
            <p className="text-xs text-slate-400">
              Observed radial FFT power vs. expected natural camera 1/f<sup>&alpha;</sup> optical decay
            </p>
          </div>
          <span className="rounded-md border border-cyan-500/30 bg-cyan-500/10 px-2 py-0.5 font-mono text-xs text-cyan-300">
            Anomaly: {(fft.frequency_anomaly_score * 100).toFixed(1)}%
          </span>
        </div>

        <div className="h-64 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart
              data={fft.radial_profile}
              margin={{ top: 10, right: 12, left: -16, bottom: 4 }}
            >
              <defs>
                <linearGradient id="fftObservedFill" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#22d3ee" stopOpacity={0.38} />
                  <stop offset="95%" stopColor="#22d3ee" stopOpacity={0.02} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.12)" />
              <XAxis
                dataKey="radius_norm"
                stroke="#64748b"
                tick={{ fontSize: 11, fill: "#94a3b8" }}
                tickFormatter={(v) => `${Math.round(Number(v) * 100)}%`}
              />
              <YAxis
                stroke="#64748b"
                tick={{ fontSize: 11, fill: "#94a3b8" }}
                domain={[0, 1]}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: "#0c1220",
                  borderColor: "rgba(56,189,248,0.35)",
                  borderRadius: "10px",
                  fontSize: "12px",
                  color: "#e2e8f0",
                }}
                labelFormatter={(v) => `Normalized Spatial Frequency: ${Math.round(Number(v) * 100)}%`}
              />
              <Area
                type="monotone"
                dataKey="observed_power"
                name="Observed Image Power"
                stroke="#22d3ee"
                strokeWidth={2.2}
                fill="url(#fftObservedFill)"
              />
              <Line
                type="monotone"
                dataKey="natural_reference"
                name="Natural Camera 1/f Reference"
                stroke="#f59e0b"
                strokeDasharray="5 4"
                strokeWidth={1.8}
                dot={false}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        <div className="mt-3 grid grid-cols-3 gap-2.5 border-t border-slate-800/80 pt-3">
          <div className="rounded-xl bg-slate-900/70 p-2.5">
            <p className="text-[11px] text-slate-400">HF / LF Ratio</p>
            <p className="mt-0.5 font-mono text-sm font-semibold text-slate-100">
              {fft.high_freq_energy_ratio.toFixed(3)}
            </p>
          </div>
          <div className="rounded-xl bg-slate-900/70 p-2.5">
            <p className="text-[11px] text-slate-400">Spectral Slope</p>
            <p className="mt-0.5 font-mono text-sm font-semibold text-slate-100">
              {fft.spectral_slope.toFixed(2)}
            </p>
          </div>
          <div className="rounded-xl bg-slate-900/70 p-2.5">
            <p className="text-[11px] text-slate-400">Periodic Peak Score</p>
            <p className="mt-0.5 font-mono text-sm font-semibold text-amber-300">
              {(fft.periodic_peak_score * 100).toFixed(1)}%
            </p>
          </div>
        </div>
      </div>

      {/* 2D Spectrum Preview + Interpretation */}
      <div className="flex flex-col justify-between rounded-2xl border border-slate-800 bg-[#0a101d] p-4 lg:col-span-2">
        <div>
          <h4 className="text-sm font-semibold text-slate-100">
            2D Log-Magnitude Spectrum
          </h4>
          <p className="mt-0.5 text-xs text-slate-400">
            Hann-windowed DC-centered Fourier transform
          </p>
          <div className="mt-3 flex items-center justify-center rounded-xl border border-slate-800 bg-[#05080f] p-2">
            <img
              src={fft.fft_spectrum_b64}
              alt="2D FFT Magnitude Spectrum"
              className="h-56 w-56 rounded-lg object-contain"
            />
          </div>
        </div>

        <p className="mt-3 rounded-xl border border-slate-800 bg-slate-900/60 p-3 text-xs leading-relaxed text-slate-300">
          {fft.interpretation}
        </p>
      </div>
    </div>
  );
}
