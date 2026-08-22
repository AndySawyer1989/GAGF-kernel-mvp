from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from backend.app.gagf.governance_paid_assessment_delivery_envelope import (
    GovernancePaidAssessmentDeliveryEnvelopeService,
    GovernedPaidAssessmentDeliveryEnvelope,
    PaidAssessmentDeliveryApproval,
)
from backend.app.gagf.governance_real_paid_assessment_delivery_readiness import (
    READY_FOR_DELIVERY_APPROVAL_REVIEW,
    RealPaidAssessmentDeliveryReadinessResult,
)


REAL_PAID_ASSESSMENT_DELIVERY_APPROVAL_HANDOFF_ID = (
    "governance-real-paid-assessment-delivery-approval-handoff"
)
REAL_PAID_ASSESSMENT_DELIVERY_APPROVAL_HANDOFF_VERSION = "0.1.0"
REAL_PAID_ASSESSMENT_DELIVERY_APPROVAL_HANDOFF_SCHEMA_VERSION = "1.0.0"

DELIVERY_APPROVAL_HANDOFF_STATUS = "approved_for_human_delivery"


class RealPaidAssessmentDeliveryApprovalHandoffError(RuntimeError):
    """Raised when human delivery approval cannot be bound safely."""


@dataclass(frozen=True, slots=True)
class RealPaidAssessmentDeliveryApprovalHandoffResult:
    readiness: RealPaidAssessmentDeliveryReadinessResult
    delivery_approval: PaidAssessmentDeliveryApproval
    delivery_envelope: GovernedPaidAssessmentDeliveryEnvelope

    handoff_status: str = DELIVERY_APPROVAL_HANDOFF_STATUS
    result_type: str = (
        REAL_PAID_ASSESSMENT_DELIVERY_APPROVAL_HANDOFF_ID
    )
    version: str = (
        REAL_PAID_ASSESSMENT_DELIVERY_APPROVAL_HANDOFF_VERSION
    )
    schema_version: str = (
        REAL_PAID_ASSESSMENT_DELIVERY_APPROVAL_HANDOFF_SCHEMA_VERSION
    )

    @property
    def hierarchy_key(self) -> str:
        return self.readiness.hierarchy_key

    def to_dict(self) -> dict[str, Any]:
        return {
            "result_type": self.result_type,
            "version": self.version,
            "schema_version": self.schema_version,
            "hierarchy_key": self.hierarchy_key,
            "handoff_status": self.handoff_status,
            "approved_for_human_delivery": (
                self.delivery_envelope.delivery_status
                == DELIVERY_APPROVAL_HANDOFF_STATUS
            ),
            "readiness": self.readiness.to_dict(),
            "delivery_approval": self.delivery_approval.to_dict(),
            "delivery_envelope": self.delivery_envelope.to_dict(),
            "boundaries": {
                "readiness_is_not_human_approval": True,
                "human_approval_is_not_pa003_envelope": True,
                "pa003_remains_delivery_envelope_authority": True,
                "approved_for_human_delivery_is_not_delivery": True,
                "approved_for_human_delivery_is_not_client_receipt": True,
                "approved_for_human_delivery_is_not_client_acceptance": True,
                "approved_for_human_delivery_is_not_customer_outcome": True,
            },
        }


