import { useCallback, useSyncExternalStore } from "react";

export type DensityMode = "compact" | "comfortable";

const DENSITY_STORAGE_KEY = "agentops:ui-density";
const DEFAULT_DENSITY: DensityMode = "compact";
const densityListeners = new Set<() => void>();

function isDensityMode(value: string | null): value is DensityMode {
  return value === "compact" || value === "comfortable";
}

export function getStoredDensityMode(): DensityMode {
  if (typeof window === "undefined") {
    return DEFAULT_DENSITY;
  }

  const stored = window.localStorage.getItem(DENSITY_STORAGE_KEY);
  return isDensityMode(stored) ? stored : DEFAULT_DENSITY;
}

export function applyDensityMode(mode: DensityMode) {
  document.documentElement.dataset.density = mode;
  window.localStorage.setItem(DENSITY_STORAGE_KEY, mode);
  densityListeners.forEach((listener) => listener());
}

function subscribeDensity(listener: () => void) {
  densityListeners.add(listener);
  return () => densityListeners.delete(listener);
}

export function useDensityMode() {
  const density = useSyncExternalStore(subscribeDensity, getStoredDensityMode, () => DEFAULT_DENSITY);
  const setDensity = useCallback((mode: DensityMode) => applyDensityMode(mode), []);

  return { density, setDensity };
}
