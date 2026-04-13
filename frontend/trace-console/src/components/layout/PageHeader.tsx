import type { ReactNode } from 'react';

interface PageHeaderProps {
  title: string;
  subtitle?: ReactNode;
  actions?: ReactNode;
  kicker?: string;
}

export function PageHeader({ title, subtitle, actions, kicker }: PageHeaderProps) {
  return (
    <section className="page-header">
      <div className="page-header-copy">
        {kicker ? <p className="page-header-kicker">{kicker}</p> : null}
        <h2 className="page-title">{title}</h2>
        {subtitle ? <p className="page-subtitle">{subtitle}</p> : null}
      </div>
      {actions ? <div className="page-header-actions">{actions}</div> : null}
    </section>
  );
}
