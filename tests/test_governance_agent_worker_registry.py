from datetime import datetime, timedelta, timezone

import pytest

from backend.app.gagf.governance_agent_worker_registry_contract import (
    AgentWorkerMatchError,
    AgentWorkerRegistrationNotFoundError,
    AgentWorkerRegistryError,
)
from backend.app.gagf.governance_agent_worker_registry_store import (
    AgentWorkerRegistryStore,
)
from backend.app.gagf.governance_agent_worker_matcher import (
    AgentWorkerMatcher,
)


TEST_NOW = datetime(2026, 11, 9, 18, 0, tzinfo=timezone.utc)


@pytest.fixture
def registry(tmp_path):
    return AgentWorkerRegistryStore(tmp_path / "agent_workflows.db")


def register(
    registry,
    *,
    tenant_id="tenant-a",
    worker_id="worker-a",
    worker_type="engineering",
    version="1.0.0",
    task_types=("code.review",),
    capabilities=("runtime.python", "tool.pytest"),
    enabled=True,
    now=TEST_NOW,
):
    return registry.register_worker(
        tenant_id=tenant_id,
        worker_id=worker_id,
        worker_type=worker_type,
        version=version,
        supported_task_types=task_types,
        capabilities=capabilities,
        enabled=enabled,
        now=now,
    )


def test_registration_creates_revision_one_and_normalizes_collections(
    registry,
):
    record = register(
        registry,
        task_types=("code.review", "code.change", "code.review"),
        capabilities=("tool.pytest", "runtime.python", "tool.pytest"),
    )

    assert record.tenant_id == "tenant-a"
    assert record.worker_id == "worker-a"
    assert record.registration_revision == 1
    assert record.supported_task_types == (
        "code.change",
        "code.review",
    )
    assert record.capabilities == (
        "runtime.python",
        "tool.pytest",
    )
    assert record.created_at == TEST_NOW
    assert record.updated_at == TEST_NOW


def test_identical_registration_replay_does_not_increment_revision(
    registry,
):
    original = register(registry)

    replay = register(
        registry,
        now=TEST_NOW + timedelta(minutes=5),
    )

    assert replay == original
    assert replay.registration_revision == 1
    assert replay.created_at == original.created_at
    assert replay.updated_at == original.updated_at


def test_changed_registration_increments_revision_and_preserves_creation(
    registry,
):
    original = register(registry)

    updated = register(
        registry,
        version="2.0.0",
        capabilities=("runtime.python", "tool.pytest", "expertise.security_review"),
        now=TEST_NOW + timedelta(minutes=5),
    )

    assert updated.registration_revision == 2
    assert updated.created_at == original.created_at
    assert updated.updated_at == TEST_NOW + timedelta(minutes=5)
    assert updated.version == "2.0.0"
    assert updated.capabilities == (
        "expertise.security_review",
        "runtime.python",
        "tool.pytest",
    )


def test_registration_can_be_disabled_and_listed(registry):
    register(registry, worker_id="worker-a")
    register(
        registry,
        worker_id="worker-b",
        enabled=False,
    )

    all_workers = registry.list_workers(tenant_id="tenant-a")
    enabled_workers = registry.list_workers(
        tenant_id="tenant-a",
        include_disabled=False,
    )

    assert [worker.worker_id for worker in all_workers] == [
        "worker-a",
        "worker-b",
    ]
    assert [worker.worker_id for worker in enabled_workers] == [
        "worker-a",
    ]


def test_same_worker_id_is_isolated_between_tenants(registry):
    tenant_a = register(
        registry,
        tenant_id="tenant-a",
        worker_id="shared-worker",
        version="1.0.0",
    )
    tenant_b = register(
        registry,
        tenant_id="tenant-b",
        worker_id="shared-worker",
        version="2.0.0",
    )

    assert tenant_a.version == "1.0.0"
    assert tenant_b.version == "2.0.0"

    assert registry.get_worker(
        tenant_id="tenant-a",
        worker_id="shared-worker",
    ).version == "1.0.0"

    assert registry.get_worker(
        tenant_id="tenant-b",
        worker_id="shared-worker",
    ).version == "2.0.0"

    with pytest.raises(AgentWorkerRegistrationNotFoundError):
        registry.get_worker(
            tenant_id="tenant-c",
            worker_id="shared-worker",
        )

    assert len(registry.list_workers(tenant_id="tenant-a")) == 1
    assert len(registry.list_workers(tenant_id="tenant-b")) == 1
    assert registry.list_workers(tenant_id="tenant-c") == ()


def test_matcher_selects_lexicographically_first_eligible_worker(registry):
    register(
        registry,
        worker_id="worker-z",
        capabilities=("runtime.python", "tool.pytest", "expertise.security_review"),
    )
    register(
        registry,
        worker_id="worker-b",
        capabilities=("runtime.python", "tool.pytest", "expertise.security_review"),
    )
    register(
        registry,
        worker_id="worker-a",
        capabilities=("runtime.python", "tool.pytest", "expertise.security_review"),
    )

    result = AgentWorkerMatcher(registry).match(
        tenant_id="tenant-a",
        task_type="code.review",
        required_capabilities=("tool.pytest", "runtime.python"),
    )

    assert result.matched is True
    assert result.selected_worker_id == "worker-a"
    assert result.selected_registration_revision == 1
    assert result.required_capabilities == (
        "runtime.python",
        "tool.pytest",
    )
    assert result.registered_worker_count == 3
    assert {
        rejection.worker_id: rejection.reasons
        for rejection in result.rejections
    } == {
        "worker-b": ("deterministic_tie_break",),
        "worker-z": ("deterministic_tie_break",),
    }


