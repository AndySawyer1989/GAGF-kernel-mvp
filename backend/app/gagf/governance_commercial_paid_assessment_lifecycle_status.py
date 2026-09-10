from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from backend.app.gagf.governance_assessment_isolation import (
    CommercialHierarchyContext,
)
from backend.app.gagf.governance_assessment_repository import (
    GovernanceAssessmentRepository,
)
from backend.app.gagf.governance_commercial_paid_assessment_execution import (
    GovernanceCommercialPaidAssessmentExecutionService,
)
from backend.app.gagf.governance_paid_assessment_lifecycle_query import (
    GovernancePaidAssessmentLifecycleQueryService,
    LIFECYCLE_STAGE_NOT_STARTED,
    NEXT_STEP_RECORD_DELIVERY,
    PaidAssessmentLifecycleQueryError,
)


COMMERCIAL_PAID_ASSESSMENT_LIFECYCLE_STATUS_ID = (
    "governance-commercial-paid-assessment-lifecycle-status"
)
COMMERCIAL_PAID_ASSESSMENT_LIFECYCLE_STATUS_VERSION = "0.1.0"
COMMERCIAL_PAID_ASSESSMENT_LIFECYCLE_STATUS_SCHEMA_VERSION = "1.0.0"


class CommercialPaidAssessmentLifecycleStatusError(ValueError):
    """Raised when commercial lifecycle status cannot be projected safely."""


@dataclass(frozen=True, slots=True)
class CommercialPaidAssessmentLifecycleStatus:
    tenant_id: str
    client_id: str
    engagement_id: str
    assessment_id: str
    current_stage: str
    pending_next_step: str
    delivery_recorded: bool
    receipt_acknowledged: bool
    client_response_recorded: bool
    report_id: str | None
    findings_disposition: str | None
    recommendations_disposition: str | None
    lifecycle_artifact_count: int
    repository_chain_valid: bool
    status_type: str = (
        COMMERCIAL_PAID_ASSESSMENT_LIFECYCLE_STATUS_ID
    )
    version: str = (
        COMMERCIAL_PAID_ASSESSMENT_LIFECYCLE_STATUS_VERSION
    )
    schema_version: str = (
        COMMERCIAL_PAID_ASSESSMENT_LIFECYCLE_STATUS_SCHEMA_VERSION
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
            "status_type": self.status_type,
            "version": self.version,
            "schema_version": self.schema_version,
            "tenant_id": self.tenant_id,
            "client_id": self.client_id,
            "engagement_id": self.engagement_id,
            "assessment_id": self.assessment_id,
            "hierarchy_key": self.hierarchy_key,
            "current_stage": self.current_stage,
            "pending_next_step": self.pending_next_step,
            "delivery_recorded": self.delivery_recorded,
            "receipt_acknowledged": self.receipt_acknowledged,
            "client_response_recorded": (
                self.client_response_recorded
            ),
            "report_id": self.report_id,
            "findings_disposition": self.findings_disposition,
            "recommendations_disposition": (
                self.recommendations_disposition
            ),
            "lifecycle_artifact_count": (
                self.lifecycle_artifact_count
            ),
            "repository_chain_valid": (
                self.repository_chain_valid
            ),
            "boundaries": {
                "lifecycle_status_is_read_only_projection": True,
                "delivery_is_not_receipt": True,
                "receipt_is_not_response": True,
                "response_is_not_closeout": True,
                "response_is_not_intervention_authority": True,
                "repository_integrity_is_not_lifecycle_correctness": True,
            },
        }


