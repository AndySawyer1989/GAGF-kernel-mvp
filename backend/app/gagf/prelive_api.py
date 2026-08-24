from __future__ import annotations

from typing import Any

from fastapi import (
    APIRouter,
    HTTPException,
    status,
)
from pydantic import BaseModel, Field

from backend.app.gagf.prelive_assessment_execution_bridge import (
    PreliveAssessmentExecutionBridge,
    PreliveAssessmentExecutionMetadata,
)
from backend.app.gagf.prelive_blind_assessment import (
    PreliveScenarioError,
)
from backend.app.gagf.prelive_blind_assessment_service import (
    PreliveBlindAssessmentService,
)


PRELIVE_API_VERSION = "1.0.0"

PRELIVE_API_PREFIX = "/api/v1/prelive"

PRELIVE_API_TAG = "prelive"


class PreliveScenarioApiRequest(BaseModel):
    """
    External blind PRELIVE evidence envelope.

    The request contains evidence only.

    It does not contain:
    - an assessment determination
    - a kernel determination
    - an intervention authorization
    - execution authority
    """

    scenario: dict[str, Any] = Field(
        ...,
        description=(
            "Blind independently generated "
            "PRELIVE-001 scenario."
        ),
    )


class PreliveBuildRequestApiRequest(BaseModel):
    """
    Human-scoped metadata plus validated blind evidence
    used to construct the real assessment execution request.

    Constructing the request does not execute it.
    """

    scenario: dict[str, Any]

    tenant_id: str
    client_id: str
    engagement_id: str
    assessment_id: str

    assessment_name: str

    workflow_names: list[str]
    organizational_units: list[str]

    objectives: list[str]
    expected_outcomes: list[str]

    client_display_name: str
    prepared_by: str

    exclusions: list[str] = Field(
        default_factory=list
    )

    maximum_priorities: int = Field(
        default=3,
        ge=1,
    )

    def to_bridge_metadata(
        self,
    ) -> PreliveAssessmentExecutionMetadata:
        return (
            PreliveAssessmentExecutionMetadata(
                tenant_id=self.tenant_id,
                client_id=self.client_id,
                engagement_id=self.engagement_id,
                assessment_id=self.assessment_id,
                assessment_name=self.assessment_name,
                workflow_names=tuple(
                    self.workflow_names
                ),
                organizational_units=tuple(
                    self.organizational_units
                ),
                objectives=tuple(
                    self.objectives
                ),
                expected_outcomes=tuple(
                    self.expected_outcomes
                ),
                client_display_name=(
                    self.client_display_name
                ),
                prepared_by=self.prepared_by,
                exclusions=tuple(
                    self.exclusions
                ),
                maximum_priorities=(
                    self.maximum_priorities
                ),
            )
        )


def _prelive_error_detail(
    *,
    code: str,
    message: str,
) -> dict[str, str]:
    return {
        "code": code,
        "message": message,
    }


def create_prelive_router(
    *,
    service: PreliveBlindAssessmentService,
) -> APIRouter:
    """
    Create the PRELIVE blind-evidence API router.

    Constitutional boundary:

    This router exposes:
    - validation
    - preparation
    - AssessmentExecutionRequest construction

    It deliberately does not expose an execution route.
    """

    router = APIRouter(
        prefix=PRELIVE_API_PREFIX,
        tags=[PRELIVE_API_TAG],
    )

    execution_bridge = (
        PreliveAssessmentExecutionBridge()
    )

    @router.post(
        "/validate",
        status_code=status.HTTP_200_OK,
    )
    def validate_prelive_scenario(
        request: PreliveScenarioApiRequest,
    ) -> dict[str, Any]:
        result = service.validate(
            request.scenario
        )

        return {
            "api_version":
                PRELIVE_API_VERSION,
            "operation":
                "validate",
            "authority":
                "GAGF_FIP_ONLY",
            "assessment_executed":
                False,
            "result":
                result,
        }

    @router.post(
        "/prepare",
        status_code=status.HTTP_200_OK,
    )
    def prepare_prelive_scenario(
        request: PreliveScenarioApiRequest,
    ) -> dict[str, Any]:
        try:
            result = service.prepare(
                request.scenario
            )
        except PreliveScenarioError as exc:
            raise HTTPException(
                status_code=(
                    status.HTTP_422_UNPROCESSABLE_CONTENT
                ),
                detail=_prelive_error_detail(
                    code=(
                        "PRELIVE_VALIDATION_FAILED"
                    ),
                    message=str(exc),
                ),
            ) from exc

        return {
            "api_version":
                PRELIVE_API_VERSION,
            "operation":
                "prepare",
            "authority":
                "GAGF_FIP_ONLY",
            "assessment_executed":
                False,
            "execution_authorized":
                False,
            "human_execution_required":
                True,
            "result":
                result,
        }

    @router.post(
        "/build-request",
        status_code=status.HTTP_200_OK,
    )
    def build_prelive_execution_request(
        request: PreliveBuildRequestApiRequest,
    ) -> dict[str, Any]:
        try:
            result = (
                execution_bridge.build_request(
                    scenario=request.scenario,
                    metadata=(
                        request.to_bridge_metadata()
                    ),
                )
            )
        except PreliveScenarioError as exc:
            raise HTTPException(
                status_code=(
                    status.HTTP_422_UNPROCESSABLE_CONTENT
                ),
                detail=_prelive_error_detail(
                    code=(
                        "PRELIVE_REQUEST_BRIDGE_FAILED"
                    ),
                    message=str(exc),
                ),
            ) from exc

        return {
            "api_version":
                PRELIVE_API_VERSION,
            "operation":
                "build-request",
            "authority":
                "GAGF_FIP_ONLY",
            "assessment_executed":
                False,
            "execution_authorized":
                False,
            "human_execution_required":
                True,
            "result":
                result.to_dict(),
        }

    return router