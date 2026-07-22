from dataclasses import FrozenInstanceError, replace

import pytest

from backend.app.gagf.scientific_authorization import (
    ROLE_PERMISSIONS,
    SCIENTIFIC_AUTHORIZATION_POLICY_ID,
    SCIENTIFIC_AUTHORIZATION_POLICY_VERSION,
    SCIENTIFIC_AUTHORIZATION_RECEIPT_SCHEMA_VERSION,
    ScientificAuthorityAction,
    ScientificAuthorityAuthorizationPolicy,
    ScientificAuthorityRole,
    ScientificAuthorizationRequest,
    ScientificTrustSignals,
)
from backend.app.gagf.scientific_calculation_contract import (
    CalculationAuthority,
)
from backend.app.gagf.scientific_execution_context import (
    ScientificExecutionContext,
)


def context(
    *,
    tenant_id="tenant-alpha",
    role_id="scientific-reviewer",
    policy_scope="scientific-authority:evaluate",
):
    return ScientificExecutionContext(
        tenant_id=tenant_id,
        actor_id="actor-1",
        credential_id="credential-1",
        session_id="session-1",
        role_id=role_id,
        policy_scope=policy_scope,
        request_id="request-1",
        correlation_id="correlation-1",
    )


def trusted_signals(
    *,
    step_up_verified=False,
):
    return ScientificTrustSignals(
        credential_verified=True,
        session_verified=True,
        device_trusted=True,
        step_up_verified=step_up_verified,
        tenant_membership_verified=True,
    )


def request(
    *,
    execution_context=None,
    action=ScientificAuthorityAction.EVALUATE,
    target_tenant_id="tenant-alpha",
    requested_authority=CalculationAuthority.ADVISORY,
    constitutional_approval_submitted=False,
    trust_signals=None,
):
    if execution_context is None:
        execution_context = context()

    if trust_signals is None:
        trust_signals = trusted_signals()

    return ScientificAuthorizationRequest(
        context=execution_context,
        action=action,
        target_tenant_id=target_tenant_id,
        requested_authority=requested_authority,
        constitutional_approval_submitted=(
            constitutional_approval_submitted
        ),
        trust_signals=trust_signals,
    )


def test_authorization_policy_has_stable_identity():
    assert SCIENTIFIC_AUTHORIZATION_POLICY_ID == (
        "scientific-authority-zero-trust-policy"
    )
    assert SCIENTIFIC_AUTHORIZATION_POLICY_VERSION == "0.1.0"
    assert (
        SCIENTIFIC_AUTHORIZATION_RECEIPT_SCHEMA_VERSION
        == "1.0.0"
    )


def test_role_permissions_are_read_only():
    with pytest.raises(TypeError):
        ROLE_PERMISSIONS[
            ScientificAuthorityRole.OBSERVER
        ] = frozenset()


def test_reviewer_can_request_advisory_authority():
    decision = ScientificAuthorityAuthorizationPolicy().evaluate(
        request()
    )

    assert decision.allowed is True
    assert all(decision.checks.values())
    assert decision.reasons == ()


def test_reviewer_can_request_non_authoritative():
    decision = ScientificAuthorityAuthorizationPolicy().evaluate(
        request(
            requested_authority=(
                CalculationAuthority.NON_AUTHORITATIVE
            )
        )
    )

    assert decision.allowed is True


def test_observer_cannot_evaluate():
    decision = ScientificAuthorityAuthorizationPolicy().evaluate(
        request(
            execution_context=context(
                role_id="scientific-observer"
            )
        )
    )

    assert decision.allowed is False
    assert decision.checks["action_permitted"] is False


def test_reviewer_cannot_request_authoritative():
    decision = ScientificAuthorityAuthorizationPolicy().evaluate(
        request(
            requested_authority=(
                CalculationAuthority.AUTHORITATIVE
            ),
            constitutional_approval_submitted=True,
            trust_signals=trusted_signals(
                step_up_verified=True
            ),
        )
    )

    assert decision.allowed is False
    assert (
        decision.checks["authority_level_permitted"]
        is False
    )


def test_approver_can_request_authoritative_with_step_up():
    decision = ScientificAuthorityAuthorizationPolicy().evaluate(
        request(
            execution_context=context(
                role_id="scientific-approver"
            ),
            requested_authority=(
                CalculationAuthority.AUTHORITATIVE
            ),
            constitutional_approval_submitted=True,
            trust_signals=trusted_signals(
                step_up_verified=True
            ),
        )
    )

    assert decision.allowed is True


def test_authoritative_request_requires_step_up():
    decision = ScientificAuthorityAuthorizationPolicy().evaluate(
        request(
            execution_context=context(
                role_id="scientific-approver"
            ),
            requested_authority=(
                CalculationAuthority.AUTHORITATIVE
            ),
            constitutional_approval_submitted=True,
        )
    )

    assert decision.allowed is False
    assert (
        decision.checks[
            "step_up_requirement_satisfied"
        ]
        is False
    )


def test_authoritative_request_requires_approval():
    decision = ScientificAuthorityAuthorizationPolicy().evaluate(
        request(
            execution_context=context(
                role_id="scientific-approver"
            ),
            requested_authority=(
                CalculationAuthority.AUTHORITATIVE
            ),
            constitutional_approval_submitted=False,
            trust_signals=trusted_signals(
                step_up_verified=True
            ),
        )
    )

    assert decision.allowed is False
    assert (
        decision.checks[
            "constitutional_approval_requirement_satisfied"
        ]
        is False
    )


