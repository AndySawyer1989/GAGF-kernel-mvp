"use client";

export function PrintReportButton() {
  return (
    <button
      className="refresh-button report-print-button"
      type="button"
      onClick={() => window.print()}
    >
      Print or save PDF
    </button>
  );
}
