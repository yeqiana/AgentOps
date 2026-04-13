import { useDensityMode, type DensityMode } from "../../hooks/useDensityMode";
import { useThemeMode, type ThemeMode } from "../../hooks/useThemeMode";

const densityOptions: Array<{ label: string; value: DensityMode }> = [
  { label: "Compact", value: "compact" },
  { label: "Comfortable", value: "comfortable" },
];

const themeOptions: Array<{ label: string; value: ThemeMode }> = [
  { label: "Light", value: "light" },
  { label: "Dark", value: "dark" },
];

export function SettingsPanel() {
  const { density, setDensity } = useDensityMode();
  const { theme, setTheme } = useThemeMode();

  return (
    <details className="settings-panel">
      <summary className="settings-trigger">Settings</summary>
      <div className="settings-menu" role="group" aria-label="UI settings">
        <section className="settings-section" aria-labelledby="density-setting-title">
          <p id="density-setting-title">Density</p>
          <div className="settings-options">
            {densityOptions.map((option) => (
              <button
                className={density === option.value ? "settings-option active" : "settings-option"}
                key={option.value}
                onClick={() => setDensity(option.value)}
                type="button"
                aria-pressed={density === option.value}
              >
                {option.label}
              </button>
            ))}
          </div>
        </section>
        <section className="settings-section" aria-labelledby="theme-setting-title">
          <p id="theme-setting-title">Theme</p>
          <div className="settings-options">
            {themeOptions.map((option) => (
              <button
                className={theme === option.value ? "settings-option active" : "settings-option"}
                key={option.value}
                onClick={() => setTheme(option.value)}
                type="button"
                aria-pressed={theme === option.value}
              >
                {option.label}
              </button>
            ))}
          </div>
        </section>
      </div>
    </details>
  );
}
