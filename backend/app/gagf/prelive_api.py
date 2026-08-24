from __future__ import annotations

from typing import Any

from fastapi import (
    APIRouter,
    HTTPException,
    status,
)
from pydantic import BaseModel, Field

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

    This router exposes validation and preparation only.

    It deliberately does not expose an execution route.
    """

    router = APIRouter(
        prefix=PRELIVE_API_PREFIX,
        tags=[PRELIVE_API_TAG],
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

    return router