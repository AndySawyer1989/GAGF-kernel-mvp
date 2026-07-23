from dataclasses import FrozenInstanceError, replace

import pytest

from backend.app.gagf.tenant_public_boundary_auditor import (
    TENANT_PUBLIC_BOUNDARY_AUDITOR_ID,
    TENANT_PUBLIC_BOUNDARY_AUDITOR_VERSION,
    TENANT_PUBLIC_BOUNDARY_AUDIT_SCHEMA_VERSION,
    TenantPublicBoundaryAuditor,
    TenantPublicBoundaryLeakError,
)


def safe_response():
    return {
        "api_id": (
            "tenant-namespaced-scientific-authority-api"
        ),
        "api_version": "0.4.0",
        "tenant_id": "tenant-alpha",
        "authorization": {
            "view_id": (
                "tenant-public-scientific-authorization-view"
            ),
            "decision": {
                "allowed": True,
                "action": "EVALUATE",
                "tenant_id": "tenant-alpha",
                "role_id": "scientific-reviewer",
                "checks": {
                    "credential_verified": True,
                    "session_verified": True,
                },
                "reasons": [],
            },
            "receipt": {
                "public_receipt_id": "a" * 64,
            },
            "view_hash": "b" * 64,
        },
        "execution": {
            "view_id": (
                "tenant-public-scientific-execution-view"
            ),
            "resumed": False,
            "decision_allowed": True,
            "checkpoint_valid": True,
            "public_artifacts": {
                "execution_id": "c" * 64,
                "authority_receipt_id": "d" * 64,
                "checkpoint_id": "e" * 64,
            },
            "view_hash": "f" * 64,
        },
    }


def test_auditor_has_stable_identity():
    assert TENANT_PUBLIC_BOUNDARY_AUDITOR_ID == (
        "tenant-public-boundary-leak-auditor"
    )
    assert TENANT_PUBLIC_BOUNDARY_AUDITOR_VERSION == (
        "0.1.0"
    )
    assert TENANT_PUBLIC_BOUNDARY_AUDIT_SCHEMA_VERSION == (
        "1.0.0"
    )


def test_safe_public_response_passes():
    result = TenantPublicBoundaryAuditor().audit(
        response=safe_response()
    )

    assert result.valid is True
    assert result.violation_count == 0
    assert result.violations == ()
    assert result.verify() is True


@pytest.mark.parametrize(
    "forbidden_key",
    [
        "canonical_artifact_id",
        "binding_hash",
        "receipt_hash",
        "authority_receipt_hash",
        "audit_receipt_hash",
        "checkpoint_hash",
        "context_hash",
        "actor_id",
        "credential_id",
        "session_id",
        "request_id",
        "correlation_id",
        "trust_signals",
        "authorization_receipt",
        "internal_receipt_commitment",
    ],
)
def test_forbidden_keys_are_detected(
    forbidden_key,
):
    response = safe_response()
    response["leak"] = {
        forbidden_key: "sensitive-value",
    }

    result = TenantPublicBoundaryAuditor().audit(
        response=response
    )

    assert result.valid is False
    assert result.violation_count == 1

    violation = result.violations[0]

    assert violation.violation_type == (
        "FORBIDDEN_KEY"
    )
    assert violation.key == forbidden_key
    assert violation.path == (
        f"$.leak.{forbidden_key}"
    )
    assert len(
        violation.value_fingerprint
    ) == 64


def test_nested_list_leak_is_detected():
    response = safe_response()
    response["items"] = [
        {
            "safe": True,
        },
        {
            "checkpoint_hash": "secret",
        },
    ]

    result = TenantPublicBoundaryAuditor().audit(
        response=response
    )

    assert result.valid is False
    assert result.violations[0].path == (
        "$.items[1].checkpoint_hash"
    )


def test_known_sensitive_value_is_detected_under_safe_key():
    response = safe_response()
    response["metadata"] = {
        "value": "canonical-secret",
    }

    result = TenantPublicBoundaryAuditor().audit(
        response=response,
        sensitive_values={
            "canonical-secret",
        },
    )

    assert result.valid is False
    assert result.violation_count == 1
    assert result.violations[0].violation_type == (
        "SENSITIVE_VALUE_EXPOSURE"
    )
    assert result.violations[0].path == (
        "$.metadata.value"
    )


