"use client";

import {
  useState
} from "react";

import {
  GovernanceAssessmentApiError,
  type GovernanceAssessmentApiConfig
} from "@/lib/governance-assessment-api";

import {
  approvePaidAssessmentDelivery,
  fetchPaidAssessmentDeliveryReadiness,
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
      reportId === null
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
            report_id: reportId,
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
      reportId === null
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
              reportId,
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
