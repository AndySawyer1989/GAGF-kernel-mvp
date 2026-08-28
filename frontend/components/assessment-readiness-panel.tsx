type ReadinessState = "ready" | "review";

export type AssessmentReadinessItem = {
  id: string;
  label: string;
  description: string;
  state: ReadinessState;
  readyLabel: string;
  reviewLabel: string;
};

type AssessmentReadinessPanelProps = {
  items: AssessmentReadinessItem[];
};

function readinessClassName(
  state: ReadinessState
): string {
  return state === "ready"
    ? "readiness-status readiness-status-ready"
    : "readiness-status readiness-status-review";
}

export function AssessmentReadinessPanel({
  items
}: AssessmentReadinessPanelProps) {
  const readyCount = items.filter(
    (item) => item.state === "ready"
  ).length;

  const deliveryReady =
    readyCount === items.length;

  return (
    <section
      className="panel assessment-readiness-panel"
      aria-labelledby="assessment-readiness-title"
    >
      <div className="panel-header readiness-panel-header">
        <div>
          <p className="panel-kicker">
            Governed delivery gate
          </p>

          <h2 id="assessment-readiness-title">
            Assessment readiness and delivery status
          </h2>

          <p className="readiness-panel-description">
            Delivery readiness is derived from the
            governed assessment summary and persisted
            artifact inventory.
          </p>
        </div>

        <span
          className={
            deliveryReady
              ? "status-badge status-healthy"
              : "status-badge status-warning"
          }
        >
          <span
            className="status-dot"
            aria-hidden="true"
          />

          {deliveryReady
            ? "Ready for delivery"
            : "Delivery review required"}
        </span>
      </div>

      <div className="readiness-progress">
        <div>
          <strong>
            {readyCount} of {items.length}
          </strong>

          <span>delivery gates satisfied</span>
        </div>

        <progress
          aria-label="Assessment delivery readiness"
          max={items.length}
          value={readyCount}
        >
          {readyCount} of {items.length}
        </progress>
      </div>

      <div className="readiness-grid">
        {items.map((item) => (
          <article
            className="readiness-item"
            key={item.id}
          >
            <div className="readiness-item-heading">
              <span
                className={
                  item.state === "ready"
                    ? "readiness-icon readiness-icon-ready"
                    : "readiness-icon readiness-icon-review"
                }
                aria-hidden="true"
              >
                {item.state === "ready" ? "OK" : "!"}
              </span>

              <div>
                <h3>{item.label}</h3>
                <p>{item.description}</p>
              </div>
            </div>

            <span
              className={readinessClassName(
                item.state
              )}
            >
              {item.state === "ready"
                ? item.readyLabel
                : item.reviewLabel}
            </span>
          </article>
        ))}
      </div>

      <footer className="readiness-panel-footer">
        <p>
          {deliveryReady
            ? "All governed delivery gates are satisfied. The assessment package can proceed to client delivery."
            : "One or more governed delivery gates require review before the assessment package is delivered."}
        </p>
      </footer>
    </section>
  );
}