def test_sensitive_value_fingerprint_hides_raw_value():
    result = TenantPublicBoundaryAuditor().audit(
        response={
            "value": "canonical-secret",
        },
        sensitive_values={
            "canonical-secret",
        },
    )

    serialized = result.to_dict()

    assert "canonical-secret" not in str(
        serialized
    )
    assert len(
        serialized["violations"][0][
            "value_fingerprint"
        ]
    ) == 64


def test_public_hash_fields_are_allowed():
    response = safe_response()
    response["artifact"] = {
        "view_hash": "a" * 64,
    }

    result = TenantPublicBoundaryAuditor().audit(
        response=response
    )

    assert result.valid is True


@pytest.mark.parametrize(
    "public_key",
    [
        "public_artifact_id",
        "public_receipt_id",
        "execution_id",
        "execution_receipt_id",
        "authority_receipt_id",
        "audit_receipt_id",
        "checkpoint_id",
        "context_binding_id",
    ],
)
def test_public_identifiers_are_allowed(
    public_key,
):
    result = TenantPublicBoundaryAuditor().audit(
        response={
            public_key: "a" * 64,
        }
    )

    assert result.valid is True


def test_generic_hash_suffix_is_denied():
    result = TenantPublicBoundaryAuditor().audit(
        response={
            "unexpected_domain_hash": "a" * 64,
        }
    )

    assert result.valid is False
    assert result.violations[0].key == (
        "unexpected_domain_hash"
    )


def test_canonical_prefix_is_denied():
    result = TenantPublicBoundaryAuditor().audit(
        response={
            "canonical_value": "secret",
        }
    )

    assert result.valid is False


def test_internal_prefix_is_denied():
    result = TenantPublicBoundaryAuditor().audit(
        response={
            "internal_reference": "secret",
        }
    )

    assert result.valid is False


def test_enforce_returns_valid_audit():
    result = TenantPublicBoundaryAuditor().enforce(
        response=safe_response()
    )

    assert result.valid is True
    assert result.verify() is True


def test_enforce_fails_closed():
    with pytest.raises(
        TenantPublicBoundaryLeakError,
        match="forbidden internal data",
    ):
        TenantPublicBoundaryAuditor().enforce(
            response={
                "credential_id": "credential-1",
            }
        )


def test_violation_order_is_deterministic():
    response = {
        "z": {
            "receipt_hash": "z",
        },
        "a": {
            "binding_hash": "a",
        },
    }

    first = TenantPublicBoundaryAuditor().audit(
        response=response
    )
    second = TenantPublicBoundaryAuditor().audit(
        response=response
    )

    assert first == second
    assert [
        violation.path
        for violation in first.violations
    ] == [
        "$.a.binding_hash",
        "$.z.receipt_hash",
    ]


def test_audit_hash_detects_tampering():
    result = TenantPublicBoundaryAuditor().audit(
        response=safe_response()
    )

    tampered = replace(
        result,
        valid=False,
    )

    assert result.verify() is True
    assert tampered.verify() is False


def test_audit_result_is_immutable():
    result = TenantPublicBoundaryAuditor().audit(
        response=safe_response()
    )

    with pytest.raises(FrozenInstanceError):
        result.valid = False


def test_public_boundary_audit_hash_is_allowed():
    response = safe_response()
    response["boundary_audit"] = {
        "schema_version": "1.0.0",
        "auditor_id": (
            "tenant-public-boundary-leak-auditor"
        ),
        "auditor_version": "0.1.0",
        "valid": True,
        "violation_count": 0,
        "violations": [],
        "audit_hash": "a" * 64,
    }

    result = TenantPublicBoundaryAuditor().audit(
        response=response
    )

    assert result.valid is True
    assert result.violation_count == 0


def test_public_boundary_ledger_proof_hashes_are_allowed():
    response = safe_response()
    response["boundary_audit_record"] = {
        "schema_version": "1.0.0",
        "ledger_id": (
            "tenant-public-boundary-audit-ledger"
        ),
        "ledger_version": "0.1.0",
        "sequence_number": 1,
        "tenant_id": "tenant-alpha",
        "response_kind": "evaluation",
        "released": True,
        "audit_valid": True,
        "violation_count": 0,
        "boundary_audit_hash": "a" * 64,
        "previous_record_hash": "0" * 64,
        "record_hash": "b" * 64,
    }

    result = TenantPublicBoundaryAuditor().audit(
        response=response
    )

    assert result.valid is True
    assert result.violation_count == 0
