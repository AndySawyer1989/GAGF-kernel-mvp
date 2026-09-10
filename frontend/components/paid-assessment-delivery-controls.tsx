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
  approvePaidAssessmentDelivery,
  fetchPaidAssessmentDeliveryReadiness,
  fetchPaidAssessmentLifecycleStatus,
  recordPaidAssessmentClientAcknowledgment,
  recordPaidAssessmentClientResponse,
  recordPaidAssessmentDelivery,
  type PaidAssessmentHierarchy
} from "@/lib/governance-paid-assessment-delivery-api";


export type PaidAssessmentDeliveryRecordedValue = {
  deliveredAt: string;
  deliveredBy: string;
};


export type PaidAssessmentDeliveryControlsProps = {
  config: GovernanceAssessmentApiConfig;
  hierarchy: PaidAssessmentHierarchy;
  reportId: string | null;
  reportReady: boolean;
  repositoryVerified: boolean;
  findingsReady: boolean;
  onDeliveryRecorded: (
    value: PaidAssessmentDeliveryRecordedValue
  ) => void;
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


export function PaidAssessmentDeliveryControls({
  config,
  hierarchy,
  reportId,
  reportReady,
  repositoryVerified,
  findingsReady,
  onDeliveryRecorded
}: PaidAssessmentDeliveryControlsProps) {
  const [
    readinessStatus,
    setReadinessStatus
  ] = useState<string | null>(null);

  const [
    readinessReportId,
    setReadinessReportId
  ] = useState<string | null>(null);

  const [
    readinessChecking,
    setReadinessChecking
  ] = useState(false);

  const [
    readinessError,
    setReadinessError
  ] = useState<string | null>(null);

  const [
    scopeApproved,
    setScopeApproved
  ] = useState(false);

  const [
    evidenceBoundaryApproved,
    setEvidenceBoundaryApproved
  ] = useState(false);

  const [
    buyerLanguageApproved,
    setBuyerLanguageApproved
  ] = useState(false);

  const [
    deliveryApproved,
    setDeliveryApproved
  ] = useState(false);

  const [
    approving,
    setApproving
  ] = useState(false);

  const [
    approvalComplete,
    setApprovalComplete
  ] = useState(false);

  const [
    approvalError,
    setApprovalError
  ] = useState<string | null>(null);

  const [
    deliveryMethod,
    setDeliveryMethod
  ] = useState("email");

  const [
    deliveryReference,
    setDeliveryReference
  ] = useState("");

  const [
    deliveryCompleted,
    setDeliveryCompleted
  ] = useState(false);

  const [
    recording,
    setRecording
  ] = useState(false);

  const [
    deliveryRecorded,
    setDeliveryRecorded
  ] = useState(false);

  const [
    recordingError,
    setRecordingError
  ] = useState<string | null>(null);


  const [
    lifecycleStage,
    setLifecycleStage
  ] = useState<string | null>(null);

  const [
    lifecycleLoading,
    setLifecycleLoading
  ] = useState(true);

  const [
    lifecycleError,
    setLifecycleError
  ] = useState<string | null>(null);

  const [
    receiptAcknowledged,
    setReceiptAcknowledged
  ] = useState(false);

  const [
    clientResponseRecorded,
    setClientResponseRecorded
  ] = useState(false);

  const [
    acknowledgmentMethod,
    setAcknowledgmentMethod
  ] = useState("email_reply");

  const [
    acknowledgmentReference,
    setAcknowledgmentReference
  ] = useState("");

  const [
    clientConfirmedReceipt,
    setClientConfirmedReceipt
  ] = useState(false);

  const [
    acknowledgmentRecording,
    setAcknowledgmentRecording
  ] = useState(false);

  const [
    acknowledgmentError,
    setAcknowledgmentError
  ] = useState<string | null>(null);


  const [
    responseMethod,
    setResponseMethod
  ] = useState("email_reply");

  const [
    responseReference,
    setResponseReference
  ] = useState("");

  const [
    findingsDisposition,
    setFindingsDisposition
  ] = useState("acknowledged");

  const [
    recommendationsDisposition,
    setRecommendationsDisposition
  ] = useState("under_review");

  const [
    responseNote,
    setResponseNote
  ] = useState("");

  const [
    responseRecording,
    setResponseRecording
  ] = useState(false);

  const [
    responseError,
    setResponseError
  ] = useState<string | null>(null);


  useEffect(() => {
    const controller = new AbortController();

    async function restoreLifecycle() {
      setLifecycleLoading(true);
      setLifecycleError(null);

      try {
        const status =
          await fetchPaidAssessmentLifecycleStatus(
            config,
            hierarchy,
            controller.signal
          );

        if (controller.signal.aborted) {
          return;
        }

        if (status.repository_chain_valid !== true) {
          setLifecycleError(
            "Governed lifecycle repository integrity could not be verified."
          );
          return;
        }

        setLifecycleStage(
          status.current_stage
        );

        setDeliveryRecorded(
          status.delivery_recorded
        );

        setReceiptAcknowledged(
          status.receipt_acknowledged
        );

        setClientResponseRecorded(
          status.client_response_recorded
        );
      } catch (caught) {
        if (controller.signal.aborted) {
          return;
        }

        /*
         * Lifecycle restoration is read-only.
         *
         * A failed status read must not infer delivery,
         * receipt, response, closeout, or intervention
         * authority.
         */
        setLifecycleError(
          apiErrorMessage(
            caught,
            "Governed client lifecycle could not be restored."
          )
        );
      } finally {
        if (!controller.signal.aborted) {
          setLifecycleLoading(false);
        }
      }
    }

    void restoreLifecycle();

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


  const localPrerequisitesReady =
    reportReady &&
    repositoryVerified &&
    findingsReady &&
    reportId !== null;


  const allApprovalConfirmations =
    scopeApproved &&
    evidenceBoundaryApproved &&
    buyerLanguageApproved &&
    deliveryApproved;


  const canApprove =
    localPrerequisitesReady &&
    readinessReportId !== null &&
    readinessStatus ===
      "ready_for_delivery_approval_review" &&
    allApprovalConfirmations &&
    !approving &&
    !approvalComplete;


  const canRecordDelivery =
    approvalComplete &&
    deliveryReference.trim().length > 0 &&
    deliveryMethod.trim().length > 0 &&
    deliveryCompleted &&
    !recording &&
    !deliveryRecorded;


  const canRecordAcknowledgment =
    deliveryRecorded &&
    !receiptAcknowledged &&
    acknowledgmentMethod.trim().length > 0 &&
    acknowledgmentReference.trim().length > 0 &&
    clientConfirmedReceipt &&
    !acknowledgmentRecording;


  async function recordClientAcknowledgment() {
    if (!canRecordAcknowledgment) {
      return;
    }

    setAcknowledgmentRecording(true);
    setAcknowledgmentError(null);

    const acknowledgedAt =
      new Date().toISOString();

    const acknowledgmentId =
      (
        `client-acknowledgment-` +
        `${hierarchy.assessmentId}-` +
        `${Date.now()}`
      );

    try {
      const result =
        await recordPaidAssessmentClientAcknowledgment(
          config,
          hierarchy,
          {
            acknowledgment_id:
              acknowledgmentId,
            acknowledged_by:
              config.actorId,
            acknowledged_at:
              acknowledgedAt,
            acknowledgment_method:
              acknowledgmentMethod.trim(),
            acknowledgment_reference:
              acknowledgmentReference.trim(),
            client_acknowledged_receipt:
              clientConfirmedReceipt
          }
        );

      if (!result.client_receipt_acknowledged) {
        setAcknowledgmentError(
          "The governed backend did not record client receipt acknowledgment."
        );
        return;
      }

      setReceiptAcknowledged(true);
      setLifecycleStage(
        "client_receipt_acknowledged"
      );
    } catch (caught) {
      setAcknowledgmentError(
        apiErrorMessage(
          caught,
          "Governed client receipt acknowledgment failed."
        )
      );
    } finally {
      setAcknowledgmentRecording(false);
    }
  }


  const canRecordClientResponse =
    receiptAcknowledged &&
    !clientResponseRecorded &&
    responseMethod.trim().length > 0 &&
    responseReference.trim().length > 0 &&
    findingsDisposition.trim().length > 0 &&
    recommendationsDisposition.trim().length > 0 &&
    !responseRecording;


  async function recordClientResponse() {
    if (!canRecordClientResponse) {
      return;
    }

    setResponseRecording(true);
    setResponseError(null);

    const respondedAt =
      new Date().toISOString();

    const responseId =
      (
        `client-response-` +
        `${hierarchy.assessmentId}-` +
        `${Date.now()}`
      );

    try {
      const result =
        await recordPaidAssessmentClientResponse(
          config,
          hierarchy,
          {
            response_id:
              responseId,
            responded_by:
              config.actorId,
            responded_at:
              respondedAt,
            response_method:
              responseMethod.trim(),
            response_reference:
              responseReference.trim(),
            findings_disposition:
              findingsDisposition,
            recommendations_disposition:
              recommendationsDisposition,
            response_note:
              responseNote.trim()
          }
        );

      if (!result.client_response_recorded) {
        setResponseError(
          "The governed backend did not record the client response."
        );
        return;
      }

      setClientResponseRecorded(true);
      setLifecycleStage(
        "client_response_recorded"
      );
    } catch (caught) {
      setResponseError(
        apiErrorMessage(
          caught,
          "Governed client response recording failed."
        )
      );
    } finally {
      setResponseRecording(false);
    }
  }


  async function checkReadiness() {
    if (!localPrerequisitesReady) {
      return;
    }

    setReadinessChecking(true);
    setReadinessError(null);

    try {
      const result =
        await fetchPaidAssessmentDeliveryReadiness(
          config,
          hierarchy
        );

      setReadinessStatus(
        result.delivery_readiness_status
      );

      setReadinessReportId(
        result.report_id
      );
    } catch (caught) {
      setReadinessStatus(null);

      setReadinessError(
        apiErrorMessage(
          caught,
          "Governed delivery readiness could not be verified."
        )
      );
    } finally {
      setReadinessChecking(false);
    }
  }


  async function approveDelivery() {
    if (
      !canApprove ||
      readinessReportId === null
    ) {
      return;
    }

    setApproving(true);
    setApprovalError(null);

    const approvedAt =
      new Date().toISOString();

    const approvalId =
      (
        `delivery-approval-` +
        `${hierarchy.assessmentId}-` +
        `${Date.now()}`
      );

    try {
      const result =
        await approvePaidAssessmentDelivery(
          config,
          hierarchy,
          {
            approval_id: approvalId,
            tenant_id: hierarchy.tenantId,
            client_id: hierarchy.clientId,
            engagement_id:
              hierarchy.engagementId,
            assessment_id:
              hierarchy.assessmentId,
            report_id:
              readinessReportId,
            approved_by: config.actorId,
            approved_at: approvedAt,
            scope_approved: scopeApproved,
            evidence_boundary_approved:
              evidenceBoundaryApproved,
            buyer_language_approved:
              buyerLanguageApproved,
            delivery_approved:
              deliveryApproved
          }
        );

      if (
        !result.approved_for_human_delivery
      ) {
        setApprovalError(
          "The governed backend did not approve this package for human delivery."
        );
        return;
      }

      setApprovalComplete(true);
    } catch (caught) {
      setApprovalError(
        apiErrorMessage(
          caught,
          "Governed delivery approval failed."
        )
      );
    } finally {
      setApproving(false);
    }
  }


  async function recordDelivery() {
    if (
      !canRecordDelivery ||
      readinessReportId === null
    ) {
      return;
    }

    setRecording(true);
    setRecordingError(null);

    const deliveredAt =
      new Date().toISOString();

    const deliveryEventId =
      (
        `delivery-event-` +
        `${hierarchy.assessmentId}-` +
        `${Date.now()}`
      );

    try {
      const result =
        await recordPaidAssessmentDelivery(
          config,
          hierarchy,
          {
            delivery_event_id:
              deliveryEventId,
            tenant_id:
              hierarchy.tenantId,
            client_id:
              hierarchy.clientId,
            engagement_id:
              hierarchy.engagementId,
            assessment_id:
              hierarchy.assessmentId,
            report_id:
              readinessReportId,
            delivered_by:
              config.actorId,
            delivered_at:
              deliveredAt,
            delivery_method:
              deliveryMethod.trim(),
            delivery_reference:
              deliveryReference.trim(),
            delivery_completed:
              deliveryCompleted
          }
        );

      if (!result.delivery_recorded) {
        setRecordingError(
          "The governed backend did not record delivery."
        );
        return;
      }

      setDeliveryRecorded(true);

      onDeliveryRecorded({
        deliveredAt,
        deliveredBy: config.actorId
      });
    } catch (caught) {
      setRecordingError(
        apiErrorMessage(
          caught,
          "Governed delivery recording failed."
        )
      );
    } finally {
      setRecording(false);
    }
  }


  return (
    <section
      className="panel"
      aria-labelledby="paid-delivery-controls-title"
    >
      <div className="panel-header">
        <div>
          <p className="panel-kicker">
            Governed client delivery
          </p>

          <h2 id="paid-delivery-controls-title">
            Delivery authorization
          </h2>

          <p>
            Delivery readiness, human approval,
            and delivery recording are separate
            governed actions.
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
            : approvalComplete
              ? "Approved for delivery"
              : readinessStatus ===
                  "ready_for_delivery_approval_review"
                ? "Ready for approval"
                : "Readiness not verified"}
        </span>
      </div>


      {!localPrerequisitesReady && (
        <div className="assessment-closeout-pending">
          <strong>
            Delivery prerequisites are incomplete.
          </strong>

          <p>
            A governed report package, verified
            repository chain, and governed findings
            are required before delivery review.
          </p>
        </div>
      )}


      <div className="form-actions">
        <button
          className="secondary-button"
          type="button"
          disabled={
            !localPrerequisitesReady ||
            readinessChecking ||
            deliveryRecorded
          }
          onClick={() =>
            void checkReadiness()
          }
        >
          {readinessChecking
            ? "Checking readiness..."
            : "Verify delivery readiness"}
        </button>
      </div>


      {readinessError && (
        <div
          className="error-panel"
          role="alert"
        >
          <div>
            <p className="error-title">
              Delivery readiness failed
            </p>
            <p>{readinessError}</p>
          </div>
        </div>
      )}


      {readinessStatus ===
        "ready_for_delivery_approval_review" &&
        !approvalComplete && (
          <fieldset
            disabled={approving}
          >
            <legend>
              Human delivery approval
            </legend>

            <label>
              <input
                type="checkbox"
                checked={scopeApproved}
                onChange={(event) =>
                  setScopeApproved(
                    event.target.checked
                  )
                }
              />
              Assessment scope reviewed and approved
            </label>

            <label>
              <input
                type="checkbox"
                checked={
                  evidenceBoundaryApproved
                }
                onChange={(event) =>
                  setEvidenceBoundaryApproved(
                    event.target.checked
                  )
                }
              />
              Evidence boundary reviewed and approved
            </label>

            <label>
              <input
                type="checkbox"
                checked={buyerLanguageApproved}
                onChange={(event) =>
                  setBuyerLanguageApproved(
                    event.target.checked
                  )
                }
              />
              Buyer-facing language reviewed and approved
            </label>

            <label>
              <input
                type="checkbox"
                checked={deliveryApproved}
                onChange={(event) =>
                  setDeliveryApproved(
                    event.target.checked
                  )
                }
              />
              I explicitly approve this governed package
              for human delivery
            </label>

            <div className="form-actions">
              <button
                className="primary-button"
                type="button"
                disabled={!canApprove}
                onClick={() =>
                  void approveDelivery()
                }
              >
                {approving
                  ? "Recording approval..."
                  : "Approve for human delivery"}
              </button>
            </div>
          </fieldset>
        )}


      {approvalError && (
        <div
          className="error-panel"
          role="alert"
        >
          <div>
            <p className="error-title">
              Delivery approval failed
            </p>
            <p>{approvalError}</p>
          </div>
        </div>
      )}


      {approvalComplete &&
        !deliveryRecorded && (
          <fieldset disabled={recording}>
            <legend>
              Human delivery confirmation
            </legend>

            <label>
              Delivery method
              <select
                value={deliveryMethod}
                onChange={(event) =>
                  setDeliveryMethod(
                    event.target.value
                  )
                }
              >
                <option value="email">
                  Email
                </option>
                <option value="secure-portal">
                  Secure portal
                </option>
                <option value="in-person">
                  In person
                </option>
                <option value="other">
                  Other
                </option>
              </select>
            </label>

            <label>
              Delivery reference
              <input
                type="text"
                value={deliveryReference}
                onChange={(event) =>
                  setDeliveryReference(
                    event.target.value
                  )
                }
                placeholder="Message ID, portal reference, or delivery note"
              />
            </label>

            <label>
              <input
                type="checkbox"
                checked={deliveryCompleted}
                onChange={(event) =>
                  setDeliveryCompleted(
                    event.target.checked
                  )
                }
              />
              I confirm that the governed report package
              was delivered
            </label>

            <p>
              Recording delivery does not establish
              client receipt, acknowledgment, or response.
            </p>

            <div className="form-actions">
              <button
                className="primary-button"
                type="button"
                disabled={!canRecordDelivery}
                onClick={() =>
                  void recordDelivery()
                }
              >
                {recording
                  ? "Recording delivery..."
                  : "Record human delivery"}
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
              Delivery recording failed
            </p>
            <p>{recordingError}</p>
          </div>
        </div>
      )}


      {lifecycleLoading && (
        <p>
          Restoring governed client lifecycle...
        </p>
      )}


      {lifecycleError && (
        <div
          className="error-panel"
          role="alert"
        >
          <div>
            <p className="error-title">
              Lifecycle restoration failed
            </p>
            <p>{lifecycleError}</p>
            <p>
              Current lifecycle state could not be
              verified. No later lifecycle stage was
              inferred. Resolve the error and retry
              lifecycle restoration before continuing.
            </p>
          </div>
        </div>
      )}


      {deliveryRecorded &&
        !receiptAcknowledged && (
          <fieldset
            disabled={acknowledgmentRecording}
          >
            <legend>
              Client receipt acknowledgment
            </legend>

            <p>
              Record this only after the client
              explicitly confirms receipt of the
              governed report package.
            </p>

            <label>
              Acknowledgment method
              <select
                value={acknowledgmentMethod}
                onChange={(event) =>
                  setAcknowledgmentMethod(
                    event.target.value
                  )
                }
              >
                <option value="email_reply">
                  Email reply
                </option>
                <option value="secure_portal">
                  Secure portal
                </option>
                <option value="phone_confirmation">
                  Phone confirmation
                </option>
                <option value="in_person">
                  In person
                </option>
                <option value="other">
                  Other
                </option>
              </select>
            </label>

            <label>
              Acknowledgment reference
              <input
                type="text"
                value={acknowledgmentReference}
                onChange={(event) =>
                  setAcknowledgmentReference(
                    event.target.value
                  )
                }
                placeholder="Message ID, portal record, or receipt reference"
              />
            </label>

            <label>
              <input
                type="checkbox"
                checked={clientConfirmedReceipt}
                onChange={(event) =>
                  setClientConfirmedReceipt(
                    event.target.checked
                  )
                }
              />
              I confirm that the client explicitly
              acknowledged receipt of the report
            </label>

            <p>
              Receipt acknowledgment does not mean
              that the client accepts the findings,
              recommendations, or any intervention.
            </p>

            <div className="form-actions">
              <button
                className="primary-button"
                type="button"
                disabled={!canRecordAcknowledgment}
                onClick={() =>
                  void recordClientAcknowledgment()
                }
              >
                {acknowledgmentRecording
                  ? "Recording receipt..."
                  : "Record client receipt"}
              </button>
            </div>
          </fieldset>
        )}


      {acknowledgmentError && (
        <div
          className="error-panel"
          role="alert"
        >
          <div>
            <p className="error-title">
              Client receipt recording failed
            </p>
            <p>{acknowledgmentError}</p>
          </div>
        </div>
      )}


      {receiptAcknowledged && (
        <div className="assessment-closeout-pending">
          <strong>
            Client receipt acknowledged.
          </strong>

          <p>
            Receipt is recorded independently from
            findings acceptance, recommendation
            acceptance, response, closeout, or
            intervention authority.
          </p>
        </div>
      )}


      {receiptAcknowledged &&
        !clientResponseRecorded && (
          <fieldset
            disabled={responseRecording}
          >
            <legend>
              Client response
            </legend>

            <p>
              Record only an explicit client response.
              Receipt alone does not establish findings
              or recommendation disposition.
            </p>

            <label>
              Response method
              <select
                value={responseMethod}
                onChange={(event) =>
                  setResponseMethod(
                    event.target.value
                  )
                }
              >
                <option value="email_reply">
                  Email reply
                </option>
                <option value="secure_portal">
                  Secure portal
                </option>
                <option value="meeting">
                  Meeting
                </option>
                <option value="phone">
                  Phone
                </option>
                <option value="other">
                  Other
                </option>
              </select>
            </label>

            <label>
              Response reference
              <input
                type="text"
                value={responseReference}
                onChange={(event) =>
                  setResponseReference(
                    event.target.value
                  )
                }
                placeholder="Message ID, meeting note, or response reference"
              />
            </label>

            <label>
              Findings disposition
              <select
                value={findingsDisposition}
                onChange={(event) =>
                  setFindingsDisposition(
                    event.target.value
                  )
                }
              >
                <option value="acknowledged">
                  Acknowledged
                </option>
                <option value="under_review">
                  Under review
                </option>
                <option value="disputed">
                  Disputed
                </option>
              </select>
            </label>

            <label>
              Recommendations disposition
              <select
                value={recommendationsDisposition}
                onChange={(event) =>
                  setRecommendationsDisposition(
                    event.target.value
                  )
                }
              >
                <option value="under_review">
                  Under review
                </option>
                <option value="accepted">
                  Accepted
                </option>
                <option value="partially_accepted">
                  Partially accepted
                </option>
                <option value="declined">
                  Declined
                </option>
              </select>
            </label>

            <label>
              Response note
              <textarea
                value={responseNote}
                onChange={(event) =>
                  setResponseNote(
                    event.target.value
                  )
                }
                placeholder="Optional client response note"
              />
            </label>

            <p>
              Findings acknowledgment is not validation.
              Recommendation acceptance does not authorize
              implementation or intervention.
            </p>

            <div className="form-actions">
              <button
                className="primary-button"
                type="button"
                disabled={!canRecordClientResponse}
                onClick={() =>
                  void recordClientResponse()
                }
              >
                {responseRecording
                  ? "Recording response..."
                  : "Record client response"}
              </button>
            </div>
          </fieldset>
        )}


      {responseError && (
        <div
          className="error-panel"
          role="alert"
        >
          <div>
            <p className="error-title">
              Client response recording failed
            </p>
            <p>{responseError}</p>
          </div>
        </div>
      )}


      {clientResponseRecorded && (
        <div className="assessment-closeout-pending">
          <strong>
            Client response recorded.
          </strong>

          <p>
            The response is persisted independently
            from findings validation, implementation
            authorization, intervention authority,
            closeout, ROI verification, or verified
            customer outcomes.
          </p>
        </div>
      )}


      {deliveryRecorded && (
        <div className="assessment-closeout-pending">
          <strong>
            Governed human delivery recorded.
          </strong>

          <p>
            This record does not mean that client
            receipt, acknowledgment, or response has
            occurred.
          </p>
        </div>
      )}
    </section>
  );
}
