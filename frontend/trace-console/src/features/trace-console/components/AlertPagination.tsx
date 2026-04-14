interface AlertPaginationProps {
  limit: number;
  offset: number;
  itemCount: number;
  disabled?: boolean;
  onPageChange: (nextOffset: number) => void;
}

export function AlertPagination({ limit, offset, itemCount, disabled = false, onPageChange }: AlertPaginationProps) {
  const start = itemCount === 0 ? 0 : offset + 1;
  const end = offset + itemCount;
  const hasNext = itemCount >= limit;

  return (
    <section className="panel pagination">
      <div className="pagination-summary">
        显示第 {start}-{end} 条
      </div>
      <div className="pagination-actions">
        <button className="button" type="button" onClick={() => onPageChange(Math.max(0, offset - limit))} disabled={disabled || offset <= 0}>
          上一页
        </button>
        <button className="button" type="button" onClick={() => onPageChange(offset + limit)} disabled={disabled || !hasNext}>
          下一页
        </button>
      </div>
    </section>
  );
}
