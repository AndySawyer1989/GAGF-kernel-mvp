from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from backend.app.gagf.governance_assessment_report_package import (
    ClientReadyReportPackage,
)
from backend.app.gagf.governance_paid_assessment_execution_coordinator import (
    PaidAssessmentExecutionResult,
)
from backend.app.gagf.governance_paid_assessment_execution_handoff import (
    canonical_json,
    sha256_text,
)


PAID_ASSESSMENT_DELIVERY_ENVELOPE_ID = (
    "governance-paid-assessment-delivery-envelope"
)
PAID_ASSESSMENT_DELIVERY_ENVELOPE_VERSION = "0.1.0"
PAID_ASSESSMENT_DELIVERY_ENVELOPE_SCHEMA_VERSION = "1.0.0"


class PaidAssessmentDeliveryEnvelopeError(ValueError):
    """Raised when completed-assessment delivery cannot be authorized."""


def require_text(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise PaidAssessmentDeliveryEnvelopeError(
            f"{field_name} must be non-empty text"
        )
    return value.strip()


def require_hash(value: str, field_name: str) -> str:
    normalized = require_text(value, field_name)

    if len(normalized) != 64:
        raise PaidAssessmentDeliveryEnvelopeError(
            f"{field_name} must be a SHA-256 hex digest"
        )

    try:
        int(normalized, 16)
    except ValueError as exc:
        raise PaidAssessmentDeliveryEnvelopeError(
            f"{field_name} must be a SHA-256 hex digest"
        ) from exc

    return normalized


@dataclass(frozen=True, slots=True)
class PaidAssessmentDeliveryApproval:
    approval_id: str
    tenant_id: str
    client_id: str
    engagement_id: str
    assessment_id: str
    report_id: str
    approved_by: str
    approved_at: str
    scope_approved: bool
    evidence_boundary_approved: bool
    buyer_language_approved: bool
    delivery_approved: bool

    def __post_init__(self) -> None:
        for field_name in (
            "approval_id",
            "tenant_id",
            "client_id",
            "engagement_id",
            "assessment_id",
            "report_id",
            "approved_by",
            "approved_at",
        ):
            object.__setattr__(
                self,
                field_name,
                require_text(
                    getattr(self, field_name),
                    field_name,
                ),
            )

        try:
            datetime.fromisoformat(
                self.approved_at.replace("Z", "+00:00")
            )
        except ValueError as exc:
            raise PaidAssessmentDeliveryEnvelopeError(
                "approved_at must be ISO-8601"
            ) from exc

        required_approvals = {
            "scope_approved": self.scope_approved,
            "evidence_boundary_approved": (
                self.evidence_boundary_approved
            ),
            "buyer_language_approved": (
                self.buyer_language_approved
            ),
            "delivery_approved": self.delivery_approved,
        }

        failed = [
            name
            for name, approved in required_approvals.items()
            if approved is not True
        ]

        if failed:
            raise PaidAssessmentDeliveryEnvelopeError(
                "delivery approval is incomplete: "
                + ", ".join(sorted(failed))
            )

    @property
    def approval_hash(self) -> str:
        return sha256_text(
            canonical_json(
                {
                    "approval_id": self.approval_id,
                    "tenant_id": self.tenant_id,
                    "client_id": self.client_id,
                    "engagement_id": self.engagement_id,
                    "assessment_id": self.assessment_id,
                    "report_id": self.report_id,
                    "approved_by": self.approved_by,
                    "approved_at": self.approved_at,
                    "scope_approved": self.scope_approved,
                    "evidence_boundary_approved": (
                        self.evidence_boundary_approved
                    ),
                    "buyer_language_approved": (
                        self.buyer_language_approved
                    ),
                    "delivery_approved": self.delivery_approved,
                }
            )
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "approval_id": self.approval_id,
            "tenant_id": self.tenant_id,
            "client_id": self.client_id,
            "engagement_id": self.engagement_id,
            "assessment_id": self.assessment_id,
            "report_id": self.report_id,
            "approved_by": self.approved_by,
            "approved_at": self.approved_at,
            "scope_approved": self.scope_approved,
            "evidence_boundary_approved": (
                self.evidence_boundary_approved
            ),
            "buyer_language_approved": (
                self.buyer_language_approved
            ),
            "delivery_approved": self.delivery_approved,
            "approval_hash": self.approval_hash,
        }


@dataclass(frozen=True, slots=True)
class GovernedPaidAssessmentDeliveryEnvelope:
    tenant_id: str
    client_id: str
    engagement_id: str
    assessment_id: str
    report_id: str
    execution_result_hash: str
    application_hash: str
    report_package_hash: str
    report_markdown_hash: str
    delivery_approval_id: str
    delivery_approval_hash: str
    delivery_status: str
    envelope_hash: str
    envelope_type: str = PAID_ASSESSMENT_DELIVERY_ENVELOPE_ID
    version: str = PAID_ASSESSMENT_DELIVERY_ENVELOPE_VERSION
    schema_version: str = (
        PAID_ASSESSMENT_DELIVERY_ENVELOPE_SCHEMA_VERSION
    )

    @property
    def hierarchy_key(self) -> str:
        return "/".join(
            (
                self.tenant_id,
                self.client_id,
                self.engagement_id,
                self.assessment_id,
            )
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "envelope_type": self.envelope_type,
            "version": self.version,
            "schema_version": self.schema_version,
            "tenant_id": self.tenant_id,
            "client_id": self.client_id,
            "engagement_id": self.engagement_id,
            "assessment_id": self.assessment_id,
            "hierarchy_key": self.hierarchy_key,
            "report_id": self.report_id,
            "execution_result_hash": self.execution_result_hash,
            "application_hash": self.application_hash,
            "report_package_hash": self.report_package_hash,
            "report_markdown_hash": self.report_markdown_hash,
            "delivery_approval_id": self.delivery_approval_id,
            "delivery_approval_hash": self.delivery_approval_hash,
            "delivery_status": self.delivery_status,
            "envelope_hash": self.envelope_hash,
        }


class GovernancePaidAssessmentDeliveryEnvelopeService:
    """
    Binds a completed governed paid-assessment execution to its existing
    client-ready report package and a separate human delivery approval.

    This service does not send or deliver the report. It does not record
    buyer receipt, buyer acceptance, intervention authorization, causal
    success, ROI, or customer-outcome verification.
    """

    DELIVERY_STATUS = "approved_for_human_delivery"

    def build_envelope(
        self,
        *,
        execution_result: PaidAssessmentExecutionResult,
        report_package: ClientReadyReportPackage,
        delivery_approval: PaidAssessmentDeliveryApproval,
    ) -> GovernedPaidAssessmentDeliveryEnvelope:
        self._validate_execution_result(execution_result)
        self._validate_report_package(
            execution_result=execution_result,
            report_package=report_package,
        )
        self._validate_delivery_approval(
            execution_result=execution_result,
            report_package=report_package,
            delivery_approval=delivery_approval,
        )

        manifest = report_package.manifest

        payload = {
            "envelope_type": PAID_ASSESSMENT_DELIVERY_ENVELOPE_ID,
            "version": PAID_ASSESSMENT_DELIVERY_ENVELOPE_VERSION,
            "schema_version": (
                PAID_ASSESSMENT_DELIVERY_ENVELOPE_SCHEMA_VERSION
            ),
            "tenant_id": execution_result.tenant_id,
            "client_id": execution_result.client_id,
            "engagement_id": execution_result.engagement_id,
            "assessment_id": execution_result.assessment_id,
            "report_id": report_package.report_id,
            "execution_result_hash": (
                execution_result.execution_result_hash
            ),
            "application_hash": execution_result.application_hash,
            "report_package_hash": manifest.package_hash,
            "report_markdown_hash": manifest.markdown_hash,
            "delivery_approval_id": delivery_approval.approval_id,
            "delivery_approval_hash": delivery_approval.approval_hash,
            "delivery_status": self.DELIVERY_STATUS,
        }

        return GovernedPaidAssessmentDeliveryEnvelope(
            tenant_id=execution_result.tenant_id,
            client_id=execution_result.client_id,
            engagement_id=execution_result.engagement_id,
            assessment_id=execution_result.assessment_id,
            report_id=report_package.report_id,
            execution_result_hash=(
                execution_result.execution_result_hash
            ),
            application_hash=execution_result.application_hash,
            report_package_hash=manifest.package_hash,
            report_markdown_hash=manifest.markdown_hash,
            delivery_approval_id=delivery_approval.approval_id,
            delivery_approval_hash=delivery_approval.approval_hash,
            delivery_status=self.DELIVERY_STATUS,
            envelope_hash=sha256_text(
                canonical_json(payload)
            ),
        )

    def _validate_execution_result(
        self,
        execution_result: PaidAssessmentExecutionResult,
    ) -> None:
        if not isinstance(
            execution_result,
            PaidAssessmentExecutionResult,
        ):
            raise PaidAssessmentDeliveryEnvelopeError(
                "execution_result must be a PaidAssessmentExecutionResult"
            )

        if execution_result.application_completed is not True:
            raise PaidAssessmentDeliveryEnvelopeError(
                "paid assessment application must be completed "
                "before delivery approval"
            )

        require_hash(
            execution_result.execution_result_hash,
            "execution_result_hash",
        )
        require_hash(
            execution_result.application_hash,
            "application_hash",
        )

    def _validate_report_package(
        self,
        *,
        execution_result: PaidAssessmentExecutionResult,
        report_package: ClientReadyReportPackage,
    ) -> None:
        if not isinstance(
            report_package,
            ClientReadyReportPackage,
        ):
            raise PaidAssessmentDeliveryEnvelopeError(
                "report_package must be a ClientReadyReportPackage"
            )

        if (
            report_package.hierarchy_key
            != execution_result.hierarchy_key
        ):
            raise PaidAssessmentDeliveryEnvelopeError(
                "report package hierarchy does not match execution result"
            )

        if report_package.report_id != execution_result.report_id:
            raise PaidAssessmentDeliveryEnvelopeError(
                "report_id does not match executed assessment result"
            )

        manifest = report_package.manifest

        expected_identity = (
            execution_result.tenant_id,
            execution_result.client_id,
            execution_result.engagement_id,
            execution_result.assessment_id,
            report_package.report_id,
        )

        actual_identity = (
            manifest.tenant_id,
            manifest.client_id,
            manifest.engagement_id,
            manifest.assessment_id,
            manifest.report_id,
        )

        if actual_identity != expected_identity:
            raise PaidAssessmentDeliveryEnvelopeError(
                "report manifest identity does not match execution result"
            )

        require_hash(
            manifest.package_hash,
            "report_package.manifest.package_hash",
        )
        require_hash(
            manifest.markdown_hash,
            "report_package.manifest.markdown_hash",
        )

        actual_markdown_hash = sha256_text(
            report_package.markdown
        )

        if actual_markdown_hash != manifest.markdown_hash:
            raise PaidAssessmentDeliveryEnvelopeError(
                "report markdown does not match manifest markdown_hash"
            )

        projection_hash = manifest.source_commitments.get(
            "executive_projection_hash"
        )

        require_hash(
            projection_hash,
            (
                "report_package.manifest.source_commitments."
                "executive_projection_hash"
            ),
        )

    def _validate_delivery_approval(
        self,
        *,
        execution_result: PaidAssessmentExecutionResult,
        report_package: ClientReadyReportPackage,
        delivery_approval: PaidAssessmentDeliveryApproval,
    ) -> None:
        if not isinstance(
            delivery_approval,
            PaidAssessmentDeliveryApproval,
        ):
            raise PaidAssessmentDeliveryEnvelopeError(
                "delivery_approval must be a "
                "PaidAssessmentDeliveryApproval"
            )

        expected = (
            execution_result.tenant_id,
            execution_result.client_id,
            execution_result.engagement_id,
            execution_result.assessment_id,
            report_package.report_id,
        )

        actual = (
            delivery_approval.tenant_id,
            delivery_approval.client_id,
            delivery_approval.engagement_id,
            delivery_approval.assessment_id,
            delivery_approval.report_id,
        )

        if actual != expected:
            raise PaidAssessmentDeliveryEnvelopeError(
                "delivery approval identity does not match "
                "completed assessment report"
            )


SERVICE = GovernancePaidAssessmentDeliveryEnvelopeService()
