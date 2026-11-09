import sqlite3

from datetime import datetime, timedelta, timezone

import pytest

from backend.app.gagf.governance_agent_approval_contract import (
    AgentApprovalDecisionRecord,
    AgentApprovalRequest,
    ApprovalActionClass,
    ApprovalActorType,
    ApprovalDecision,
    ApprovalRequesterType,
)
from backend.app.gagf.governance_agent_approval_store import (
    AgentApprovalConflictError,
    AgentApprovalIntegrityError,
    AgentApprovalNotFoundError,
    AgentApprovalStore,
    AgentApprovalStoreError,
)


def make_store(tmp_path):
    return AgentApprovalStore(
        tmp_path / "agent_approvals.db",
    )


def make_request(**overrides):
    now = datetime.now(timezone.utc)

    values = {
        "request_id": "approval-request-001",
        "tenant_id": "tenant-a",
        "workflow_id": "workflow-001",
        "work_item_id": "work-item-001",
        "action_class": ApprovalActionClass.EXTERNAL_SYSTEM_MUTATION,
        "requester_id": "engineering-worker",
        "requester_type": ApprovalRequesterType.WORKER,
        "requested_at": now,
        "expires_at": now + timedelta(minutes=15),
        "correlation_id": "correlation-001",
        "idempotency_key": "request-key-001",
        "action": {
            "operation": "update_policy",
            "resource_id": "policy-001",
            "enabled": True,
        },
    }

    values.update(overrides)
    return AgentApprovalRequest.create(**values)


def make_decision(request, **overrides):
    values = {
        "decision_id": "approval-decision-001",
        "request": request,
        "decision": ApprovalDecision.APPROVE,
        "approver_id": "human-operator-001",
        "approver_type": ApprovalActorType.HUMAN,
        "decided_at": request.requested_at + timedelta(seconds=30),
        "idempotency_key": "decision-key-001",
        "reason": "Reviewed and approved.",
    }

    values.update(overrides)
    return AgentApprovalDecisionRecord.create(**values)


def test_save_and_retrieve_request(tmp_path):
    store = make_store(tmp_path)
    request = make_request()

    saved = store.save_request(request)
    retrieved = store.get_request(
        tenant_id="tenant-a",
        request_id=request.request_id,
    )

    assert saved == request
    assert retrieved == request
    assert retrieved.request_hash == request.request_hash
    assert retrieved.action == request.action


def test_request_creation_is_idempotent(tmp_path):
    store = make_store(tmp_path)
    request = make_request()

    first = store.save_request(request)
    second = store.save_request(request)

    assert first == second


def test_request_idempotency_key_reuse_with_different_payload_conflicts(
    tmp_path,
):
    store = make_store(tmp_path)
    store.save_request(make_request())

    conflicting = make_request(
        request_id="approval-request-002",
        action={"operation": "different_operation"},
    )

    with pytest.raises(AgentApprovalConflictError):
        store.save_request(conflicting)


def test_duplicate_request_id_with_different_key_conflicts(tmp_path):
    store = make_store(tmp_path)
    store.save_request(make_request())

    conflicting = make_request(
        idempotency_key="request-key-002",
    )

    with pytest.raises(AgentApprovalConflictError):
        store.save_request(conflicting)


def test_same_request_id_is_isolated_between_tenants(tmp_path):
    store = make_store(tmp_path)

    tenant_a = make_request()
    tenant_b = make_request(
        tenant_id="tenant-b",
        idempotency_key="request-key-tenant-b",
    )

    store.save_request(tenant_a)
    store.save_request(tenant_b)

    assert store.get_request(
        tenant_id="tenant-a",
        request_id=tenant_a.request_id,
    ).tenant_id == "tenant-a"

    assert store.get_request(
        tenant_id="tenant-b",
        request_id=tenant_b.request_id,
    ).tenant_id == "tenant-b"


