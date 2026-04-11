import { UI_TEXT } from "../../../constants/uiText";
import type { TaskPayload } from "../types/traceConsole";

interface TaskOverviewProps {
  task: TaskPayload;
}

function displayValue(value: string | number | null | undefined): string {
  if (value === null || value === undefined || value === "") {
    return "-";
  }
  return String(value);
}

function KeyValue({ label, value }: { label: string; value: string | number | null | undefined }) {
  return (
    <div className="detail-kv-item">
      <dt>{label}</dt>
      <dd>{displayValue(value)}</dd>
    </div>
  );
}

function SummaryText({ label, value }: { label: string; value: string | null | undefined }) {
  const text = displayValue(value);

  return (
    <div className="detail-kv-item task-summary-item">
      <dt>{label}</dt>
      <dd className="summary-text">
        <div className="long-text-block line-clamp-4">{text}</div>
        <details className="long-text-details">
          <summary>{UI_TEXT.action.viewFullContent}</summary>
          <div className="long-text-block">{text}</div>
        </details>
      </dd>
    </div>
  );
}

export function TaskOverview({ task }: TaskOverviewProps) {
  return (
    <section className="panel detail-panel">
      <div className="detail-panel-header">
        <div>
          <p className="detail-panel-kicker">{UI_TEXT.panel.overview}</p>
          <h3>{UI_TEXT.panel.taskOverview}</h3>
        </div>
      </div>

      <dl className="detail-kv-grid">
        <KeyValue label={UI_TEXT.field.taskId} value={task.id} />
        <KeyValue label={UI_TEXT.field.sessionId} value={task.session_id} />
        <KeyValue label={UI_TEXT.field.turnId} value={task.turn_id} />
        <KeyValue label={UI_TEXT.field.traceId} value={task.trace_id} />
        <KeyValue label={UI_TEXT.field.createdAt} value={task.created_at} />
        <KeyValue label={UI_TEXT.field.updatedAt} value={task.updated_at} />
        <SummaryText label={UI_TEXT.field.userInput} value={task.user_input} />
        <SummaryText label={UI_TEXT.field.answer} value={task.answer} />
      </dl>
    </section>
  );
}
