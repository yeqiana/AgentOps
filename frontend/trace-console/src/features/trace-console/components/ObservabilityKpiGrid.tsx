import { UI_TEXT } from "../../../constants/uiText";
import type { OperationsOverviewSummary, TraceStat } from "../types/traceConsole";

interface ObservabilityKpiGridProps {
  summary: OperationsOverviewSummary;
  traceStats: TraceStat[];
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

function buildTraceStatsSummary(traceStats: TraceStat[]) {
  const totalTraces = traceStats.reduce((total, item) => total + item.trace_count, 0);
  const errorTraces = traceStats.reduce((total, item) => (item.status_code >= 400 ? total + item.trace_count : total), 0);
  const rateLimitedTraces = traceStats.reduce((total, item) => (item.rate_limited ? total + item.trace_count : total), 0);
  const successRate = totalTraces === 0 ? "-" : `${(((totalTraces - errorTraces) / totalTraces) * 100).toFixed(1)}%`;

  return {
    totalTraces,
    errorTraces,
    rateLimitedTraces,
    successRate
  };
}

export function ObservabilityKpiGrid({ summary, traceStats }: ObservabilityKpiGridProps) {
  const runtime = summary.runtime;
  const traceSummary = buildTraceStatsSummary(traceStats);

  return (
    <section className="observability-kpi-grid">
      <KpiCard label={UI_TEXT.observability.activeTasks} value={runtime.active_task_count} hint={UI_TEXT.observability.currentRuntimeActiveCount} />
      <KpiCard label={UI_TEXT.observability.maxWorkers} value={runtime.max_workers} hint={UI_TEXT.observability.configuredWorkerCapacity} />
      <KpiCard label={UI_TEXT.observability.activeTaskIds} value={runtime.active_task_ids.length} hint={activeTaskPreview(runtime.active_task_ids)} />
      <KpiCard label={UI_TEXT.observability.recentTasks} value={summary.recent_tasks.length} hint={UI_TEXT.observability.fromOperationsOverview} />
      <KpiCard label={UI_TEXT.observability.recentAlerts} value={summary.recent_alerts.length} hint={UI_TEXT.observability.fromOperationsOverview} />
      <KpiCard label={UI_TEXT.observability.totalTraces} value={traceSummary.totalTraces} hint={UI_TEXT.observability.fromTraceStats} />
      <KpiCard label={UI_TEXT.observability.estimatedSuccessRate} value={traceSummary.successRate} hint={UI_TEXT.observability.fromTraceStats} />
      <KpiCard label={UI_TEXT.observability.errorTraces} value={traceSummary.errorTraces} hint={UI_TEXT.observability.fromTraceStats} />
      <KpiCard label={UI_TEXT.observability.rateLimitedTraces} value={traceSummary.rateLimitedTraces} hint={UI_TEXT.observability.fromTraceStats} />
    </section>
  );
}
