import type { ReactNode } from "react";
import { PageHeader } from "../components/layout/PageHeader";
import { PageHintBar } from "../components/layout/PageHintBar";
import { UI_CONFIG } from "../config/ui.config";

interface DetailPageShellProps {
  title: string;
  subtitle?: ReactNode;
  hint?: string;
  actions?: ReactNode;
  children: ReactNode;
}

export function DetailPageShell({ title, subtitle, hint, actions, children }: DetailPageShellProps) {
  return (
    <div className="page-shell page-shell-detail">
      <PageHeader title={title} subtitle={subtitle} actions={actions} />
      {hint && UI_CONFIG.pageShell.showHintBar ? <PageHintBar message={hint} /> : null}
      <div className="page-shell-content">{children}</div>
    </div>
  );
}
