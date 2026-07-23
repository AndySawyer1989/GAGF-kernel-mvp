from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.app.gagf.tenant_scientific_authority_api import (
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
                audit_database_path=tmp_path / "audit.db",
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
    request_id="request-1",
):
    return {
        "x-tenant-id": tenant_id,
        "x-target-tenant-id": tenant_id,
        "x-actor-id": "actor-1",
        "x-credential-id": "credential-1",
        "x-session-id": "session-1",
        "x-role-id": "scientific-reviewer",
        "x-policy-scope": "scientific-authority:evaluate",
        "x-request-id": request_id,
        "x-correlation-id": "correlation-1",
    }


def evaluation_payload():
    return {
        "calculation_id": "evidence-confidence",
        "requested_authority": "ADVISORY",
        "constitutional_approval_submitted": False,
        "evidence": {
            "deterministic_replay_verified": True,
            "canonical_input_binding_verified": True,
            "calculation_version_frozen": True,
            "regression_suite_passed": True,
            "validation_report_present": True,
            "constitutional_approval_present": True,
        },
        "trust_signals": {
            "credential_verified": True,
            "session_verified": True,
            "device_trusted": True,
            "step_up_verified": False,
            "tenant_membership_verified": True,
        },
    }


def artifact_headers(
    *,
    tenant_id="tenant-alpha",
    policy_scope="scientific-authority:read-receipt",
    role_id="scientific-observer",
    request_id="artifact-read-1",
):
    return {
        "x-tenant-id": tenant_id,
        "x-actor-id": "actor-1",
        "x-credential-id": "credential-1",
        "x-session-id": "session-1",
        "x-role-id": role_id,
        "x-policy-scope": policy_scope,
        "x-request-id": request_id,
        "x-correlation-id": "artifact-correlation",
        "x-credential-verified": "true",
        "x-session-verified": "true",
        "x-device-trusted": "true",
        "x-tenant-membership-verified": "true",
    }


def create_execution(client):
    response = client.post(
        "/tenant-scientific-authority/evaluate",
        headers=evaluation_headers(),
        json=evaluation_payload(),
    )
    assert response.status_code == 200
    return response.json()


def test_tenant_can_read_bound_receipt(tmp_path):
    client = build_client(tmp_path)
    execution = create_execution(client)

    receipt_hash = (
        execution["execution"]["pipeline_result"]
        ["authority_receipt_hash"]
    )

    response = client.get(
        f"/tenant-scientific-authority/receipts/{receipt_hash}",
        headers=artifact_headers(),
    )

    assert response.status_code == 200
    assert response.json()["tenant_id"] == "tenant-alpha"
    assert response.json()["artifact_type"] == (
        "authority_receipt"
    )


def test_other_tenant_cannot_read_receipt(tmp_path):
    client = build_client(tmp_path)
    execution = create_execution(client)

    receipt_hash = (
        execution["execution"]["pipeline_result"]
        ["authority_receipt_hash"]
    )

    response = client.get(
        f"/tenant-scientific-authority/receipts/{receipt_hash}",
        headers=artifact_headers(
            tenant_id="tenant-beta"
        ),
    )

    assert response.status_code == 403


def test_unknown_receipt_returns_404(tmp_path):
    client = build_client(tmp_path)

    response = client.get(
        "/tenant-scientific-authority/receipts/"
        + ("0" * 64),
        headers=artifact_headers(),
    )

    assert response.status_code == 404


def test_tenant_can_read_bound_checkpoint(tmp_path):
    client = build_client(tmp_path)
    execution = create_execution(client)

    checkpoint_hash = (
        execution["execution"]["pipeline_result"]
        ["checkpoint_hash"]
    )

    response = client.get(
        "/tenant-scientific-authority/checkpoints/"
        + checkpoint_hash,
        headers=artifact_headers(
            policy_scope=(
                "scientific-authority:read-checkpoint"
            )
        ),
    )

    assert response.status_code == 200
    assert response.json()["artifact_type"] == "checkpoint"


def test_other_tenant_cannot_read_checkpoint(tmp_path):
    client = build_client(tmp_path)
    execution = create_execution(client)

    checkpoint_hash = (
        execution["execution"]["pipeline_result"]
        ["checkpoint_hash"]
    )

    response = client.get(
        "/tenant-scientific-authority/checkpoints/"
        + checkpoint_hash,
        headers=artifact_headers(
            tenant_id="tenant-beta",
            policy_scope=(
                "scientific-authority:read-checkpoint"
            ),
        ),
    )

    assert response.status_code == 403


