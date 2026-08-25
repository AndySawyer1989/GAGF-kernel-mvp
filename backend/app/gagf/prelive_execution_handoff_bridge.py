from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from backend.app.gagf.governance_paid_assessment_execution_handoff import (
    GovernancePaidAssessmentExecutionHandoffService,
    PaidAssessmentExecutionHandoff,
    PaidAssessmentExecutionHandoffError,
    PaidAssessmentWorkAuthorization,
)
from backend.app.gagf.prelive_assessment_execution_bridge import (
    PreliveAssessmentExecutionBridge,
    PreliveAssessmentExecutionBridgeResult,
    PreliveAssessmentExecutionMetadata,
)
from backend.app.gagf.prelive_blind_assessment import (
    PreliveScenarioError,
)


PRELIVE_EXECUTION_HANDOFF_BRIDGE_VERSION = "1.0.0"

PRELIVE_EXECUTION_HANDOFF_STATUS = (
    "prepared_for_authorized_execution_handoff"
)

PRELIVE_EXECUTION_HANDOFF_AUTHORITY = (
    "GAGF_FIP_ONLY"
)


@dataclass(frozen=True, slots=True)
class PreliveExecutionHandoffBridgeResult:
    """
    PRELIVE result at the governed execution-handoff
    boundary.

    A READY handoff means the existing paid-assessment
    prerequisites were satisfied.

    It does not mean that this PRELIVE bridge executed
    the assessment.
    """

    request_bridge: PreliveAssessmentExecutionBridgeResult
    handoff: PaidAssessmentExecutionHandoff

    bridge_status: str = (
        PRELIVE_EXECUTION_HANDOFF_STATUS
    )

    authority: str = (
        PRELIVE_EXECUTION_HANDOFF_AUTHORITY
    )

    bridge_version: str = (
        PRELIVE_EXECUTION_HANDOFF_BRIDGE_VERSION
    )

    assessment_executed: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "bridge_status":
                self.bridge_status,
            "authority":
                self.authority,
            "bridge_version":
                self.bridge_version,
            "assessment_executed":
                self.assessment_executed,
            "request_bridge":
                self.request_bridge.to_dict(),
            "handoff":
                self.handoff.to_dict(),
        }


class PreliveExecutionHandoffBridge:
    """
    Prepare PRELIVE evidence for the repository's
    existing paid-assessment execution-handoff boundary.

    This bridge:

    1. Validates and converts blind PRELIVE evidence
       into a real AssessmentExecutionRequest.

    2. Requires an independently supplied
       PaidAssessmentWorkAuthorization.

    3. Requires the repository's real contract-execution
       event contract.

    4. Delegates handoff construction to
       GovernancePaidAssessmentExecutionHandoffService.

    This bridge does not execute an assessment and does
    not manufacture paid-work authority.
    """

    def __init__(
        self,
        *,
        request_bridge: (
            PreliveAssessmentExecutionBridge | None
        ) = None,
        handoff_service: (
            GovernancePaidAssessmentExecutionHandoffService
            | None
        ) = None,
    ) -> None:
        self._request_bridge = (
            request_bridge
            or PreliveAssessmentExecutionBridge()
        )

        self._handoff_service = (
            handoff_service
            or GovernancePaidAssessmentExecutionHandoffService()
        )

    def prepare_handoff(
        self,
        *,
        scenario: Mapping[str, Any],
        metadata: PreliveAssessmentExecutionMetadata,
        contract_execution_event: Mapping[str, Any],
        paid_work_authorization: PaidAssessmentWorkAuthorization,
    ) -> PreliveExecutionHandoffBridgeResult:
        if not isinstance(
            paid_work_authorization,
            PaidAssessmentWorkAuthorization,
        ):
            raise PreliveScenarioError(
                "PRELIVE execution handoff requires "
                "an independently supplied "
                "PaidAssessmentWorkAuthorization."
            )

        if not isinstance(
            contract_execution_event,
            Mapping,
        ):
            raise PreliveScenarioError(
                "PRELIVE execution handoff requires "
                "a contract-execution event mapping."
            )

        request_bridge_result = (
            self._request_bridge.build_request(
                scenario=scenario,
                metadata=metadata,
            )
        )

        try:
            handoff = (
                self._handoff_service.build_handoff(
                    contract_execution_event=dict(
                        contract_execution_event
                    ),
                    paid_work_authorization=(
                        paid_work_authorization
                    ),
                    assessment_execution_request=(
                        request_bridge_result.request
                    ),
                )
            )
        except PaidAssessmentExecutionHandoffError as exc:
            raise PreliveScenarioError(
                "PRELIVE authorized execution handoff "
                f"failed: {exc}"
            ) from exc

        return PreliveExecutionHandoffBridgeResult(
            request_bridge=request_bridge_result,
            handoff=handoff,
        )