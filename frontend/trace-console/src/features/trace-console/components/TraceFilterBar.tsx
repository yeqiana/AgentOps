import type { FormEvent } from 'react';
import { UI_TEXT } from '../../../constants/uiText';
import type { TraceListFilters } from '../types/traceConsole';

interface TraceFilterBarProps {
  filters: TraceListFilters;
  disabled?: boolean;
  onChange: (next: TraceListFilters) => void;
  onSubmit: () => void;
  onReset: () => void;
}

const methodOptions = ['', 'GET', 'POST', 'PUT', 'PATCH', 'DELETE'];

export function TraceFilterBar({ filters, disabled = false, onChange, onSubmit, onReset }: TraceFilterBarProps) {
  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    onSubmit();
  }

  function updateField<K extends keyof TraceListFilters>(key: K, value: TraceListFilters[K]) {
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
          <h3>请求链路检索</h3>
        </div>
        <div className="toolbar-actions">
          <button className="button button-primary" type="submit" form="trace-filter-form" disabled={disabled}>
            {UI_TEXT.action.search}
          </button>
          <button className="button" type="button" onClick={onReset} disabled={disabled}>
            {UI_TEXT.action.reset}
          </button>
        </div>
      </div>
      <form className="toolbar-form" id="trace-filter-form" onSubmit={handleSubmit}>
        <div className="field-group">
          <label htmlFor="trace_id">{UI_TEXT.field.traceId}</label>
          <input id="trace_id" value={filters.trace_id} onChange={(event) => updateField('trace_id', event.target.value)} disabled={disabled} />
        </div>
        <div className="field-group">
          <label htmlFor="task_id">{UI_TEXT.field.taskId}</label>
          <input id="task_id" value={filters.task_id} onChange={(event) => updateField('task_id', event.target.value)} disabled={disabled} />
        </div>
        <div className="field-group">
          <label htmlFor="path">{UI_TEXT.field.path}</label>
          <input id="path" value={filters.path} onChange={(event) => updateField('path', event.target.value)} disabled={disabled} />
        </div>
        <div className="field-group field-group-sm">
          <label htmlFor="method">{UI_TEXT.field.method}</label>
          <select id="method" value={filters.method} onChange={(event) => updateField('method', event.target.value)} disabled={disabled}>
            {methodOptions.map((option) => (
              <option key={option || 'all'} value={option}>
                {option || UI_TEXT.common.all}
              </option>
            ))}
          </select>
        </div>
        <div className="field-group field-group-sm">
          <label htmlFor="status_code">{UI_TEXT.field.statusCode}</label>
          <input
            id="status_code"
            inputMode="numeric"
            value={filters.status_code}
            onChange={(event) => updateField('status_code', event.target.value.replace(/[^\d]/g, ''))}
            disabled={disabled}
          />
        </div>
        <div className="field-group">
          <label htmlFor="route_name">{UI_TEXT.field.routeName}</label>
          <input id="route_name" value={filters.route_name} onChange={(event) => updateField('route_name', event.target.value)} disabled={disabled} />
        </div>
      </form>
    </section>
  );
}
