from dataclasses import FrozenInstanceError, replace
from datetime import datetime, timedelta, timezone

import pytest

from backend.app.gagf.governance_agent_approval_contract import (
    APPROVAL_REQUIRED_ACTION_CLASSES,
    AgentApprovalContractError,
    AgentApprovalDecisionRecord,
    AgentApprovalRequest,
    ApprovalActionClass,
    ApprovalActorType,
    ApprovalDecision,
    ApprovalRequesterType,
    requires_human_approval,
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
        "idempotency_key": "approval-request-key-001",
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
        "idempotency_key": "approval-decision-key-001",
        "reason": "Reviewed and approved.",
    }

    values.update(overrides)
    return AgentApprovalDecisionRecord.create(**values)


def test_action_payload_is_canonical():
    first = make_request(
        action={"b": 2, "a": 1},
    )
    second = make_request(
        action={"a": 1, "b": 2},
    )

    assert first.action_json == second.action_json
    assert first.action_hash == second.action_hash


def test_action_hash_changes_when_action_changes():
    first = make_request()
    second = make_request(
        action={
            "operation": "update_policy",
            "resource_id": "policy-001",
            "enabled": False,
        },
    )

    assert first.action_hash != second.action_hash
    assert first.request_hash != second.request_hash


def test_read_only_action_does_not_require_human_approval():
    assert requires_human_approval(
        ApprovalActionClass.READ_ONLY
    ) is False


def test_internal_workflow_mutation_does_not_require_human_approval():
    assert requires_human_approval(
        ApprovalActionClass.INTERNAL_WORKFLOW_MUTATION
    ) is False


@pytest.mark.parametrize(
    "action_class",
    sorted(APPROVAL_REQUIRED_ACTION_CLASSES, key=lambda item: item.value),
)
def test_consequential_action_classes_require_human_approval(action_class):
    assert requires_human_approval(action_class) is True


def test_approval_policy_rejects_unknown_action_class():
    with pytest.raises(AgentApprovalContractError):
        requires_human_approval("external_system_mutation")


def test_request_rejects_naive_requested_at():
    with pytest.raises(AgentApprovalContractError):
        make_request(requested_at=datetime.now())


def test_request_rejects_expiration_before_request():
    now = datetime.now(timezone.utc)

    with pytest.raises(AgentApprovalContractError):
        make_request(
            requested_at=now,
            expires_at=now - timedelta(seconds=1),
        )


def test_request_is_immutable():
    request = make_request()

    with pytest.raises(FrozenInstanceError):
        request.tenant_id = "tenant-b"


def test_action_property_returns_independent_dictionary():
    request = make_request()

    action = request.action
    action["enabled"] = False

    assert request.action["enabled"] is True


def test_request_rejects_direct_action_hash_tampering():
    request = make_request()

    with pytest.raises(AgentApprovalContractError):
        replace(request, action_hash="tampered")


def test_approval_decision_preserves_request_context():
    request = make_request()
    decision = make_decision(request)

    decision.validate_against(request)

    assert decision.request_id == request.request_id
    assert decision.request_hash == request.request_hash
    assert decision.tenant_id == request.tenant_id
    assert decision.workflow_id == request.workflow_id
    assert decision.work_item_id == request.work_item_id
    assert decision.action_hash == request.action_hash
    assert decision.decision is ApprovalDecision.APPROVE


def test_rejection_is_a_valid_human_decision():
    request = make_request()

    decision = make_decision(
        request,
        decision=ApprovalDecision.REJECT,
        reason="The proposed change is not justified.",
    )

    decision.validate_against(request)

    assert decision.decision is ApprovalDecision.REJECT


def test_worker_cannot_issue_approval_decision():
    request = make_request()

    with pytest.raises(
        AgentApprovalContractError,
        match="Only a human actor",
    ):
        make_decision(
            request,
            approver_type=ApprovalActorType.WORKER,
        )


def test_system_cannot_issue_approval_decision():
    request = make_request()

    with pytest.raises(
        AgentApprovalContractError,
        match="Only a human actor",
    ):
        make_decision(
            request,
            approver_type=ApprovalActorType.SYSTEM,
        )


