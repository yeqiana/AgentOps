import { Link } from "react-router-dom";
import { AuthLayout } from "../../layouts/AuthLayout";
import { UI_TEXT } from "../../constants/uiText";

export function LoginPage() {
  return (
    <AuthLayout>
      <div className="login-card">
        <div>
          <p className="app-eyebrow">{UI_TEXT.login.environmentHint}</p>
          <h2>{UI_TEXT.login.title}</h2>
          <p>{UI_TEXT.login.subtitle}</p>
        </div>

        {/* 登录表单区 */}
        <form className="login-form">
          <label>
            {UI_TEXT.login.accountLabel}
            <input placeholder={UI_TEXT.login.accountPlaceholder} />
          </label>
          <label>
            {UI_TEXT.login.passwordLabel}
            <input placeholder={UI_TEXT.login.passwordPlaceholder} type="password" />
          </label>
          <div className="login-form-options">
            <label>
              <input defaultChecked type="checkbox" />
              {UI_TEXT.login.rememberLogin}
            </label>
            <button type="button">{UI_TEXT.login.forgotPassword}</button>
          </div>
          <Link className="button button-primary" to="/console/observability">
            {UI_TEXT.action.login}
          </Link>
          <p className="login-form-hint">{UI_TEXT.login.formHint}</p>
        </form>
      </div>
    </AuthLayout>
  );
}
