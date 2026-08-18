from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from backend.app.gagf.governance_assessment_application import (
    AssessmentApplicationResult,
    AssessmentExecutionRequest,
    GovernanceAssessmentApplicationService,
)
from backend.app.gagf.governance_paid_assessment_execution_handoff import (
    PaidAssessmentExecutionHandoff,
    PaidAssessmentExecutionHandoffStatus,
    canonical_json,
    sha256_text,
)


PAID_ASSESSMENT_EXECUTION_COORDINATOR_ID = (
    "governance-paid-assessment-execution-coordinator"
)
PAID_ASSESSMENT_EXECUTION_COORDINATOR_VERSION = "0.1.0"
PAID_ASSESSMENT_EXECUTION_COORDINATOR_SCHEMA_VERSION = "1.0.0"


class PaidAssessmentExecutionCoordinatorError(RuntimeError):
    """Raised when governed paid-assessment execution cannot proceed."""


@dataclass(frozen=True, slots=True)
class PaidAssessmentExecutionResult:
    tenant_id: str
    client_id: str
    engagement_id: str
    assessment_id: str
    handoff_hash: str
    assessment_execution_request_hash: str
    application_request_hash: str
    application_hash: str
    demonstration_hash: str
    persistence_hash: str
    report_id: str
    artifact_count: int
    application_completed: bool
    execution_result_hash: str
    result_type: str = PAID_ASSESSMENT_EXECUTION_COORDINATOR_ID
    version: str = PAID_ASSESSMENT_EXECUTION_COORDINATOR_VERSION
    schema_version: str = (
        PAID_ASSESSMENT_EXECUTION_COORDINATOR_SCHEMA_VERSION
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
            "result_type": self.result_type,
            "version": self.version,
            "schema_version": self.schema_version,
            "tenant_id": self.tenant_id,
            "client_id": self.client_id,
            "engagement_id": self.engagement_id,
            "assessment_id": self.assessment_id,
            "hierarchy_key": self.hierarchy_key,
            "handoff_hash": self.handoff_hash,
            "assessment_execution_request_hash": (
                self.assessment_execution_request_hash
            ),
            "application_request_hash": (
                self.application_request_hash
            ),
            "application_hash": self.application_hash,
            "demonstration_hash": self.demonstration_hash,
            "persistence_hash": self.persistence_hash,
            "report_id": self.report_id,
            "artifact_count": self.artifact_count,
            "application_completed": self.application_completed,
            "execution_result_hash": self.execution_result_hash,
        }


