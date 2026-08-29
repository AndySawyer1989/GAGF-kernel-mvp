import Link from "next/link";

export type AssessmentDeliveryStatusProps = {
  reportReady: boolean;
  repositoryVerified: boolean;
  findingsReady: boolean;
  reportHref: string;
};

export function AssessmentDeliveryStatus({
  reportReady,
  repositoryVerified,
  findingsReady,
  reportHref
}: AssessmentDeliveryStatusProps) {
  const deliveryReady =
    reportReady &&
    repositoryVerified &&
    findingsReady;

  return (
    <section
      className={
        deliveryReady
          ? "panel assessment-delivery-status assessment-delivery-status-ready"
          : "panel assessment-delivery-status"
      }
      aria-labelledby="assessment-delivery-status-title"
    >
      <div className="panel-header">
        <div>
          <p className="panel-kicker">
            Assessment completion
          </p>

          <h2 id="assessment-delivery-status-title">
            {deliveryReady
              ? "Ready for client delivery"
              : "Delivery review required"}
          </h2>

          <p>
            {deliveryReady
              ? "The governed findings, repository verification, and client-report package are ready for operator review and customer delivery."
              : "Complete the remaining governed assessment requirements before treating this assessment as ready for customer delivery."}
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
            ? "Delivery ready"
            : "Review required"}
        </span>
      </div>

      <div className="assessment-delivery-checks">
        <div>
          <span
            className={
              findingsReady
                ? "status-badge status-healthy"
                : "status-badge status-warning"
            }
          >
            <span
              className="status-dot"
              aria-hidden="true"
            />

            {findingsReady
              ? "Findings ready"
              : "Findings incomplete"}
          </span>
        </div>

        <div>
          <span
            className={
              repositoryVerified
                ? "status-badge status-healthy"
                : "status-badge status-warning"
            }
          >
            <span
              className="status-dot"
              aria-hidden="true"
            />

            {repositoryVerified
              ? "Repository verified"
              : "Repository review required"}
          </span>
        </div>

        <div>
          <span
            className={
              reportReady
                ? "status-badge status-healthy"
                : "status-badge status-warning"
            }
          >
            <span
              className="status-dot"
              aria-hidden="true"
            />

            {reportReady
              ? "Client report ready"
              : "Client report unavailable"}
          </span>
        </div>
      </div>

      <div className="assessment-delivery-actions">
        {reportReady ? (
          <Link
            className="refresh-button button-link"
            href={reportHref}
          >
            Open delivery report
          </Link>
        ) : (
          <span className="assessment-delivery-disabled">
            Report delivery becomes available when the
            governed client-report package exists.
          </span>
        )}
      </div>

      <p className="assessment-delivery-boundary">
        Delivery readiness summarizes completion state.
        It does not create a new assessment
        determination, modify governed evidence, or
        replace repository integrity verification.
      </p>
    </section>
  );
}