import { UI_CONFIG } from "../../config/ui.config";
import { SettingsPanel } from "../settings/SettingsPanel";
import { UserMenu } from "./UserMenu";

export function Header() {
  return (
    <header className="layout-header">
      <div>
        <p className="app-eyebrow">{UI_CONFIG.header.stage}</p>
        <h1>{UI_CONFIG.header.title}</h1>
        <span>{UI_CONFIG.header.subtitle}</span>
      </div>
      <div className="header-actions">
        <input aria-label={UI_CONFIG.header.searchPlaceholder} placeholder={UI_CONFIG.header.searchPlaceholder} />
        {UI_CONFIG.header.showEnvironmentTag ? <span className="environment-tag">{UI_CONFIG.header.environmentLabel}</span> : null}
        <SettingsPanel />
        <UserMenu />
      </div>
    </header>
  );
}