class GovernancePaidAssessmentExecutionCoordinator:
    """
    Revalidates a READY paid-assessment execution handoff and invokes the
    existing Governance Assessment application.

    Application completion means only that the governed assessment
    application completed its demonstration and persistence contract.
    It is not customer-outcome verification, causal proof, intervention
    success, or authorization for future action.
    """

    def __init__(
        self,
        *,
        application_service: GovernanceAssessmentApplicationService,
    ) -> None:
        self._application_service = application_service

    def execute(
        self,
        *,
        handoff: PaidAssessmentExecutionHandoff,
        request: AssessmentExecutionRequest,
    ) -> PaidAssessmentExecutionResult:
        self._validate_handoff(handoff)

        request_payload = request.to_dict()

        if not isinstance(request_payload, dict):
            raise PaidAssessmentExecutionCoordinatorError(
                "assessment execution request to_dict() must return a dict"
            )

        request_hash = sha256_text(
            canonical_json(request_payload)
        )

        if (
            request_hash
            != handoff.assessment_execution_request_hash
        ):
            raise PaidAssessmentExecutionCoordinatorError(
                "assessment execution request hash does not match handoff"
            )

        request_hierarchy = getattr(
            request.context,
            "hierarchy_key",
            None,
        )

        if request_hierarchy != handoff.hierarchy_key:
            raise PaidAssessmentExecutionCoordinatorError(
                "assessment execution request hierarchy does not match "
                "handoff"
            )

        application_result = self._application_service.execute(
            request=request
        )

        self._validate_application_result(
            handoff=handoff,
            request_hash=request_hash,
            application_result=application_result,
        )

        payload = {
            "result_type": (
                PAID_ASSESSMENT_EXECUTION_COORDINATOR_ID
            ),
            "version": (
                PAID_ASSESSMENT_EXECUTION_COORDINATOR_VERSION
            ),
            "schema_version": (
                PAID_ASSESSMENT_EXECUTION_COORDINATOR_SCHEMA_VERSION
            ),
            "tenant_id": handoff.tenant_id,
            "client_id": handoff.client_id,
            "engagement_id": handoff.engagement_id,
            "assessment_id": handoff.assessment_id,
            "handoff_hash": handoff.handoff_hash,
            "assessment_execution_request_hash": request_hash,
            "application_request_hash": (
                application_result.request_hash
            ),
            "application_hash": application_result.application_hash,
            "demonstration_hash": (
                application_result.demonstration.demonstration_hash
            ),
            "persistence_hash": (
                application_result.persistence.persistence_hash
            ),
            "report_id": (
                application_result.demonstration.report_package.report_id
            ),
            "artifact_count": (
                application_result.persistence.artifact_count
            ),
            "application_completed": application_result.completed,
        }

        return PaidAssessmentExecutionResult(
            tenant_id=handoff.tenant_id,
            client_id=handoff.client_id,
            engagement_id=handoff.engagement_id,
            assessment_id=handoff.assessment_id,
            handoff_hash=handoff.handoff_hash,
            assessment_execution_request_hash=request_hash,
            application_request_hash=(
                application_result.request_hash
            ),
            application_hash=application_result.application_hash,
            demonstration_hash=(
                application_result.demonstration.demonstration_hash
            ),
            persistence_hash=(
                application_result.persistence.persistence_hash
            ),
            report_id=(
                application_result.demonstration.report_package.report_id
            ),
            artifact_count=(
                application_result.persistence.artifact_count
            ),
            application_completed=application_result.completed,
            execution_result_hash=sha256_text(
                canonical_json(payload)
            ),
        )

    def _validate_handoff(
        self,
        handoff: PaidAssessmentExecutionHandoff,
    ) -> None:
        if not isinstance(
            handoff,
            PaidAssessmentExecutionHandoff,
        ):
            raise PaidAssessmentExecutionCoordinatorError(
                "handoff must be a PaidAssessmentExecutionHandoff"
            )

        if (
            handoff.status
            is not PaidAssessmentExecutionHandoffStatus.READY
        ):
            raise PaidAssessmentExecutionCoordinatorError(
                "handoff must be ready_for_assessment_execution"
            )

        if not handoff.handoff_hash:
            raise PaidAssessmentExecutionCoordinatorError(
                "handoff_hash must not be empty"
            )

        if not handoff.assessment_execution_request_hash:
            raise PaidAssessmentExecutionCoordinatorError(
                "assessment_execution_request_hash must not be empty"
            )

    def _validate_application_result(
        self,
        *,
        handoff: PaidAssessmentExecutionHandoff,
        request_hash: str,
        application_result: AssessmentApplicationResult,
    ) -> None:
        if (
            application_result.hierarchy_key
            != handoff.hierarchy_key
        ):
            raise PaidAssessmentExecutionCoordinatorError(
                "application result hierarchy does not match handoff"
            )

        if application_result.request_hash != request_hash:
            raise PaidAssessmentExecutionCoordinatorError(
                "application result request hash does not match "
                "authorized request"
            )

        if application_result.completed is not True:
            raise PaidAssessmentExecutionCoordinatorError(
                "governance assessment application did not complete"
            )

        if (
            application_result.persistence.demonstration_hash
            != application_result.demonstration.demonstration_hash
        ):
            raise PaidAssessmentExecutionCoordinatorError(
                "application persistence does not reference the "
                "executed demonstration"
            )


def build_paid_assessment_execution_coordinator(
    *,
    application_service: GovernanceAssessmentApplicationService,
) -> GovernancePaidAssessmentExecutionCoordinator:
    return GovernancePaidAssessmentExecutionCoordinator(
        application_service=application_service
    )
