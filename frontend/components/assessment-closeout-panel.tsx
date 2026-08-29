export type AssessmentCloseoutPanelProps = {
  deliveryRecorded: boolean;
  reportId: string;
  packageHash: string;
  deliveredAt?: string | null;
  deliveredBy?: string | null;
};

export function AssessmentCloseoutPanel({
  deliveryRecorded,
  reportId,
  packageHash,
  deliveredAt = null,
  deliveredBy = null
}: AssessmentCloseoutPanelProps) {
  return (
    <section
      className="panel assessment-closeout-panel"
      aria-labelledby="assessment-closeout-title"
    >
      <div className="panel-header">
        <div>
          <p className="panel-kicker">
            Assessment closeout
          </p>

          <h2 id="assessment-closeout-title">
            {deliveryRecorded
              ? "Client delivery recorded"
              : "Delivery confirmation pending"}
          </h2>

          <p>
            {deliveryRecorded
              ? "A delivery record exists for this governed report package."
              : "The assessment is ready for closeout when the operator records that the governed report package was delivered to the client."}
          </p>
        </div>

        <span
          className={
            deliveryRecorded
              ? "status-badge status-healthy"
              : "status-badge status-warning"
          }
        >
          <span
            className="status-dot"
            aria-hidden="true"
          />

          {deliveryRecorded
            ? "Delivery recorded"
            : "Confirmation pending"}
        </span>
      </div>

      <dl className="assessment-closeout-metadata">
        <div>
          <dt>Report ID</dt>
          <dd>{reportId}</dd>
        </div>

        <div>
          <dt>Package hash</dt>
          <dd>
            <code>{packageHash}</code>
          </dd>
        </div>

        <div>
          <dt>Delivered at</dt>
          <dd>
            {deliveryRecorded && deliveredAt
              ? deliveredAt
              : "Not recorded"}
          </dd>
        </div>

        <div>
          <dt>Delivered by</dt>
          <dd>
            {deliveryRecorded && deliveredBy
              ? deliveredBy
              : "Not recorded"}
          </dd>
        </div>
      </dl>

      {!deliveryRecorded ? (
        <div className="assessment-closeout-pending">
          <strong>
            No governed delivery receipt has been
            persisted.
          </strong>

          <p>
            Do not treat report generation or PDF
            export alone as proof that the client
            received the report.
          </p>
        </div>
      ) : null}

      <p className="assessment-closeout-boundary">
        Delivery confirmation records report
        transmission state only. It does not modify the
        governed assessment determination, diagnostic
        findings, evidence, repository integrity state,
        or intervention authority.
      </p>
    </section>
  );
}