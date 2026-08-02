"use client";

export type ConsolePaginationProps = {
  currentPage: number;
  pageSize: number;
  totalItems: number;
  label: string;
  onPageChange: (page: number) => void;
};

function clampPage(
  page: number,
  totalPages: number
): number {
  return Math.min(
    Math.max(page, 1),
    Math.max(totalPages, 1)
  );
}

export function ConsolePagination({
  currentPage,
  pageSize,
  totalItems,
  label,
  onPageChange
}: ConsolePaginationProps) {
  const totalPages = Math.max(
    Math.ceil(totalItems / pageSize),
    1
  );

  const safePage = clampPage(
    currentPage,
    totalPages
  );

  const firstItem =
    totalItems === 0
      ? 0
      : (safePage - 1) * pageSize + 1;

  const lastItem = Math.min(
    safePage * pageSize,
    totalItems
  );

  return (
    <nav
      aria-label={`${label} pagination`}
      className="console-pagination"
    >
      <p className="pagination-range">
        {totalItems === 0
          ? `No ${label.toLowerCase()}`
          : `Showing ${firstItem} to ${lastItem} of ${totalItems}`}
      </p>

      <div className="pagination-controls">
        <button
          aria-label={`Previous ${label} page`}
          className="pagination-button"
          disabled={
            totalItems === 0 ||
            safePage <= 1
          }
          onClick={() =>
            onPageChange(safePage - 1)
          }
          type="button"
        >
          Previous
        </button>

        <span className="pagination-page">
          Page {safePage} of {totalPages}
        </span>

        <button
          aria-label={`Next ${label} page`}
          className="pagination-button"
          disabled={
            totalItems === 0 ||
            safePage >= totalPages
          }
          onClick={() =>
            onPageChange(safePage + 1)
          }
          type="button"
        >
          Next
        </button>
      </div>
    </nav>
  );
}
