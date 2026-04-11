import { LinkButton } from "../../../components/LinkButton";
import { StatusBadge } from "../../../components/StatusBadge";
import { UI_TEXT } from "../../../constants/uiText";
import type { TaskPayload, TaskRelatedTracePayload } from "../types/traceConsole";

interface RelatedTraceProps {
  task: TaskPayload;
  trace: TaskRelatedTracePayload | null;
}

function displayValue(value: string | number | null | undefined): string {
  if (value === null || value === undefined || value === "") {
    return "-";
  }
  return String(value);
}

function statusTone(statusCode: number | null | undefined): "neutral" | "success" | "warning" | "error" {
  if (statusCode === null || statusCode === undefined) {
    return "neutral";
  }
  if (statusCode >= 500) {
    return "error";
  }
  if (statusCode >= 400) {
    return "warning";
  }
  return "success";
}

function KeyValue({ label, value }: { label: string; value: string | number | null | undefined }) {
  return (
    <div className="detail-kv-item">
      <dt>{label}</dt>
      <dd>{displayValue(value)}</dd>
    </div>
  );
}

export function RelatedTrace({ task, trace }: RelatedTraceProps) {
  const traceId = trace?.trace_id || task.trace_id || "";

  return (
    <section className="panel detail-panel">
      <div className="detail-panel-header">
        <div>
          <p className="detail-panel-kicker">{UI_TEXT.panel.relatedTrace}</p>
          <h3>{traceId || UI_TEXT.state.noRelatedTrace}</h3>
        </div>
        {trace?.status_code !== undefined && trace?.status_code !== null ? (
          <StatusBadge label={String(trace.status_code)} tone={statusTone(trace.status_code)} />
        ) : null}
      </div>

      {traceId ? (
        <>
          <dl className="detail-kv-grid">
            <KeyValue label={UI_TEXT.field.traceId} value={traceId} />
            <KeyValue label={UI_TEXT.field.method} value={trace?.method} />
            <KeyValue label={UI_TEXT.field.path} value={trace?.path} />
            <KeyValue label={UI_TEXT.field.statusCode} value={trace?.status_code} />
          </dl>
          <div className="panel-actions">
            <LinkButton to={`/console/traces/${encodeURIComponent(traceId)}`}>{UI_TEXT.action.openTraceDetail}</LinkButton>
          </div>
        </>
      ) : (
        <p className="muted-text">{UI_TEXT.state.noRelatedRequestTrace}</p>
      )}
    </section>
  );
}
