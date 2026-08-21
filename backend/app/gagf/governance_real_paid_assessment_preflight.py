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
    BRIDGE_STATUS_READY,
    RealPaidAssessmentAuthorizationBridge,
)
from backend.app.gagf.governance_real_paid_assessment_execution_evidence import (
    EXECUTION_EVIDENCE_STATUS_APPROVED,
    RealPaidAssessmentExecutionEvidenceBinding,
)
from backend.app.gagf.governance_real_paid_assessment_readiness import (
    RealPaidAssessmentIntake,
)


PREFLIGHT_STATUS_READY = "ready"
PREFLIGHT_STATUS_BLOCKED = "blocked"


class RealPaidAssessmentPreflightError(ValueError):
    """Raised when PILOT-004 preflight inputs are structurally invalid."""


@dataclass(frozen=True)
class RealPaidAssessmentPreflightResult:
    tenant_id: str
    client_id: str
    engagement_id: str
    assessment_id: str
    database_path: str
    status: str
    blockers: tuple[str, ...]
    database_exists: bool
    intake_storage_matches_database: bool
    hierarchy_consistent: bool
    authorization_affirmative: bool
    authorization_bridge_ready: bool
    evidence_binding_approved: bool
    contract_event_matches_authorization: bool

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

    @property
    def ready_for_operator_execution(self) -> bool:
        return self.status == PREFLIGHT_STATUS_READY

    def to_dict(self) -> dict[str, Any]:
        return {
            "tenant_id": self.tenant_id,
            "client_id": self.client_id,
            "engagement_id": self.engagement_id,
            "assessment_id": self.assessment_id,
            "hierarchy_key": self.hierarchy_key,
            "database_path": self.database_path,
            "status": self.status,
            "blockers": list(self.blockers),
            "database_exists": self.database_exists,
            "intake_storage_matches_database": (
                self.intake_storage_matches_database
            ),
            "hierarchy_consistent": self.hierarchy_consistent,
            "authorization_affirmative": (
                self.authorization_affirmative
            ),
            "authorization_bridge_ready": (
                self.authorization_bridge_ready
            ),
            "evidence_binding_approved": (
                self.evidence_binding_approved
            ),
            "contract_event_matches_authorization": (
                self.contract_event_matches_authorization
            ),
            "ready_for_operator_execution": (
                self.ready_for_operator_execution
            ),
            "boundaries": {
                "preflight_is_not_paid_work_authorization": True,
                "preflight_is_not_execution": True,
                "preflight_is_not_execution_authority": True,
                "preflight_is_not_recovery_authority": True,
                "ready_does_not_mean_executed": True,
            },
        }


class GovernanceRealPaidAssessmentPreflightService:
    """
    Deterministically evaluate whether an already-governed real
    paid-assessment input set is ready to be handed to the PA015
    operator execution command.

    This service never executes the assessment and never grants
    paid-work, execution, or recovery authority.
    """

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
    ) -> RealPaidAssessmentPreflightResult:
        if not isinstance(intake, RealPaidAssessmentIntake):
            raise RealPaidAssessmentPreflightError(
                "intake must be a RealPaidAssessmentIntake"
            )

        if not isinstance(
            authorization_bridge,
            RealPaidAssessmentAuthorizationBridge,
        ):
            raise RealPaidAssessmentPreflightError(
                "authorization_bridge must be a "
                "RealPaidAssessmentAuthorizationBridge"
            )

        if not isinstance(
            evidence_binding,
            RealPaidAssessmentExecutionEvidenceBinding,
        ):
            raise RealPaidAssessmentPreflightError(
                "evidence_binding must be a "
                "RealPaidAssessmentExecutionEvidenceBinding"
            )

        if not isinstance(
            paid_work_authorization,
            PaidAssessmentWorkAuthorization,
        ):
            raise RealPaidAssessmentPreflightError(
                "paid_work_authorization must be a "
                "PaidAssessmentWorkAuthorization"
            )

        if not isinstance(request, AssessmentExecutionRequest):
            raise RealPaidAssessmentPreflightError(
                "request must be an AssessmentExecutionRequest"
            )

        if not isinstance(contract_execution_event, dict):
            raise RealPaidAssessmentPreflightError(
                "contract_execution_event must be a dict"
            )

        path = Path(database_path)

        if not str(path).strip():
            raise RealPaidAssessmentPreflightError(
                "database_path is required"
            )

        expected_hierarchy = intake.hierarchy_key

        declared_path = Path(
            intake.storage.repository_path
        )

        storage_matches = (
            path.resolve()
            == declared_path.resolve()
        )

        authorization_hierarchy = "/".join(
            (
                paid_work_authorization.tenant_id,
                paid_work_authorization.client_id,
                paid_work_authorization.engagement_id,
                paid_work_authorization.assessment_id,
            )
        )

        hierarchy_consistent = all(
            (
                authorization_bridge.hierarchy_key
                == expected_hierarchy,
                evidence_binding.hierarchy_key
                == expected_hierarchy,
                request.context.hierarchy_key
                == expected_hierarchy,
                authorization_hierarchy
                == expected_hierarchy,
            )
        )

        authorization_affirmative = (
            paid_work_authorization.paid_assessment_authorized
            is True
        )

        bridge_ready = (
            authorization_bridge.bridge_status
            == BRIDGE_STATUS_READY
        )

        evidence_approved = (
            evidence_binding.binding_status
            == EXECUTION_EVIDENCE_STATUS_APPROVED
        )

        contract_event_id = str(
            contract_execution_event.get(
                "contract_execution_event_id",
                "",
            )
        ).strip()

        contract_matches = bool(
            contract_event_id
            and contract_event_id
            == paid_work_authorization.contract_execution_event_id
        )

        database_exists = path.exists()

        blockers: list[str] = []

        if not storage_matches:
            blockers.append(
                "database_path_does_not_match_intake_storage"
            )

        if not hierarchy_consistent:
            blockers.append(
                "commercial_hierarchy_mismatch"
            )

        if not authorization_affirmative:
            blockers.append(
                "paid_work_authorization_not_affirmative"
            )

        if not bridge_ready:
            blockers.append(
                "authorization_bridge_not_ready"
            )

        if not evidence_approved:
            blockers.append(
                "execution_evidence_not_approved"
            )

        if not contract_matches:
            blockers.append(
                "contract_event_authorization_mismatch"
            )

        # PILOT-004 v1 is deliberately fresh-run only.
        # Existing-database recovery remains owned by PA014/PA015.
        if database_exists:
            blockers.append(
                "database_already_exists_use_governed_recovery_path"
            )

        status = (
            PREFLIGHT_STATUS_READY
            if not blockers
            else PREFLIGHT_STATUS_BLOCKED
        )

        return RealPaidAssessmentPreflightResult(
            tenant_id=request.context.tenant_id,
            client_id=request.context.client_id,
            engagement_id=request.context.engagement_id,
            assessment_id=request.context.assessment_id,
            database_path=str(path),
            status=status,
            blockers=tuple(blockers),
            database_exists=database_exists,
            intake_storage_matches_database=storage_matches,
            hierarchy_consistent=hierarchy_consistent,
            authorization_affirmative=authorization_affirmative,
            authorization_bridge_ready=bridge_ready,
            evidence_binding_approved=evidence_approved,
            contract_event_matches_authorization=contract_matches,
        )


SERVICE_TYPE = GovernanceRealPaidAssessmentPreflightService