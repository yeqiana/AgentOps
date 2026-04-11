import { UI_TEXT } from "../../../constants/uiText";
import type { TraceTimelineEvent } from "../types/traceConsole";

interface TraceTimelinePanelProps {
  events: TraceTimelineEvent[];
}

export function TraceTimelinePanel({ events }: TraceTimelinePanelProps) {
  return (
    <section className="panel detail-panel">
      <div className="detail-panel-header">
        <div>
          <p className="detail-panel-kicker">{UI_TEXT.panel.timeline}</p>
          <h3>{UI_TEXT.panel.eventTimeline}</h3>
        </div>
        <span className="detail-count">{events.length}</span>
      </div>

      {events.length === 0 ? (
        <p className="muted-text">{UI_TEXT.state.noTimelineEvents}</p>
      ) : (
        <ol className="timeline-list">
          {events.map((event, index) => (
            <li key={`${event.happened_at}-${event.event_type}-${index}`} className="timeline-item">
              <div className="timeline-marker" />
              <div>
                <div className="timeline-meta">
                  {event.happened_at} · {event.source_type} / {event.source_name}
                </div>
                <h4>{event.title || event.event_type}</h4>
                <p className="long-text-block line-clamp-3">{event.details || "-"}</p>
                <details className="long-text-details">
                  <summary>{UI_TEXT.action.viewFullContent}</summary>
                  <p className="long-text-block">{event.details || "-"}</p>
                </details>
              </div>
            </li>
          ))}
        </ol>
      )}
    </section>
  );
}
