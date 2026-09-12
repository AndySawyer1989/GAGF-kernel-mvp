type CustomerTrialExecutionHandoffControlProps = {
  trialReady: boolean;

  authorizationComplete: boolean;

  bindingAvailable: boolean;

  handoffPrepared: boolean;

  preparing: boolean;

  error?: string | null;

  onPrepare: () => void;
};


export function
CustomerTrialExecutionHandoffControl({
  trialReady,
  authorizationComplete,
  bindingAvailable,
  handoffPrepared,
  preparing,
  error = null,
  onPrepare
}: CustomerTrialExecutionHandoffControlProps) {
  const canPrepare =
    trialReady &&
    authorizationComplete &&
    bindingAvailable &&
    !handoffPrepared &&
    !preparing;

  let readinessMessage =
    "Controlled-trial preflight is required.";

  if (
    trialReady &&
    !authorizationComplete
  ) {
    readinessMessage =
      (
        "Complete contract execution and "
        + "paid-work authorization before "
        + "preparing the handoff."
      );
  } else if (
    trialReady &&
    authorizationComplete &&
    !bindingAvailable
  ) {
    readinessMessage =
      (
        "The governed execution-input "
        + "binding must be available."
      );
  } else if (
    handoffPrepared
  ) {
    readinessMessage =
      (
        "The execution handoff has been "
        + "prepared and durably recorded."
      );
  } else if (
    canPrepare
  ) {
    readinessMessage =
      (
        "All preparation prerequisites "
        + "are satisfied."
      );
  }

  return (
    <section
      className="panel"
      aria-labelledby={
        "customer-trial-handoff-control-title"
      }
    >
      <div className="panel-header">
        <div>
          <p className="panel-kicker">
            Controlled customer trial
          </p>

          <h2
            id={
              "customer-trial-handoff-control-title"
            }
          >
            Prepare execution handoff
          </h2>

          <p className="assessment-workflow-description">
            Create the governed handoff evidence
            that binds trial readiness, contract
            execution, human paid-work
            authorization, and the immutable
            execution-input binding.
          </p>
        </div>

        <span
          className={
            handoffPrepared
              ? "status-badge status-healthy"
              : (
                  canPrepare
                    ? "status-badge status-warning"
                    : "status-badge"
                )
          }
        >
          <span
            className="status-dot"
            aria-hidden="true"
          />

          {handoffPrepared
            ? "Handoff prepared"
            : (
                canPrepare
                  ? "Ready to prepare"
                  : "Prerequisites incomplete"
              )}
        </span>
      </div>

      <div
        className="assessment-workflow-description"
      >
        <p>
          {readinessMessage}
        </p>

        <p>
          Preparing this handoff does not execute
          the assessment. The existing governed
          paid-assessment execution path remains
          authoritative.
        </p>
      </div>

      {error && (
        <div
          className="error-panel"
          role="alert"
        >
          <div>
            <p className="error-title">
              Execution handoff preparation failed
            </p>

            <p>
              {error}
            </p>
          </div>
        </div>
      )}

      <div className="panel-actions">
        <button
          type="button"
          disabled={!canPrepare}
          onClick={onPrepare}
        >
          {preparing
            ? "Preparing handoff..."
            : (
                handoffPrepared
                  ? "Handoff prepared"
                  : "Prepare execution handoff"
              )}
        </button>
      </div>

      <footer className="readiness-panel-footer">
        <p>
          Handoff preparation is not execution
          authority, recovery authority, delivery
          authority, administrative closeout
          authority, or intervention authority.
        </p>
      </footer>
    </section>
  );
}