import axios from "axios";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000",
  timeout: 10000
});

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";
const API_KEY = import.meta.env.VITE_API_KEY;

if (API_KEY) {
  api.defaults.headers.common["X-API-Key"] = API_KEY;
}

async function withRetry(request, retries = 1) {
  try {
    return await request();
  } catch (error) {
    if (retries <= 0) {
      throw error;
    }
    await new Promise((resolve) => setTimeout(resolve, 400));
    return withRetry(request, retries - 1);
  }
}

export function readApiError(error) {
  if (error?.code === "ERR_NETWORK" || error?.message === "Network Error") {
    return "Runtime service is not reachable. Start the full app with scripts\\start_full_app.ps1.";
  }

  if (error?.code === "ECONNABORTED") {
    return "Runtime request timed out. Check that the full app is running and responsive.";
  }

  return (
    error?.response?.data?.error ??
    error?.response?.data?.detail ??
    error?.message ??
    "Request failed."
  );
}

export async function getHealth() {
  const response = await withRetry(() => api.get("/health"));
  return response.data;
}

export async function getHistory(limit = 100) {
  const response = await withRetry(() => api.get("/history", { params: { limit } }));
  return response.data.records ?? [];
}

export async function getReport() {
  const response = await withRetry(() => api.get("/report"));
  return response.data;
}

export async function getLiveStatus() {
  const response = await withRetry(() => api.get("/live/status"));
  return response.data;
}

export async function ingestLiveTick() {
  const response = await withRetry(() => api.post("/live/tick"));
  return response.data;
}

export async function getModelInfo() {
  const response = await withRetry(() => api.get("/model-info"));
  return response.data;
}

export async function getEda() {
  const response = await withRetry(() => api.get("/eda"));
  return response.data;
}

export async function getBenchmarkReport() {
  const response = await withRetry(() => api.get("/benchmark-report"));
  return response.data;
}

export async function predictFailure(payload) {
  const response = await withRetry(() => api.post("/predict", payload));
  return response.data;
}

export async function detectAnomaly(payload) {
  const response = await withRetry(() => api.post("/anomaly", payload));
  return response.data;
}

export async function runDiagnosis(payload) {
  const response = await withRetry(() => api.post("/diagnose", payload));
  return response.data;
}

export async function analyzeTelemetry(payload) {
  const response = await withRetry(() => api.post("/ai/analyze", payload));
  return response.data;
}

export async function runWhatIf(baseline, candidate) {
  const response = await withRetry(() => api.post("/ai/what-if", { baseline, candidate }));
  return response.data;
}

export async function getNovaBriefing() {
  const response = await withRetry(() => api.get("/ai/nova/briefing"));
  return response.data;
}

export async function uploadDataset(file) {
  const formData = new FormData();
  formData.append("file", file);
  const response = await api.post("/upload", formData, {
    headers: { "Content-Type": "multipart/form-data" }
  });
  return response.data;
}
