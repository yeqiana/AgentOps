import type { ReactNode } from "react";

interface PageStateViewProps {
  title: string;
  description: string;
  actions?: ReactNode;
}

export function PageStateView({ title, description, actions }: PageStateViewProps) {
  return (
    <section className="panel state-view">
      <h2>{title}</h2>
      <p>{description}</p>
      {actions ? <div className="state-actions">{actions}</div> : null}
    </section>
  );
}
