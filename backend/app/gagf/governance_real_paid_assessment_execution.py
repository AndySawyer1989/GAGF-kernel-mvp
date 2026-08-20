from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from backend.app.gagf.governance_assessment_application import (
    AssessmentExecutionRequest,
    GovernanceAssessmentApplicationService,
)
from backend.app.gagf.governance_assessment_repository import (
    GovernanceAssessmentRepository,
)
from backend.app.gagf.governance_paid_assessment_execution_coordinator import (
    GovernancePaidAssessmentExecutionCoordinator,
)
from backend.app.gagf.governance_paid_assessment_execution_handoff import (
    GovernancePaidAssessmentExecutionHandoffService,
    PaidAssessmentExecutionHandoffStatus,
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


REAL_PAID_ASSESSMENT_EXECUTION_ID = (
    "governance-real-paid-assessment-execution"
)
REAL_PAID_ASSESSMENT_EXECUTION_VERSION = "0.1.0"
REAL_PAID_ASSESSMENT_EXECUTION_SCHEMA_VERSION = "1.0.0"

REAL_EXECUTION_STATUS_COMPLETE = "assessment_execution_complete"

EXPECTED_CORE_ARTIFACT_COUNT = 10


class RealPaidAssessmentExecutionError(RuntimeError):
    """Raised when controlled real paid-assessment execution cannot proceed."""


class _CapturingGovernanceAssessmentApplicationService(
    GovernanceAssessmentApplicationService
):
    """
    Production application execution remains super().execute().

    This wrapper only retains the exact application result returned during
    the same PA-002 execution so PILOT-003 can verify persistence/report
    lineage without executing the assessment twice.
    """

    def __init__(
        self,
        *,
        repository: GovernanceAssessmentRepository,
    ) -> None:
        super().__init__(repository=repository)
        self.last_result = None

    def execute(
        self,
        *,
        request: AssessmentExecutionRequest,
    ):
        result = super().execute(request=request)
        self.last_result = result
        return result


@dataclass(frozen=True, slots=True)
class RealPaidAssessmentExecutionResult:
    tenant_id: str
    client_id: str
    engagement_id: str
    assessment_id: str

    execution_status: str

    handoff_hash: str
    execution_result_hash: str
    application_hash: str
    persistence_hash: str

    report_id: str
    report_package_hash: str

    artifact_count: int
    application_completed: bool
    repository_chain_valid: bool

    execution_type: str = REAL_PAID_ASSESSMENT_EXECUTION_ID
    version: str = REAL_PAID_ASSESSMENT_EXECUTION_VERSION
    schema_version: str = REAL_PAID_ASSESSMENT_EXECUTION_SCHEMA_VERSION

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
            "execution_type": self.execution_type,
            "version": self.version,
            "schema_version": self.schema_version,
            "tenant_id": self.tenant_id,
            "client_id": self.client_id,
            "engagement_id": self.engagement_id,
            "assessment_id": self.assessment_id,
            "hierarchy_key": self.hierarchy_key,
            "execution_status": self.execution_status,
            "handoff_hash": self.handoff_hash,
            "execution_result_hash": self.execution_result_hash,
            "application_hash": self.application_hash,
            "persistence_hash": self.persistence_hash,
            "report_id": self.report_id,
            "report_package_hash": self.report_package_hash,
            "artifact_count": self.artifact_count,
            "application_completed": self.application_completed,
            "repository_chain_valid": self.repository_chain_valid,
            "boundaries": {
                "execution_complete_is_not_delivery_approval": True,
                "execution_complete_is_not_delivery": True,
                "execution_complete_is_not_client_receipt": True,
                "execution_complete_is_not_client_acceptance": True,
                "execution_complete_is_not_recommendation_implementation": True,
                "execution_complete_is_not_intervention_authorization": True,
                "execution_complete_is_not_remediation_success": True,
                "execution_complete_is_not_roi_verified": True,
                "execution_complete_is_not_customer_outcome_verified": True,
            },
        }


