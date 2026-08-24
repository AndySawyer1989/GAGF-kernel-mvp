from __future__ import annotations

from fastapi import FastAPI

from backend.app.gagf.prelive_api import (
    create_prelive_router,
)
from backend.app.gagf.prelive_blind_assessment_service import (
    PreliveBlindAssessmentService,
)


PRELIVE_API_REGISTERED_STATE_KEY = (
    "prelive_api_registered"
)

PRELIVE_SERVICE_STATE_KEY = (
    "prelive_blind_assessment_service"
)


def register_prelive_api(
    *,
    app: FastAPI,
) -> PreliveBlindAssessmentService:
    """
    Register the PRELIVE validation/preparation API.

    Registration is idempotent.

    PRELIVE routes are flattened into the application's
    existing route table rather than inserted as an
    _IncludedRouter container.

    This preserves the established repository invariant
    that top-level app.routes entries expose .path.

    No PRELIVE execution route is created.
    """

    if getattr(
        app.state,
        PRELIVE_API_REGISTERED_STATE_KEY,
        False,
    ):
        existing_service = getattr(
            app.state,
            PRELIVE_SERVICE_STATE_KEY,
            None,
        )

        if not isinstance(
            existing_service,
            PreliveBlindAssessmentService,
        ):
            raise RuntimeError(
                "PRELIVE API registration state "
                "is inconsistent."
            )

        return existing_service

    service = (
        PreliveBlindAssessmentService()
    )

    router = create_prelive_router(
        service=service
    )

    for route in router.routes:
        app.router.routes.append(route)

    app.openapi_schema = None

    setattr(
        app.state,
        PRELIVE_SERVICE_STATE_KEY,
        service,
    )

    setattr(
        app.state,
        PRELIVE_API_REGISTERED_STATE_KEY,
        True,
    )

    return service
