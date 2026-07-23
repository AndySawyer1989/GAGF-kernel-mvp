from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.app.gagf.tenant_scientific_authority_api import (
    TENANT_SCIENTIFIC_AUTHORITY_API_ID,
    TENANT_SCIENTIFIC_AUTHORITY_API_VERSION,
    TenantScientificAuthorityApiPaths,
    create_tenant_scientific_authority_router,
)


def build_client(tmp_path) -> TestClient:
    app = FastAPI()

    app.include_router(
        create_tenant_scientific_authority_router(
            paths=TenantScientificAuthorityApiPaths(
                authority_database_path=(
                    tmp_path / "authority.db"
                ),
                audit_database_path=(
                    tmp_path / "audit.db"
                ),
                checkpoint_database_path=(
                    tmp_path / "checkpoint.db"
                ),
                journal_database_path=(
                    tmp_path / "journal.db"
                ),
                context_binding_database_path=(
                    tmp_path / "bindings.db"
                ),
            )
        )
    )

    return TestClient(app)


def evaluation_headers(
    *,
    tenant_id="tenant-alpha",
    target_tenant_id="tenant-alpha",
    role_id="scientific-reviewer",
    policy_scope="scientific-authority:evaluate",
    request_id="request-1",
):
    return {
        "x-tenant-id": tenant_id,
        "x-target-tenant-id": target_tenant_id,
        "x-actor-id": "actor-1",
        "x-credential-id": "credential-1",
        "x-session-id": "session-1",
        "x-role-id": role_id,
        "x-policy-scope": policy_scope,
        "x-request-id": request_id,
        "x-correlation-id": "correlation-1",
    }


def evaluation_payload(
    *,
    requested_authority="ADVISORY",
    constitutional_approval_submitted=False,
    credential_verified=True,
    session_verified=True,
    device_trusted=True,
    step_up_verified=False,
    tenant_membership_verified=True,
):
    return {
        "calculation_id": "evidence-confidence",
        "requested_authority": requested_authority,
        "constitutional_approval_submitted": (
            constitutional_approval_submitted
        ),
        "evidence": {
            "deterministic_replay_verified": True,
            "canonical_input_binding_verified": True,
            "calculation_version_frozen": True,
            "regression_suite_passed": True,
            "validation_report_present": True,
            "constitutional_approval_present": True,
        },
        "trust_signals": {
            "credential_verified": credential_verified,
            "session_verified": session_verified,
            "device_trusted": device_trusted,
            "step_up_verified": step_up_verified,
            "tenant_membership_verified": (
                tenant_membership_verified
            ),
        },
    }


def binding_headers(
    *,
    tenant_id="tenant-alpha",
    role_id="scientific-observer",
    policy_scope="scientific-authority:read-execution",
):
    return {
        "x-tenant-id": tenant_id,
        "x-actor-id": "actor-1",
        "x-credential-id": "credential-1",
        "x-session-id": "session-1",
        "x-role-id": role_id,
        "x-policy-scope": policy_scope,
        "x-request-id": "binding-read-request",
        "x-correlation-id": "binding-read-correlation",
        "x-credential-verified": "true",
        "x-session-verified": "true",
        "x-device-trusted": "true",
        "x-tenant-membership-verified": "true",
    }


def test_tenant_api_has_stable_identity():
    assert TENANT_SCIENTIFIC_AUTHORITY_API_ID == (
        "tenant-scientific-authority-api"
    )
    assert TENANT_SCIENTIFIC_AUTHORITY_API_VERSION == (
        "0.1.0"
    )


def test_authorized_evaluation_persists_context_binding(
    tmp_path,
):
    client = build_client(tmp_path)

    response = client.post(
        "/tenant-scientific-authority/evaluate",
        headers=evaluation_headers(),
        json=evaluation_payload(),
    )

    assert response.status_code == 200

    body = response.json()

    assert body["authorization"]["decision"]["allowed"] is True
    assert body["execution"]["pipeline_result"][
        "decision_allowed"
    ] is True
    assert body["context_binding"]["sequence_number"] == 1
    assert body["context_binding"]["binding"]["context"][
        "tenant_id"
    ] == "tenant-alpha"
    assert len(
        body["context_binding"]["binding"]["binding_hash"]
    ) == 64


def test_cross_tenant_evaluation_is_denied(tmp_path):
    client = build_client(tmp_path)

    response = client.post(
        "/tenant-scientific-authority/evaluate",
        headers=evaluation_headers(
            target_tenant_id="tenant-beta"
        ),
        json=evaluation_payload(),
    )

    assert response.status_code == 403

    detail = response.json()["detail"]

    assert detail["decision"]["allowed"] is False
    assert (
        detail["decision"]["checks"][
            "tenant_matches_context"
        ]
        is False
    )


