import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { LinkButton } from '../../components/LinkButton';
import { PageStateView } from '../../components/PageStateView';
import { UI_CONFIG } from '../../config/ui.config';
import { UI_TEXT } from '../../constants/uiText';
import { getTaskSummary } from '../../features/trace-console/api/traceConsoleApi';
import { RelatedTrace } from '../../features/trace-console/components/RelatedTrace';
import { TaskEvents } from '../../features/trace-console/components/TaskEvents';
import { TaskOverview } from '../../features/trace-console/components/TaskOverview';
import { TaskStatus } from '../../features/trace-console/components/TaskStatus';
import type { TaskSummary } from '../../features/trace-console/types/traceConsole';
import { DetailPageShell } from '../../layouts/DetailPageShell';
import { HttpError } from '../../lib/http/client';

export function TaskDetailPage() {
  const { taskId = '' } = useParams();
  const [summary, setSummary] = useState<TaskSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [noPermission, setNoPermission] = useState(false);
  const [retryKey, setRetryKey] = useState(0);

  useEffect(() => {
    let active = true;

    async function loadSummary() {
      if (!taskId) {
        setLoading(false);
        setError(UI_TEXT.state.missingTaskId);
        setSummary(null);
        return;
      }

      setLoading(true);
      setError(null);
      setNoPermission(false);

      try {
        const response = await getTaskSummary(taskId);
        if (!active) return;
        setSummary(response.summary);
      } catch (caught) {
        if (!active) return;
        setSummary(null);
        if (caught instanceof HttpError && (caught.status === 401 || caught.status === 403)) {
          setNoPermission(true);
          return;
        }
        setError(UI_TEXT.state.taskSummaryLoadFailed);
      } finally {
        if (active) setLoading(false);
      }
    }

    void loadSummary();

    return () => {
      active = false;
    };
  }, [taskId, retryKey]);

  const task = summary?.task ?? null;

  return (
    <DetailPageShell
      title={UI_TEXT.page.taskDetailTitle}
      subtitle={taskId ? `${UI_TEXT.page.taskDetailSubtitle} ${taskId}` : UI_TEXT.state.missingTaskId}
      hint={UI_TEXT.hint.taskDetail}
      kicker={UI_CONFIG.pageShell.pageKickers.taskDetail}
      actions={<LinkButton to="/console/traces">{UI_TEXT.action.backToTraceList}</LinkButton>}
    >
      {loading ? <PageStateView title={UI_TEXT.common.loading} description={UI_TEXT.state.loadingTaskSummary} /> : null}
      {!loading && noPermission ? <PageStateView title={UI_TEXT.common.noPermission} description={UI_TEXT.state.taskNoPermission} /> : null}
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
      {!loading && !noPermission && !error && summary && !task ? (
        <PageStateView title={UI_TEXT.state.taskNotFound} description={UI_TEXT.state.noTaskSummary} />
      ) : null}
      {!loading && !noPermission && !error && summary && task ? (
        <div className="trace-detail-grid trace-detail-grid-3col">
          <div className="trace-detail-column trace-detail-column-primary">
            <TaskOverview task={task} />
            <TaskEvents events={summary.task_events ?? []} />
          </div>
          <div className="trace-detail-column trace-detail-column-secondary">
            <TaskStatus task={task} />
          </div>
          <div className="trace-detail-column trace-detail-column-aside">
            <RelatedTrace task={task} trace={summary.trace ?? null} />
          </div>
        </div>
      ) : null}
    </DetailPageShell>
  );
}
