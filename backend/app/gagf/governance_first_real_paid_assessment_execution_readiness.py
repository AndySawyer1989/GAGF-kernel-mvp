from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from backend.app.gagf.governance_assessment_application import (
    AssessmentExecutionRequest,
)
from backend.app.gagf.governance_paid_assessment_execution_handoff import (
    PaidAssessmentWorkAuthorization,
)
from backend.app.gagf.governance_real_paid_assessment_authorization_bridge import (
    RealPaidAssessmentAuthorizationBridge,
)
from backend.app.gagf.governance_real_paid_assessment_execution_evidence import (
    RealPaidAssessmentExecutionEvidenceBinding,
)
from backend.app.gagf.governance_real_paid_assessment_preflight import (
    PREFLIGHT_STATUS_READY,
    GovernanceRealPaidAssessmentPreflightService,
    RealPaidAssessmentPreflightResult,
)
from backend.app.gagf.governance_real_paid_assessment_readiness import (
    READINESS_STATUS_READY,
    GovernanceRealPaidAssessmentReadinessService,
    RealPaidAssessmentIntake,
    RealPaidAssessmentReadinessResult,
)


FIRST_REAL_EXECUTION_READINESS_ID = (
    "governance-first-real-paid-assessment-execution-readiness"
)
FIRST_REAL_EXECUTION_READINESS_VERSION = "0.1.0"
FIRST_REAL_EXECUTION_READINESS_SCHEMA_VERSION = "1.0.0"

FIRST_REAL_EXECUTION_STATUS_READY = (
    "ready_for_controlled_execution"
)
FIRST_REAL_EXECUTION_STATUS_BLOCKED = "blocked"

ACTION_BEGIN_CONTROLLED_EXECUTION = (
    "begin_controlled_real_paid_assessment_execution"
)
ACTION_RESOLVE_EXECUTION_READINESS_BLOCKERS = (
    "resolve_execution_readiness_blockers"
)


class FirstRealPaidAssessmentExecutionReadinessError(ValueError):
    """Raised when first-run readiness inputs are structurally invalid."""


@dataclass(frozen=True, slots=True)
class FirstRealPaidAssessmentExecutionReadinessResult:
    tenant_id: str
    client_id: str
    engagement_id: str
    assessment_id: str

    database_path: str

    status: str
    ready_for_controlled_execution: bool
    required_operator_action: str
    blockers: tuple[str, ...]

    intake_readiness: RealPaidAssessmentReadinessResult
    execution_preflight: RealPaidAssessmentPreflightResult | None

    readiness_type: str = FIRST_REAL_EXECUTION_READINESS_ID
    version: str = FIRST_REAL_EXECUTION_READINESS_VERSION
    schema_version: str = (
        FIRST_REAL_EXECUTION_READINESS_SCHEMA_VERSION
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
            "readiness_type": self.readiness_type,
            "version": self.version,
            "schema_version": self.schema_version,
            "tenant_id": self.tenant_id,
            "client_id": self.client_id,
            "engagement_id": self.engagement_id,
            "assessment_id": self.assessment_id,
            "hierarchy_key": self.hierarchy_key,
            "database_path": self.database_path,
            "status": self.status,
            "ready_for_controlled_execution": (
                self.ready_for_controlled_execution
            ),
            "required_operator_action": (
                self.required_operator_action
            ),
            "blockers": self.blockers,
            "intake_readiness": self.intake_readiness.to_dict(),
            "execution_preflight": (
                None
                if self.execution_preflight is None
                else self.execution_preflight.to_dict()
            ),
            "boundaries": {
                "pilot012_is_read_only": True,
                "readiness_is_not_paid_work_authorization": True,
                "readiness_is_not_execution_authority": True,
                "preflight_is_not_execution": True,
                "ready_does_not_mean_executed": True,
                "ready_does_not_create_delivery_approval": True,
                "ready_does_not_create_client_receipt": True,
                "ready_does_not_create_client_acceptance": True,
                "ready_does_not_create_intervention_authorization": True,
                "ready_does_not_verify_remediation_success": True,
                "ready_does_not_verify_roi": True,
                "ready_does_not_verify_customer_outcome": True,
                "existing_database_requires_governed_recovery": True,
            },
        }


