import { useNavigate } from "react-router-dom";
import { UI_TEXT } from "../../constants/uiText";
import { useAuth } from "../../features/auth/useAuth";

export function UserMenu() {
  const { logout, profile } = useAuth();
  const navigate = useNavigate();
  const subject = profile?.subject || "未认证主体";
  const roleText = profile?.roles.length ? profile.roles.join(", ") : "未分配角色";

  function handleLogout() {
    logout();
    navigate("/login", { replace: true });
  }

  return (
    <details className="user-menu">
      <summary>
        <span className="user-avatar">A</span>
        <span>
          <strong>{subject}</strong>
          <small>{roleText}</small>
        </span>
      </summary>
      <div className="user-menu-panel">
        <button type="button">{UI_TEXT.shell.profile}</button>
        <button type="button">{UI_TEXT.shell.accountSettings}</button>
        <button type="button">{UI_TEXT.shell.preferences}</button>
        <button type="button">{UI_TEXT.shell.switchEnvironment}</button>
        <button className="user-menu-danger" onClick={handleLogout} type="button">
          {UI_TEXT.shell.logout}
        </button>
      </div>
    </details>
  );
}
