import subprocess
from pathlib import Path

import pytest

from backend.app.gagf.governance_agent_workspace_manager import (
    AgentWorkspaceConflictError,
    AgentWorkspaceManager,
    AgentWorkspaceNotFoundError,
    AgentWorkspaceValidationError,
)


def run_git(repository: Path, *arguments: str) -> str:
    result = subprocess.run(
        ["git", *arguments],
        cwd=str(repository),
        capture_output=True,
        text=True,
        check=False,
        shell=False,
    )
    if result.returncode != 0:
        raise AssertionError(result.stderr or result.stdout)
    return result.stdout.strip()


@pytest.fixture
def repository(tmp_path):
    root = tmp_path / "repository"
    root.mkdir()

    run_git(root, "init")
    run_git(root, "config", "user.name", "Workspace Test")
    run_git(root, "config", "user.email", "workspace@example.test")

    (root / "README.md").write_text(
        "workspace test\n",
        encoding="utf-8",
    )

    run_git(root, "add", "README.md")
    run_git(root, "commit", "-m", "initial commit")

    return root


@pytest.fixture
def manager(repository, tmp_path):
    return AgentWorkspaceManager(
        repository,
        tmp_path / "managed-workspaces",
    )


def test_manager_rejects_workspace_root_inside_repository(repository):
    with pytest.raises(AgentWorkspaceValidationError):
        AgentWorkspaceManager(
            repository,
            repository / "agent-workspaces",
        )


def test_manager_rejects_workspace_root_equal_to_repository(repository):
    with pytest.raises(AgentWorkspaceValidationError):
        AgentWorkspaceManager(repository, repository)


def test_allocation_creates_dedicated_worktree_and_branch(manager):
    record = manager.allocate_workspace(
        tenant_id="tenant-a",
        work_item_id="work-item-001",
    )

    assert record.state == "ACTIVE"
    assert record.tenant_id == "tenant-a"
    assert record.work_item_id == "work-item-001"
    assert record.workspace_id.startswith("ws_")
    assert record.branch_name.startswith("agent-work/")
    assert Path(record.workspace_path).is_dir()
    assert (Path(record.workspace_path) / "README.md").is_file()

    branch = run_git(
        Path(record.workspace_path),
        "branch",
        "--show-current",
    )
    assert branch == record.branch_name


def test_allocation_is_deterministic_and_duplicate_is_rejected(manager):
    first = manager.allocate_workspace(
        tenant_id="tenant-a",
        work_item_id="work-item-001",
    )

    with pytest.raises(AgentWorkspaceConflictError):
        manager.allocate_workspace(
            tenant_id="tenant-a",
            work_item_id="work-item-001",
        )

    persisted = manager.get_workspace(
        tenant_id="tenant-a",
        work_item_id="work-item-001",
    )

    assert persisted.workspace_id == first.workspace_id
    assert persisted.workspace_path == first.workspace_path


def test_same_work_item_identifier_is_isolated_between_tenants(manager):
    tenant_a = manager.allocate_workspace(
        tenant_id="tenant-a",
        work_item_id="shared-item",
    )
    tenant_b = manager.allocate_workspace(
        tenant_id="tenant-b",
        work_item_id="shared-item",
    )

    assert tenant_a.workspace_id != tenant_b.workspace_id
    assert tenant_a.workspace_path != tenant_b.workspace_path
    assert Path(tenant_a.workspace_path).is_dir()
    assert Path(tenant_b.workspace_path).is_dir()


def test_tenant_cannot_read_another_tenants_workspace(manager):
    manager.allocate_workspace(
        tenant_id="tenant-a",
        work_item_id="work-item-001",
    )

    with pytest.raises(AgentWorkspaceNotFoundError):
        manager.get_workspace(
            tenant_id="tenant-b",
            work_item_id="work-item-001",
        )


def test_listing_is_tenant_scoped(manager):
    manager.allocate_workspace(
        tenant_id="tenant-a",
        work_item_id="item-a",
    )
    manager.allocate_workspace(
        tenant_id="tenant-b",
        work_item_id="item-b",
    )

    records = manager.list_workspaces(tenant_id="tenant-a")

    assert len(records) == 1
    assert records[0].work_item_id == "item-a"


def test_invalid_identifiers_are_rejected(manager):
    with pytest.raises(AgentWorkspaceValidationError):
        manager.allocate_workspace(
            tenant_id=" ",
            work_item_id="item-a",
        )

    with pytest.raises(AgentWorkspaceValidationError):
        manager.allocate_workspace(
            tenant_id="tenant-a",
            work_item_id="x" * 201,
        )


def test_release_removes_clean_worktree_and_preserves_record(manager):
    created = manager.allocate_workspace(
        tenant_id="tenant-a",
        work_item_id="work-item-001",
    )

    released = manager.release_workspace(
        tenant_id="tenant-a",
        work_item_id="work-item-001",
    )

    assert released.state == "RELEASED"
    assert not Path(created.workspace_path).exists()

    historical = manager.list_workspaces(
        tenant_id="tenant-a",
        include_released=True,
    )
    assert len(historical) == 1
    assert historical[0].state == "RELEASED"


def test_release_does_not_force_delete_modified_worktree(manager):
    created = manager.allocate_workspace(
        tenant_id="tenant-a",
        work_item_id="work-item-001",
    )

    marker = Path(created.workspace_path) / "uncommitted.txt"
    marker.write_text("preserve this file\n", encoding="utf-8")

    with pytest.raises(Exception):
        manager.release_workspace(
            tenant_id="tenant-a",
            work_item_id="work-item-001",
        )

    assert marker.is_file()
    assert manager.get_workspace(
        tenant_id="tenant-a",
        work_item_id="work-item-001",
    ).state == "ACTIVE"


def test_release_cannot_be_repeated(manager):
    manager.allocate_workspace(
        tenant_id="tenant-a",
        work_item_id="work-item-001",
    )

    manager.release_workspace(
        tenant_id="tenant-a",
        work_item_id="work-item-001",
    )

    with pytest.raises(AgentWorkspaceConflictError):
        manager.release_workspace(
            tenant_id="tenant-a",
            work_item_id="work-item-001",
        )


def test_list_limit_is_validated(manager):
    for invalid_limit in (0, -1, 501, True, 1.5):
        with pytest.raises(AgentWorkspaceValidationError):
            manager.list_workspaces(
                tenant_id="tenant-a",
                limit=invalid_limit,
            )
