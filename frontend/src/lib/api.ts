export function getApiBase(): string {
  if (process.env.NEXT_PUBLIC_API_URL) {
    return process.env.NEXT_PUBLIC_API_URL;
  }
  if (typeof window !== "undefined" && window.location.hostname) {
    // Avoid IPv6 resolution issues on Windows by using 127.0.0.1 when on localhost
    const host = window.location.hostname === "localhost" ? "127.0.0.1" : window.location.hostname;
    return `http://${host}:8000`;
  }
  return "http://127.0.0.1:8000";
}

export const API_BASE = "http://127.0.0.1:8000";

export async function apiFetch(endpoint: string, options: RequestInit = {}) {
  const base = getApiBase();
  const url = endpoint.startsWith("http") ? endpoint : `${base}${endpoint.startsWith("/") ? endpoint : `/${endpoint}`}`;

  try {
    const res = await fetch(url, options);

    const contentType = res.headers.get("content-type") || "";
    let data: any = null;

    if (contentType.includes("application/json")) {
      data = await res.json().catch(() => null);
    } else {
      const text = await res.text().catch(() => "");
      try {
        data = JSON.parse(text);
      } catch {
        data = { detail: text };
      }
    }

    if (!res.ok) {
      const errorMessage = data?.detail || data?.message || data?.error || `Server responded with status ${res.status}`;
      throw new Error(errorMessage);
    }

    return data;
  } catch (err: any) {
    if (err.message?.includes("Failed to fetch") || err.message?.includes("NetworkError") || err.message?.includes("connect ECONNREFUSED")) {
      throw new Error(`Cannot connect to FastAPI backend at ${url}. Please ensure uvicorn is running: uv run uvicorn app:app --reload --host 0.0.0.0 --port 8000`);
    }
    throw err;
  }
}
