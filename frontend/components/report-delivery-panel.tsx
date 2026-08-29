export type ReportDeliveryPanelProps = {
  reportId: string;
  packageHash: string;
  schemaVersion: string;
};

export function ReportDeliveryPanel({
  reportId,
  packageHash,
  schemaVersion
}: ReportDeliveryPanelProps) {
  return (
    <section
      className="panel report-delivery-panel"
      aria-labelledby="report-delivery-title"
    >
      <div className="panel-header">
        <div>
          <p className="panel-kicker">
            Client delivery
          </p>

          <h2 id="report-delivery-title">
            Report delivery
          </h2>

          <p>
            Use the Print or save PDF control above to
            create the customer-facing deliverable.
            The exported report retains the governed
            verification metadata shown below.
          </p>
        </div>

        <span className="status-badge status-healthy">
          <span
            className="status-dot"
            aria-hidden="true"
          />

          Delivery ready
        </span>
      </div>

      <div className="report-delivery-steps">
        <article>
          <span>1</span>

          <div>
            <strong>Review report</strong>
            <p>
              Confirm the findings, priorities,
              roadmap, and evidence commitments before
              delivery.
            </p>
          </div>
        </article>

        <article>
          <span>2</span>

          <div>
            <strong>Print or save PDF</strong>
            <p>
              Use the browser print dialog and choose
              Save as PDF when a digital customer copy
              is required.
            </p>
          </div>
        </article>

        <article>
          <span>3</span>

          <div>
            <strong>Preserve verification</strong>
            <p>
              Keep the report ID, package hash, and
              schema version with the delivered copy
              so its governed package can be identified.
            </p>
          </div>
        </article>
      </div>

      <dl className="report-delivery-verification">
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
          <dt>Schema</dt>
          <dd>{schemaVersion}</dd>
        </div>
      </dl>

      <p className="report-delivery-boundary">
        Delivery readiness confirms that the governed
        report package is available for export. It does
        not create a new assessment determination or
        alter the underlying governed evidence.
      </p>
    </section>
  );
}