def test_reviewer_can_verify_bound_checkpoint(tmp_path):
    client = build_client(tmp_path)
    execution = create_execution(client)

    checkpoint_hash = (
        execution["execution"]["pipeline_result"]
        ["checkpoint_hash"]
    )

    response = client.post(
        "/tenant-scientific-authority/checkpoints/"
        + checkpoint_hash
        + "/verify",
        headers=artifact_headers(
            role_id="scientific-reviewer",
            policy_scope=(
                "scientific-authority:verify-checkpoint"
            ),
        ),
    )

    assert response.status_code == 200
    assert response.json()["verification"]["valid"] is True
    assert len(response.json()["binding_hash"]) == 64


def test_observer_cannot_verify_checkpoint(tmp_path):
    client = build_client(tmp_path)
    execution = create_execution(client)

    checkpoint_hash = (
        execution["execution"]["pipeline_result"]
        ["checkpoint_hash"]
    )

    response = client.post(
        "/tenant-scientific-authority/checkpoints/"
        + checkpoint_hash
        + "/verify",
        headers=artifact_headers(
            role_id="scientific-observer",
            policy_scope=(
                "scientific-authority:verify-checkpoint"
            ),
        ),
    )

    assert response.status_code == 403


def test_tenant_can_read_bound_execution(tmp_path):
    client = build_client(tmp_path)
    created = create_execution(client)

    execution_id = created["execution"]["execution_id"]

    response = client.get(
        f"/tenant-scientific-authority/executions/{execution_id}",
        headers=artifact_headers(
            policy_scope=(
                "scientific-authority:read-execution"
            )
        ),
    )

    assert response.status_code == 200
    assert response.json()["execution_id"] == execution_id
    assert response.json()["execution"]["state"] == "COMPLETED"


def test_other_tenant_cannot_read_execution(tmp_path):
    client = build_client(tmp_path)
    created = create_execution(client)

    execution_id = created["execution"]["execution_id"]

    response = client.get(
        f"/tenant-scientific-authority/executions/{execution_id}",
        headers=artifact_headers(
            tenant_id="tenant-beta",
            policy_scope=(
                "scientific-authority:read-execution"
            ),
        ),
    )

    assert response.status_code == 403


def test_tenant_can_read_its_binding(tmp_path):
    client = build_client(tmp_path)
    created = create_execution(client)

    binding_hash = (
        created["context_binding"]["binding"]
        ["binding_hash"]
    )

    response = client.get(
        f"/tenant-scientific-authority/bindings/{binding_hash}",
        headers=artifact_headers(
            policy_scope=(
                "scientific-authority:read-execution"
            )
        ),
    )

    assert response.status_code == 200
    assert response.json()["artifact_type"] == (
        "context_binding"
    )


def test_other_tenant_cannot_read_binding(tmp_path):
    client = build_client(tmp_path)
    created = create_execution(client)

    binding_hash = (
        created["context_binding"]["binding"]
        ["binding_hash"]
    )

    response = client.get(
        f"/tenant-scientific-authority/bindings/{binding_hash}",
        headers=artifact_headers(
            tenant_id="tenant-beta",
            policy_scope=(
                "scientific-authority:read-execution"
            ),
        ),
    )

    assert response.status_code == 403


def test_untrusted_device_cannot_read_artifact(tmp_path):
    client = build_client(tmp_path)
    execution = create_execution(client)

    receipt_hash = (
        execution["execution"]["pipeline_result"]
        ["authority_receipt_hash"]
    )
    headers = artifact_headers()
    headers["x-device-trusted"] = "false"

    response = client.get(
        f"/tenant-scientific-authority/receipts/{receipt_hash}",
        headers=headers,
    )

    assert response.status_code == 403
    assert (
        response.json()["detail"]["decision"]["checks"]
        ["device_trusted"]
        is False
    )


def test_wrong_scope_cannot_read_receipt(tmp_path):
    client = build_client(tmp_path)
    execution = create_execution(client)

    receipt_hash = (
        execution["execution"]["pipeline_result"]
        ["authority_receipt_hash"]
    )

    response = client.get(
        f"/tenant-scientific-authority/receipts/{receipt_hash}",
        headers=artifact_headers(
            policy_scope=(
                "scientific-authority:read-checkpoint"
            )
        ),
    )

    assert response.status_code == 403
