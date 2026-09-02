from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from backend.app.gagf.governance_commercial_paid_assessment_delivery_readiness import (
    CommercialPaidAssessmentDeliveryReadiness,
    CommercialPaidAssessmentDeliveryReadinessError,
    GovernanceCommercialPaidAssessmentDeliveryReadinessService,
)
from backend.app.gagf.governance_commercial_paid_assessment_approved_delivery_store import (
    CommercialPaidAssessmentApprovedDeliveryStoreError,
    GovernanceCommercialPaidAssessmentApprovedDeliveryStore,
)
from backend.app.gagf.governance_real_paid_assessment_delivery_approval_handoff import (
    GovernanceRealPaidAssessmentDeliveryApprovalHandoffService,
    RealPaidAssessmentDeliveryApprovalHandoffError,
    RealPaidAssessmentDeliveryApprovalHandoffResult,
)


COMMERCIAL_PAID_ASSESSMENT_DELIVERY_APPROVAL_HANDOFF_ID = (
    "governance-commercial-paid-assessment-delivery-approval-handoff"
)
COMMERCIAL_PAID_ASSESSMENT_DELIVERY_APPROVAL_HANDOFF_VERSION = "0.1.0"
COMMERCIAL_PAID_ASSESSMENT_DELIVERY_APPROVAL_HANDOFF_SCHEMA_VERSION = "1.0.0"
COMMERCIAL_PAID_ASSESSMENT_APPROVED_DELIVERY_DATABASE = (
    "commercial-paid-assessment-approved-deliveries.sqlite3"
)


class CommercialPaidAssessmentDeliveryApprovalHandoffError(RuntimeError):
    """Raised when explicit human delivery approval cannot be bound safely."""


@dataclass(frozen=True, slots=True)
class CommercialPaidAssessmentDeliveryApprovalHandoff:
    commercial_readiness: CommercialPaidAssessmentDeliveryReadiness
    handoff: RealPaidAssessmentDeliveryApprovalHandoffResult

    result_type: str = COMMERCIAL_PAID_ASSESSMENT_DELIVERY_APPROVAL_HANDOFF_ID
    version: str = COMMERCIAL_PAID_ASSESSMENT_DELIVERY_APPROVAL_HANDOFF_VERSION
    schema_version: str = (
        COMMERCIAL_PAID_ASSESSMENT_DELIVERY_APPROVAL_HANDOFF_SCHEMA_VERSION
    )

    @property
    def hierarchy_key(self) -> str:
        return self.commercial_readiness.hierarchy_key

    def to_dict(self) -> dict[str, Any]:
        """
        Safe commercial projection.

        The full real handoff remains available server-side for the next
        delivery-recording stage. Browser serialization exposes approval and
        envelope commitments, not the report body or execution internals.
        """
        approval = self.handoff.delivery_approval
        envelope = self.handoff.delivery_envelope

        return {
            "result_type": self.result_type,
            "version": self.version,
            "schema_version": self.schema_version,
            "hierarchy_key": self.hierarchy_key,
            "handoff_status": self.handoff.handoff_status,
            "approved_for_human_delivery": (
                envelope.delivery_status
                == "approved_for_human_delivery"
            ),
            "approval_id": approval.approval_id,
            "approval_hash": approval.approval_hash,
            "approved_by": approval.approved_by,
            "approved_at": approval.approved_at,
            "report_id": envelope.report_id,
            "delivery_status": envelope.delivery_status,
            "delivery_envelope_hash": envelope.envelope_hash,
            "execution_status_hash": (
                self.commercial_readiness.execution_status_hash
            ),
            "operator_snapshot_hash": (
                self.commercial_readiness.operator_snapshot_hash
            ),
            "boundaries": {
                "readiness_is_not_human_approval": True,
                "human_approval_must_be_explicit": True,
                "commercial_handoff_does_not_auto_approve": True,
                "existing_real_approval_handoff_is_authoritative": True,
                "pa003_remains_delivery_envelope_authority": True,
                "approved_for_human_delivery_is_not_delivery": True,
                "approved_for_human_delivery_is_not_client_receipt": True,
                "approved_for_human_delivery_is_not_client_acceptance": True,
                "approved_for_human_delivery_is_not_customer_outcome": True,
                "report_payload_not_exposed": True,
                "execution_result_not_exposed": True,
            },
        }