def test_observer_cannot_evaluate(tmp_path):
    client = build_client(tmp_path)

    response = client.post(
        "/tenant-scientific-authority/evaluate",
        headers=evaluation_headers(
            role_id="scientific-observer"
        ),
        json=evaluation_payload(),
    )

    assert response.status_code == 403
    assert (
        response.json()["detail"]["decision"]["checks"][
            "action_permitted"
        ]
        is False
    )


def test_unverified_credential_is_denied(tmp_path):
    client = build_client(tmp_path)

    response = client.post(
        "/tenant-scientific-authority/evaluate",
        headers=evaluation_headers(),
        json=evaluation_payload(
            credential_verified=False
        ),
    )

    assert response.status_code == 403
    assert (
        response.json()["detail"]["decision"]["checks"][
            "credential_verified"
        ]
        is False
    )


def test_authoritative_request_requires_approver(tmp_path):
    client = build_client(tmp_path)

    response = client.post(
        "/tenant-scientific-authority/evaluate",
        headers=evaluation_headers(),
        json=evaluation_payload(
            requested_authority="AUTHORITATIVE",
            constitutional_approval_submitted=True,
            step_up_verified=True,
        ),
    )

    assert response.status_code == 403


def test_approver_can_submit_authoritative_request(
    tmp_path,
):
    client = build_client(tmp_path)

    response = client.post(
        "/tenant-scientific-authority/evaluate",
        headers=evaluation_headers(
            role_id="scientific-approver"
        ),
        json=evaluation_payload(
            requested_authority="AUTHORITATIVE",
            constitutional_approval_submitted=True,
            step_up_verified=True,
        ),
    )

    assert response.status_code == 200
    assert response.json()["authorization"]["decision"][
        "allowed"
    ] is True


def test_missing_identity_header_returns_422(tmp_path):
    client = build_client(tmp_path)
    headers = evaluation_headers()
    del headers["x-tenant-id"]

    response = client.post(
        "/tenant-scientific-authority/evaluate",
        headers=headers,
        json=evaluation_payload(),
    )

    assert response.status_code == 422


def test_identical_tenant_request_is_idempotent(tmp_path):
    client = build_client(tmp_path)
    headers = evaluation_headers()
    payload = evaluation_payload()

    first = client.post(
        "/tenant-scientific-authority/evaluate",
        headers=headers,
        json=payload,
    )
    second = client.post(
        "/tenant-scientific-authority/evaluate",
        headers=headers,
        json=payload,
    )

    assert first.status_code == 200
    assert second.status_code == 200

    assert first.json()["context_binding"] == (
        second.json()["context_binding"]
    )
    assert second.json()["execution"]["resumed"] is True


def test_request_id_rebinding_is_rejected(tmp_path):
    client = build_client(tmp_path)

    first = client.post(
        "/tenant-scientific-authority/evaluate",
        headers=evaluation_headers(
            role_id="scientific-reviewer",
            request_id="shared-request",
        ),
        json=evaluation_payload(
            requested_authority="ADVISORY"
        ),
    )

    second = client.post(
        "/tenant-scientific-authority/evaluate",
        headers=evaluation_headers(
            role_id="scientific-approver",
            request_id="shared-request",
        ),
        json=evaluation_payload(
            requested_authority="AUTHORITATIVE",
            constitutional_approval_submitted=True,
            step_up_verified=True,
        ),
    )

    assert first.status_code == 200
    assert second.status_code == 409


def test_tenant_can_list_its_own_bindings(tmp_path):
    client = build_client(tmp_path)

    client.post(
        "/tenant-scientific-authority/evaluate",
        headers=evaluation_headers(),
        json=evaluation_payload(),
    )

    response = client.get(
        "/tenant-scientific-authority/"
        "tenants/tenant-alpha/bindings",
        headers=binding_headers(),
    )

    assert response.status_code == 200
    assert response.json()["tenant_id"] == "tenant-alpha"
    assert response.json()["count"] == 1


def test_tenant_cannot_list_another_tenants_bindings(
    tmp_path,
):
    client = build_client(tmp_path)

    response = client.get(
        "/tenant-scientific-authority/"
        "tenants/tenant-beta/bindings",
        headers=binding_headers(
            tenant_id="tenant-alpha"
        ),
    )

    assert response.status_code == 403
    assert (
        response.json()["detail"]["decision"]["checks"][
            "tenant_matches_context"
        ]
        is False
    )


def test_untrusted_binding_read_is_denied(tmp_path):
    client = build_client(tmp_path)
    headers = binding_headers()
    headers["x-device-trusted"] = "false"

    response = client.get(
        "/tenant-scientific-authority/"
        "tenants/tenant-alpha/bindings",
        headers=headers,
    )

    assert response.status_code == 403
