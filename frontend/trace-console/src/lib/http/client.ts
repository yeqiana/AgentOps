import { getStoredCredential } from "../../features/auth/authStorage";

export class HttpError extends Error {
  status: number;
  payload: unknown;

  constructor(message: string, status: number, payload: unknown) {
    super(message);
    this.name = "HttpError";
    this.status = status;
    this.payload = payload;
  }
}

type QueryValue = string | number | undefined;

function buildUrl(path: string, query?: Record<string, QueryValue>) {
  const baseUrl = import.meta.env.VITE_API_BASE_URL ?? "/api";
  const normalizedPath = `${baseUrl.replace(/\/$/, "")}/${path.replace(/^\//, "")}`;
  const url = new URL(normalizedPath, window.location.origin);
  if (query) {
    for (const [key, value] of Object.entries(query)) {
      if (value === undefined || value === "") {
        continue;
      }
      url.searchParams.set(key, String(value));
    }
  }
  return `${url.pathname}${url.search}`;
}

function buildHeaders() {
  const credential = getStoredCredential();
  return {
    Accept: "application/json",
    ...(credential ? { "X-API-Key": credential } : {})
  };
}

export async function getJson<T>(path: string, query?: Record<string, QueryValue>): Promise<T> {
  const response = await fetch(buildUrl(path, query), {
    method: "GET",
    headers: buildHeaders()
  });

  const text = await response.text();
  const payload = text ? (JSON.parse(text) as unknown) : null;

  if (!response.ok) {
    const message =
      typeof payload === "object" && payload !== null && "message" in payload
        ? String(payload.message)
        : `Request failed with status ${response.status}`;
    throw new HttpError(message, response.status, payload);
  }

  return payload as T;
}
