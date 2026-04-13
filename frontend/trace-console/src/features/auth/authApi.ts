import { getStoredCredential } from "./authStorage";
import type { AuthProfile } from "./auth.types";

interface AuthMeResponse {
  profile?: {
    auth_subject?: string;
    auth_type?: string;
    roles?: string[];
    permissions?: string[];
  };
}

function buildAuthUrl(path: string) {
  const baseUrl = import.meta.env.VITE_API_BASE_URL ?? "/api";
  const normalizedPath = `${baseUrl.replace(/\/$/, "")}/${path.replace(/^\//, "")}`;
  const url = new URL(normalizedPath, window.location.origin);
  return `${url.pathname}${url.search}`;
}

function normalizeAuthProfile(payload: AuthMeResponse): AuthProfile {
  const profile = payload.profile ?? {};
  return {
    subject: profile.auth_subject ?? "",
    roles: profile.roles ?? [],
    permissions: profile.permissions ?? [],
    authType: profile.auth_type ?? ""
  };
}

export async function getAuthMe(): Promise<AuthProfile> {
  const credential = getStoredCredential();
  const response = await fetch(buildAuthUrl("/auth/me"), {
    method: "GET",
    headers: {
      Accept: "application/json",
      ...(credential ? { "X-API-Key": credential } : {})
    }
  });

  if (!response.ok) {
    throw new Error(`Auth profile request failed with status ${response.status}`);
  }

  const payload = (await response.json()) as AuthMeResponse;
  return normalizeAuthProfile(payload);
}
