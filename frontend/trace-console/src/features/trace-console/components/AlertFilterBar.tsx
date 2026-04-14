import type { FormEvent } from "react";
import type { AlertListFilters } from "../types/traceConsole";

interface AlertFilterBarProps {
  filters: AlertListFilters;
  disabled?: boolean;
  onChange: (next: AlertListFilters) => void;
  onSubmit: () => void;
  onReset: () => void;
}

const severityOptions = ["", "critical", "error", "warning", "info"];

export function AlertFilterBar({ filters, disabled = false, onChange, onSubmit, onReset }: AlertFilterBarProps) {
  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    onSubmit();
  }

  function updateField<K extends keyof AlertListFilters>(key: K, value: AlertListFilters[K]) {
    onChange({
      ...filters,
      [key]: value
    });
  }

  return (
    <section className="panel toolbar toolbar-compact">
      <div className="toolbar-header">
        <div>
          <p className="toolbar-kicker">筛选条件</p>
          <h3>告警检索</h3>
        </div>
        <div className="toolbar-actions">
          <button className="button button-primary" type="submit" form="alert-filter-form" disabled={disabled}>
            查询
          </button>
          <button className="button" type="button" onClick={onReset} disabled={disabled}>
            重置
          </button>
        </div>
      </div>
      <form className="toolbar-form" id="alert-filter-form" onSubmit={handleSubmit}>
        <div className="field-group field-group-sm">
          <label htmlFor="alert_severity">严重级别</label>
          <select id="alert_severity" value={filters.severity} onChange={(event) => updateField("severity", event.target.value)} disabled={disabled}>
            {severityOptions.map((option) => (
              <option key={option || "all"} value={option}>
                {option || "全部"}
              </option>
            ))}
          </select>
        </div>
        <div className="field-group">
          <label htmlFor="alert_source_type">来源类型</label>
          <input
            id="alert_source_type"
            value={filters.source_type}
            onChange={(event) => updateField("source_type", event.target.value)}
            disabled={disabled}
          />
        </div>
        <div className="field-group">
          <label htmlFor="alert_trace_id">请求链路 ID</label>
          <input id="alert_trace_id" value={filters.trace_id} onChange={(event) => updateField("trace_id", event.target.value)} disabled={disabled} />
        </div>
      </form>
    </section>
  );
}
