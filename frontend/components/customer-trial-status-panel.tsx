import type {
  CustomerTrialExecutionHandoffStatus,
  CustomerTrialPreflightStatus
} from "@/lib/governance-customer-trial-api";


type CustomerTrialStatusPanelProps = {
  preflight:
    CustomerTrialPreflightStatus | null;
  handoff:
    CustomerTrialExecutionHandoffStatus | null;
  loading?: boolean;
};


function displayHash(
  value: unknown
): string {
  return typeof value === "string" &&
    value.length > 0
    ? value
    : "Not recorded";
}


export function CustomerTrialStatusPanel({
  preflight,
  handoff,
  loading = false
}: CustomerTrialStatusPanelProps) {
  const preflightReady =
    preflight?.result.receipt_found === true;

  const handoffPrepared =
    handoff?.result.receipt_found === true;

  const preflightReceipt =
    preflight?.result.receipt ?? null;

  const handoffReceipt =
    handoff?.result.receipt ?? null;

  const handoffHash =
    handoffReceipt
      ?.execution_handoff_lineage
      ?.handoff_hash;

  return (
    <section
      className="panel"
      aria-labelledby="customer-trial-status-title"
    >
      <div className="panel-header">
        <div>
          <p className="panel-kicker">
            Controlled customer trial
          </p>

          <h2 id="customer-trial-status-title">
            Trial readiness and execution handoff
          </h2>

          <p className="assessment-workflow-description">
            Read-only projection of governed trial
            readiness and execution-handoff evidence.
            This panel does not grant execution,
            delivery, closeout, or intervention
            authority.
          </p>
        </div>

        <span
          className={
            handoffPrepared
              ? "status-badge status-healthy"
              : "status-badge status-warning"
          }
        >
          <span
            className="status-dot"
            aria-hidden="true"
          />

          {loading
            ? "Restoring trial state"
            : handoffPrepared
              ? "Handoff prepared"
              : preflightReady
                ? "Trial ready"
                : "Preflight required"}
        </span>
      </div>

      <div className="readiness-grid">
        <article className="readiness-item">
          <div className="readiness-item-heading">
            <span
              className={
                preflightReady
                  ? "readiness-icon readiness-icon-ready"
                  : "readiness-icon readiness-icon-review"
              }
              aria-hidden="true"
            >
              {preflightReady ? "OK" : "!"}
            </span>

            <div>
              <h3>Trial readiness</h3>
              <p>
                Controlled-customer-trial preflight
                receipt.
              </p>
            </div>
          </div>

          <span
            className={
              preflightReady
                ? "readiness-status readiness-status-ready"
                : "readiness-status readiness-status-review"
            }
          >
            {preflightReady
              ? "Trial ready"
              : "Preflight not recorded"}
          </span>
        </article>

        <article className="readiness-item">
          <div className="readiness-item-heading">
            <span
              className={
                handoffPrepared
                  ? "readiness-icon readiness-icon-ready"
                  : "readiness-icon readiness-icon-review"
              }
              aria-hidden="true"
            >
              {handoffPrepared ? "OK" : "!"}
            </span>

            <div>
              <h3>Execution handoff</h3>
              <p>
                Durable evidence that the governed
                handoff was prepared.
              </p>
            </div>
          </div>

          <span
            className={
              handoffPrepared
                ? "readiness-status readiness-status-ready"
                : "readiness-status readiness-status-review"
            }
          >
            {handoffPrepared
              ? "Handoff prepared"
              : "Handoff unavailable"}
          </span>
        </article>
      </div>

      <dl className="assessment-workflow-identity">
        <div>
          <dt>Package hash</dt>
          <dd>
            <code>
              {displayHash(
                preflightReceipt?.package_hash
              )}
            </code>
          </dd>
        </div>

        <div>
          <dt>Preflight receipt</dt>
          <dd>
            <code>
              {displayHash(
                preflightReceipt?.receipt_hash
              )}
            </code>
          </dd>
        </div>

        <div>
          <dt>Handoff hash</dt>
          <dd>
            <code>
              {displayHash(handoffHash)}
            </code>
          </dd>
        </div>

        <div>
          <dt>Handoff receipt</dt>
          <dd>
            <code>
              {displayHash(
                handoffReceipt?.receipt_hash
              )}
            </code>
          </dd>
        </div>

        <div>
          <dt>Lineage hash</dt>
          <dd>
            <code>
              {displayHash(
                handoffReceipt?.lineage_hash
              )}
            </code>
          </dd>
        </div>
      </dl>

      <footer className="readiness-panel-footer">
        <p>
          Trial readiness is not execution authority.
          A prepared handoff is not an executed
          assessment. The governed backend remains
          authoritative.
        </p>
      </footer>
    </section>
  );
}