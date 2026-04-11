import { UI_TEXT } from "../../../constants/uiText";
import type { OperationsOverviewSummary } from "../types/traceConsole";

interface ObservabilityKpiGridProps {
  summary: OperationsOverviewSummary;
}

function activeTaskPreview(activeTaskIds: string[]) {
  if (activeTaskIds.length === 0) {
    return "-";
  }
  const preview = activeTaskIds.slice(0, 3).join(", ");
  return activeTaskIds.length > 3 ? `${preview} +${activeTaskIds.length - 3}` : preview;
}

function KpiCard({ label, value, hint }: { label: string; value: string | number; hint?: string }) {
  return (
    <article className="observability-kpi-card">
      <p>{label}</p>
      <strong>{value}</strong>
      {hint ? <span>{hint}</span> : null}
    </article>
  );
}

export function ObservabilityKpiGrid({ summary }: ObservabilityKpiGridProps) {
  const runtime = summary.runtime;

  return (
    <section className="observability-kpi-grid">
      <KpiCard label={UI_TEXT.observability.activeTasks} value={runtime.active_task_count} hint={UI_TEXT.observability.currentRuntimeActiveCount} />
      <KpiCard label={UI_TEXT.observability.maxWorkers} value={runtime.max_workers} hint={UI_TEXT.observability.configuredWorkerCapacity} />
      <KpiCard label={UI_TEXT.observability.activeTaskIds} value={runtime.active_task_ids.length} hint={activeTaskPreview(runtime.active_task_ids)} />
      <KpiCard label={UI_TEXT.observability.recentTasks} value={summary.recent_tasks.length} hint={UI_TEXT.observability.fromOperationsOverview} />
      <KpiCard label={UI_TEXT.observability.recentAlerts} value={summary.recent_alerts.length} hint={UI_TEXT.observability.fromOperationsOverview} />
    </section>
  );
}
