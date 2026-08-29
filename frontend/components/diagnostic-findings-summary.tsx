import Link from "next/link";

export type DiagnosticFindingsSummaryProps = {
  dominantConstraint: string;
  governanceDebtScore: number;
  governanceDebtBand: string;
  totalFriction: number;
  evidenceQualityScore: number;
  evidenceQualityGrade: string;
  recognizedConstraintEvents: number;
  uniqueWorkItemCount: number;
  findings: string[];
  readyForAnalysis: boolean;
  evidenceHref: string;
};

function categoryLabel(value: string): string {
  return value
    .toLowerCase()
    .split("_")
    .map((word) =>
      word.length > 0
        ? word[0].toUpperCase() + word.slice(1)
        : word
    )
    .join(" ");
}

function formatScore(value: number): string {
  return Number.isInteger(value)
    ? value.toString()
    : value.toFixed(1);
}

export function DiagnosticFindingsSummary({
  dominantConstraint,
  governanceDebtScore,
  governanceDebtBand,
  totalFriction,
  evidenceQualityScore,
  evidenceQualityGrade,
  recognizedConstraintEvents,
  uniqueWorkItemCount,
  findings,
  readyForAnalysis,
  evidenceHref
}: DiagnosticFindingsSummaryProps) {
  const dominantConstraintLabel =
    dominantConstraint.length > 0
      ? categoryLabel(dominantConstraint)
      : "Not identified";

  const dominantEvidenceHref =
    dominantConstraint.length > 0
      ? `${evidenceHref}?constraint=${encodeURIComponent(
          dominantConstraint
        )}`
      : evidenceHref;

  return (
    <section
      className="panel diagnostic-findings-summary"
      aria-labelledby="diagnostic-findings-summary-title"
    >
      <div className="panel-header">
        <div>
          <p className="panel-kicker">
            FIP diagnostic findings
          </p>

          <h2 id="diagnostic-findings-summary-title">
            What FIP diagnosed
          </h2>

          <p className="diagnostic-findings-description">
            Governed interpretation of the persisted
            assessment evidence and measured friction.
          </p>
        </div>

        <span
          className={
            readyForAnalysis
              ? "status-badge status-success"
              : "status-badge status-warning"
          }
        >
          <span
            className="status-dot"
            aria-hidden="true"
          />

          {readyForAnalysis
            ? "Ready for analysis"
            : "Analysis constrained"}
        </span>
      </div>

      <div className="diagnostic-findings-primary">
        <div>
          <p className="diagnostic-findings-label">
            Primary diagnostic
          </p>

          <h3>{dominantConstraintLabel}</h3>

          <p>
            This is the highest-ranked measured
            constraint in the governed diagnostic
            output. It is a primary diagnostic finding,
            not an assertion of root cause.
          </p>
        </div>

        <Link
          className="diagnostic-findings-evidence-link"
          href={dominantEvidenceHref}
        >
          View supporting evidence
        </Link>
      </div>

      <div className="diagnostic-findings-metric-grid">
        <article className="diagnostic-findings-metric">
          <span>Governance debt</span>

          <strong>
            {formatScore(governanceDebtScore)}
          </strong>

          <small>
          {`${governanceDebtBand.charAt(0).toUpperCase()}${governanceDebtBand.slice(1)} band`}
          </small>
        </article>

        <article className="diagnostic-findings-metric">
          <span>Weighted friction</span>

          <strong>
            {formatScore(totalFriction)}
          </strong>

          <small>
            Across recognized governed constraints
          </small>
        </article>

        <article className="diagnostic-findings-metric">
          <span>Evidence quality</span>

          <strong>
            {evidenceQualityScore.toFixed(2)}
          </strong>

          <small>
      {`${evidenceQualityGrade.charAt(0).toUpperCase()}${evidenceQualityGrade.slice(1)} quality`}
          </small>
        </article>

        <article className="diagnostic-findings-metric">
          <span>Observed constraints</span>

          <strong>
            {recognizedConstraintEvents}
          </strong>

          <small>Recognized constraint events</small>
        </article>

        <article className="diagnostic-findings-metric">
          <span>Affected work</span>

          <strong>{uniqueWorkItemCount}</strong>

          <small>Unique work items</small>
        </article>
      </div>

      <div className="diagnostic-findings-supporting">
       <div className="diagnostic-findings-supporting-header">
        <p className="diagnostic-findings-label">
        Supporting findings
       </p>

    <span>
      {findings.length}{" "}
      {findings.length === 1 ? "finding" : "findings"}
    </span>
  </div>

        {findings.length > 0 ? (
          <ul>
            {findings.map((finding, index) => (
              <li key={`${index}-${finding}`}>
                {finding}
              </li>
            ))}
          </ul>
        ) : (
          <p className="diagnostic-findings-empty">
            No additional governed findings were
            persisted for this assessment.
          </p>
        )}
      </div>

      <footer className="diagnostic-findings-boundary">
        <p>
          Interpretation boundary: diagnostic ranking
          summarizes measured evidence. Dominant
          constraint does not independently establish
          root cause, causality, systemic scope, or
          intervention authority.
        </p>
      </footer>
    </section>
  );
}
