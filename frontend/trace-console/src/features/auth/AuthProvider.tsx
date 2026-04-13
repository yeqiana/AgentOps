import { createContext, type PropsWithChildren, useCallback, useEffect, useMemo, useState } from "react";
import { getAuthMe } from "./authApi";
import { clearStoredCredential, getStoredCredential, setStoredCredential } from "./authStorage";
import type { AuthContextValue, AuthProfile, AuthStatus } from "./auth.types";

export const AuthContext = createContext<AuthContextValue | null>(null);

function getErrorMessage(error: unknown) {
  return error instanceof Error ? error.message : "Authentication failed.";
}

export function AuthProvider({ children }: PropsWithChildren) {
  const [status, setStatus] = useState<AuthStatus>("idle");
  const [profile, setProfile] = useState<AuthProfile | null>(null);
  const [error, setError] = useState<string | null>(null);

  const refreshProfile = useCallback(async () => {
    setStatus("loading");
    setError(null);
    try {
      const nextProfile = await getAuthMe();
      setProfile(nextProfile);
      setStatus("authenticated");
      return nextProfile;
    } catch (refreshError) {
      const message = getErrorMessage(refreshError);
      clearStoredCredential();
      setProfile(null);
      setError(message);
      setStatus("unauthenticated");
      return null;
    }
  }, []);

  const setCredential = useCallback(
    async (credential: string) => {
      setStoredCredential(credential);
      return refreshProfile();
    },
    [refreshProfile]
  );

  const logout = useCallback(() => {
    clearStoredCredential();
    setProfile(null);
    setError(null);
    setStatus("unauthenticated");
  }, []);

  useEffect(() => {
    let isMounted = true;

    async function restoreAuthState() {
      const credential = getStoredCredential();
      if (!credential) {
        if (isMounted) {
          setProfile(null);
          setError(null);
          setStatus("unauthenticated");
        }
        return;
      }

      setStatus("loading");
      setError(null);
      try {
        const restoredProfile = await getAuthMe();
        if (!isMounted) {
          return;
        }
        setProfile(restoredProfile);
        setStatus("authenticated");
      } catch (restoreError) {
        if (!isMounted) {
          return;
        }
        clearStoredCredential();
        setProfile(null);
        setError(getErrorMessage(restoreError));
        setStatus("unauthenticated");
      }
    }

    void restoreAuthState();

    return () => {
      isMounted = false;
    };
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({ status, profile, error, refreshProfile, setCredential, logout }),
    [error, logout, profile, refreshProfile, setCredential, status]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
