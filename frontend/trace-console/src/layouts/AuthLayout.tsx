import type { ReactNode } from "react";
import { Footer } from "../components/layout/Footer";
import { UI_TEXT } from "../constants/uiText";

interface AuthLayoutProps {
  children: ReactNode;
}

export function AuthLayout({ children }: AuthLayoutProps) {
  return (
    <div className="auth-layout">
      <section className="auth-brand-panel">
        <p className="app-eyebrow">{UI_TEXT.app.stage}</p>
        <h1>{UI_TEXT.login.brandTitle}</h1>
        <p>{UI_TEXT.login.brandDescription}</p>
        <ul>
          <li>{UI_TEXT.login.capabilityTask}</li>
          <li>{UI_TEXT.login.capabilityTrace}</li>
          <li>{UI_TEXT.login.capabilityGovernance}</li>
        </ul>
        <p className="auth-footnote">{UI_TEXT.login.positioning}</p>
      </section>
      <section className="auth-form-panel">{children}</section>
      <Footer />
    </div>
  );
}