def test_cross_tenant_request_is_denied():
    decision = ScientificAuthorityAuthorizationPolicy().evaluate(
        request(target_tenant_id="tenant-beta")
    )

    assert decision.allowed is False
    assert (
        decision.checks["tenant_matches_context"]
        is False
    )
    assert "Cross-tenant access is denied." in (
        decision.reasons
    )


@pytest.mark.parametrize(
    ("signal_name", "expected_check"),
    [
        ("credential_verified", "credential_verified"),
        ("session_verified", "session_verified"),
        ("device_trusted", "device_trusted"),
        (
            "tenant_membership_verified",
            "tenant_membership_verified",
        ),
    ],
)
def test_zero_trust_signal_failure_denies_request(
    signal_name,
    expected_check,
):
    values = {
        "credential_verified": True,
        "session_verified": True,
        "device_trusted": True,
        "step_up_verified": False,
        "tenant_membership_verified": True,
    }
    values[signal_name] = False

    decision = ScientificAuthorityAuthorizationPolicy().evaluate(
        request(
            trust_signals=ScientificTrustSignals(**values)
        )
    )

    assert decision.allowed is False
    assert decision.checks[expected_check] is False


def test_unknown_role_is_denied():
    decision = ScientificAuthorityAuthorizationPolicy().evaluate(
        request(
            execution_context=context(
                role_id="unknown-role"
            )
        )
    )

    assert decision.allowed is False
    assert decision.checks["role_recognized"] is False


def test_wrong_policy_scope_is_denied():
    decision = ScientificAuthorityAuthorizationPolicy().evaluate(
        request(
            execution_context=context(
                policy_scope=(
                    "scientific-authority:read-receipt"
                )
            )
        )
    )

    assert decision.allowed is False
    assert (
        decision.checks["policy_scope_matches_action"]
        is False
    )


def test_wildcard_scope_is_accepted():
    decision = ScientificAuthorityAuthorizationPolicy().evaluate(
        request(
            execution_context=context(
                policy_scope="scientific-authority:*"
            )
        )
    )

    assert decision.allowed is True


def test_read_action_requires_no_authority_level():
    decision = ScientificAuthorityAuthorizationPolicy().evaluate(
        request(
            execution_context=context(
                role_id="scientific-observer",
                policy_scope=(
                    "scientific-authority:read-receipt"
                ),
            ),
            action=ScientificAuthorityAction.READ_RECEIPT,
            requested_authority=None,
        )
    )

    assert decision.allowed is True


def test_read_action_with_authority_level_is_denied():
    decision = ScientificAuthorityAuthorizationPolicy().evaluate(
        request(
            execution_context=context(
                role_id="scientific-observer",
                policy_scope=(
                    "scientific-authority:read-receipt"
                ),
            ),
            action=ScientificAuthorityAction.READ_RECEIPT,
            requested_authority=CalculationAuthority.ADVISORY,
        )
    )

    assert decision.allowed is False
    assert (
        decision.checks["authority_level_permitted"]
        is False
    )


def test_contract_administration_requires_admin_and_step_up():
    allowed = ScientificAuthorityAuthorizationPolicy().evaluate(
        request(
            execution_context=context(
                role_id="scientific-administrator",
                policy_scope=(
                    "scientific-authority:"
                    "administer-contracts"
                ),
            ),
            action=(
                ScientificAuthorityAction.ADMINISTER_CONTRACTS
            ),
            requested_authority=None,
            trust_signals=trusted_signals(
                step_up_verified=True
            ),
        )
    )

    denied = ScientificAuthorityAuthorizationPolicy().evaluate(
        request(
            execution_context=context(
                role_id="scientific-approver",
                policy_scope=(
                    "scientific-authority:"
                    "administer-contracts"
                ),
            ),
            action=(
                ScientificAuthorityAction.ADMINISTER_CONTRACTS
            ),
            requested_authority=None,
            trust_signals=trusted_signals(
                step_up_verified=True
            ),
        )
    )

    assert allowed.allowed is True
    assert denied.allowed is False


def test_authorization_receipt_is_deterministic():
    policy = ScientificAuthorityAuthorizationPolicy()
    authorization_request = request()

    first_decision, first_receipt = (
        policy.evaluate_with_receipt(
            authorization_request
        )
    )
    second_decision, second_receipt = (
        policy.evaluate_with_receipt(
            authorization_request
        )
    )

    assert first_decision == second_decision
    assert first_receipt == second_receipt
    assert first_receipt.verify() is True


def test_denied_decision_also_has_valid_receipt():
    decision, receipt = (
        ScientificAuthorityAuthorizationPolicy()
        .evaluate_with_receipt(
            request(target_tenant_id="tenant-beta")
        )
    )

    assert decision.allowed is False
    assert receipt.verify() is True


def test_tampered_authorization_receipt_fails_verification():
    _, receipt = (
        ScientificAuthorityAuthorizationPolicy()
        .evaluate_with_receipt(request())
    )

    tampered = replace(
        receipt,
        receipt_hash="0" * 64,
    )

    assert tampered.verify() is False


def test_authorization_decision_is_immutable():
    decision = ScientificAuthorityAuthorizationPolicy().evaluate(
        request()
    )

    with pytest.raises(FrozenInstanceError):
        decision.allowed = False


def test_authorization_serialization_contains_checks():
    decision, receipt = (
        ScientificAuthorityAuthorizationPolicy()
        .evaluate_with_receipt(request())
    )

    serialized_decision = decision.to_dict()
    serialized_receipt = receipt.to_dict()

    assert serialized_decision["allowed"] is True
    assert serialized_decision["checks"] == decision.checks
    assert serialized_receipt["receipt_hash"] == (
        receipt.receipt_hash
    )
