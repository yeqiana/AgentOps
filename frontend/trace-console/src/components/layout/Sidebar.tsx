import { NavLink } from 'react-router-dom';
import { NAVIGATION_SECTIONS } from '../../config/navigation.config';
import { UI_TEXT } from '../../constants/uiText';
import { usePermission } from '../../features/auth/usePermission';

function buildBadge(item: string) {
  return item.slice(0, 1).toUpperCase();
}

export function Sidebar() {
  const { hasAnyPermission } = usePermission();
  const visibleSections = NAVIGATION_SECTIONS.map((section) => ({
    ...section,
    items: section.items.filter((item) => !item.permissionCodes || hasAnyPermission(item.permissionCodes))
  })).filter((section) => section.items.length > 0);

  return (
    <aside className="layout-sidebar">
      <div className="sidebar-brand">
        <span className="sidebar-logo">AO</span>
        <div>
          <strong>{UI_TEXT.shell.productName}</strong>
          <span>{UI_TEXT.shell.productSubtitle}</span>
        </div>
      </div>

      <div className="sidebar-overview-card">
        <p className="app-eyebrow">Web Admin</p>
        <strong>统一运行、观测与治理</strong>
        <span>按主流 SaaS 控制台骨架组织信息，保持高密度与清晰层级。</span>
      </div>

      <nav className="sidebar-nav" aria-label={UI_TEXT.app.navigationLabel}>
        {visibleSections.map((section) => (
          <section className="sidebar-section" key={section.title}>
            <p>{section.title}</p>
            {section.items.map((item) =>
              item.disabled ? (
                <span className="sidebar-link sidebar-link-disabled" key={item.label}>
                  <span className="sidebar-link-content">
                    <span className="sidebar-link-icon" aria-hidden="true">{buildBadge(item.label)}</span>
                    <span>{item.label}</span>
                  </span>
                </span>
              ) : (
                <NavLink className="sidebar-link" to={item.to} key={item.label}>
                  <span className="sidebar-link-content">
                    <span className="sidebar-link-icon" aria-hidden="true">{buildBadge(item.label)}</span>
                    <span>{item.label}</span>
                  </span>
                  {item.badge ? <small>{item.badge}</small> : null}
                </NavLink>
              )
            )}
          </section>
        ))}
      </nav>
    </aside>
  );
}
