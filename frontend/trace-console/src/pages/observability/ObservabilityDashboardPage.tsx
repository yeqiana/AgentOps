import { useEffect, useState } from "react";
import { LinkButton } from "../../components/LinkButton";
import { PageStateView } from "../../components/PageStateView";
import { getOperationsOverview } from "../../features/trace-console/api/traceConsoleApi";
import { AlertSummaryPanel } from "../../features/trace-console/components/AlertSummaryPanel";
import { ObservabilityKpiGrid } from "../../features/trace-console/components/ObservabilityKpiGrid";
import { RecentActivityPanel } from "../../features/trace-console/components/RecentActivityPanel";
import { RouteStatsPanel } from "../../features/trace-console/components/RouteStatsPanel";
import { TaskStatusSummaryPanel } from "../../features/trace-console/components/TaskStatusSummaryPanel";
import type { OperationsOverviewSummary } from "../../features/trace-console/types/traceConsole";
import { UI_TEXT } from "../../constants/uiText";
import { HttpError } from "../../lib/http/client";

function hasOverviewData(summary: OperationsOverviewSummary) {
  return (
    summary.runtime.active_task_count > 0 ||
    summary.runtime.active_task_ids.length > 0 ||
    summary.task_stats.length > 0 ||
    summary.recent_tasks.length > 0 ||
    summary.recent_alerts.length > 0 ||
    summary.route_stats.length > 0
  );
}

export function ObservabilityDashboardPage() {
  const [summary, setSummary] = useState<OperationsOverviewSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [noPermission, setNoPermission] = useState(false);
  const [retryKey, setRetryKey] = useState(0);

  useEffect(() => {
    let active = true;

    async function loadOverview() {
      setLoading(true);
      setError(null);
      setNoPermission(false);

      try {
        const response = await getOperationsOverview();
        if (!active) {
          return;
        }
        setSummary(response.summary);
      } catch (caught) {
        if (!active) {
          return;
        }
        setSummary(null);
        if (caught instanceof HttpError && (caught.status === 401 || caught.status === 403)) {
          setNoPermission(true);
          return;
        }
        setError(UI_TEXT.state.operationsOverviewLoadFailed);
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }

    void loadOverview();

    return () => {
      active = false;
    };
  }, [retryKey]);

  return (
    <div>
      <section className="panel page-card trace-detail-hero">
        <div>
          <h2 className="page-title">{UI_TEXT.page.observabilityTitle}</h2>
          <p className="page-subtitle">{UI_TEXT.page.observabilitySubtitle}</p>
        </div>
        <LinkButton to="/console/traces">{UI_TEXT.action.backToTraceList}</LinkButton>
      </section>

      {loading ? <PageStateView title={UI_TEXT.common.loading} description={UI_TEXT.state.loadingOperationsOverview} /> : null}

      {!loading && noPermission ? (
        <PageStateView title={UI_TEXT.common.noPermission} description={UI_TEXT.state.operationsNoPermission} />
      ) : null}

      {!loading && !noPermission && error ? (
        <PageStateView
          title={UI_TEXT.common.loadFailed}
          description={error}
          actions={
            <button className="button button-primary" type="button" onClick={() => setRetryKey((current) => current + 1)}>
              {UI_TEXT.action.retry}
            </button>
          }
        />
      ) : null}

      {!loading && !noPermission && !error && summary && !hasOverviewData(summary) ? (
        <PageStateView title={UI_TEXT.state.noRecentData} description={UI_TEXT.state.noRecentActivity} />
      ) : null}

      {!loading && !noPermission && !error && summary && hasOverviewData(summary) ? (
        <div className="observability-grid">
          <ObservabilityKpiGrid summary={summary} />
          <TaskStatusSummaryPanel stats={summary.task_stats} />
          <RecentActivityPanel tasks={summary.recent_tasks} />
          <AlertSummaryPanel alerts={summary.recent_alerts} />
          <RouteStatsPanel stats={summary.route_stats} />
        </div>
      ) : null}
    </div>
  );
}
