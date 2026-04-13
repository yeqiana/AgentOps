const AUTH_CREDENTIAL_STORAGE_KEY = "agentops.traceConsole.auth.apiKey";

function canUseStorage() {
  return typeof window !== "undefined" && typeof window.localStorage !== "undefined";
}

export function getStoredCredential() {
  if (!canUseStorage()) {
    return null;
  }
  const credential = window.localStorage.getItem(AUTH_CREDENTIAL_STORAGE_KEY);
  return credential && credential.trim() ? credential : null;
}

export function setStoredCredential(credential: string) {
  if (!canUseStorage()) {
    return;
  }
  const normalizedCredential = credential.trim();
  if (!normalizedCredential) {
    clearStoredCredential();
    return;
  }
  window.localStorage.setItem(AUTH_CREDENTIAL_STORAGE_KEY, normalizedCredential);
}

export function clearStoredCredential() {
  if (!canUseStorage()) {
    return;
  }
  window.localStorage.removeItem(AUTH_CREDENTIAL_STORAGE_KEY);
}
