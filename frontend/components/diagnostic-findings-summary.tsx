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
};

function formatBand(
  value: string
): string {
  if (!value.trim()) {
    return "Unknown";
  }

  return value
    .trim()
    .replace(
      /[_-]+/g,
      " "
    )
    .replace(
      /\b\w/g,
      (character) =>
        character.toUpperCase()
    );
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
  readyForAnalysis
}: DiagnosticFindingsSummaryProps) {
  return (
    <section
      className="diagnostic-findings-summary"
      aria-labelledby="diagnostic-findings-summary-title"
    >
      <header className="diagnostic-findings-summary-header">
        <div>
          <p className="panel-kicker">
            FIP diagnostic findings
          </p>

          <h2
            id="diagnostic-findings-summary-title"
          >
            What FIP diagnosed
          </h2>

          <p>
            This summary presents the governed
            diagnostic conclusion before the
            detailed friction, intervention, and
            roadmap analysis.
          </p>
        </div>

        <span
          className={
            readyForAnalysis
              ? "status-badge status-healthy"
              : "status-badge status-warning"
          }
        >
          <span
            className="status-dot"
            aria-hidden="true"
          />

          {readyForAnalysis
            ? "Evidence ready"
            : "Evidence review"}
        </span>
      </header>

      <div className="diagnostic-primary-finding">
        <div className="diagnostic-primary-marker">
          01
        </div>

        <div>
          <span>
            Primary diagnostic
          </span>

          <h3>
            {dominantConstraint}
          </h3>

          <p>
            This is the dominant governed
            constraint identified by the
            persisted friction analysis. It is
            the primary diagnostic finding, not
            an assertion of root cause.
          </p>
        </div>
      </div>

      <div className="diagnostic-findings-metrics">
        <article>
          <span>
            Governance debt
          </span>

          <strong>
            {governanceDebtScore.toFixed(1)}
          </strong>

          <small>
            {formatBand(
              governanceDebtBand
            )}{" "}
            band
          </small>
        </article>

        <article>
          <span>
            Weighted friction
          </span>

          <strong>
            {totalFriction.toFixed(1)}
          </strong>

          <small>
            Governed constraint pressure
          </small>
        </article>

        <article>
          <span>
            Evidence quality
          </span>

          <strong>
            {evidenceQualityScore.toFixed(
              2
            )}
          </strong>

          <small>
            {formatBand(
              evidenceQualityGrade
            )}{" "}
            quality
          </small>
        </article>

        <article>
          <span>
            Observed constraints
          </span>

          <strong>
            {recognizedConstraintEvents}
          </strong>

          <small>
            Recognized constraint events
          </small>
        </article>

        <article>
          <span>
            Affected work
          </span>

          <strong>
            {uniqueWorkItemCount}
          </strong>

          <small>
            Unique work items
          </small>
        </article>
      </div>

      <div className="diagnostic-findings-evidence">
        <div className="diagnostic-findings-evidence-heading">
          <div>
            <p className="panel-kicker">
              Supporting findings
            </p>

            <h3>
              Evidence-backed observations
            </h3>
          </div>

          <span>
            {findings.length}{" "}
            {findings.length === 1
              ? "finding"
              : "findings"}
          </span>
        </div>

        {findings.length > 0 ? (
          <ol className="diagnostic-findings-list">
            {findings.map(
              (
                finding,
                index
              ) => (
                <li
                  key={`${index}-${finding}`}
                >
                  <span
                    className="diagnostic-finding-number"
                    aria-hidden="true"
                  >
                    {String(
                      index + 1
                    ).padStart(
                      2,
                      "0"
                    )}
                  </span>

                  <p>
                    {finding}
                  </p>
                </li>
              )
            )}
          </ol>
        ) : (
          <p className="diagnostic-findings-empty">
            No supporting findings were
            generated for this assessment.
          </p>
        )}
      </div>

      <aside className="diagnostic-interpretation-boundary">
        <strong>
          Diagnostic interpretation boundary
        </strong>

        <p>
          The dominant constraint identifies
          the strongest governed friction signal
          in this assessment. It should not be
          interpreted automatically as the root
          cause or as authorization for an
          intervention.
        </p>
      </aside>
    </section>
  );
}