from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from backend.app.engineering_agent.composition.container import (
    EngineeringAgentContainer,
)
from backend.app.engineering_agent.config import (
    EngineeringAgentSettings,
)
from backend.app.engineering_agent.contracts.v1 import (
    ApplicationStatusResponse,
    ErrorResponse,
    HealthResponse,
)

APPLICATION_VERSION = "0.1.0"
API_VERSION = "v1"


def create_app(
    settings: EngineeringAgentSettings | None = None,
) -> FastAPI:

    @asynccontextmanager
    async def lifespan(
        application: FastAPI,
    ) -> AsyncIterator[None]:

        resolved_settings = settings or (
            EngineeringAgentSettings.from_environment()
        )

        container = EngineeringAgentContainer.build(
            resolved_settings
        )

        application.state.container = container

        try:
            yield
        finally:
            container.close()
            application.state.container = None

    application = FastAPI(
        title="Engineering Agent",
        version=APPLICATION_VERSION,
        description=(
            "Standalone engineering operations application. "
            "Execution authority is not enabled in this release."
        ),
        lifespan=lifespan,
    )

    @application.middleware("http")
    async def request_correlation_middleware(
        request: Request,
        call_next,
    ):
        request_id = str(uuid4())
        request.state.request_id = request_id

        response = await call_next(request)

        response.headers["X-Request-ID"] = request_id

        return response

    def get_request_id(request: Request) -> str:
        return getattr(
            request.state,
            "request_id",
            str(uuid4()),
        )

    @application.exception_handler(StarletteHTTPException)
    async def http_exception_handler(
        request: Request,
        exc: StarletteHTTPException,
    ) -> JSONResponse:
        messages = {
            400: "The request could not be processed.",
            401: "Authentication is required.",
            403: "The requested operation is forbidden.",
            404: "The requested resource was not found.",
            409: "The request conflicts with the current resource state.",
            429: "Too many requests.",
        }

        request_id = get_request_id(request)

        payload = ErrorResponse(
            error={
                "code": (
                    "NOT_FOUND"
                    if exc.status_code == 404
                    else "HTTP_ERROR"
                ),
                "message": messages.get(
                    exc.status_code,
                    "The HTTP request could not be completed.",
                ),
            },
            request_id=request_id,
        )

        headers = dict(exc.headers or {})
        headers["X-Request-ID"] = request_id

        return JSONResponse(
            status_code=exc.status_code,
            content=payload.model_dump(),
            headers=headers,
        )

    @application.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        request_id = get_request_id(request)

        payload = ErrorResponse(
            error={
                "code": "REQUEST_VALIDATION_ERROR",
                "message": "Request validation failed.",
            },
            request_id=request_id,
        )

        return JSONResponse(
            status_code=422,
            content=payload.model_dump(),
            headers={"X-Request-ID": request_id},
        )

    @application.exception_handler(Exception)
    async def unexpected_exception_handler(
        request: Request,
        exc: Exception,
    ) -> JSONResponse:
        request_id = get_request_id(request)

        payload = ErrorResponse(
            error={
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred.",
            },
            request_id=request_id,
        )

        return JSONResponse(
            status_code=500,
            content=payload.model_dump(),
            headers={"X-Request-ID": request_id},
        )

    @application.get(
        "/health",
        response_model=HealthResponse,
    )
    async def health() -> HealthResponse:
        return HealthResponse(
            status="healthy",
            application="engineering-agent",
            version=APPLICATION_VERSION,
        )

    @application.get(
        f"/{API_VERSION}/status",
        response_model=ApplicationStatusResponse,
    )
    async def status(
        request: Request,
    ) -> ApplicationStatusResponse:
        container = getattr(
            request.app.state,
            "container",
            None,
        )

        return ApplicationStatusResponse(
            application="engineering-agent",
            version=APPLICATION_VERSION,
            api_version="v1",
            initialized=container is not None,
            execution_enabled=False,
            workspace_manager_initialized=False,
            approval_service_initialized=(
                container is not None
                and container.approval_service is not None
            ),
        )

    return application


# Importing this module does not require environment variables.
# Configuration is resolved when the ASGI application starts.
app = create_app()