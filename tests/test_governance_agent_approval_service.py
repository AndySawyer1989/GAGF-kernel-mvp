from datetime import datetime, timedelta, timezone

import pytest

from backend.app.gagf.governance_agent_approval_contract import (
    AgentApprovalContractError,
    AgentApprovalRequest,
    ApprovalActionClass,
    ApprovalActorType,
    ApprovalDecision,
    ApprovalRequesterType,
)
from backend.app.gagf.governance_agent_approval_service import (
    AgentApprovalIdentityError,
    AgentApprovalServiceError,
    AuthenticatedApprovalActor,
    GovernanceAgentApprovalService,
)
from backend.app.gagf.governance_agent_approval_store import (
    AgentApprovalConflictError,
    AgentApprovalNotFoundError,
    AgentApprovalStore,
)


class FakeIdentityProvider:
    """Controlled identity provider for service tests."""

    def __init__(
        self,
        *,
        tenant_id="tenant-a",
        actor_id="human-operator-001",
        actor_type=ApprovalActorType.HUMAN,
        error=None,
    ):
        self.tenant_id = tenant_id
        self.actor_id = actor_id
        self.actor_type = actor_type
        self.error = error

    def resolve_actor(
        self,
        *,
        tenant_id,
        authentication_context,
    ):
        if self.error is not None:
            raise self.error

        if authentication_context != "valid-test-auth-context":
            raise ValueError("Invalid test authentication context")

        return AuthenticatedApprovalActor(
            tenant_id=self.tenant_id,
            actor_id=self.actor_id,
            actor_type=self.actor_type,
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


def make_service(
    tmp_path,
    *,
    identity_provider=None,
):
    store = make_store(tmp_path)

    provider = identity_provider or FakeIdentityProvider()

    service = GovernanceAgentApprovalService(
        store=store,
        identity_provider=provider,
    )

    return service, store, provider


def submit(
    service,
    *,
    tenant_id="tenant-a",
    request_id="approval-request-001",
    decision=ApprovalDecision.APPROVE,
    authentication_context="valid-test-auth-context",
    idempotency_key="decision-key-001",
    reason="Reviewed and approved.",
):
    return service.submit_decision(
        tenant_id=tenant_id,
        request_id=request_id,
        decision=decision,
        authentication_context=authentication_context,
        idempotency_key=idempotency_key,
        reason=reason,
    )


def test_create_request_persists_and_returns_request(tmp_path):
    service, store, _ = make_service(tmp_path)
    request = make_request()

    saved = service.create_request(request)

    assert saved == request
    assert store.get_request(
        tenant_id="tenant-a",
        request_id=request.request_id,
    ) == request


def test_create_request_replay_is_idempotent(tmp_path):
    service, _, _ = make_service(tmp_path)
    request = make_request()

    first = service.create_request(request)
    second = service.create_request(request)

    assert first == second


def test_create_request_rejects_non_approval_action(tmp_path):
    service, _, _ = make_service(tmp_path)

    request = make_request(
        action_class=ApprovalActionClass.READ_ONLY,
    )

    with pytest.raises(AgentApprovalServiceError, match="does not require human approval"):
        service.create_request(request)


def test_get_request_is_tenant_scoped(tmp_path):
    service, _, _ = make_service(tmp_path)
    service.create_request(make_request())

    with pytest.raises(AgentApprovalNotFoundError):
        service.get_request(
            tenant_id="tenant-b",
            request_id="approval-request-001",
        )


@pytest.mark.parametrize(
    "decision",
    [
        ApprovalDecision.APPROVE,
        ApprovalDecision.REJECT,
    ],
)
def test_submit_decision_persists_human_decision(
    tmp_path,
    decision,
):
    service, store, _ = make_service(tmp_path)
    request = make_request()
    service.create_request(request)

    result = submit(
        service,
        decision=decision,
    )

    persisted = store.get_decision(
        tenant_id="tenant-a",
        request_id=request.request_id,
    )

    assert result == persisted
    assert result.decision is decision
    assert result.approver_id == "human-operator-001"
    assert result.approver_type is ApprovalActorType.HUMAN
    assert result.verify_integrity()


def test_submit_decision_replay_returns_original_record(tmp_path):
    service, _, _ = make_service(tmp_path)
    service.create_request(make_request())

    first = submit(service)
    second = submit(service)

    assert first == second
    assert first.decision_id == second.decision_id
    assert first.decided_at == second.decided_at


def test_submit_decision_rejects_conflicting_replay(tmp_path):
    service, _, _ = make_service(tmp_path)
    service.create_request(make_request())

    submit(service)

    with pytest.raises(AgentApprovalConflictError):
        submit(
            service,
            decision=ApprovalDecision.REJECT,
            idempotency_key="decision-key-002",
            reason="Different decision.",
        )


def test_submit_decision_rejects_same_key_with_different_intent(
    tmp_path,
):
    service, _, _ = make_service(tmp_path)
    service.create_request(make_request())

    submit(service)

    with pytest.raises(AgentApprovalConflictError):
        submit(
            service,
            decision=ApprovalDecision.APPROVE,
            idempotency_key="decision-key-001",
            reason="Different reason.",
        )


@pytest.mark.parametrize(
    "actor_type",
    [
        ApprovalActorType.WORKER,
        ApprovalActorType.SYSTEM,
    ],
)
def test_submit_decision_rejects_non_human_actor(
    tmp_path,
    actor_type,
):
    provider = FakeIdentityProvider(actor_type=actor_type)
    service, store, _ = make_service(
        tmp_path,
        identity_provider=provider,
    )
    service.create_request(make_request())

    with pytest.raises(
        AgentApprovalIdentityError,
        match="Only an authenticated human actor",
    ):
        submit(service)

    with pytest.raises(AgentApprovalNotFoundError):
        store.get_decision(
            tenant_id="tenant-a",
            request_id="approval-request-001",
        )


def test_submit_decision_rejects_actor_from_different_tenant(
    tmp_path,
):
    provider = FakeIdentityProvider(tenant_id="tenant-b")
    service, store, _ = make_service(
        tmp_path,
        identity_provider=provider,
    )
    service.create_request(make_request())

    with pytest.raises(
        AgentApprovalIdentityError,
        match="tenant does not match",
    ):
        submit(service)

    with pytest.raises(AgentApprovalNotFoundError):
        store.get_decision(
            tenant_id="tenant-a",
            request_id="approval-request-001",
        )


def test_submit_decision_rejects_requester_self_approval(tmp_path):
    provider = FakeIdentityProvider(
        actor_id="engineering-worker",
    )
    service, store, _ = make_service(
        tmp_path,
        identity_provider=provider,
    )
    service.create_request(make_request())

    with pytest.raises(
        AgentApprovalContractError,
        match="requester cannot",
    ):
        submit(service)

    with pytest.raises(AgentApprovalNotFoundError):
        store.get_decision(
            tenant_id="tenant-a",
            request_id="approval-request-001",
        )


def test_submit_decision_rejects_invalid_authentication_context(
    tmp_path,
):
    service, store, _ = make_service(tmp_path)
    service.create_request(make_request())

    with pytest.raises(
        AgentApprovalIdentityError,
        match="Unable to resolve authenticated approval actor",
    ):
        submit(
            service,
            authentication_context="invalid-context",
        )

    with pytest.raises(AgentApprovalNotFoundError):
        store.get_decision(
            tenant_id="tenant-a",
            request_id="approval-request-001",
        )


def test_submit_decision_normalizes_identity_provider_failure(
    tmp_path,
):
    provider = FakeIdentityProvider(
        error=RuntimeError("Authentication service unavailable"),
    )
    service, _, _ = make_service(
        tmp_path,
        identity_provider=provider,
    )
    service.create_request(make_request())

    with pytest.raises(
        AgentApprovalIdentityError,
        match="Unable to resolve authenticated approval actor",
    ) as captured:
        submit(service)

    assert isinstance(captured.value.__cause__, RuntimeError)


def test_submit_decision_rejects_expired_request(tmp_path):
    service, store, _ = make_service(tmp_path)

    now = datetime.now(timezone.utc)
    request = make_request(
        requested_at=now - timedelta(minutes=10),
        expires_at=now - timedelta(minutes=1),
    )
    service.create_request(request)

    with pytest.raises(AgentApprovalContractError, match="Expired approval requests"):
        submit(service)

    with pytest.raises(AgentApprovalNotFoundError):
        store.get_decision(
            tenant_id="tenant-a",
            request_id=request.request_id,
        )


def test_get_decision_is_tenant_scoped(tmp_path):
    service, _, _ = make_service(tmp_path)
    service.create_request(make_request())
    submit(service)

    with pytest.raises(AgentApprovalNotFoundError):
        service.get_decision(
            tenant_id="tenant-b",
            request_id="approval-request-001",
        )


def test_get_decision_returns_persisted_decision(tmp_path):
    service, _, _ = make_service(tmp_path)
    service.create_request(make_request())

    submitted = submit(service)
    retrieved = service.get_decision(
        tenant_id="tenant-a",
        request_id="approval-request-001",
    )

    assert retrieved == submitted