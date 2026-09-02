from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

from backend.app.gagf.governance_assessment_application import (
    AssessmentExecutionRequest,
)
from backend.app.gagf.governance_commercial_paid_assessment_adapter import (
    CommercialContractExecutionEventInput,
    CommercialExecutionEvidenceApprovalInput,
    CommercialPaidAssessmentAdapterError,
    CommercialPaidAssessmentIntakeInput,
    CommercialPaidWorkAuthorizationInput,
    GovernanceCommercialPaidAssessmentAdapter,
)
from backend.app.gagf.governance_commercial_paid_assessment_execution_status import (
    CommercialPaidAssessmentExecutionStatusError,
    GovernanceCommercialPaidAssessmentExecutionStatusStore,
)
from backend.app.gagf.governance_real_paid_assessment_authorization_bridge import (
    GovernanceRealPaidAssessmentAuthorizationBridgeService,
)
from backend.app.gagf.governance_real_paid_assessment_execution_evidence import (
    GovernanceRealPaidAssessmentExecutionEvidenceService,
)
from backend.app.gagf.governance_real_paid_assessment_execution_recovery import (
    GovernanceRealPaidAssessmentExecutionRecoveryService,
    RealPaidAssessmentExecutionRecoveryResult,
)
from backend.app.gagf.governance_real_paid_assessment_readiness import (
    GovernanceRealPaidAssessmentReadinessService,
)
from backend.app.gagf.governance_commercial_paid_assessment_execution_snapshot_bridge import (
    CommercialPaidAssessmentExecutionSnapshotBridgeError,
    GovernanceCommercialPaidAssessmentExecutionSnapshotBridgeService,
)

COMMERCIAL_PAID_ASSESSMENT_EXECUTION_VERSION = "0.4.0"

COMMERCIAL_PAID_ASSESSMENT_EXECUTION_STATUS_DATABASE = (
    "commercial-paid-assessment-execution-status.sqlite3"
)


class CommercialPaidAssessmentExecutionError(RuntimeError):
    """Raised when governed commercial paid-assessment execution fails."""


@dataclass(frozen=True, slots=True)
class CommercialPaidAssessmentExecutionInput:
    intake: CommercialPaidAssessmentIntakeInput
    contract_execution_event: CommercialContractExecutionEventInput
    paid_work_authorization: CommercialPaidWorkAuthorizationInput
    execution_evidence_approvals: tuple[
        CommercialExecutionEvidenceApprovalInput,
        ...,
    ]
    assessment_execution_request: AssessmentExecutionRequest

    def __post_init__(self) -> None:
        if not isinstance(
            self.intake,
            CommercialPaidAssessmentIntakeInput,
        ):
            raise CommercialPaidAssessmentExecutionError(
                "intake must be a CommercialPaidAssessmentIntakeInput"
            )

        if not isinstance(
            self.contract_execution_event,
            CommercialContractExecutionEventInput,
        ):
            raise CommercialPaidAssessmentExecutionError(
                "contract_execution_event must be a "
                "CommercialContractExecutionEventInput"
            )

        if not isinstance(
            self.paid_work_authorization,
            CommercialPaidWorkAuthorizationInput,
        ):
            raise CommercialPaidAssessmentExecutionError(
                "paid_work_authorization must be a "
                "CommercialPaidWorkAuthorizationInput"
            )

        if not isinstance(
            self.assessment_execution_request,
            AssessmentExecutionRequest,
        ):
            raise CommercialPaidAssessmentExecutionError(
                "assessment_execution_request must be an "
                "AssessmentExecutionRequest"
            )

        if not self.execution_evidence_approvals:
            raise CommercialPaidAssessmentExecutionError(
                "at least one execution-evidence approval is required"
            )

        for approval in self.execution_evidence_approvals:
            if not isinstance(
                approval,
                CommercialExecutionEvidenceApprovalInput,
            ):
                raise CommercialPaidAssessmentExecutionError(
                    "execution_evidence_approvals must contain only "
                    "CommercialExecutionEvidenceApprovalInput values"
                )


