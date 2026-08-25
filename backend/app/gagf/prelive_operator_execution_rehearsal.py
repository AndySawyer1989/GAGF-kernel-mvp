from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from backend.app.gagf.governance_assessment_application import (
    GovernanceAssessmentApplicationService,
)
from backend.app.gagf.governance_assessment_repository import (
    GovernanceAssessmentRepository,
)
from backend.app.gagf.governance_paid_assessment_execution_coordinator import (
    GovernancePaidAssessmentExecutionCoordinator,
    PaidAssessmentExecutionCoordinatorError,
    PaidAssessmentExecutionResult,
)
from backend.app.gagf.governance_paid_assessment_execution_handoff import (
    PaidAssessmentWorkAuthorization,
)
from backend.app.gagf.prelive_assessment_execution_bridge import (
    PreliveAssessmentExecutionMetadata,
)
from backend.app.gagf.prelive_blind_assessment import (
    PreliveScenarioError,
)
from backend.app.gagf.prelive_execution_handoff_bridge import (
    PreliveExecutionHandoffBridge,
    PreliveExecutionHandoffBridgeResult,
)


PRELIVE_OPERATOR_EXECUTION_REHEARSAL_VERSION = "1.0.0"

PRELIVE_OPERATOR_EXECUTION_REHEARSAL_STATUS = (
    "assessment_execution_completed"
)

PRELIVE_OPERATOR_EXECUTION_AUTHORITY = (
    "GAGF_FIP_ONLY"
)


@dataclass(frozen=True, slots=True)
class PreliveOperatorExecutionConfirmation:
    """
    Explicit operator confirmation for one exact PRELIVE
    execution rehearsal.

    This confirmation does not create paid-work authority.

    It confirms that the operator intends to invoke the
    already-authorized READY handoff using the exact
    request bound into that handoff.
    """

    operator_id: str
    confirmed_at: str
    handoff_hash: str
    assessment_execution_request_hash: str
    execution_confirmed: bool = True

    def __post_init__(self) -> None:
        for field_name in (
            "operator_id",
            "confirmed_at",
            "handoff_hash",
            "assessment_execution_request_hash",
        ):
            value = getattr(
                self,
                field_name,
            )

            if (
                not isinstance(value, str)
                or not value.strip()
            ):
                raise PreliveScenarioError(
                    f"{field_name} must not be empty."
                )

        if self.execution_confirmed is not True:
            raise PreliveScenarioError(
                "PRELIVE operator execution "
                "confirmation must be explicit."
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "operator_id":
                self.operator_id,
            "confirmed_at":
                self.confirmed_at,
            "handoff_hash":
                self.handoff_hash,
            "assessment_execution_request_hash":
                self.assessment_execution_request_hash,
            "execution_confirmed":
                self.execution_confirmed,
        }


@dataclass(frozen=True, slots=True)
class PreliveOperatorExecutionRehearsalResult:
    """
    Result of one operator-controlled PRELIVE execution.

    Application completion means only that the governed
    assessment application completed its execution and
    persistence contract.

    It does not establish customer outcome, intervention
    success, causal proof, production onboarding, or
    authorization for future action.
    """

    handoff_bridge: PreliveExecutionHandoffBridgeResult
    operator_confirmation: PreliveOperatorExecutionConfirmation
    execution_result: PaidAssessmentExecutionResult

    rehearsal_status: str = (
        PRELIVE_OPERATOR_EXECUTION_REHEARSAL_STATUS
    )

    authority: str = (
        PRELIVE_OPERATOR_EXECUTION_AUTHORITY
    )

    rehearsal_version: str = (
        PRELIVE_OPERATOR_EXECUTION_REHEARSAL_VERSION
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "rehearsal_status":
                self.rehearsal_status,
            "authority":
                self.authority,
            "rehearsal_version":
                self.rehearsal_version,
            "application_completed":
                self.execution_result.application_completed,
            "handoff":
                self.handoff_bridge.handoff.to_dict(),
            "operator_confirmation":
                self.operator_confirmation.to_dict(),
            "execution_result":
                self.execution_result.to_dict(),
        }


