from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager
from time import perf_counter
from typing import AsyncIterator

from fastapi import FastAPI, HTTPException, Request
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
    RuntimeBoundedDispatchResponse,
    RuntimeDispatchOutcomeResponse,
    RuntimeDispatchRequest,
    RuntimeDispatchResponse,
    RuntimeRoutingDecisionResponse,
)
from backend.app.engineering_agent.runtime_identity import (
    AuthenticatedRuntimePrincipal,
    RuntimeAuthenticationError,
    RuntimeIdentityError,
    RuntimeIdentityProvider,
    RuntimeIdentityProviderError,
)

from backend.app.engineering_agent.logging import (
    configure_logging,
    get_request_id,
    new_request_id,
    reset_request_id,
    set_request_id,
)

from backend.app.engineering_agent.tracing import (
    new_trace_context,
    reset_trace_context,
    set_trace_context,
)

APPLICATION_VERSION = "0.1.0"
API_VERSION = "v1"

logger = logging.getLogger("engineering_agent")


def create_app(
    settings: EngineeringAgentSettings | None = None,
    *,
    runtime_identity_provider: RuntimeIdentityProvider | None = None,
) -> FastAPI:

    @asynccontextmanager
    async def lifespan(
        application: FastAPI,
    ) -> AsyncIterator[None]:

        resolved_settings = settings or (
            EngineeringAgentSettings.from_environment()
        )

        configure_logging(
            application="engineering-agent",
        )

        logger.info(
            "Engineering Agent starting",
            extra={"event": "application_starting"},
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

            logger.info(
                "Engineering Agent stopping",
                extra={"event": "application_stopping"},
            )

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
        request_id = new_request_id()
        token = set_request_id(request_id)

        trace_context = new_trace_context(
            request.headers.get("traceparent")
        )
        trace_token = set_trace_context(trace_context)

        started_at = perf_counter()

        request.state.request_id = request_id
        request.state.trace_id = trace_context.trace_id
        request.state.span_id = trace_context.span_id

        try:
            response = await call_next(request)

            duration_ms = round(
                (perf_counter() - started_at) * 1000,
                3,
            )

            logger.info(
                "HTTP request completed",
                extra={
                    "event": "http_request_completed",
                    "http_method": request.method,
                    "http_path": request.url.path,
                    "http_status": response.status_code,
                    "duration_ms": duration_ms,
                },
            )

            response.headers["X-Request-ID"] = request_id
            response.headers["traceparent"] = (
                trace_context.to_traceparent()
            )

            return response
        finally:
            reset_trace_context(trace_token)
            reset_request_id(token)

    def request_error_response(
        *,
        status_code: int,
        code: str,
        message: str,
        request_id: str,
        headers: dict[str, str] | None = None,
    ) -> JSONResponse:
        payload = ErrorResponse(
            error={
                "code": code,
                "message": message,
            },
            request_id=request_id,
        )

        response_headers = dict(headers or {})
        response_headers["X-Request-ID"] = request_id

        return JSONResponse(
            status_code=status_code,
            content=payload.model_dump(),
            headers=response_headers,
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
            503: "The requested service is not currently available.",
        }

        request_id = get_request_id()

        logger.warning(
            "HTTP request rejected",
            extra={
                "event": "http_error",
                "http_status": exc.status_code,
                "http_path": request.url.path,
            },
        )

        return request_error_response(
            status_code=exc.status_code,
            code=(
                "NOT_FOUND"
                if exc.status_code == 404
                else (
                    "SERVICE_UNAVAILABLE"
                    if exc.status_code == 503
                    else "HTTP_ERROR"
                )
            ),
            message=messages.get(
                exc.status_code,
                "The HTTP request could not be completed.",
            ),
            request_id=request_id,
            headers=exc.headers,
        )

    @application.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        request_id = get_request_id()

        logger.warning(
            "Request validation failed",
            extra={
                "event": "request_validation_failed",
                "http_path": request.url.path,
            },
        )

        return request_error_response(
            status_code=422,
            code="REQUEST_VALIDATION_ERROR",
            message="Request validation failed.",
            request_id=request_id,
        )

    @application.exception_handler(Exception)
    async def unexpected_exception_handler(
        request: Request,
        exc: Exception,
    ) -> JSONResponse:
        request_id = get_request_id()

        logger.exception(
            "Unhandled application exception",
            extra={
                "event": "unhandled_exception",
                "http_path": request.url.path,
                "http_method": request.method,
            },
        )

        return request_error_response(
            status_code=500,
            code="INTERNAL_SERVER_ERROR",
            message="An unexpected error occurred.",
            request_id=request_id,
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

    @application.post(
        f"/{API_VERSION}/workflows/{{workflow_id}}/dispatch",
        response_model=RuntimeDispatchResponse,
    )
    async def dispatch_workflow(
        workflow_id: str,
        payload: RuntimeDispatchRequest,
        request: Request,
    ) -> RuntimeDispatchResponse:
        if runtime_identity_provider is None:
            raise HTTPException(status_code=503)

        try:
            principal = await runtime_identity_provider.authenticate(
                authentication_context=request,
            )
        except RuntimeAuthenticationError:
            raise HTTPException(status_code=401) from None
        except RuntimeIdentityProviderError:
            raise HTTPException(status_code=503) from None
        except RuntimeIdentityError:
            raise HTTPException(status_code=503) from None

        if not isinstance(
            principal,
            AuthenticatedRuntimePrincipal,
        ):
            raise HTTPException(status_code=503)

        if "runtime:dispatch" not in principal.permissions:
            raise HTTPException(status_code=403)

        container = getattr(
            request.app.state,
            "container",
            None,
        )

        if container is None:
            raise HTTPException(status_code=503)

        result = await asyncio.to_thread(
            container.runtime_operations.dispatch_workflow,
            tenant_id=principal.tenant_id,
            workflow_id=workflow_id,
            dispatch_cycle_id=payload.dispatch_cycle_id,
            lease_seconds=payload.lease_seconds,
            max_candidates=payload.max_candidates,
            max_claims=payload.max_claims,
        )

        routing = result.routing_decision

        routing_response = RuntimeRoutingDecisionResponse(
            workflow_id=routing.workflow_id,
            workflow_type=routing.workflow_type,
            current_state=routing.current_state.value,
            action=routing.action.value,
            allowed_transitions=tuple(
                state.value
                for state in routing.allowed_transitions
            ),
            requires_human_approval=routing.requires_human_approval,
            terminal=routing.terminal,
            reason=routing.reason,
        )

        dispatch_response = None

        if result.dispatch_result is not None:
            dispatch = result.dispatch_result
            sanitized_outcomes = []

            for outcome in dispatch.outcomes:
                status = outcome.status
                raw_reasons = tuple(outcome.reason_codes or ())

                if status == "unmatched":
                    reason_codes = ("no_eligible_worker",)
                elif status == "rejected":
                    if "missing_capability_policy" in raw_reasons:
                        reason_codes = ("missing_capability_policy",)
                    elif any(
                        str(reason).startswith("claim_conflict:")
                        for reason in raw_reasons
                    ):
                        reason_codes = ("claim_conflict",)
                    else:
                        reason_codes = ("rejected",)
                else:
                    reason_codes = ()

                sanitized_outcomes.append(
                    RuntimeDispatchOutcomeResponse(
                        work_item_id=outcome.work_item_id,
                        status=status,
                        reason_codes=reason_codes,
                    )
                )

            dispatch_response = RuntimeBoundedDispatchResponse(
                dispatch_cycle_id=dispatch.dispatch_cycle_id,
                dispatched_at=dispatch.dispatched_at,
                candidate_limit=dispatch.candidate_limit,
                claim_limit=dispatch.claim_limit,
                candidate_count=dispatch.candidate_count,
                scanned_count=dispatch.scanned_count,
                claimed_count=dispatch.claimed_count,
                outcomes=tuple(sanitized_outcomes),
            )

        return RuntimeDispatchResponse(
            routing_decision=routing_response,
            dispatch_performed=dispatch_response is not None,
            dispatch_result=dispatch_response,
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