def test_request_read_is_tenant_scoped(tmp_path):
    store = make_store(tmp_path)
    store.save_request(make_request())

    with pytest.raises(AgentApprovalNotFoundError):
        store.get_request(
            tenant_id="tenant-b",
            request_id="approval-request-001",
        )


def test_missing_request_raises_not_found(tmp_path):
    store = make_store(tmp_path)

    with pytest.raises(AgentApprovalNotFoundError):
        store.get_request(
            tenant_id="tenant-a",
            request_id="missing",
        )


def test_save_and_retrieve_decision(tmp_path):
    store = make_store(tmp_path)
    request = make_request()
    decision = make_decision(request)

    store.save_request(request)
    saved = store.record_decision(decision)

    retrieved = store.get_decision(
        tenant_id=request.tenant_id,
        request_id=request.request_id,
    )

    assert saved == decision
    assert retrieved == decision
    assert retrieved.verify_integrity()


def test_decision_requires_persisted_request(tmp_path):
    store = make_store(tmp_path)
    request = make_request()
    decision = make_decision(request)

    with pytest.raises(AgentApprovalNotFoundError):
        store.record_decision(decision)


def test_decision_replay_is_idempotent(tmp_path):
    store = make_store(tmp_path)
    request = make_request()
    decision = make_decision(request)

    store.save_request(request)

    first = store.record_decision(decision)
    second = store.record_decision(decision)

    assert first == second


def test_decision_idempotency_key_reuse_with_different_payload_conflicts(
    tmp_path,
):
    store = make_store(tmp_path)
    request = make_request()
    store.save_request(request)

    first = make_decision(request)
    store.record_decision(first)

    conflicting = make_decision(
        request,
        decision_id="approval-decision-002",
        decision=ApprovalDecision.REJECT,
        idempotency_key="decision-key-001",
        reason="Different decision.",
    )

    with pytest.raises(AgentApprovalConflictError):
        store.record_decision(conflicting)


def test_request_cannot_receive_two_different_final_decisions(tmp_path):
    store = make_store(tmp_path)
    request = make_request()
    store.save_request(request)

    first = make_decision(request)
    store.record_decision(first)

    conflicting = make_decision(
        request,
        decision_id="approval-decision-002",
        decision=ApprovalDecision.REJECT,
        idempotency_key="decision-key-002",
        reason="Rejected after review.",
    )

    with pytest.raises(AgentApprovalConflictError):
        store.record_decision(conflicting)


def test_decision_is_scoped_to_its_own_tenant(tmp_path):
    store = make_store(tmp_path)

    request_a = make_request()
    request_b = make_request(
        tenant_id="tenant-b",
        idempotency_key="request-key-tenant-b",
    )

    store.save_request(request_a)
    store.save_request(request_b)

    decision_b = make_decision(request_b)

    saved = store.record_decision(decision_b)

    assert saved == decision_b

    tenant_b_decision = store.get_decision(
        tenant_id="tenant-b",
        request_id=request_b.request_id,
    )

    assert tenant_b_decision == decision_b

    with pytest.raises(AgentApprovalNotFoundError):
        store.get_decision(
            tenant_id="tenant-a",
            request_id=request_a.request_id,
        )


def test_expired_request_cannot_receive_persisted_decision(
    tmp_path,
    monkeypatch,
):
    store = make_store(tmp_path)
    request = make_request()
    decision = make_decision(request)

    store.save_request(request)

    monkeypatch.setattr(
        store,
        "_now",
        lambda: request.expires_at,
    )

    with pytest.raises(AgentApprovalConflictError):
        store.record_decision(decision)


def test_decision_read_is_tenant_scoped(tmp_path):
    store = make_store(tmp_path)
    request = make_request()

    store.save_request(request)
    store.record_decision(make_decision(request))

    with pytest.raises(AgentApprovalNotFoundError):
        store.get_decision(
            tenant_id="tenant-b",
            request_id=request.request_id,
        )


