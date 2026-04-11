import { UI_TEXT } from "../../../constants/uiText";
import type { TraceTaskEvent } from "../types/traceConsole";

interface TaskEventsProps {
  events: TraceTaskEvent[];
}

function displayValue(value: string | null | undefined): string {
  if (value === null || value === undefined || value === "") {
    return "-";
  }
  return value;
}

function LongText({ value }: { value: string | null | undefined }) {
  const text = displayValue(value);

  return (
    <>
      <p className="long-text-block line-clamp-3">{text}</p>
      <details className="long-text-details">
        <summary>{UI_TEXT.action.viewFullContent}</summary>
        <p className="long-text-block">{text}</p>
      </details>
    </>
  );
}

export function TaskEvents({ events }: TaskEventsProps) {
  return (
    <section className="panel detail-panel">
      <div className="detail-panel-header">
        <div>
          <p className="detail-panel-kicker">{UI_TEXT.panel.events}</p>
          <h3>{UI_TEXT.panel.taskEvents}</h3>
        </div>
        <span className="detail-count">{events.length}</span>
      </div>

      {events.length === 0 ? (
        <p className="muted-text">{UI_TEXT.state.noTaskEvents}</p>
      ) : (
        <div className="log-stack">
          {events.map((event, index) => (
            <article className="log-entry" key={event.id || `${event.event_type}-${event.created_at}-${index}`}>
              <div className="log-entry-header">
                <strong>{displayValue(event.event_type)}</strong>
                <span>{displayValue(event.created_at)}</span>
              </div>
              <LongText value={event.event_message} />
              {event.event_payload_json ? <pre>{event.event_payload_json}</pre> : null}
            </article>
          ))}
        </div>
      )}
    </section>
  );
}
