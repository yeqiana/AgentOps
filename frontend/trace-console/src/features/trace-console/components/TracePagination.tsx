import { UI_TEXT } from "../../../constants/uiText";

interface TracePaginationProps {
  page: number;
  pageSize: number;
  total: number;
  hasNext: boolean;
  disabled?: boolean;
  onPageChange: (page: number) => void;
}

export function TracePagination({
  page,
  pageSize,
  total,
  hasNext,
  disabled = false,
  onPageChange
}: TracePaginationProps) {
  const start = total === 0 ? 0 : (page - 1) * pageSize + 1;
  const end = Math.min(total, page * pageSize);

  return (
    <section className="panel pagination">
      <div className="pagination-summary">
        {UI_TEXT.pagination.summary(start, end, total)}
      </div>
      <div className="pagination-actions">
        <button className="button" type="button" onClick={() => onPageChange(page - 1)} disabled={disabled || page <= 1}>
          {UI_TEXT.action.previousPage}
        </button>
        <button className="button" type="button" onClick={() => onPageChange(page + 1)} disabled={disabled || !hasNext}>
          {UI_TEXT.action.nextPage}
        </button>
      </div>
    </section>
  );
}