def test_missing_decision_raises_not_found(tmp_path):
    store = make_store(tmp_path)
    request = make_request()
    store.save_request(request)

    with pytest.raises(AgentApprovalNotFoundError):
        store.get_decision(
            tenant_id=request.tenant_id,
            request_id=request.request_id,
        )


def test_request_update_and_delete_are_blocked(tmp_path):
    store = make_store(tmp_path)
    request = make_request()
    store.save_request(request)

    with sqlite3.connect(store.database_path) as connection:
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                """
                UPDATE gagf_agent_approval_requests
                SET requester_id = ?
                WHERE tenant_id = ?
                  AND request_id = ?
                """,
                (
                    "tampered-requester",
                    request.tenant_id,
                    request.request_id,
                ),
            )

        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                """
                DELETE FROM gagf_agent_approval_requests
                WHERE tenant_id = ?
                  AND request_id = ?
                """,
                (request.tenant_id, request.request_id),
            )


def test_decision_update_and_delete_are_blocked(tmp_path):
    store = make_store(tmp_path)
    request = make_request()
    decision = make_decision(request)

    store.save_request(request)
    store.record_decision(decision)

    with sqlite3.connect(store.database_path) as connection:
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                """
                UPDATE gagf_agent_approval_decisions
                SET approver_id = ?
                WHERE tenant_id = ?
                  AND request_id = ?
                """,
                (
                    "tampered-approver",
                    request.tenant_id,
                    request.request_id,
                ),
            )

        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                """
                DELETE FROM gagf_agent_approval_decisions
                WHERE tenant_id = ?
                  AND request_id = ?
                """,
                (request.tenant_id, request.request_id),
            )


def test_tampered_persisted_request_is_detected_on_read(tmp_path):
    store = make_store(tmp_path)
    request = make_request()
    store.save_request(request)

    with sqlite3.connect(store.database_path) as connection:
        connection.execute(
            """
            DROP TRIGGER trg_gagf_agent_approval_requests_no_update
            """
        )
        connection.execute(
            """
            UPDATE gagf_agent_approval_requests
            SET action_hash = ?
            WHERE tenant_id = ?
              AND request_id = ?
            """,
            (
                "tampered",
                request.tenant_id,
                request.request_id,
            ),
        )

    with pytest.raises(AgentApprovalIntegrityError):
        store.get_request(
            tenant_id=request.tenant_id,
            request_id=request.request_id,
        )


def test_tampered_persisted_decision_is_detected_on_read(tmp_path):
    store = make_store(tmp_path)
    request = make_request()
    decision = make_decision(request)

    store.save_request(request)
    store.record_decision(decision)

    with sqlite3.connect(store.database_path) as connection:
        connection.execute(
            """
            DROP TRIGGER trg_gagf_agent_approval_decisions_no_update
            """
        )
        connection.execute(
            """
            UPDATE gagf_agent_approval_decisions
            SET decision_hash = ?
            WHERE tenant_id = ?
              AND request_id = ?
            """,
            (
                "tampered",
                request.tenant_id,
                request.request_id,
            ),
        )

    with pytest.raises(AgentApprovalIntegrityError):
        store.get_decision(
            tenant_id=request.tenant_id,
            request_id=request.request_id,
        )

def test_connection_failure_is_normalized(tmp_path, monkeypatch):
    store = make_store(tmp_path)

    def fail_connect(*args, **kwargs):
        raise sqlite3.OperationalError("simulated connection failure")

    monkeypatch.setattr(sqlite3, "connect", fail_connect)

    with pytest.raises(AgentApprovalStoreError) as exc_info:
        store.get_request(
            tenant_id="tenant-a",
            request_id="missing-request",
        )

    assert isinstance(exc_info.value.__cause__, sqlite3.OperationalError)
    assert str(exc_info.value) == (
        "Unable to establish approval-store database connection"
    )