class GovernanceRealPaidAssessmentDeliveryApprovalHandoffService:
    """
    Bind an explicit external human delivery decision to a verified
    PILOT-006 readiness result and delegate envelope authority to PA003.

    This service does not infer, manufacture, or auto-approve a human
    delivery decision. All required approval decisions must already be
    present in the supplied approval payload.

    This service does not deliver or send the report.
    """

    def handoff(
        self,
        *,
        readiness: RealPaidAssessmentDeliveryReadinessResult,
        approval_payload: dict[str, Any],
    ) -> RealPaidAssessmentDeliveryApprovalHandoffResult:
        self._validate_readiness(readiness)

        delivery_approval = self._build_delivery_approval(
            readiness=readiness,
            approval_payload=approval_payload,
        )

        envelope = (
            GovernancePaidAssessmentDeliveryEnvelopeService()
            .build_envelope(
                execution_result=readiness.execution_result,
                report_package=readiness.report_package,
                delivery_approval=delivery_approval,
            )
        )

        if (
            envelope.delivery_status
            != DELIVERY_APPROVAL_HANDOFF_STATUS
        ):
            raise RealPaidAssessmentDeliveryApprovalHandoffError(
                "PA003 did not produce approved_for_human_delivery"
            )

        if envelope.hierarchy_key != readiness.hierarchy_key:
            raise RealPaidAssessmentDeliveryApprovalHandoffError(
                "PA003 delivery envelope hierarchy does not match readiness"
            )

        if (
            envelope.report_id
            != readiness.execution_result.report_id
        ):
            raise RealPaidAssessmentDeliveryApprovalHandoffError(
                "PA003 delivery envelope report_id does not match readiness"
            )

        if (
            envelope.delivery_approval_hash
            != delivery_approval.approval_hash
        ):
            raise RealPaidAssessmentDeliveryApprovalHandoffError(
                "PA003 delivery envelope approval hash does not match "
                "validated human approval"
            )

        return RealPaidAssessmentDeliveryApprovalHandoffResult(
            readiness=readiness,
            delivery_approval=delivery_approval,
            delivery_envelope=envelope,
        )

    @staticmethod
    def _validate_readiness(
        readiness: RealPaidAssessmentDeliveryReadinessResult,
    ) -> None:
        if not isinstance(
            readiness,
            RealPaidAssessmentDeliveryReadinessResult,
        ):
            raise RealPaidAssessmentDeliveryApprovalHandoffError(
                "readiness must be a "
                "RealPaidAssessmentDeliveryReadinessResult"
            )

        if (
            readiness.delivery_readiness_status
            != READY_FOR_DELIVERY_APPROVAL_REVIEW
        ):
            raise RealPaidAssessmentDeliveryApprovalHandoffError(
                "assessment is not ready for delivery approval review"
            )

        if readiness.repository_chain_valid is not True:
            raise RealPaidAssessmentDeliveryApprovalHandoffError(
                "readiness repository chain is not valid"
            )

    def _build_delivery_approval(
        self,
        *,
        readiness: RealPaidAssessmentDeliveryReadinessResult,
        approval_payload: dict[str, Any],
    ) -> PaidAssessmentDeliveryApproval:
        if not isinstance(approval_payload, dict):
            raise RealPaidAssessmentDeliveryApprovalHandoffError(
                "approval_payload must be an object"
            )

        execution_result = readiness.execution_result

        self._require_exact_identity(
            approval_payload=approval_payload,
            field_name="tenant_id",
            expected=execution_result.tenant_id,
        )
        self._require_exact_identity(
            approval_payload=approval_payload,
            field_name="client_id",
            expected=execution_result.client_id,
        )
        self._require_exact_identity(
            approval_payload=approval_payload,
            field_name="engagement_id",
            expected=execution_result.engagement_id,
        )
        self._require_exact_identity(
            approval_payload=approval_payload,
            field_name="assessment_id",
            expected=execution_result.assessment_id,
        )
        self._require_exact_identity(
            approval_payload=approval_payload,
            field_name="report_id",
            expected=execution_result.report_id,
        )

        # Do not default any approval decision to True.
        # Absence, False, null, or any non-boolean value must fail closed.
        for field_name in (
            "scope_approved",
            "evidence_boundary_approved",
            "buyer_language_approved",
            "delivery_approved",
        ):
            if approval_payload.get(field_name) is not True:
                raise RealPaidAssessmentDeliveryApprovalHandoffError(
                    f"{field_name} must be explicitly true"
                )

        approval_id = self._require_text(
            approval_payload.get("approval_id"),
            "approval_id",
        )
        approved_by = self._require_text(
            approval_payload.get("approved_by"),
            "approved_by",
        )
        approved_at = self._require_text(
            approval_payload.get("approved_at"),
            "approved_at",
        )

        # The existing PA003 type remains authoritative for ISO timestamp
        # validation, complete approval validation, and approval_hash
        # derivation.
        return PaidAssessmentDeliveryApproval(
            approval_id=approval_id,
            tenant_id=execution_result.tenant_id,
            client_id=execution_result.client_id,
            engagement_id=execution_result.engagement_id,
            assessment_id=execution_result.assessment_id,
            report_id=execution_result.report_id,
            approved_by=approved_by,
            approved_at=approved_at,
            scope_approved=True,
            evidence_boundary_approved=True,
            buyer_language_approved=True,
            delivery_approved=True,
        )

    @staticmethod
    def _require_exact_identity(
        *,
        approval_payload: dict[str, Any],
        field_name: str,
        expected: str,
    ) -> None:
        actual = approval_payload.get(field_name)

        if not isinstance(actual, str) or not actual.strip():
            raise RealPaidAssessmentDeliveryApprovalHandoffError(
                f"{field_name} must be a non-empty string"
            )

        if actual.strip() != expected:
            raise RealPaidAssessmentDeliveryApprovalHandoffError(
                f"{field_name} does not match verified readiness"
            )

    @staticmethod
    def _require_text(
        value: Any,
        field_name: str,
    ) -> str:
        if not isinstance(value, str) or not value.strip():
            raise RealPaidAssessmentDeliveryApprovalHandoffError(
                f"{field_name} must be a non-empty string"
            )

        return value.strip()


SERVICE_TYPE = (
    GovernanceRealPaidAssessmentDeliveryApprovalHandoffService
)