class PreliveOperatorExecutionRehearsal:
    """
    Execute one blind PRELIVE assessment rehearsal
    through the existing governed paid-assessment
    execution coordinator.

    This service:

    1. Builds the real AssessmentExecutionRequest.
    2. Builds the real READY PaidAssessmentExecutionHandoff.
    3. Requires explicit operator confirmation bound to
       the exact handoff and request hashes.
    4. Instantiates the real governance assessment
       repository and application service.
    5. Delegates execution to
       GovernancePaidAssessmentExecutionCoordinator.

    This service does not expose an HTTP execution route.
    """

    def __init__(
        self,
        *,
        handoff_bridge: (
            PreliveExecutionHandoffBridge | None
        ) = None,
    ) -> None:
        self._handoff_bridge = (
            handoff_bridge
            or PreliveExecutionHandoffBridge()
        )

    def prepare(
        self,
        *,
        scenario: Mapping[str, Any],
        metadata: PreliveAssessmentExecutionMetadata,
        contract_execution_event: Mapping[str, Any],
        paid_work_authorization: PaidAssessmentWorkAuthorization,
    ) -> PreliveExecutionHandoffBridgeResult:
        return self._handoff_bridge.prepare_handoff(
            scenario=scenario,
            metadata=metadata,
            contract_execution_event=(
                contract_execution_event
            ),
            paid_work_authorization=(
                paid_work_authorization
            ),
        )

    def execute_prepared(
        self,
        *,
        database_path: str | Path,
        prepared: PreliveExecutionHandoffBridgeResult,
        operator_confirmation: (
            PreliveOperatorExecutionConfirmation
        ),
    ) -> PreliveOperatorExecutionRehearsalResult:
        if not isinstance(
            prepared,
            PreliveExecutionHandoffBridgeResult,
        ):
            raise PreliveScenarioError(
                "PRELIVE execution requires a prepared "
                "execution handoff result."
            )

        if not isinstance(
            operator_confirmation,
            PreliveOperatorExecutionConfirmation,
        ):
            raise PreliveScenarioError(
                "PRELIVE execution requires explicit "
                "operator execution confirmation."
            )

        self._validate_operator_confirmation(
            prepared=prepared,
            confirmation=operator_confirmation,
        )

        repository = GovernanceAssessmentRepository(
            database_path
        )

        application_service = (
            GovernanceAssessmentApplicationService(
                repository=repository
            )
        )

        coordinator = (
            GovernancePaidAssessmentExecutionCoordinator(
                application_service=application_service
            )
        )

        try:
            execution_result = coordinator.execute(
                handoff=prepared.handoff,
                request=prepared.request_bridge.request,
            )
        except (
            PaidAssessmentExecutionCoordinatorError
        ) as exc:
            raise PreliveScenarioError(
                "PRELIVE governed assessment execution "
                f"failed: {exc}"
            ) from exc

        return PreliveOperatorExecutionRehearsalResult(
            handoff_bridge=prepared,
            operator_confirmation=(
                operator_confirmation
            ),
            execution_result=execution_result,
        )

    def execute(
        self,
        *,
        database_path: str | Path,
        scenario: Mapping[str, Any],
        metadata: PreliveAssessmentExecutionMetadata,
        contract_execution_event: Mapping[str, Any],
        paid_work_authorization: PaidAssessmentWorkAuthorization,
        operator_confirmation: (
            PreliveOperatorExecutionConfirmation
        ),
    ) -> PreliveOperatorExecutionRehearsalResult:
        prepared = self.prepare(
            scenario=scenario,
            metadata=metadata,
            contract_execution_event=(
                contract_execution_event
            ),
            paid_work_authorization=(
                paid_work_authorization
            ),
        )

        return self.execute_prepared(
            database_path=database_path,
            prepared=prepared,
            operator_confirmation=(
                operator_confirmation
            ),
        )

    def _validate_operator_confirmation(
        self,
        *,
        prepared: PreliveExecutionHandoffBridgeResult,
        confirmation: PreliveOperatorExecutionConfirmation,
    ) -> None:
        handoff = prepared.handoff

        if (
            confirmation.handoff_hash
            != handoff.handoff_hash
        ):
            raise PreliveScenarioError(
                "PRELIVE operator confirmation "
                "handoff hash does not match the "
                "prepared governed handoff."
            )

        if (
            confirmation.assessment_execution_request_hash
            != handoff.assessment_execution_request_hash
        ):
            raise PreliveScenarioError(
                "PRELIVE operator confirmation "
                "request hash does not match the "
                "prepared governed request."
            )