class GovernanceFirstRealPaidAssessmentExecutionReadinessService:
    """
    Consolidate existing governed intake readiness and execution preflight.

    This service creates no paid-work authorization, execution authority,
    execution event, database, delivery event, intervention authority, or
    customer-outcome claim.

    Existing services remain authoritative:
    - Real paid-assessment readiness owns intake readiness.
    - Paid-work authorization remains external and pre-existing.
    - Authorization bridge remains external and pre-existing.
    - Execution-evidence binding remains external and pre-existing.
    - Real paid-assessment preflight owns execution preflight.
    - PA015 / governed recovery remains execution authority.
    """

    def __init__(self) -> None:
        self._readiness = (
            GovernanceRealPaidAssessmentReadinessService()
        )
        self._preflight = (
            GovernanceRealPaidAssessmentPreflightService()
        )

    def evaluate(
        self,
        *,
        database_path: str | Path,
        intake: RealPaidAssessmentIntake,
        authorization_bridge: RealPaidAssessmentAuthorizationBridge,
        evidence_binding: RealPaidAssessmentExecutionEvidenceBinding,
        contract_execution_event: dict[str, Any],
        paid_work_authorization: PaidAssessmentWorkAuthorization,
        request: AssessmentExecutionRequest,
    ) -> FirstRealPaidAssessmentExecutionReadinessResult:
        if not isinstance(intake, RealPaidAssessmentIntake):
            raise FirstRealPaidAssessmentExecutionReadinessError(
                "intake must be a RealPaidAssessmentIntake"
            )

        if not isinstance(
            authorization_bridge,
            RealPaidAssessmentAuthorizationBridge,
        ):
            raise FirstRealPaidAssessmentExecutionReadinessError(
                "authorization_bridge must be a "
                "RealPaidAssessmentAuthorizationBridge"
            )

        if not isinstance(
            evidence_binding,
            RealPaidAssessmentExecutionEvidenceBinding,
        ):
            raise FirstRealPaidAssessmentExecutionReadinessError(
                "evidence_binding must be a "
                "RealPaidAssessmentExecutionEvidenceBinding"
            )

        if not isinstance(
            paid_work_authorization,
            PaidAssessmentWorkAuthorization,
        ):
            raise FirstRealPaidAssessmentExecutionReadinessError(
                "paid_work_authorization must be a "
                "PaidAssessmentWorkAuthorization"
            )

        if not isinstance(request, AssessmentExecutionRequest):
            raise FirstRealPaidAssessmentExecutionReadinessError(
                "request must be an AssessmentExecutionRequest"
            )

        if not isinstance(contract_execution_event, dict):
            raise FirstRealPaidAssessmentExecutionReadinessError(
                "contract_execution_event must be a dict"
            )

        path = Path(database_path)

        if not str(path).strip():
            raise FirstRealPaidAssessmentExecutionReadinessError(
                "database_path is required"
            )

        intake_readiness = self._readiness.evaluate(
            intake=intake
        )

        if (
            intake_readiness.readiness_status
            != READINESS_STATUS_READY
            or intake_readiness.ready_for_paid_work_authorization
            is not True
        ):
            blockers = tuple(
                f"intake:{item}"
                for item in intake_readiness.blockers
            )

            if not blockers:
                blockers = (
                    "intake:not_ready_for_paid_work_authorization",
                )

            return self._build_result(
                database_path=path,
                intake=intake,
                intake_readiness=intake_readiness,
                execution_preflight=None,
                blockers=blockers,
            )

        execution_preflight = self._preflight.evaluate(
            database_path=path,
            intake=intake,
            authorization_bridge=authorization_bridge,
            evidence_binding=evidence_binding,
            contract_execution_event=contract_execution_event,
            paid_work_authorization=paid_work_authorization,
            request=request,
        )

        blockers = tuple(
            f"preflight:{item}"
            for item in execution_preflight.blockers
        )

        return self._build_result(
            database_path=path,
            intake=intake,
            intake_readiness=intake_readiness,
            execution_preflight=execution_preflight,
            blockers=blockers,
        )

    def _build_result(
        self,
        *,
        database_path: Path,
        intake: RealPaidAssessmentIntake,
        intake_readiness: RealPaidAssessmentReadinessResult,
        execution_preflight: (
            RealPaidAssessmentPreflightResult | None
        ),
        blockers: tuple[str, ...],
    ) -> FirstRealPaidAssessmentExecutionReadinessResult:
        preflight_ready = (
            execution_preflight is not None
            and execution_preflight.status
            == PREFLIGHT_STATUS_READY
            and execution_preflight.ready_for_operator_execution
            is True
        )

        ready = (
            intake_readiness.readiness_status
            == READINESS_STATUS_READY
            and intake_readiness.ready_for_paid_work_authorization
            is True
            and preflight_ready
            and len(blockers) == 0
        )

        return FirstRealPaidAssessmentExecutionReadinessResult(
            tenant_id=intake.tenant_id,
            client_id=intake.client_id,
            engagement_id=intake.engagement_id,
            assessment_id=intake.assessment_id,
            database_path=str(database_path),
            status=(
                FIRST_REAL_EXECUTION_STATUS_READY
                if ready
                else FIRST_REAL_EXECUTION_STATUS_BLOCKED
            ),
            ready_for_controlled_execution=ready,
            required_operator_action=(
                ACTION_BEGIN_CONTROLLED_EXECUTION
                if ready
                else ACTION_RESOLVE_EXECUTION_READINESS_BLOCKERS
            ),
            blockers=blockers,
            intake_readiness=intake_readiness,
            execution_preflight=execution_preflight,
        )


SERVICE_TYPE = (
    GovernanceFirstRealPaidAssessmentExecutionReadinessService
)