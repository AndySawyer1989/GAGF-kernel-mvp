"use client";

import {
  useEffect,
  useState
} from "react";

import {
  GovernanceAssessmentApiError,
  type GovernanceAssessmentApiConfig
} from "@/lib/governance-assessment-api";

import {
  fetchPaidAssessmentCloseoutStatus,
  fetchPaidAssessmentLifecycleStatus,
  recordPaidAssessmentAdministrativeCloseout,
  type PaidAssessmentHierarchy
} from "@/lib/governance-paid-assessment-delivery-api";


export type AssessmentCloseoutPanelProps = {
  config: GovernanceAssessmentApiConfig;
  hierarchy: PaidAssessmentHierarchy;
};


function apiErrorMessage(
  caught: unknown,
  fallback: string
): string {
  if (
    caught instanceof GovernanceAssessmentApiError
  ) {
    const payload =
      typeof caught.payload === "object" &&
      caught.payload !== null
        ? caught.payload as Record<string, unknown>
        : null;

    const detail =
      typeof payload?.detail === "string"
        ? payload.detail
        : null;

    return detail ??
      `${fallback} Backend returned ${caught.status}.`;
  }

  return fallback;
}


export function AssessmentCloseoutPanel({
  config,
  hierarchy
}: AssessmentCloseoutPanelProps) {
  const [
    loading,
    setLoading
  ] = useState(true);

  const [
    restorationError,
    setRestorationError
  ] = useState<string | null>(null);

  const [
    clientResponseRecorded,
    setClientResponseRecorded
  ] = useState(false);

  const [
    closeoutRecorded,
    setCloseoutRecorded
  ] = useState(false);

  const [
    closeoutStatus,
    setCloseoutStatus
  ] = useState<string | null>(null);

  const [
    reportId,
    setReportId
  ] = useState<string | null>(null);

  const [
    closedBy,
    setClosedBy
  ] = useState<string | null>(null);

  const [
    closedAt,
    setClosedAt
  ] = useState<string | null>(null);

  const [
    persistedCloseoutReason,
    setPersistedCloseoutReason
  ] = useState<string | null>(null);

  const [
    closeoutReason,
    setCloseoutReason
  ] = useState("");

  const [
    administrativeCloseoutConfirmed,
    setAdministrativeCloseoutConfirmed
  ] = useState(false);

  const [
    recording,
    setRecording
  ] = useState(false);

  const [
    recordingError,
    setRecordingError
  ] = useState<string | null>(null);


  useEffect(() => {
    const controller = new AbortController();

    async function restoreCloseoutState() {
      setLoading(true);
      setRestorationError(null);

      try {
        const [
          lifecycle,
          closeout
        ] = await Promise.all([
          fetchPaidAssessmentLifecycleStatus(
            config,
            hierarchy,
            controller.signal
          ),
          fetchPaidAssessmentCloseoutStatus(
            config,
            hierarchy,
            controller.signal
          )
        ]);

        if (controller.signal.aborted) {
          return;
        }

        if (
          lifecycle.repository_chain_valid !== true
        ) {
          setRestorationError(
            "Governed lifecycle repository integrity could not be verified."
          );
          return;
        }

        if (
          closeout.repository_chain_valid !== true
        ) {
          setRestorationError(
            "Governed closeout repository integrity could not be verified."
          );
          return;
        }

        setClientResponseRecorded(
          lifecycle.client_response_recorded &&
          lifecycle.current_stage ===
            "client_response_recorded"
        );

        if (
          closeout.found &&
          closeout.closeout_recorded &&
          closeout.closeout_status ===
            "assessment_closed"
        ) {
          setCloseoutRecorded(true);
          setCloseoutStatus(
            closeout.closeout_status
          );
          setReportId(
            closeout.report_id
          );
          setClosedBy(
            closeout.closed_by
          );
          setClosedAt(
            closeout.closed_at
          );
          setPersistedCloseoutReason(
            closeout.closeout_reason
          );
        } else {
          setCloseoutRecorded(false);
          setCloseoutStatus(null);
          setReportId(
            lifecycle.report_id
          );
        }
      } catch (caught) {
        if (controller.signal.aborted) {
          return;
        }

        /*
         * Restoration is read-only.
         *
         * A failed read must not infer:
         * - client response,
         * - administrative closeout,
         * - recommendation implementation,
         * - intervention authority,
         * - remediation success.
         */
        setRestorationError(
          apiErrorMessage(
            caught,
            "Governed administrative closeout state could not be restored."
          )
        );
      } finally {
        if (!controller.signal.aborted) {
          setLoading(false);
        }
      }
    }

    void restoreCloseoutState();

    return () => controller.abort();
  }, [
    config.baseUrl,
    config.tenantId,
    config.actorId,
    config.actorRoles,
    hierarchy.tenantId,
    hierarchy.clientId,
    hierarchy.engagementId,
    hierarchy.assessmentId
  ]);


  const closeoutEligible =
    clientResponseRecorded &&
    !closeoutRecorded;

  const canRecordCloseout =
    closeoutEligible &&
    closeoutReason.trim().length > 0 &&
    administrativeCloseoutConfirmed &&
    !recording;


  async function recordAdministrativeCloseout() {
    if (!canRecordCloseout) {
      return;
    }

    setRecording(true);
    setRecordingError(null);

    try {
      const result =
        await recordPaidAssessmentAdministrativeCloseout(
          config,
          hierarchy,
          {
            closed_by: config.actorId,
            closeout_reason:
              closeoutReason.trim(),
            administrative_closeout_confirmed:
              administrativeCloseoutConfirmed
          }
        );

      if (
        !result.administrative_closeout_recorded ||
        result.closeout_status !==
          "assessment_closed" ||
        result.repository_chain_valid !== true
      ) {
        setRecordingError(
          "The governed backend did not confirm administrative closeout."
        );
        return;
      }

      setCloseoutRecorded(true);
      setCloseoutStatus(
        result.closeout_status
      );
      setReportId(
        result.report_id
      );
      setClosedBy(
        result.closed_by
      );
      setClosedAt(
        new Date().toISOString()
      );
      setPersistedCloseoutReason(
        result.closeout_reason
      );
    } catch (caught) {
      setRecordingError(
        apiErrorMessage(
          caught,
          "Governed administrative closeout failed."
        )
      );
    } finally {
      setRecording(false);
    }
  }


  const heading =
    closeoutRecorded
      ? "Assessment administratively closed"
      : clientResponseRecorded
        ? "Administrative closeout available"
        : "Client response required";

  const badge =
    closeoutRecorded
      ? "Assessment closed"
      : clientResponseRecorded
        ? "Closeout available"
        : "Closeout unavailable";


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
            {heading}
          </h2>

          <p>
            Administrative closeout is a separate governed
            action performed only after an explicit client
            response has been persisted.
          </p>
        </div>

        <span
          className={
            closeoutRecorded
              ? "status-badge status-healthy"
              : "status-badge status-warning"
          }
        >
          <span
            className="status-dot"
            aria-hidden="true"
          />

          {badge}
        </span>
      </div>


      {loading && (
        <p>
          Restoring governed administrative closeout state...
        </p>
      )}


      {restorationError && (
        <div
          className="error-panel"
          role="alert"
        >
          <div>
            <p className="error-title">
              Closeout restoration failed
            </p>

            <p>{restorationError}</p>
            <p>
              Closeout state could not be verified.
              No administrative closeout state was
              inferred. Resolve the error and retry
              restoration before continuing.
            </p>
          </div>
        </div>
      )}


      {!loading &&
        !restorationError &&
        !clientResponseRecorded &&
        !closeoutRecorded && (
          <div className="assessment-closeout-pending">
            <strong>
              Administrative closeout is not yet available.
            </strong>

            <p>
              The governed lifecycle must contain an explicit
              client response before an operator can perform
              administrative closeout.
            </p>

            <p>
              Delivery or receipt acknowledgment alone does
              not authorize closeout.
            </p>
          </div>
        )}


      {closeoutEligible && (
        <fieldset disabled={recording}>
          <legend>
            Explicit administrative closeout
          </legend>

          <p>
            Closing the assessment records an administrative
            terminal state only.
          </p>

          <label>
            Closeout reason
            <textarea
              value={closeoutReason}
              onChange={(event) =>
                setCloseoutReason(
                  event.target.value
                )
              }
              placeholder="Describe why administrative closeout is appropriate"
            />
          </label>

          <label>
            <input
              type="checkbox"
              checked={
                administrativeCloseoutConfirmed
              }
              onChange={(event) =>
                setAdministrativeCloseoutConfirmed(
                  event.target.checked
                )
              }
            />

            I explicitly confirm administrative closeout
            of this paid assessment
          </label>

          <div className="form-actions">
            <button
              className="primary-button"
              type="button"
              disabled={!canRecordCloseout}
              onClick={() =>
                void recordAdministrativeCloseout()
              }
            >
              {recording
                ? "Recording closeout..."
                : "Record administrative closeout"}
            </button>
          </div>
        </fieldset>
      )}


      {recordingError && (
        <div
          className="error-panel"
          role="alert"
        >
          <div>
            <p className="error-title">
              Administrative closeout failed
            </p>

            <p>{recordingError}</p>
            <p>
              Administrative closeout was not inferred
              from this failed operation. Verify governed
              closeout status before retrying.
            </p>
          </div>
        </div>
      )}


      {closeoutRecorded && (
        <>
          <dl className="assessment-closeout-metadata">
            <div>
              <dt>Status</dt>
              <dd>
                {closeoutStatus ??
                  "assessment_closed"}
              </dd>
            </div>

            <div>
              <dt>Report ID</dt>
              <dd>
                {reportId ??
                  "Governed report"}
              </dd>
            </div>

            <div>
              <dt>Closed by</dt>
              <dd>
                {closedBy ??
                  "Governed operator"}
              </dd>
            </div>

            <div>
              <dt>Closed at</dt>
              <dd>
                {closedAt ??
                  "Recorded by governed backend"}
              </dd>
            </div>

            <div>
              <dt>Closeout reason</dt>
              <dd>
                {persistedCloseoutReason ??
                  "Administrative closeout recorded"}
              </dd>
            </div>
          </dl>

          <div className="assessment-closeout-pending">
            <strong>
              Governed administrative closeout recorded.
            </strong>

            <p>
              This state is restored from the persisted
              closeout artifact and is not inferred from
              delivery, receipt, or client response alone.
            </p>
          </div>
        </>
      )}


      <p className="assessment-closeout-boundary">
        Administrative closeout does not validate findings,
        implement recommendations, request or authorize an
        intervention, establish execution authority,
        establish causation or ROI, prove remediation
        success, or establish a verified customer outcome.
      </p>
    </section>
  );
}