class GovernanceCommercialPaidAssessmentLifecycleStatusService:
    """
    Commercial read-only adapter over the authoritative PA012 lifecycle query.

    The browser never selects a repository path. The governed PA015
    execution service derives the hierarchy database server-side.

    This service creates no delivery, acknowledgment, response, closeout,
    intervention, execution, ROI, or outcome authority.
    """

    def __init__(
        self,
        *,
        execution_service: GovernanceCommercialPaidAssessmentExecutionService,
    ) -> None:
        if not isinstance(
            execution_service,
            GovernanceCommercialPaidAssessmentExecutionService,
        ):
            raise CommercialPaidAssessmentLifecycleStatusError(
                "execution_service must be a "
                "GovernanceCommercialPaidAssessmentExecutionService"
            )

        self._execution_service = execution_service

    def get_status(
        self,
        *,
        tenant_id: str,
        client_id: str,
        engagement_id: str,
        assessment_id: str,
    ) -> CommercialPaidAssessmentLifecycleStatus:
        hierarchy = self._validate_hierarchy(
            tenant_id=tenant_id,
            client_id=client_id,
            engagement_id=engagement_id,
            assessment_id=assessment_id,
        )

        database_path = (
            self._execution_service.database_path_for_hierarchy(
                tenant_id=hierarchy[0],
                client_id=hierarchy[1],
                engagement_id=hierarchy[2],
                assessment_id=hierarchy[3],
            )
        )

        database_path = Path(database_path)

        if not database_path.exists():
            return CommercialPaidAssessmentLifecycleStatus(
                tenant_id=hierarchy[0],
                client_id=hierarchy[1],
                engagement_id=hierarchy[2],
                assessment_id=hierarchy[3],
                current_stage=LIFECYCLE_STAGE_NOT_STARTED,
                pending_next_step=NEXT_STEP_RECORD_DELIVERY,
                delivery_recorded=False,
                receipt_acknowledged=False,
                client_response_recorded=False,
                report_id=None,
                findings_disposition=None,
                recommendations_disposition=None,
                lifecycle_artifact_count=0,
                repository_chain_valid=True,
            )

        if not database_path.is_file():
            raise CommercialPaidAssessmentLifecycleStatusError(
                "paid assessment hierarchy database path is not a file"
            )

        repository = GovernanceAssessmentRepository(
            database_path
        )

        context = CommercialHierarchyContext(
            tenant_id=hierarchy[0],
            client_id=hierarchy[1],
            engagement_id=hierarchy[2],
            assessment_id=hierarchy[3],
        )

        try:
            state = (
                GovernancePaidAssessmentLifecycleQueryService(
                    repository=repository
                ).get_state(
                    context=context
                )
            )
        except PaidAssessmentLifecycleQueryError as exc:
            raise CommercialPaidAssessmentLifecycleStatusError(
                str(exc)
            ) from exc

        if state.repository_chain_valid is not True:
            raise CommercialPaidAssessmentLifecycleStatusError(
                "paid assessment repository chain is invalid"
            )

        return CommercialPaidAssessmentLifecycleStatus(
            tenant_id=state.tenant_id,
            client_id=state.client_id,
            engagement_id=state.engagement_id,
            assessment_id=state.assessment_id,
            current_stage=state.current_stage,
            pending_next_step=state.pending_next_step,
            delivery_recorded=state.delivery_recorded,
            receipt_acknowledged=state.receipt_acknowledged,
            client_response_recorded=(
                state.client_response_recorded
            ),
            report_id=state.report_id,
            findings_disposition=state.findings_disposition,
            recommendations_disposition=(
                state.recommendations_disposition
            ),
            lifecycle_artifact_count=(
                state.lifecycle_artifact_count
            ),
            repository_chain_valid=True,
        )

    def _validate_hierarchy(
        self,
        *,
        tenant_id: str,
        client_id: str,
        engagement_id: str,
        assessment_id: str,
    ) -> tuple[str, str, str, str]:
        return (
            self._require_text(tenant_id, "tenant_id"),
            self._require_text(client_id, "client_id"),
            self._require_text(
                engagement_id,
                "engagement_id",
            ),
            self._require_text(
                assessment_id,
                "assessment_id",
            ),
        )

    def _require_text(
        self,
        value: Any,
        field_name: str,
    ) -> str:
        if not isinstance(value, str):
            raise CommercialPaidAssessmentLifecycleStatusError(
                f"{field_name} must be a string"
            )

        normalized = value.strip()

        if not normalized:
            raise CommercialPaidAssessmentLifecycleStatusError(
                f"{field_name} must not be empty"
            )

        return normalized
