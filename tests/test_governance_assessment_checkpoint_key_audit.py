import sqlite3

import pytest

from backend.app.gagf.governance_assessment_checkpoint_key_audit import (
    CHECKPOINT_KEY_ACTIVATED,
    AssessmentCheckpointKeyAuditStore,
    create_checkpoint_key_activation_audit_event,
)


def event(**overrides):
    values = {
        "tenant_id": "tenant-alpha",
        "actor_id": "actor-admin",
        "previous_key_id": "key-001",
        "active_key_id": "key-002",
        "metadata": {"source": "admin-api"},
    }
    values.update(overrides)
    return create_checkpoint_key_activation_audit_event(
        **values
    )


def test_activation_event_contains_expected_fields():
    value = event()

    assert value.event_id
    assert value.tenant_id == "tenant-alpha"
    assert value.actor_id == "actor-admin"
    assert value.operation == CHECKPOINT_KEY_ACTIVATED
    assert value.previous_key_id == "key-001"
    assert value.active_key_id == "key-002"
    assert value.occurred_at
    assert value.metadata == {"source": "admin-api"}


def test_audit_event_round_trips_through_store(tmp_path):
    store = AssessmentCheckpointKeyAuditStore(
        tmp_path / "key-audit.sqlite3"
    )
    value = event()

    store.append(value)
    stored = store.list_events(
        tenant_id="tenant-alpha"
    )

    assert stored == [value]


def test_audit_events_are_tenant_scoped(tmp_path):
    store = AssessmentCheckpointKeyAuditStore(
        tmp_path / "key-audit.sqlite3"
    )
    store.append(event())
    store.append(
        event(
            tenant_id="tenant-beta",
            previous_key_id=None,
            active_key_id="key-beta-001",
        )
    )

    alpha = store.list_events(
        tenant_id="tenant-alpha"
    )
    beta = store.list_events(
        tenant_id="tenant-beta"
    )

    assert len(alpha) == 1
    assert len(beta) == 1
    assert alpha[0].tenant_id == "tenant-alpha"
    assert beta[0].tenant_id == "tenant-beta"


def test_audit_events_are_returned_newest_first(tmp_path):
    store = AssessmentCheckpointKeyAuditStore(
        tmp_path / "key-audit.sqlite3"
    )
    first = event(active_key_id="key-002")
    second = event(active_key_id="key-003")

    store.append(first)
    store.append(second)

    stored = store.list_events(
        tenant_id="tenant-alpha"
    )

    assert stored[0].active_key_id == "key-003"
    assert stored[1].active_key_id == "key-002"


def test_list_events_honors_limit(tmp_path):
    store = AssessmentCheckpointKeyAuditStore(
        tmp_path / "key-audit.sqlite3"
    )
    store.append(event(active_key_id="key-002"))
    store.append(event(active_key_id="key-003"))

    stored = store.list_events(
        tenant_id="tenant-alpha",
        limit=1,
    )

    assert len(stored) == 1


def test_invalid_limit_is_rejected(tmp_path):
    store = AssessmentCheckpointKeyAuditStore(
        tmp_path / "key-audit.sqlite3"
    )

    with pytest.raises(
        ValueError,
        match="limit must be at least 1",
    ):
        store.list_events(
            tenant_id="tenant-alpha",
            limit=0,
        )


def test_secret_material_is_not_required_or_stored(tmp_path):
    database_path = tmp_path / "key-audit.sqlite3"
    store = AssessmentCheckpointKeyAuditStore(database_path)
    store.append(event())

    database_bytes = database_path.read_bytes()

    assert b"secret-001" not in database_bytes
    assert b"secret-002" not in database_bytes


def test_duplicate_event_id_is_rejected(tmp_path):
    store = AssessmentCheckpointKeyAuditStore(
        tmp_path / "key-audit.sqlite3"
    )
    value = event()
    store.append(value)

    with pytest.raises(sqlite3.IntegrityError):
        store.append(value)
