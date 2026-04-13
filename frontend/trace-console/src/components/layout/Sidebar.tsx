import { NavLink } from "react-router-dom";
import { NAVIGATION_SECTIONS } from "../../config/navigation.config";
import { UI_TEXT } from "../../constants/uiText";

export function Sidebar() {
  return (
    <aside className="layout-sidebar">
      <div className="sidebar-brand">
        <span className="sidebar-logo">AO</span>
        <div>
          <strong>{UI_TEXT.shell.productName}</strong>
          <span>{UI_TEXT.shell.productSubtitle}</span>
        </div>
      </div>

      <nav className="sidebar-nav" aria-label={UI_TEXT.app.navigationLabel}>
        {NAVIGATION_SECTIONS.map((section) => (
          <section className="sidebar-section" key={section.title}>
            <p>{section.title}</p>
            {section.items.map((item) =>
              item.disabled ? (
                <span className="sidebar-link sidebar-link-disabled" key={item.label}>
                  {item.label}
                </span>
              ) : (
                <NavLink className="sidebar-link" to={item.to} key={item.label}>
                  <span>{item.label}</span>
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