class GovernanceCommercialPaidAssessmentExecutionService:
    """
    Orchestrate explicit commercial operator inputs through the existing
    governed real-paid-assessment execution path.

    The service owns only a server-controlled execution directory.
    Each assessment hierarchy receives one deterministic SQLite database
    inside that directory so a fresh assessment is not mistaken for a
    recovery attempt belonging to another hierarchy.

    Durable commercial execution status is recorded only after PA015
    successfully returns.

    This service does not:
    - create paid-work authorization,
    - infer contract execution,
    - infer execution-evidence approval,
    - establish execution authority,
    - establish recovery authority,
    - bypass real-paid-assessment readiness,
    - bypass authorization binding,
    - bypass exact evidence binding,
    - create a second execution authority,
    - allow browser-selected filesystem paths,
    - approve delivery,
    - record delivery.

    The existing PA015 recovery service remains the authoritative
    execution/recovery path.
    """

    def __init__(
        self,
        *,
        execution_directory: str | Path,
        adapter: GovernanceCommercialPaidAssessmentAdapter | None = None,
        status_store: (
            GovernanceCommercialPaidAssessmentExecutionStatusStore
            | None
        ) = None,
    ) -> None:
        directory = Path(execution_directory)

        if not str(directory).strip():
            raise CommercialPaidAssessmentExecutionError(
                "execution_directory must not be empty"
            )

        self.execution_directory = directory

        self._adapter = (
            adapter
            if adapter is not None
            else GovernanceCommercialPaidAssessmentAdapter()
        )

        self._status_store = (
            status_store
            if status_store is not None
            else GovernanceCommercialPaidAssessmentExecutionStatusStore(
                directory.parent
                / COMMERCIAL_PAID_ASSESSMENT_EXECUTION_STATUS_DATABASE
            )
        )

    @property
    def status_store(
        self,
    ) -> GovernanceCommercialPaidAssessmentExecutionStatusStore:
        return self._status_store

    def database_path_for_hierarchy(
        self,
        *,
        tenant_id: str,
        client_id: str,
        engagement_id: str,
        assessment_id: str,
    ) -> Path:
        hierarchy_key = "/".join(
            (
                tenant_id.strip(),
                client_id.strip(),
                engagement_id.strip(),
                assessment_id.strip(),
            )
        )

        if (
            "//" in hierarchy_key
            or hierarchy_key.startswith("/")
        ):
            raise CommercialPaidAssessmentExecutionError(
                "assessment hierarchy contains an empty identifier"
            )

        digest = hashlib.sha256(
            hierarchy_key.encode("utf-8")
        ).hexdigest()

        return (
            self.execution_directory
            / f"paid-assessment-{digest}.sqlite3"
        )

    def database_path_for_input(
        self,
        *,
        execution_input: CommercialPaidAssessmentExecutionInput,
    ) -> Path:
        if not isinstance(
            execution_input,
            CommercialPaidAssessmentExecutionInput,
        ):
            raise CommercialPaidAssessmentExecutionError(
                "execution_input must be a "
                "CommercialPaidAssessmentExecutionInput"
            )

        intake = execution_input.intake

        return self.database_path_for_hierarchy(
            tenant_id=intake.tenant_id,
            client_id=intake.client_id,
            engagement_id=intake.engagement_id,
            assessment_id=intake.assessment_id,
        )

    def execute(
        self,
        *,
        execution_input: CommercialPaidAssessmentExecutionInput,
        execution_input_binding_hash: str,
    ) -> RealPaidAssessmentExecutionRecoveryResult:
        if not isinstance(
            execution_input,
            CommercialPaidAssessmentExecutionInput,
        ):
            raise CommercialPaidAssessmentExecutionError(
                "execution_input must be a "
                "CommercialPaidAssessmentExecutionInput"
            )

        if (
            not isinstance(
                execution_input_binding_hash,
                str,
            )
            or not execution_input_binding_hash.strip()
        ):
            raise CommercialPaidAssessmentExecutionError(
                "execution_input_binding_hash must be non-empty"
            )

        try:
            database_path = self.database_path_for_input(
                execution_input=execution_input
            )

            database_path.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            intake = self._adapter.build_intake(
                payload=execution_input.intake
            )

            if (
                Path(
                    intake.storage.repository_path
                )
                != database_path
            ):
                raise CommercialPaidAssessmentExecutionError(
                    "commercial intake storage repository_path does not "
                    "match the server-assigned governed execution database"
                )

            readiness = (
                GovernanceRealPaidAssessmentReadinessService()
                .evaluate(
                    intake=intake
                )
            )

            contract_execution_event = (
                self._adapter.build_contract_execution_event(
                    payload=(
                        execution_input.contract_execution_event
                    )
                )
            )

            paid_work_authorization = (
                self._adapter.build_paid_work_authorization(
                    payload=(
                        execution_input.paid_work_authorization
                    )
                )
            )

            authorization_bridge = (
                GovernanceRealPaidAssessmentAuthorizationBridgeService()
                .bind(
                    intake=intake,
                    readiness=readiness,
                    paid_work_authorization=(
                        paid_work_authorization
                    ),
                )
            )

            approvals = tuple(
                self._adapter.build_execution_evidence_approval(
                    payload=approval
                )
                for approval
                in execution_input.execution_evidence_approvals
            )

            evidence_binding = (
                GovernanceRealPaidAssessmentExecutionEvidenceService()
                .bind(
                    intake=intake,
                    request=(
                        execution_input.assessment_execution_request
                    ),
                    approvals=approvals,
                )
            )

            result = (
                GovernanceRealPaidAssessmentExecutionRecoveryService()
                .execute(
                    database_path=database_path,
                    intake=intake,
                    authorization_bridge=authorization_bridge,
                    evidence_binding=evidence_binding,
                    contract_execution_event=(
                        contract_execution_event
                    ),
                    paid_work_authorization=(
                        paid_work_authorization
                    ),
                    request=(
                        execution_input.assessment_execution_request
                    ),
                )
            )

            status_record = (
                self._status_store.build_status(
                    tenant_id=(
                        result.attempt.tenant_id
                    ),
                    client_id=(
                        result.attempt.client_id
                    ),
                    engagement_id=(
                        result.attempt.engagement_id
                    ),
                    assessment_id=(
                        result.attempt.assessment_id
                    ),
                    disposition=(
                        result.disposition
                    ),
                    attempt_hash=(
                        result.attempt.attempt_hash
                    ),
                    attempt_record_hash=(
                        result.attempt.record_hash
                    ),
                    assessment_execution_request_hash=(
                        result.attempt
                        .assessment_execution_request_hash
                    ),
                    execution_input_binding_hash=(
                        execution_input_binding_hash
                    ),
                    artifact_count_before=(
                        result.artifact_count_before
                    ),
                    artifact_count_after=(
                        result.artifact_count_after
                    ),
                )
            )
            self._status_store.record_status(
                status=status_record
            )

            (
                GovernanceCommercialPaidAssessmentExecutionSnapshotBridgeService(
                    execution_service=self
                )
                .capture(
                    result=result
                )
            )

            return result

        except CommercialPaidAssessmentExecutionError:
            raise

        except CommercialPaidAssessmentAdapterError as exc:
            raise CommercialPaidAssessmentExecutionError(
                f"commercial paid-assessment input is invalid: {exc}"
            ) from exc

        except CommercialPaidAssessmentExecutionStatusError as exc:
            raise CommercialPaidAssessmentExecutionError(
                "governed paid-assessment execution completed but "
                f"durable execution status failed: {exc}"
            ) from exc

        except (
            CommercialPaidAssessmentExecutionSnapshotBridgeError
        ) as exc:
            raise CommercialPaidAssessmentExecutionError(
                "governed paid-assessment execution completed but "
                "durable operator-result snapshot failed: "
                f"{exc}"
            ) from exc

        except Exception as exc:
            raise CommercialPaidAssessmentExecutionError(
                "governed commercial paid-assessment execution failed: "
                f"{type(exc).__name__}: {exc}"
            ) from exc