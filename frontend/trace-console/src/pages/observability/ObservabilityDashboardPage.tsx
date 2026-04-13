import { useEffect, useState } from 'react';
import { LinkButton } from '../../components/LinkButton';
import { PageStateView } from '../../components/PageStateView';
import { UI_CONFIG } from '../../config/ui.config';
import { UI_TEXT } from '../../constants/uiText';
import { getAlertStats, getOperationsOverview, getTraceStats } from '../../features/trace-console/api/traceConsoleApi';
import { AlertStatsPanel } from '../../features/trace-console/components/AlertStatsPanel';
import { AlertSummaryPanel } from '../../features/trace-console/components/AlertSummaryPanel';
import { ObservabilityKpiGrid } from '../../features/trace-console/components/ObservabilityKpiGrid';
import { RecentActivityPanel } from '../../features/trace-console/components/RecentActivityPanel';
import { RouteStatsPanel } from '../../features/trace-console/components/RouteStatsPanel';
import { TaskStatusSummaryPanel } from '../../features/trace-console/components/TaskStatusSummaryPanel';
import { TraceTrafficStatsPanel } from '../../features/trace-console/components/TraceTrafficStatsPanel';
import type { AlertStat, OperationsOverviewSummary, TraceStat } from '../../features/trace-console/types/traceConsole';
import { DashboardPageShell } from '../../layouts/DashboardPageShell';
import { HttpError } from '../../lib/http/client';

function hasOverviewData(summary: OperationsOverviewSummary, traceStats: TraceStat[], alertStats: AlertStat[]) {
  return (
    summary.runtime.active_task_count > 0 ||
    summary.runtime.active_task_ids.length > 0 ||
    summary.task_stats.length > 0 ||
    summary.recent_tasks.length > 0 ||
    summary.recent_alerts.length > 0 ||
    summary.route_stats.length > 0 ||
    traceStats.length > 0 ||
    alertStats.length > 0
  );
}

export function ObservabilityDashboardPage() {
  const [summary, setSummary] = useState<OperationsOverviewSummary | null>(null);
  const [traceStats, setTraceStats] = useState<TraceStat[]>([]);
  const [alertStats, setAlertStats] = useState<AlertStat[]>([]);
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
        const [overviewResponse, traceStatsResponse, alertStatsResponse] = await Promise.all([
          getOperationsOverview(),
          getTraceStats(),
          getAlertStats()
        ]);
        if (!active) return;
        setSummary(overviewResponse.summary);
        setTraceStats(traceStatsResponse.stats);
        setAlertStats(alertStatsResponse.stats);
      } catch (caught) {
        if (!active) return;
        setSummary(null);
        setTraceStats([]);
        setAlertStats([]);
        if (caught instanceof HttpError && (caught.status === 401 || caught.status === 403)) {
          setNoPermission(true);
          return;
        }
        setError(UI_TEXT.state.operationsOverviewLoadFailed);
      } finally {
        if (active) setLoading(false);
      }
    }

    void loadOverview();

    return () => {
      active = false;
    };
  }, [retryKey]);

  return (
    <DashboardPageShell
      title="控制台首页"
      subtitle="统一查看任务执行、Trace 观测、Agent 配置与系统治理，保持控制台风格紧凑、清晰、专业。"
      hint="以后台管理系统的组织视图为主，而不是展示型首页；优先突出近期任务、Trace 异常与能力模块入口。"
      kicker={UI_CONFIG.pageShell.pageKickers.dashboard}
      actions={
        <>
          <button className="button" type="button" onClick={() => setRetryKey((current) => current + 1)}>
            刷新概览
          </button>
          <LinkButton to="/console/traces">进入观测</LinkButton>
        </>
      }
    >
      {loading ? <PageStateView title={UI_TEXT.common.loading} description={UI_TEXT.state.loadingOperationsOverview} /> : null}
      {!loading && noPermission ? <PageStateView title={UI_TEXT.common.noPermission} description={UI_TEXT.state.operationsNoPermission} /> : null}
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
      {!loading && !noPermission && !error && summary && !hasOverviewData(summary, traceStats, alertStats) ? (
        <PageStateView title={UI_TEXT.state.noRecentData} description={UI_TEXT.state.noRecentActivity} />
      ) : null}
      {!loading && !noPermission && !error && summary && hasOverviewData(summary, traceStats, alertStats) ? (
        <div className="observability-grid">
          <ObservabilityKpiGrid summary={summary} traceStats={traceStats} />
          <div className="observability-grid-half">
            <RecentActivityPanel tasks={summary.recent_tasks} />
            <AlertSummaryPanel alerts={summary.recent_alerts} />
          </div>
          <div className="observability-grid-full">
            <TraceTrafficStatsPanel stats={traceStats} />
          </div>
          <div className="observability-grid-half">
            <TaskStatusSummaryPanel stats={summary.task_stats} />
            <AlertStatsPanel stats={alertStats} />
          </div>
          <div className="observability-grid-full">
            <RouteStatsPanel stats={summary.route_stats} />
          </div>
          <section className="panel overview-module-panel">
            <div className="detail-panel-header">
              <div>
                <p className="detail-panel-kicker">功能模块</p>
                <h3>以后台组织视图聚合能力入口</h3>
              </div>
            </div>
            <div className="overview-module-grid">
              <article className="overview-module-card">
                <h4>任务管理</h4>
                <p>管理异步任务、状态机、执行记录与重试流程，是系统主运行入口。</p>
                <span>列表页 · 详情页</span>
              </article>
              <article className="overview-module-card">
                <h4>Trace 观测</h4>
                <p>查看链路、工具调用、错误定位与 token 消耗，是核心观测模块。</p>
                <span>链路页 · 详情页</span>
              </article>
              <article className="overview-module-card">
                <h4>Agent 管理</h4>
                <p>配置 Agent 定义、执行策略与模块关系，为生产部署预留能力。</p>
                <span>配置页</span>
              </article>
              <article className="overview-module-card">
                <h4>工具管理</h4>
                <p>统一管理 OCR、搜索、数据库与权限策略等工具能力。</p>
                <span>列表页 · 配置页</span>
              </article>
            </div>
          </section>
        </div>
      ) : null}
    </DashboardPageShell>
  );
}
