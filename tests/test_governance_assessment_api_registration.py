from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest

from backend.app.gagf.governance_assessment_api_registration import (
    ASSESSMENT_API_REGISTERED_STATE_KEY,
    AssessmentApiRegistrationError,
    register_governance_assessment_api,
)
from backend.app.gagf.governance_assessment_application import (
    GovernanceAssessmentApplicationService,
)
from backend.app.gagf.governance_assessment_repository import (
    GovernanceAssessmentRepository,
)


def route_paths(app: FastAPI) -> tuple[str, ...]:
    return tuple(route.path for route in app.routes)


def test_registration_adds_assessment_routes(tmp_path):
    app = FastAPI()

    register_governance_assessment_api(
        app=app,
        database_path=tmp_path / "assessment.sqlite3",
    )

    assert "/api/v1/governance-assessments/execute" in (
        route_paths(app)
    )


def test_registration_returns_application_service(tmp_path):
    app = FastAPI()

    service = register_governance_assessment_api(
        app=app,
        database_path=tmp_path / "assessment.sqlite3",
    )

    assert isinstance(
        service,
        GovernanceAssessmentApplicationService,
    )


def test_registration_stores_service_on_app_state(tmp_path):
    app = FastAPI()

    service = register_governance_assessment_api(
        app=app,
        database_path=tmp_path / "assessment.sqlite3",
    )

    assert app.state.governance_assessment_service is service


def test_registration_stores_repository_on_app_state(tmp_path):
    app = FastAPI()

    register_governance_assessment_api(
        app=app,
        database_path=tmp_path / "assessment.sqlite3",
    )

    assert isinstance(
        app.state.governance_assessment_repository,
        GovernanceAssessmentRepository,
    )


def test_registration_sets_state_flag(tmp_path):
    app = FastAPI()

    register_governance_assessment_api(
        app=app,
        database_path=tmp_path / "assessment.sqlite3",
    )

    assert getattr(
        app.state,
        ASSESSMENT_API_REGISTERED_STATE_KEY,
    ) is True


def test_registration_is_idempotent(tmp_path):
    app = FastAPI()
    database_path = tmp_path / "assessment.sqlite3"

    first_service = register_governance_assessment_api(
        app=app,
        database_path=database_path,
    )
    first_route_paths = route_paths(app)

    second_service = register_governance_assessment_api(
        app=app,
        database_path=database_path,
    )

    assert first_service is second_service
    assert route_paths(app) == first_route_paths


def test_registration_accepts_existing_repository(tmp_path):
    app = FastAPI()
    repository = GovernanceAssessmentRepository(
        tmp_path / "assessment.sqlite3"
    )

    register_governance_assessment_api(
        app=app,
        repository=repository,
    )

    assert (
        app.state.governance_assessment_repository
        is repository
    )


def test_registration_creates_parent_directory(tmp_path):
    app = FastAPI()
    database_path = (
        tmp_path
        / "nested"
        / "data"
        / "assessment.sqlite3"
    )

    register_governance_assessment_api(
        app=app,
        database_path=database_path,
    )

    assert database_path.parent.exists()
    assert database_path.exists()


def test_registration_rejects_repository_and_path(tmp_path):
    app = FastAPI()
    repository = GovernanceAssessmentRepository(
        tmp_path / "first.sqlite3"
    )

    with pytest.raises(
        AssessmentApiRegistrationError,
        match="not both",
    ):
        register_governance_assessment_api(
            app=app,
            repository=repository,
            database_path=tmp_path / "second.sqlite3",
        )


def test_registration_requires_storage_configuration():
    app = FastAPI()

    with pytest.raises(
        AssessmentApiRegistrationError,
        match="required",
    ):
        register_governance_assessment_api(app=app)


def test_registered_list_endpoint_is_reachable(tmp_path):
    app = FastAPI()
    register_governance_assessment_api(
        app=app,
        database_path=tmp_path / "assessment.sqlite3",
    )
    client = TestClient(app)

    response = client.get(
        "/api/v1/governance-assessments",
        params={"tenant_id": "tenant-alpha"},
        headers={
            "X-Tenant-ID": "tenant-alpha",
            "X-Actor-ID": "actor-001",
            "X-Actor-Roles": "assessment:read",
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "items": [],
        "count": 0,
    }


def test_registered_unknown_assessment_returns_404(tmp_path):
    app = FastAPI()
    register_governance_assessment_api(
        app=app,
        database_path=tmp_path / "assessment.sqlite3",
    )
    client = TestClient(app)

    response = client.get(
        "/api/v1/governance-assessments/"
        "tenant-alpha/client-acme/"
        "engagement-001/missing",
        headers={
            "X-Tenant-ID": "tenant-alpha",
            "X-Actor-ID": "actor-001",
            "X-Actor-Roles": "assessment:read",
        },
    )

    assert response.status_code == 404


def test_database_path_can_be_a_string(tmp_path):
    app = FastAPI()
    database_path = str(
        tmp_path / "assessment.sqlite3"
    )

    register_governance_assessment_api(
        app=app,
        database_path=database_path,
    )

    assert Path(database_path).exists()