class GovernanceCommercialPaidAssessmentDeliveryApprovalHandoffService:
    """
    Bind an explicit human delivery approval to restart-safe commercial
    readiness and delegate approval/envelope authority to the existing real
    paid-assessment approval handoff.

    This service does not infer approval, auto-approve, deliver the report,
    record delivery, record client receipt, or establish customer outcome.
    """

    def __init__(
        self,
        *,
        readiness_service: GovernanceCommercialPaidAssessmentDeliveryReadinessService,
        approval_handoff_service: (
            GovernanceRealPaidAssessmentDeliveryApprovalHandoffService | None
        ) = None,
        approved_delivery_store: (
            GovernanceCommercialPaidAssessmentApprovedDeliveryStore | None
        ) = None,
    ) -> None:
        if not isinstance(
            readiness_service,
            GovernanceCommercialPaidAssessmentDeliveryReadinessService,
        ):
            raise CommercialPaidAssessmentDeliveryApprovalHandoffError(
                "readiness_service must be a "
                "GovernanceCommercialPaidAssessmentDeliveryReadinessService"
            )

        self._readiness_service = readiness_service
        self._approval_handoff_service = (
            approval_handoff_service
            if approval_handoff_service is not None
            else GovernanceRealPaidAssessmentDeliveryApprovalHandoffService()
        )

        execution_directory = Path(
            readiness_service.execution_service.execution_directory
        )
        self._approved_delivery_store = (
            approved_delivery_store
            if approved_delivery_store is not None
            else GovernanceCommercialPaidAssessmentApprovedDeliveryStore(
                execution_directory
                / COMMERCIAL_PAID_ASSESSMENT_APPROVED_DELIVERY_DATABASE
            )
        )

    def handoff(
        self,
        *,
        tenant_id: str,
        client_id: str,
        engagement_id: str,
        assessment_id: str,
        approval_payload: dict[str, Any],
    ) -> CommercialPaidAssessmentDeliveryApprovalHandoff:
        if not isinstance(approval_payload, dict):
            raise CommercialPaidAssessmentDeliveryApprovalHandoffError(
                "approval_payload must be an object"
            )

        try:
            commercial_readiness = self._readiness_service.verify(
                tenant_id=tenant_id,
                client_id=client_id,
                engagement_id=engagement_id,
                assessment_id=assessment_id,
            )
        except CommercialPaidAssessmentDeliveryReadinessError as exc:
            raise CommercialPaidAssessmentDeliveryApprovalHandoffError(
                "commercial delivery readiness failed: "
                f"{exc}"
            ) from exc

        try:
            handoff = self._approval_handoff_service.handoff(
                readiness=commercial_readiness.readiness,
                approval_payload=approval_payload,
            )
        except RealPaidAssessmentDeliveryApprovalHandoffError as exc:
            raise CommercialPaidAssessmentDeliveryApprovalHandoffError(
                "explicit human delivery approval handoff failed: "
                f"{exc}"
            ) from exc

        if handoff.hierarchy_key != commercial_readiness.hierarchy_key:
            raise CommercialPaidAssessmentDeliveryApprovalHandoffError(
                "approval handoff hierarchy does not match verified readiness"
            )

        if (
            handoff.delivery_envelope.report_id
            != commercial_readiness.readiness.execution_result.report_id
        ):
            raise CommercialPaidAssessmentDeliveryApprovalHandoffError(
                "approval handoff report_id does not match verified readiness"
            )

        if handoff.handoff_status != "approved_for_human_delivery":
            raise CommercialPaidAssessmentDeliveryApprovalHandoffError(
                "approval handoff did not produce approved_for_human_delivery"
            )

        result = CommercialPaidAssessmentDeliveryApprovalHandoff(
            commercial_readiness=commercial_readiness,
            handoff=handoff,
        )

        durable_approved_delivery_payload = {
            "operator_handoff_passed": True,
            "approved_for_human_delivery": (
                handoff.delivery_envelope.delivery_status
                == "approved_for_human_delivery"
            ),
            "result": handoff.to_dict(),
            "boundaries": {
                "commercial_wrapper_is_not_approval_authority": True,
                "real_approval_handoff_remains_authoritative": True,
                "pa003_remains_delivery_envelope_authority": True,
                "operator_handoff_passed_is_not_delivery": True,
                "approved_for_human_delivery_is_not_delivery": True,
            },
        }

        try:
            self._approved_delivery_store.put(
                tenant_id=tenant_id,
                client_id=client_id,
                engagement_id=engagement_id,
                assessment_id=assessment_id,
                execution_status_hash=(
                    commercial_readiness.execution_status_hash
                ),
                operator_snapshot_hash=(
                    commercial_readiness.operator_snapshot_hash
                ),
                approved_delivery_payload=(
                    durable_approved_delivery_payload
                ),
            )
        except CommercialPaidAssessmentApprovedDeliveryStoreError as exc:
            raise CommercialPaidAssessmentDeliveryApprovalHandoffError(
                "approved delivery handoff was created but durable "
                f"approved-delivery persistence failed: {exc}"
            ) from exc

        return result
