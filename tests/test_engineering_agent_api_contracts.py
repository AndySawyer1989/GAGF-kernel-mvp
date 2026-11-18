from pathlib import Path

import pytest
from pydantic import ValidationError
from fastapi.testclient import TestClient

from backend.app.engineering_agent.config import (
    EngineeringAgentSettings,
)
from backend.app.engineering_agent.contracts.v1 import (
    ApplicationStatusResponse,
    ErrorResponse,
    HealthResponse,
)
from backend.app.engineering_agent.main import create_app


@pytest.fixture
def settings(tmp_path: Path) -> EngineeringAgentSettings:
    repository = tmp_path / "repository"
    repository.mkdir()

    return EngineeringAgentSettings(
        repository_path=repository,
        workspace_root=tmp_path / "workspaces",
        data_root=tmp_path / "data",
    )


def test_health_contract() -> None:
    response = HealthResponse(
        status="healthy",
        application="engineering-agent",
        version="0.1.0",
    )

    assert response.status == "healthy"
    assert response.application == "engineering-agent"


def test_status_contract() -> None:
    response = ApplicationStatusResponse(
        application="engineering-agent",
        version="0.1.0",
        api_version="v1",
        initialized=True,
        execution_enabled=False,
        workspace_manager_initialized=False,
        approval_service_initialized=False,
    )

    assert response.api_version == "v1"
    assert response.initialized is True
    assert response.execution_enabled is False


def test_contract_rejects_unexpected_fields() -> None:
    with pytest.raises(ValidationError):
        HealthResponse(
            status="healthy",
            application="engineering-agent",
            version="0.1.0",
            unexpected_field=True,
        )


def test_error_contract() -> None:
    response = ErrorResponse(
        error={
            "code": "CONFIGURATION_ERROR",
            "message": "Invalid application configuration",
        },
        request_id="test-request-001",
    )

    assert response.error.code == "CONFIGURATION_ERROR"
    assert response.request_id == "test-request-001"


def test_health_endpoint_uses_contract(
    settings: EngineeringAgentSettings,
) -> None:
    application = create_app(settings)

    with TestClient(application) as client:
        response = client.get("/health")

    assert response.status_code == 200

    validated = HealthResponse.model_validate(
        response.json()
    )

    assert validated.application == "engineering-agent"


def test_status_endpoint_uses_contract(
    settings: EngineeringAgentSettings,
) -> None:
    application = create_app(settings)

    with TestClient(application) as client:
        response = client.get("/v1/status")

    assert response.status_code == 200

    validated = ApplicationStatusResponse.model_validate(
        response.json()
    )

    assert validated.initialized is True
    assert validated.execution_enabled is False


def test_openapi_exposes_versioned_contracts(
    settings: EngineeringAgentSettings,
) -> None:
    application = create_app(settings)

    with TestClient(application) as client:
        response = client.get("/openapi.json")

    assert response.status_code == 200

    schemas = response.json()["components"]["schemas"]

    assert "HealthResponse" in schemas
    assert "ApplicationStatusResponse" in schemas


def test_http_error_uses_standard_error_contract(
    settings: EngineeringAgentSettings,
) -> None:
    application = create_app(settings)

    with TestClient(application) as client:
        response = client.get("/route-that-does-not-exist")

    assert response.status_code == 404

    payload = ErrorResponse.model_validate(response.json())

    assert payload.error.code == "NOT_FOUND"
    assert payload.error.message
    assert payload.request_id == response.headers["X-Request-ID"]


def test_request_validation_error_uses_standard_contract(
    settings: EngineeringAgentSettings,
) -> None:
    application = create_app(settings)

    @application.get("/test/validation")
    async def validation_endpoint(quantity: int):
        return {"quantity": quantity}

    with TestClient(application) as client:
        response = client.get(
            "/test/validation",
            params={"quantity": "not-an-integer"},
        )

    assert response.status_code == 422

    payload = ErrorResponse.model_validate(response.json())

    assert payload.error.code == "REQUEST_VALIDATION_ERROR"
    assert payload.request_id == response.headers["X-Request-ID"]


def test_unexpected_exception_uses_standard_contract(
    settings: EngineeringAgentSettings,
) -> None:
    application = create_app(settings)

    @application.get("/test/failure")
    async def failure_endpoint():
        raise RuntimeError("internal diagnostic detail")

    with TestClient(
        application,
        raise_server_exceptions=False,
    ) as client:
        response = client.get("/test/failure")

    assert response.status_code == 500

    payload = ErrorResponse.model_validate(response.json())

    assert payload.error.code == "INTERNAL_SERVER_ERROR"
    assert payload.error.message == "An unexpected error occurred."
    assert "internal diagnostic detail" not in response.text
    assert payload.request_id == response.headers["X-Request-ID"]


def test_successful_response_includes_request_id(
    settings: EngineeringAgentSettings,
) -> None:
    application = create_app(settings)

    with TestClient(application) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.headers["X-Request-ID"]

    payload = HealthResponse.model_validate(response.json())

    assert payload.status == "healthy"