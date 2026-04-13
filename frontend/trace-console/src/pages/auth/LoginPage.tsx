import type { FormEvent } from "react";
import { useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { AuthLayout } from "../../layouts/AuthLayout";
import { UI_TEXT } from "../../constants/uiText";
import { useAuth } from "../../features/auth/useAuth";

interface RedirectState {
  from?: {
    pathname?: string;
    search?: string;
    hash?: string;
  };
}

export function LoginPage() {
  const { error, setCredential, status } = useAuth();
  const [credential, setCredentialInput] = useState("");
  const [submitError, setSubmitError] = useState<string | null>(null);
  const location = useLocation();
  const navigate = useNavigate();

  const isSubmitting = status === "loading";

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitError(null);

    const profile = await setCredential(credential);
    if (!profile) {
      setSubmitError(error ?? "开发凭证校验失败，请确认 API Key 是否有效。");
      return;
    }

    const redirectState = location.state as RedirectState | null;
    const from = redirectState?.from;
    const redirectTo = from?.pathname ? `${from.pathname}${from.search ?? ""}${from.hash ?? ""}` : "/console/observability";
    navigate(redirectTo, { replace: true });
  }

  return (
    <AuthLayout>
      <div className="login-card">
        <div className="login-card-header">
          <p className="app-eyebrow">{UI_TEXT.login.environmentHint}</p>
          <h2>开发凭证登录</h2>
          <p>请输入后端配置的 API Key，用于进入 AgentOps Trace Console。</p>
        </div>

        <form className="login-form" onSubmit={handleSubmit}>
          <label>
            API Key
            <input
              autoComplete="off"
              onChange={(event) => setCredentialInput(event.target.value)}
              placeholder="请输入 APP_API_KEYS 中配置的开发凭证"
              value={credential}
            />
          </label>
          <button className="button button-primary" disabled={isSubmitting || !credential.trim()} type="submit">
            {isSubmitting ? "校验中..." : "使用开发凭证进入"}
          </button>
          {submitError ? <p className="login-form-hint">{submitError}</p> : null}
          <div className="login-form-hint">
            <strong>说明</strong>
            <p>当前阶段复用后端 API Key 认证能力，正式用户名密码与 SSO 登录后续接入。</p>
          </div>
        </form>
      </div>
    </AuthLayout>
  );
}
