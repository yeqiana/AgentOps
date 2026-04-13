import type { ReactNode } from 'react';
import { PageHeader } from '../components/layout/PageHeader';
import { PageHintBar } from '../components/layout/PageHintBar';
import { UI_CONFIG } from '../config/ui.config';

interface DashboardPageShellProps {
  title: string;
  subtitle?: ReactNode;
  hint?: string;
  actions?: ReactNode;
  children: ReactNode;
  kicker?: string;
}

export function DashboardPageShell({ title, subtitle, hint, actions, children, kicker }: DashboardPageShellProps) {
  return (
    <div className="page-shell page-shell-dashboard">
      <PageHeader title={title} subtitle={subtitle} actions={actions} kicker={kicker} />
      {hint && UI_CONFIG.pageShell.showHintBar ? <PageHintBar message={hint} /> : null}
      <div className="page-shell-content">{children}</div>
    </div>
  );
}
