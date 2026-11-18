from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.app.engineering_agent.config import (
    EngineeringAgentConfigurationError,
    EngineeringAgentSettings,
)
from backend.app.engineering_agent.composition.container import (
    EngineeringAgentContainer,
)
from backend.app.engineering_agent.main import create_app


@pytest.fixture
def settings(tmp_path: Path) -> EngineeringAgentSettings:
    repository = tmp_path / "repository"
    workspace = tmp_path / "workspaces"
    data = tmp_path / "data"

    repository.mkdir()

    return EngineeringAgentSettings(
        repository_path=repository,
        workspace_root=workspace,
        data_root=data,
    )


def test_settings_resolve_paths(
    settings: EngineeringAgentSettings,
) -> None:
    assert settings.repository_path.is_absolute()
    assert settings.workspace_root.is_absolute()
    assert settings.data_root.is_absolute()


def test_settings_reject_workspace_inside_repository(
    tmp_path: Path,
) -> None:
    repository = tmp_path / "repository"
    repository.mkdir()

    with pytest.raises(EngineeringAgentConfigurationError):
        EngineeringAgentSettings(
            repository_path=repository,
            workspace_root=repository / "workspaces",
            data_root=tmp_path / "data",
        )


def test_settings_reject_data_inside_repository(
    tmp_path: Path,
) -> None:
    repository = tmp_path / "repository"
    repository.mkdir()

    with pytest.raises(EngineeringAgentConfigurationError):
        EngineeringAgentSettings(
            repository_path=repository,
            workspace_root=tmp_path / "workspaces",
            data_root=repository / "data",
        )


def test_settings_reject_overlapping_data_and_workspace(
    tmp_path: Path,
) -> None:
    repository = tmp_path / "repository"
    shared = tmp_path / "shared"

    repository.mkdir()

    with pytest.raises(EngineeringAgentConfigurationError):
        EngineeringAgentSettings(
            repository_path=repository,
            workspace_root=shared,
            data_root=shared / "data",
        )


def test_settings_reject_non_finite_database_timeout(
    tmp_path: Path,
) -> None:
    repository = tmp_path / "repository"
    repository.mkdir()

    with pytest.raises(EngineeringAgentConfigurationError):
        EngineeringAgentSettings(
            repository_path=repository,
            workspace_root=tmp_path / "workspaces",
            data_root=tmp_path / "data",
            database_timeout_seconds=float("inf"),
        )


def test_container_builds_shared_workflow_services(
    settings: EngineeringAgentSettings,
) -> None:
    container = EngineeringAgentContainer.build(settings)

    try:
        assert container.workflow_store is not None
        assert container.work_item_store is not None
        assert container.worker_registry_store is not None

        assert container.state_router is not None
        assert container.worker_matcher is not None
        assert container.bounded_dispatcher is not None
        assert container.runtime_coordinator is not None
        assert container.orchestrator is not None

        assert settings.workflow_database_path.exists()

    finally:
        container.close()


def test_container_does_not_initialize_workspace_manager(
    settings: EngineeringAgentSettings,
) -> None:
    container = EngineeringAgentContainer.build(settings)

    try:
        assert not settings.workspace_root.exists()
        assert not (
            settings.workspace_root / ".gagf-manager"
        ).exists()

    finally:
        container.close()


def test_application_health_endpoint(
    settings: EngineeringAgentSettings,
) -> None:
    application = create_app(settings)

    with TestClient(application) as client:
        response = client.get("/health")

    assert response.status_code == 200

    payload = response.json()

    assert payload["status"] == "healthy"
    assert payload["application"] == "engineering-agent"


def test_application_status_endpoint(
    settings: EngineeringAgentSettings,
) -> None:
    application = create_app(settings)

    with TestClient(application) as client:
        response = client.get("/v1/status")

    assert response.status_code == 200

    payload = response.json()

    assert payload["application"] == "engineering-agent"
    assert payload["initialized"] is True
    assert payload["execution_enabled"] is False
    assert payload["workspace_manager_initialized"] is False
    assert payload["approval_service_initialized"] is False