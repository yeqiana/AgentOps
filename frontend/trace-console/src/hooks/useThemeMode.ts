import { useCallback, useSyncExternalStore } from "react";

export type ThemeMode = "light" | "dark";

const THEME_STORAGE_KEY = "agentops:ui-theme";
const DEFAULT_THEME: ThemeMode = "light";
const themeListeners = new Set<() => void>();

function isThemeMode(value: string | null): value is ThemeMode {
  return value === "light" || value === "dark";
}

export function getStoredThemeMode(): ThemeMode {
  if (typeof window === "undefined") {
    return DEFAULT_THEME;
  }

  const stored = window.localStorage.getItem(THEME_STORAGE_KEY);
  return isThemeMode(stored) ? stored : DEFAULT_THEME;
}

export function applyThemeMode(mode: ThemeMode) {
  document.documentElement.dataset.theme = mode;
  window.localStorage.setItem(THEME_STORAGE_KEY, mode);
  themeListeners.forEach((listener) => listener());
}

function subscribeTheme(listener: () => void) {
  themeListeners.add(listener);
  return () => themeListeners.delete(listener);
}

export function useThemeMode() {
  const theme = useSyncExternalStore(subscribeTheme, getStoredThemeMode, () => DEFAULT_THEME);
  const setTheme = useCallback((mode: ThemeMode) => applyThemeMode(mode), []);

  return { theme, setTheme };
}
