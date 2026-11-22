import type {
  AnalysisResponse,
  DemoSampleItem,
  HealthResponse,
} from "@/types/forensics";

const API_BASE =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") || "http://127.0.0.1:8000";

async function handleResponse<T>(resp: Response): Promise<T> {
  if (!resp.ok) {
    let detail = `Request failed (${resp.status})`;
    try {
      const errBody = await resp.json();
      if (errBody?.detail) detail = String(errBody.detail);
    } catch {
      // ignore non-json errors
    }
    throw new Error(detail);
  }
  return resp.json() as Promise<T>;
}

export async function fetchHealth(): Promise<HealthResponse> {
  const resp = await fetch(`${API_BASE}/api/health`, { cache: "no-store" });
  return handleResponse<HealthResponse>(resp);
}

export async function fetchDemoSamples(): Promise<DemoSampleItem[]> {
  const resp = await fetch(`${API_BASE}/api/samples`, { cache: "no-store" });
  return handleResponse<DemoSampleItem[]>(resp);
}

export async function analyzeUploadedFile(file: File): Promise<AnalysisResponse> {
  const form = new FormData();
  form.append("file", file);

  const resp = await fetch(`${API_BASE}/api/analyze`, {
    method: "POST",
    body: form,
  });
  return handleResponse<AnalysisResponse>(resp);
}

export async function analyzeDemoSample(sampleId: string): Promise<AnalysisResponse> {
  const resp = await fetch(
    `${API_BASE}/api/samples/${encodeURIComponent(sampleId)}/analyze`,
    { method: "POST" }
  );
  return handleResponse<AnalysisResponse>(resp);
}
