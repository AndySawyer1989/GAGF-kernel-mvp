from dataclasses import FrozenInstanceError, replace

import pytest

from backend.app.gagf.scientific_authorization import (
    ScientificAuthorityAction,
    ScientificAuthorityAuthorizationPolicy,
    ScientificAuthorizationRequest,
    ScientificTrustSignals,
)
from backend.app.gagf.scientific_calculation_contract import (
    CalculationAuthority,
)
from backend.app.gagf.scientific_execution_context import (
    ScientificExecutionContext,
)
from backend.app.gagf.tenant_public_authorization_view import (
    TENANT_PUBLIC_AUTHORIZATION_VIEW_ID,
    TENANT_PUBLIC_AUTHORIZATION_VIEW_SCHEMA_VERSION,
    TENANT_PUBLIC_AUTHORIZATION_VIEW_VERSION,
    TenantPublicAuthorizationViewBuilder,
)


def build_context(
    *,
    tenant_id="tenant-alpha",
    role_id="scientific-reviewer",
):
    return ScientificExecutionContext(
        tenant_id=tenant_id,
        actor_id="actor-sensitive",
        credential_id="credential-sensitive",
        session_id="session-sensitive",
        role_id=role_id,
        policy_scope="scientific-authority:evaluate",
        request_id="request-sensitive",
        correlation_id="correlation-sensitive",
    )


def trusted_signals():
    return ScientificTrustSignals(
        credential_verified=True,
        session_verified=True,
        device_trusted=True,
        step_up_verified=False,
        tenant_membership_verified=True,
    )


def authorization_request(
    *,
    tenant_id="tenant-alpha",
    target_tenant_id="tenant-alpha",
    role_id="scientific-reviewer",
):
    return ScientificAuthorizationRequest(
        context=build_context(
            tenant_id=tenant_id,
            role_id=role_id,
        ),
        action=ScientificAuthorityAction.EVALUATE,
        target_tenant_id=target_tenant_id,
        requested_authority=CalculationAuthority.ADVISORY,
        constitutional_approval_submitted=False,
        trust_signals=trusted_signals(),
    )


def build_view(**request_kwargs):
    decision, receipt = (
        ScientificAuthorityAuthorizationPolicy()
        .evaluate_with_receipt(
            authorization_request(**request_kwargs)
        )
    )

    view = TenantPublicAuthorizationViewBuilder().build(
        decision=decision,
        receipt=receipt,
    )

    return decision, receipt, view


def collect_keys(value):
    keys = set()

    if isinstance(value, dict):
        keys.update(value.keys())

        for child in value.values():
            keys.update(collect_keys(child))

    elif isinstance(value, list):
        for child in value:
            keys.update(collect_keys(child))

    return keys


def collect_strings(value):
    strings = set()

    if isinstance(value, str):
        strings.add(value)

    elif isinstance(value, dict):
        for child in value.values():
            strings.update(collect_strings(child))

    elif isinstance(value, list):
        for child in value:
            strings.update(collect_strings(child))

    return strings


def test_public_authorization_view_has_stable_identity():
    assert TENANT_PUBLIC_AUTHORIZATION_VIEW_ID == (
        "tenant-public-scientific-authorization-view"
    )
    assert TENANT_PUBLIC_AUTHORIZATION_VIEW_VERSION == (
        "0.1.0"
    )
    assert TENANT_PUBLIC_AUTHORIZATION_VIEW_SCHEMA_VERSION == (
        "1.0.0"
    )


def test_allowed_decision_is_projected():
    decision, _, view = build_view()

    assert decision.allowed is True
    assert view.decision.allowed is True
    assert view.decision.action == "EVALUATE"
    assert view.decision.tenant_id == "tenant-alpha"
    assert view.decision.role_id == "scientific-reviewer"
    assert all(view.decision.checks.values())
    assert view.decision.reasons == ()


def test_denied_decision_is_projected():
    decision, _, view = build_view(
        target_tenant_id="tenant-beta"
    )

    assert decision.allowed is False
    assert view.decision.allowed is False
    assert (
        view.decision.checks["tenant_matches_context"]
        is False
    )
    assert "Cross-tenant access is denied." in (
        view.decision.reasons
    )


def test_public_view_excludes_identity_context():
    _, receipt, view = build_view()

    serialized = view.to_dict()
    keys = collect_keys(serialized)
    strings = collect_strings(serialized)

    forbidden_keys = {
        "actor_id",
        "credential_id",
        "session_id",
        "request_id",
        "correlation_id",
        "context",
        "trust_signals",
        "receipt_hash",
    }

    forbidden_values = {
        "actor-sensitive",
        "credential-sensitive",
        "session-sensitive",
        "request-sensitive",
        "correlation-sensitive",
        receipt.receipt_hash,
    }

    assert forbidden_keys.isdisjoint(keys)
    assert forbidden_values.isdisjoint(strings)


def test_public_receipt_id_is_deterministic():
    _, _, first = build_view()
    _, _, second = build_view()

    assert first.receipt == second.receipt
    assert len(first.receipt.public_receipt_id) == 64


def test_different_tenants_receive_different_public_receipts():
    _, _, alpha = build_view(
        tenant_id="tenant-alpha",
        target_tenant_id="tenant-alpha",
    )
    _, _, beta = build_view(
        tenant_id="tenant-beta",
        target_tenant_id="tenant-beta",
    )

    assert (
        alpha.receipt.public_receipt_id
        != beta.receipt.public_receipt_id
    )


def test_public_authorization_view_hash_verifies():
    _, _, view = build_view()

    assert view.verify() is True
    assert len(view.view_hash) == 64


def test_tampered_view_fails_verification():
    _, _, view = build_view()

    tampered = replace(
        view,
        view_version="changed",
    )

    assert tampered.verify() is False


def test_public_authorization_view_is_immutable():
    _, _, view = build_view()

    with pytest.raises(FrozenInstanceError):
        view.view_version = "changed"
