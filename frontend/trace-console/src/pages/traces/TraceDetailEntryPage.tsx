import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { LinkButton } from '../../components/LinkButton';
import { PageStateView } from '../../components/PageStateView';
import { UI_CONFIG } from '../../config/ui.config';
import { UI_TEXT } from '../../constants/uiText';
import { getTraceConsoleViewer } from '../../features/trace-console/api/traceConsoleApi';
import { TraceAlertsPanel } from '../../features/trace-console/components/TraceAlertsPanel';
import { TraceConsoleLogsPanel } from '../../features/trace-console/components/TraceConsoleLogsPanel';
import { TraceGraphPanel } from '../../features/trace-console/components/TraceGraphPanel';
import { TraceOverviewPanel } from '../../features/trace-console/components/TraceOverviewPanel';
import { TraceTimelinePanel } from '../../features/trace-console/components/TraceTimelinePanel';
import type { TraceConsoleViewer } from '../../features/trace-console/types/traceConsole';
import { DetailPageShell } from '../../layouts/DetailPageShell';
import { HttpError } from '../../lib/http/client';

export function TraceDetailEntryPage() {
  const { traceId = '' } = useParams();
  const [viewer, setViewer] = useState<TraceConsoleViewer | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [noPermission, setNoPermission] = useState(false);
  const [retryKey, setRetryKey] = useState(0);

  useEffect(() => {
    let active = true;

    async function loadViewer() {
      if (!traceId) {
        setLoading(false);
        setError(UI_TEXT.state.missingTraceId);
        setViewer(null);
        return;
      }

      setLoading(true);
      setError(null);
      setNoPermission(false);

      try {
        const response = await getTraceConsoleViewer(traceId);
        if (!active) return;
        setViewer(response.viewer);
      } catch (caught) {
        if (!active) return;
        setViewer(null);
        if (caught instanceof HttpError && (caught.status === 401 || caught.status === 403)) {
          setNoPermission(true);
          return;
        }
        if (caught instanceof HttpError && caught.status === 404) {
          setError(UI_TEXT.state.traceRecordMissing);
          return;
        }
        setError(UI_TEXT.state.traceDetailLoadFailed);
      } finally {
        if (active) setLoading(false);
      }
    }

    void loadViewer();

    return () => {
      active = false;
    };
  }, [traceId, retryKey]);

  return (
    <DetailPageShell
      title={UI_TEXT.page.traceDetailTitle}
      subtitle={traceId || UI_TEXT.state.missingTraceId}
      hint={UI_TEXT.hint.traceDetail}
      kicker={UI_CONFIG.pageShell.pageKickers.traceDetail}
      actions={<LinkButton to="/console/traces">{UI_TEXT.action.backToTraceList}</LinkButton>}
    >
      {loading ? <PageStateView title={UI_TEXT.common.loading} description={UI_TEXT.state.loadingTraceDetail} /> : null}
      {!loading && noPermission ? <PageStateView title={UI_TEXT.common.noPermission} description={UI_TEXT.state.traceDetailNoPermission} /> : null}
      {!loading && !noPermission && error ? (
        <PageStateView
          title={UI_TEXT.common.loadFailed}
          description={error}
          actions={
            <>
              <LinkButton to="/console/traces">{UI_TEXT.action.backToTraceList}</LinkButton>
              <LinkButton to="/console/observability">{UI_TEXT.nav.observability}</LinkButton>
              <button className="button button-primary" type="button" onClick={() => setRetryKey((current) => current + 1)}>
                {UI_TEXT.action.retry}
              </button>
            </>
          }
        />
      ) : null}
      {!loading && !noPermission && !error && viewer ? (
        <div className="trace-detail-grid trace-detail-grid-3col">
          <div className="trace-detail-column trace-detail-column-primary">
            <TraceOverviewPanel viewer={viewer} />
            <TraceTimelinePanel events={viewer.timeline} />
          </div>
          <div className="trace-detail-column trace-detail-column-secondary">
            <TraceConsoleLogsPanel taskEvents={viewer.summary.task_events} toolResults={viewer.summary.tool_results} />
          </div>
          <div className="trace-detail-column trace-detail-column-aside">
            <TraceAlertsPanel alerts={viewer.alerts} />
            <TraceGraphPanel nodes={viewer.graph_nodes} edges={viewer.graph_edges} />
          </div>
        </div>
      ) : null}
    </DetailPageShell>
  );
}