def test_matcher_rejects_disabled_worker(registry):
    register(
        registry,
        worker_id="worker-disabled",
        enabled=False,
    )

    result = AgentWorkerMatcher(registry).match(
        tenant_id="tenant-a",
        task_type="code.review",
    )

    assert result.matched is False
    assert result.selected_worker is None
    assert result.registered_worker_count == 1
    assert result.rejections[0].worker_id == "worker-disabled"
    assert result.rejections[0].reasons == ("worker_disabled",)


def test_matcher_rejects_unsupported_task_type(registry):
    register(
        registry,
        task_types=("code.change",),
    )

    result = AgentWorkerMatcher(registry).match(
        tenant_id="tenant-a",
        task_type="code.review",
    )

    assert result.matched is False
    assert result.rejections[0].reasons == ("unsupported_task_type",)


def test_matcher_rejects_missing_required_capabilities(registry):
    register(
        registry,
        capabilities=("runtime.python",),
    )

    result = AgentWorkerMatcher(registry).match(
        tenant_id="tenant-a",
        task_type="code.review",
        required_capabilities=("runtime.python", "tool.pytest", "expertise.security_review"),
    )

    assert result.matched is False
    assert result.rejections[0].reasons == (
        "missing_capabilities:expertise.security_review,tool.pytest",
    )


def test_matcher_reports_multiple_rejection_reasons(registry):
    register(
        registry,
        worker_id="worker-disabled",
        enabled=False,
        task_types=("code.change",),
        capabilities=(),
    )

    result = AgentWorkerMatcher(registry).match(
        tenant_id="tenant-a",
        task_type="code.review",
        required_capabilities=("tool.pytest",),
    )

    assert result.matched is False
    assert result.rejections[0].reasons == (
        "missing_capabilities:tool.pytest",
        "unsupported_task_type",
        "worker_disabled",
    )


def test_matcher_does_not_select_workers_from_another_tenant(registry):
    register(
        registry,
        tenant_id="tenant-b",
        worker_id="tenant-b-worker",
    )

    result = AgentWorkerMatcher(registry).match(
        tenant_id="tenant-a",
        task_type="code.review",
    )

    assert result.matched is False
    assert result.registered_worker_count == 0
    assert result.rejections == ()


def test_matcher_normalizes_and_deduplicates_required_capabilities(
    registry,
):
    register(
        registry,
        capabilities=("runtime.python", "tool.pytest"),
    )

    result = AgentWorkerMatcher(registry).match(
        tenant_id="tenant-a",
        task_type="code.review",
        required_capabilities=(" tool.pytest ", "runtime.python", "tool.pytest"),
    )

    assert result.matched is True
    assert result.required_capabilities == (
        "runtime.python",
        "tool.pytest",
    )


def test_matcher_rejects_invalid_capability_generator(registry):
    matcher = AgentWorkerMatcher(registry)

    invalid_capabilities = (
        capability
        for capability in ("runtime.python", "", "tool.pytest")
    )

    with pytest.raises(AgentWorkerMatchError):
        matcher.match(
            tenant_id="tenant-a",
            task_type="code.review",
            required_capabilities=invalid_capabilities,
        )


@pytest.mark.parametrize(
    "invalid_capabilities",
    [
        "runtime.python",
        b"runtime.python",
        ("runtime.python", ""),
        ("runtime.python", None),
        123,
    ],
)
def test_matcher_rejects_invalid_capability_inputs(
    registry,
    invalid_capabilities,
):
    with pytest.raises(AgentWorkerMatchError):
        AgentWorkerMatcher(registry).match(
            tenant_id="tenant-a",
            task_type="code.review",
            required_capabilities=invalid_capabilities,
        )


def test_registration_rejects_naive_timestamp(registry):
    with pytest.raises(AgentWorkerRegistryError):
        register(
            registry,
            now=datetime(2026, 11, 9, 18, 0),
        )


def test_registration_update_rejects_time_before_creation(registry):
    register(registry)

    with pytest.raises(Exception) as exc_info:
        register(
            registry,
            version="2.0.0",
            now=TEST_NOW - timedelta(seconds=1),
        )

    assert "precede creation time" in str(exc_info.value)

    unchanged = registry.get_worker(
        tenant_id="tenant-a",
        worker_id="worker-a",
    )
    assert unchanged.registration_revision == 1
    assert unchanged.version == "1.0.0"


def test_registry_rejects_in_memory_database():
    with pytest.raises(AgentWorkerRegistryError):
        AgentWorkerRegistryStore(":memory:")

@pytest.mark.parametrize(
    "legacy_capability",
    ("python", "pytest", "security-review"),
)
def test_registration_rejects_legacy_capability_identifiers(
    registry,
    legacy_capability,
):
    with pytest.raises(AgentWorkerRegistryError):
        register(
            registry,
            capabilities=(legacy_capability,),
        )


def test_registration_rejects_unknown_capability_identifier(registry):
    with pytest.raises(AgentWorkerRegistryError):
        register(
            registry,
            capabilities=("unknown.capability",),
        )