def test_requester_cannot_approve_own_request():
    request = make_request()

    with pytest.raises(
        AgentApprovalContractError,
        match="requester cannot",
    ):
        make_decision(
            request,
            approver_id=request.requester_id,
        )


def test_human_requester_cannot_approve_own_request():
    request = make_request(
        requester_id="human-operator-001",
        requester_type=ApprovalRequesterType.HUMAN,
    )

    with pytest.raises(
        AgentApprovalContractError,
        match="requester cannot",
    ):
        make_decision(
            request,
            approver_id="human-operator-001",
        )


def test_decision_cannot_predate_request():
    request = make_request()

    with pytest.raises(
        AgentApprovalContractError,
        match="predate",
    ):
        make_decision(
            request,
            decided_at=request.requested_at - timedelta(seconds=1),
        )


def test_expired_request_cannot_receive_decision():
    request = make_request()

    with pytest.raises(
        AgentApprovalContractError,
        match="Expired",
    ):
        make_decision(
            request,
            decided_at=request.expires_at,
        )


def test_request_expiration_is_deterministic():
    request = make_request()

    assert request.is_expired(request.expires_at) is True
    assert request.is_expired(
        request.expires_at - timedelta(microseconds=1)
    ) is False


def test_decision_rejects_different_tenant():
    request = make_request()
    decision = make_decision(request)

    different_request = replace(
        request,
        tenant_id="tenant-b",
    )

    with pytest.raises(
        AgentApprovalContractError,
        match="does not match",
    ):
        decision.validate_against(different_request)


def test_decision_rejects_different_work_item():
    request = make_request()
    decision = make_decision(request)

    different_request = replace(
        request,
        work_item_id="work-item-002",
    )

    with pytest.raises(
        AgentApprovalContractError,
        match="does not match",
    ):
        decision.validate_against(different_request)


def test_decision_rejects_different_action():
    request = make_request()
    decision = make_decision(request)

    different_request = make_request(
        action={
            "operation": "delete_policy",
            "resource_id": "policy-001",
        },
    )

    with pytest.raises(
        AgentApprovalContractError,
        match="does not match",
    ):
        decision.validate_against(different_request)


def test_decision_is_immutable():
    request = make_request()
    decision = make_decision(request)

    with pytest.raises(FrozenInstanceError):
        decision.tenant_id = "tenant-b"


def test_decision_integrity_verification():
    request = make_request()
    decision = make_decision(request)

    assert decision.verify_integrity() is True
    decision.validate_against(request)


def test_decision_rejects_direct_hash_tampering():
    request = make_request()
    decision = make_decision(request)

    with pytest.raises(AgentApprovalContractError):
        replace(decision, decision_hash="tampered")


def test_request_rejects_non_object_action():
    with pytest.raises(AgentApprovalContractError):
        make_request(action=["not", "an", "object"])


def test_request_rejects_non_string_action_keys():
    with pytest.raises(AgentApprovalContractError):
        make_request(action={1: "invalid-key"})

@pytest.mark.parametrize(
    "action_class",
    [
        ApprovalActionClass.READ_ONLY,
        ApprovalActionClass.INTERNAL_WORKFLOW_MUTATION,
    ],
)
def test_decision_creation_rejects_non_approval_actions(action_class):
    request = make_request(action_class=action_class)

    with pytest.raises(
        AgentApprovalContractError,
        match="does not require human approval",
    ):
        make_decision(request)


@pytest.mark.parametrize(
    "action_class",
    [
        ApprovalActionClass.READ_ONLY,
        ApprovalActionClass.INTERNAL_WORKFLOW_MUTATION,
    ],
)
def test_decision_validation_rejects_non_approval_actions(action_class):
    request = make_request()
    decision = make_decision(request)

    non_approval_request = replace(
        request,
        action_class=action_class,
    )

    with pytest.raises(
        AgentApprovalContractError,
        match="does not require human approval",
    ):
        decision.validate_against(non_approval_request)