class GovernanceRealPaidAssessmentExecutionService:
    """
    Execute a controlled real paid assessment through the existing PA-001
    and PA-002 governed execution path.

    Preconditions must already exist independently:
    - PILOT-002 real-client intake
    - PILOT-002 authorization bridge
    - PILOT-003 exact execution-evidence binding
    - separate contract-execution event
    - separate PaidAssessmentWorkAuthorization

    This service stops after governed application execution, ten core
    artifacts, repository-chain verification, and report generation.
    """

    def execute(
        self,
        *,
        database_path: str | Path,
        intake: RealPaidAssessmentIntake,
        authorization_bridge: RealPaidAssessmentAuthorizationBridge,
        evidence_binding: RealPaidAssessmentExecutionEvidenceBinding,
        contract_execution_event: dict[str, Any],
        paid_work_authorization: PaidAssessmentWorkAuthorization,
        request: AssessmentExecutionRequest,
    ) -> RealPaidAssessmentExecutionResult:
        if not isinstance(
            intake,
            RealPaidAssessmentIntake,
        ):
            raise RealPaidAssessmentExecutionError(
                "intake must be a RealPaidAssessmentIntake"
            )

        if not isinstance(
            authorization_bridge,
            RealPaidAssessmentAuthorizationBridge,
        ):
            raise RealPaidAssessmentExecutionError(
                "authorization_bridge must be a "
                "RealPaidAssessmentAuthorizationBridge"
            )

        if not isinstance(
            evidence_binding,
            RealPaidAssessmentExecutionEvidenceBinding,
        ):
            raise RealPaidAssessmentExecutionError(
                "evidence_binding must be a "
                "RealPaidAssessmentExecutionEvidenceBinding"
            )

        if not isinstance(
            paid_work_authorization,
            PaidAssessmentWorkAuthorization,
        ):
            raise RealPaidAssessmentExecutionError(
                "paid_work_authorization must be a "
                "PaidAssessmentWorkAuthorization"
            )

        if not isinstance(
            request,
            AssessmentExecutionRequest,
        ):
            raise RealPaidAssessmentExecutionError(
                "request must be an AssessmentExecutionRequest"
            )

        if not isinstance(
            contract_execution_event,
            dict,
        ):
            raise RealPaidAssessmentExecutionError(
                "contract_execution_event must be a dict"
            )

        path = Path(database_path)

        if not str(path).strip():
            raise RealPaidAssessmentExecutionError(
                "database_path is required"
            )

        if path.exists():
            raise RealPaidAssessmentExecutionError(
                "real paid-assessment database already exists: "
                f"{path}"
            )

        declared_path = Path(
            intake.storage.repository_path
        )

        if path != declared_path:
            raise RealPaidAssessmentExecutionError(
                "database_path does not match intake storage declaration"
            )

        expected_hierarchy = intake.hierarchy_key

        if authorization_bridge.hierarchy_key != expected_hierarchy:
            raise RealPaidAssessmentExecutionError(
                "authorization bridge hierarchy does not match intake"
            )

        if authorization_bridge.bridge_status != BRIDGE_STATUS_READY:
            raise RealPaidAssessmentExecutionError(
                "authorization bridge is not READY"
            )

        if evidence_binding.hierarchy_key != expected_hierarchy:
            raise RealPaidAssessmentExecutionError(
                "execution evidence binding hierarchy does not match intake"
            )

        if (
            evidence_binding.binding_status
            != EXECUTION_EVIDENCE_STATUS_APPROVED
        ):
            raise RealPaidAssessmentExecutionError(
                "execution evidence binding is not approved"
            )

        if request.context.hierarchy_key != expected_hierarchy:
            raise RealPaidAssessmentExecutionError(
                "assessment execution request hierarchy does not match intake"
            )

        authorization_hierarchy = "/".join(
            (
                paid_work_authorization.tenant_id,
                paid_work_authorization.client_id,
                paid_work_authorization.engagement_id,
                paid_work_authorization.assessment_id,
            )
        )

        if authorization_hierarchy != expected_hierarchy:
            raise RealPaidAssessmentExecutionError(
                "paid-work authorization hierarchy does not match intake"
            )

        if (
            authorization_bridge.authorization_id
            != paid_work_authorization.authorization_id
        ):
            raise RealPaidAssessmentExecutionError(
                "authorization bridge does not reference supplied "
                "paid-work authorization"
            )

        if (
            paid_work_authorization.paid_assessment_authorized
            is not True
        ):
            raise RealPaidAssessmentExecutionError(
                "paid-work authorization is not affirmative"
            )

        contract_event_id = str(
            contract_execution_event.get(
                "contract_execution_event_id",
                "",
            )
        ).strip()

        if not contract_event_id:
            raise RealPaidAssessmentExecutionError(
                "contract execution event ID is required"
            )

        if (
            contract_event_id
            != paid_work_authorization.contract_execution_event_id
        ):
            raise RealPaidAssessmentExecutionError(
                "contract execution event does not match "
                "paid-work authorization"
            )

        if path.parent and not path.parent.exists():
            path.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

        repository = GovernanceAssessmentRepository(path)

        handoff = (
            GovernancePaidAssessmentExecutionHandoffService()
            .build_handoff(
                contract_execution_event=contract_execution_event,
                paid_work_authorization=paid_work_authorization,
                assessment_execution_request=request,
            )
        )

        if (
            handoff.status
            is not PaidAssessmentExecutionHandoffStatus.READY
        ):
            raise RealPaidAssessmentExecutionError(
                "PA-001 execution handoff is not READY"
            )

        if handoff.hierarchy_key != expected_hierarchy:
            raise RealPaidAssessmentExecutionError(
                "PA-001 execution handoff hierarchy mismatch"
            )

        application_service = (
            _CapturingGovernanceAssessmentApplicationService(
                repository=repository
            )
        )

        coordinator = (
            GovernancePaidAssessmentExecutionCoordinator(
                application_service=application_service
            )
        )

        execution_result = coordinator.execute(
            handoff=handoff,
            request=request,
        )

        application_result = application_service.last_result

        if application_result is None:
            raise RealPaidAssessmentExecutionError(
                "application result was not captured"
            )

        if execution_result.application_completed is not True:
            raise RealPaidAssessmentExecutionError(
                "PA-002 application execution did not complete"
            )

        if application_result.completed is not True:
            raise RealPaidAssessmentExecutionError(
                "assessment application did not complete"
            )

        if (
            execution_result.artifact_count
            != EXPECTED_CORE_ARTIFACT_COUNT
        ):
            raise RealPaidAssessmentExecutionError(
                "unexpected PA-002 artifact count: "
                f"{execution_result.artifact_count}"
            )

        if (
            application_result.persistence.artifact_count
            != EXPECTED_CORE_ARTIFACT_COUNT
        ):
            raise RealPaidAssessmentExecutionError(
                "unexpected application persistence artifact count"
            )

        if (
            application_result.persistence.repository_chain_valid
            is not True
        ):
            raise RealPaidAssessmentExecutionError(
                "application persistence repository chain is invalid"
            )

        chain_valid = repository.verify_chain(
            context=request.context
        )

        if chain_valid is not True:
            raise RealPaidAssessmentExecutionError(
                "post-execution repository chain verification failed"
            )

        artifacts = repository.list_artifacts(
            context=request.context
        )

        if len(artifacts) != EXPECTED_CORE_ARTIFACT_COUNT:
            raise RealPaidAssessmentExecutionError(
                "repository does not contain exactly ten core artifacts"
            )

        report_package = (
            application_result.demonstration.report_package
        )

        if not report_package.markdown:
            raise RealPaidAssessmentExecutionError(
                "client-ready report markdown is empty"
            )

        if report_package.report_id != execution_result.report_id:
            raise RealPaidAssessmentExecutionError(
                "report package identity does not match PA-002 result"
            )

        committed_report_hash = (
            application_result.demonstration.artifact_commitments[
                "report_package_hash"
            ]
        )

        if (
            report_package.manifest.package_hash
            != committed_report_hash
        ):
            raise RealPaidAssessmentExecutionError(
                "report package hash does not match application commitment"
            )

        return RealPaidAssessmentExecutionResult(
            tenant_id=execution_result.tenant_id,
            client_id=execution_result.client_id,
            engagement_id=execution_result.engagement_id,
            assessment_id=execution_result.assessment_id,
            execution_status=REAL_EXECUTION_STATUS_COMPLETE,
            handoff_hash=execution_result.handoff_hash,
            execution_result_hash=(
                execution_result.execution_result_hash
            ),
            application_hash=execution_result.application_hash,
            persistence_hash=execution_result.persistence_hash,
            report_id=execution_result.report_id,
            report_package_hash=(
                report_package.manifest.package_hash
            ),
            artifact_count=len(artifacts),
            application_completed=True,
            repository_chain_valid=True,
        )


SERVICE_TYPE = GovernanceRealPaidAssessmentExecutionService