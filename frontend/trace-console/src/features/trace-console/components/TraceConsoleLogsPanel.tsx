import { StatusBadge } from "../../../components/StatusBadge";
import { UI_TEXT } from "../../../constants/uiText";
import type { TraceTaskEvent, TraceToolResult } from "../types/traceConsole";

interface TraceConsoleLogsPanelProps {
  taskEvents: TraceTaskEvent[];
  toolResults: TraceToolResult[];
}

export function TraceConsoleLogsPanel({ taskEvents, toolResults }: TraceConsoleLogsPanelProps) {
  return (
    <section className="panel detail-panel">
      <div className="detail-panel-header">
        <div>
          <p className="detail-panel-kicker">{UI_TEXT.panel.consoleLogs}</p>
          <h3>{UI_TEXT.panel.taskEventsAndToolResults}</h3>
        </div>
        <span className="detail-count">{taskEvents.length + toolResults.length}</span>
      </div>

      {taskEvents.length === 0 && toolResults.length === 0 ? (
        <p className="muted-text">{UI_TEXT.state.noTaskEventsOrToolResults}</p>
      ) : (
        <div className="log-stack">
          {taskEvents.map((event) => (
            <article className="log-entry" key={`event-${event.id}`}>
              <div className="log-entry-header">
                <strong>{event.event_type}</strong>
                <span>{event.created_at}</span>
              </div>
              <p className="long-text-block line-clamp-3">{event.event_message || "-"}</p>
              <details className="long-text-details">
                <summary>{UI_TEXT.action.viewFullContent}</summary>
                <p className="long-text-block">{event.event_message || "-"}</p>
              </details>
              {event.event_payload_json ? <pre>{event.event_payload_json}</pre> : null}
            </article>
          ))}

          {toolResults.map((result) => (
            <article className="log-entry" key={`tool-${result.id}`}>
              <div className="log-entry-header">
                <strong>{result.tool_name}</strong>
                <StatusBadge label={result.success ? UI_TEXT.status.success : UI_TEXT.status.failed} tone={result.success ? "success" : "error"} />
              </div>
              <p>
                {UI_TEXT.field.exitCode}={result.exit_code} · {result.created_at || "-"}
              </p>
              {result.stdout ? (
                <>
                  <pre className="line-clamp-4">{result.stdout}</pre>
                  <details className="long-text-details">
                    <summary>{UI_TEXT.action.viewFullContent}</summary>
                    <pre>{result.stdout}</pre>
                  </details>
                </>
              ) : null}
              {result.stderr ? (
                <>
                  <pre className="line-clamp-4">{result.stderr}</pre>
                  <details className="long-text-details">
                    <summary>{UI_TEXT.action.viewFullContent}</summary>
                    <pre>{result.stderr}</pre>
                  </details>
                </>
              ) : null}
            </article>
          ))}
        </div>
      )}
    </section>
  );
}
