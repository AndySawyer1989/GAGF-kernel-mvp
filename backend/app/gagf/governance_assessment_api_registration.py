from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI

from backend.app.gagf.governance_assessment_api import (
    create_governance_assessment_router,
)
from backend.app.gagf.governance_assessment_application import (
    GovernanceAssessmentApplicationService,
)
from backend.app.gagf.governance_assessment_repository import (
    GovernanceAssessmentRepository,
)


ASSESSMENT_API_REGISTRATION_VERSION = "1.0.0"
ASSESSMENT_API_REGISTERED_STATE_KEY = (
    "governance_assessment_api_registered"
)


class AssessmentApiRegistrationError(RuntimeError):
    """Raised when the assessment API cannot be registered."""


def register_governance_assessment_api(
    *,
    app: FastAPI,
    repository: GovernanceAssessmentRepository | None = None,
    database_path: str | Path | None = None,
) -> GovernanceAssessmentApplicationService:
    if repository is not None and database_path is not None:
        raise AssessmentApiRegistrationError(
            "provide repository or database_path, not both"
        )

    existing_service = getattr(
        app.state,
        "governance_assessment_service",
        None,
    )
    already_registered = bool(
        getattr(
            app.state,
            ASSESSMENT_API_REGISTERED_STATE_KEY,
            False,
        )
    )

    if already_registered:
        if existing_service is None:
            raise AssessmentApiRegistrationError(
                "assessment API registration state is inconsistent"
            )

        return existing_service

    resolved_repository = repository

    if resolved_repository is None:
        if database_path is None:
            raise AssessmentApiRegistrationError(
                "repository or database_path is required"
            )

        resolved_path = Path(database_path)
        resolved_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )
        resolved_repository = GovernanceAssessmentRepository(
            resolved_path
        )

    service = GovernanceAssessmentApplicationService(
        repository=resolved_repository
    )
    router = create_governance_assessment_router(
        service=service
    )

    app.router.routes.extend(router.routes)

    app.state.governance_assessment_repository = (
        resolved_repository
    )
    app.state.governance_assessment_service = service
    setattr(
        app.state,
        ASSESSMENT_API_REGISTERED_STATE_KEY,
        True,
    )

    return service


