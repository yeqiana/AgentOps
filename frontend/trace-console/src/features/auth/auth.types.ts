export type AuthStatus = "idle" | "loading" | "authenticated" | "unauthenticated" | "error";

export interface AuthProfile {
  subject: string;
  roles: string[];
  permissions: string[];
  authType: string;
}

export interface AuthContextValue {
  status: AuthStatus;
  profile: AuthProfile | null;
  error: string | null;
  refreshProfile: () => Promise<AuthProfile | null>;
  setCredential: (credential: string) => Promise<AuthProfile | null>;
  logout: () => void;
}
