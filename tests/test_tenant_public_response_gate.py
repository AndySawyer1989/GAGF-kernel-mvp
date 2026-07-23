from dataclasses import FrozenInstanceError

import pytest

from backend.app.gagf.tenant_public_response_gate import (
    TENANT_PUBLIC_RESPONSE_GATE_ID,
    TENANT_PUBLIC_RESPONSE_GATE_VERSION,
    TenantPublicResponseGate,
    TenantPublicResponseRejectedError,
)


def safe_response():
    return {
        "api_id": "tenant-api",
        "api_version": "1.0.0",
        "tenant_id": "tenant-alpha",
        "execution": {
            "view_id": "tenant-public-execution-view",
            "public_artifact_id": "a" * 64,
            "view_hash": "b" * 64,
        },
    }


def test_gate_has_stable_identity():
    assert TENANT_PUBLIC_RESPONSE_GATE_ID == (
        "tenant-public-response-boundary-gate"
    )
    assert TENANT_PUBLIC_RESPONSE_GATE_VERSION == "0.1.0"


def test_safe_response_is_released():
    result = TenantPublicResponseGate().release(
        response=safe_response()
    )

    assert result["api_id"] == "tenant-api"
    assert result["tenant_id"] == "tenant-alpha"
    assert result["boundary_audit"]["valid"] is True
    assert (
        result["boundary_audit"]["violation_count"]
        == 0
    )


def test_release_can_omit_audit_metadata():
    result = TenantPublicResponseGate().release(
        response=safe_response(),
        include_audit=False,
    )

    assert result == safe_response()
    assert "boundary_audit" not in result


def test_inspect_returns_invalid_envelope_without_raising():
    response = safe_response()
    response["canonical_artifact_id"] = "secret"

    envelope = TenantPublicResponseGate().inspect(
        response=response
    )

    assert envelope.boundary_audit.valid is False
    assert (
        envelope.boundary_audit.violation_count
        == 1
    )


@pytest.mark.parametrize(
    "forbidden_key",
    [
        "canonical_artifact_id",
        "binding_hash",
        "receipt_hash",
        "credential_id",
        "session_id",
        "request_id",
        "correlation_id",
        "trust_signals",
    ],
)
def test_forbidden_response_is_rejected(
    forbidden_key,
):
    response = safe_response()
    response["leak"] = {
        forbidden_key: "secret",
    }

    with pytest.raises(
        TenantPublicResponseRejectedError,
        match="constitutional boundary gate",
    ):
        TenantPublicResponseGate().release(
            response=response
        )


def test_sensitive_value_under_safe_key_is_rejected():
    response = safe_response()
    response["metadata"] = {
        "value": "canonical-secret",
    }

    with pytest.raises(
        TenantPublicResponseRejectedError,
    ):
        TenantPublicResponseGate().release(
            response=response,
            sensitive_values={
                "canonical-secret",
            },
        )


def test_rejection_message_does_not_expose_value():
    response = {
        "credential_id": "credential-secret",
    }

    try:
        TenantPublicResponseGate().release(
            response=response
        )
    except TenantPublicResponseRejectedError as exc:
        assert "credential-secret" not in str(exc)
    else:
        raise AssertionError(
            "Expected response rejection."
        )


def test_error_detail_is_also_audited():
    detail = {
        "message": "Request denied.",
        "view_id": (
            "tenant-public-scientific-authorization-view"
        ),
        "decision": {
            "allowed": False,
            "reasons": [
                "Role not permitted.",
            ],
        },
        "view_hash": "a" * 64,
    }

    result = (
        TenantPublicResponseGate()
        .release_error_detail(detail=detail)
    )

    assert result["message"] == "Request denied."
    assert result["boundary_audit"]["valid"] is True


def test_unsafe_error_detail_is_rejected():
    detail = {
        "message": "Request denied.",
        "credential_id": "credential-secret",
    }

    with pytest.raises(
        TenantPublicResponseRejectedError,
    ):
        TenantPublicResponseGate().release_error_detail(
            detail=detail
        )


def test_boundary_audit_hash_verifies():
    result = TenantPublicResponseGate().release(
        response=safe_response()
    )

    assert len(
        result["boundary_audit"]["audit_hash"]
    ) == 64


def test_envelope_is_immutable():
    envelope = TenantPublicResponseGate().inspect(
        response=safe_response()
    )

    with pytest.raises(FrozenInstanceError):
        envelope.gate_id = "changed"
