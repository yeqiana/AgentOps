import type { ReactNode } from 'react';
import { PageHeader } from '../components/layout/PageHeader';
import { PageHintBar } from '../components/layout/PageHintBar';
import { UI_CONFIG } from '../config/ui.config';

interface ListPageShellProps {
  title: string;
  subtitle?: ReactNode;
  hint?: string;
  filters?: ReactNode;
  pagination?: ReactNode;
  children: ReactNode;
  kicker?: string;
}

export function ListPageShell({ title, subtitle, hint, filters, children, pagination, kicker }: ListPageShellProps) {
  return (
    <div className="page-shell page-shell-list">
      <PageHeader title={title} subtitle={subtitle} kicker={kicker} />
      {hint && UI_CONFIG.pageShell.showHintBar ? <PageHintBar message={hint} /> : null}
      {filters ? <div className="page-filter-section">{filters}</div> : null}
      <div className="page-shell-content">{children}</div>
      {pagination ? <div className="page-pagination-section">{pagination}</div> : null}
    </div>
  );
}
