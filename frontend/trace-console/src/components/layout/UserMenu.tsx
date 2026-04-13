import { UI_TEXT } from "../../constants/uiText";

export function UserMenu() {
  return (
    <details className="user-menu">
      <summary>
        <span className="user-avatar">A</span>
        <span>
          <strong>{UI_TEXT.shell.userName}</strong>
          <small>{UI_TEXT.shell.userRole}</small>
        </span>
      </summary>
      <div className="user-menu-panel">
        <button type="button">{UI_TEXT.shell.profile}</button>
        <button type="button">{UI_TEXT.shell.accountSettings}</button>
        <button type="button">{UI_TEXT.shell.preferences}</button>
        <button type="button">{UI_TEXT.shell.switchEnvironment}</button>
        <button className="user-menu-danger" type="button">
          {UI_TEXT.shell.logout}
        </button>
      </div>
    </details>
  );
}
