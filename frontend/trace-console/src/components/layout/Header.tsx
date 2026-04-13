import { Link } from 'react-router-dom';
import { UI_CONFIG } from '../../config/ui.config';
import { SettingsPanel } from '../settings/SettingsPanel';
import { UserMenu } from './UserMenu';

export function Header() {
  return (
    <header className="layout-header">
      <div className="header-title-group">
        <p className="app-eyebrow">{UI_CONFIG.header.stage}</p>
        <div>
          <h1>{UI_CONFIG.header.title}</h1>
          <span>{UI_CONFIG.header.subtitle}</span>
        </div>
      </div>
      <div className="header-actions">
        {UI_CONFIG.header.showEnvironmentTag ? <span className="environment-tag">{UI_CONFIG.header.environmentLabel}</span> : null}
        <label className="header-search" aria-label={UI_CONFIG.header.searchPlaceholder}>
          <span className="header-search-icon" aria-hidden="true">⌕</span>
          <input aria-label={UI_CONFIG.header.searchPlaceholder} placeholder={UI_CONFIG.header.searchPlaceholder} />
        </label>
        <button className="button button-ghost" type="button">{UI_CONFIG.header.secondaryActionLabel}</button>
        <Link className="button button-primary" to="/console/traces">{UI_CONFIG.header.primaryActionLabel}</Link>
        <SettingsPanel />
        <UserMenu />
      </div>
    </header>
  );
}
