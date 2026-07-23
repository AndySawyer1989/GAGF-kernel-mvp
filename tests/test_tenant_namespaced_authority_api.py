from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.app.gagf.tenant_namespaced_authority_api import (
    TENANT_NAMESPACED_AUTHORITY_API_ID,
    TENANT_NAMESPACED_AUTHORITY_API_VERSION,
    TenantNamespacedAuthorityApiPaths,
    create_tenant_namespaced_authority_router,
)


def build_client(tmp_path) -> TestClient:
    app = FastAPI()

    app.include_router(
        create_tenant_namespaced_authority_router(
            paths=TenantNamespacedAuthorityApiPaths(
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
                namespace_database_path=(
                    tmp_path / "namespaces.db"
                ),
            )
        )
    )

    return TestClient(app)


def evaluation_headers(
    *,
    tenant_id="tenant-alpha",
    request_id="request-alpha",
):
    return {
        "x-tenant-id": tenant_id,
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


def read_headers(
    *,
    tenant_id="tenant-alpha",
    scope="scientific-authority:read-execution",
    role_id="scientific-observer",
):
    return {
        "x-tenant-id": tenant_id,
        "x-actor-id": "actor-1",
        "x-credential-id": "credential-1",
        "x-session-id": "session-1",
        "x-role-id": role_id,
        "x-policy-scope": scope,
        "x-request-id": "read-request",
        "x-correlation-id": "read-correlation",
        "x-credential-verified": "true",
        "x-session-verified": "true",
        "x-device-trusted": "true",
        "x-tenant-membership-verified": "true",
    }


def create_execution(
    client,
    *,
    tenant_id="tenant-alpha",
    request_id="request-alpha",
):
    response = client.post(
        "/tenant-namespaced-scientific-authority/evaluate",
        headers=evaluation_headers(
            tenant_id=tenant_id,
            request_id=request_id,
        ),
        json=evaluation_payload(),
    )

    assert response.status_code == 200
    return response.json()


def test_api_has_stable_identity():
    assert TENANT_NAMESPACED_AUTHORITY_API_ID == (
        "tenant-namespaced-scientific-authority-api"
    )
    assert TENANT_NAMESPACED_AUTHORITY_API_VERSION == (
        "0.1.0"
    )


def test_evaluation_returns_public_artifact_ids(tmp_path):
    client = build_client(tmp_path)

    body = create_execution(client)
    public = body["public_artifacts"]

    assert body["tenant_id"] == "tenant-alpha"
    assert len(public["execution_id"]) == 64
    assert len(public["authority_receipt_id"]) == 64
    assert len(public["checkpoint_id"]) == 64
    assert len(public["context_binding_id"]) == 64


def test_identical_cross_tenant_evaluations_are_allowed(
    tmp_path,
):
    client = build_client(tmp_path)

    alpha = create_execution(
        client,
        tenant_id="tenant-alpha",
        request_id="request-alpha",
    )
    beta = create_execution(
        client,
        tenant_id="tenant-beta",
        request_id="request-beta",
    )

    assert alpha["execution"]["pipeline_result"][
        "execution_id"
    ] == beta["execution"]["pipeline_result"][
        "execution_id"
    ]

    assert alpha["public_artifacts"]["execution_id"] != (
        beta["public_artifacts"]["execution_id"]
    )


def test_same_tenant_replay_returns_same_public_ids(
    tmp_path,
):
    client = build_client(tmp_path)

    first = create_execution(client)
    second = create_execution(client)

    assert first["public_artifacts"] == (
        second["public_artifacts"]
    )
    assert second["execution"]["pipeline_result"][
        "resumed"
    ] is True


def test_tenant_reads_public_authority_receipt(tmp_path):
    client = build_client(tmp_path)
    created = create_execution(client)

    public_id = created["public_artifacts"][
        "authority_receipt_id"
    ]

    response = client.get(
        "/tenant-namespaced-scientific-authority/"
        f"receipts/{public_id}",
        headers=read_headers(
            scope="scientific-authority:read-receipt"
        ),
    )

    assert response.status_code == 200
    assert response.json()["artifact_type"] == (
        "authority_receipt"
    )


def test_tenant_reads_public_checkpoint(tmp_path):
    client = build_client(tmp_path)
    created = create_execution(client)

    public_id = created["public_artifacts"][
        "checkpoint_id"
    ]

    response = client.get(
        "/tenant-namespaced-scientific-authority/"
        f"checkpoints/{public_id}",
        headers=read_headers(
            scope="scientific-authority:read-checkpoint"
        ),
    )

    assert response.status_code == 200
    assert response.json()["artifact_type"] == "checkpoint"


def test_tenant_reads_public_execution(tmp_path):
    client = build_client(tmp_path)
    created = create_execution(client)

    public_id = created["public_artifacts"][
        "execution_id"
    ]

    response = client.get(
        "/tenant-namespaced-scientific-authority/"
        f"executions/{public_id}",
        headers=read_headers(),
    )

    assert response.status_code == 200
    assert response.json()["artifact_type"] == "execution"


def test_tenant_reads_public_context_binding(tmp_path):
    client = build_client(tmp_path)
    created = create_execution(client)

    public_id = created["public_artifacts"][
        "context_binding_id"
    ]

    response = client.get(
        "/tenant-namespaced-scientific-authority/"
        f"bindings/{public_id}",
        headers=read_headers(),
    )

    assert response.status_code == 200
    assert response.json()["artifact_type"] == (
        "context_binding"
    )


def test_other_tenant_cannot_resolve_public_id(tmp_path):
    client = build_client(tmp_path)
    created = create_execution(client)

    public_id = created["public_artifacts"][
        "checkpoint_id"
    ]

    response = client.get(
        "/tenant-namespaced-scientific-authority/"
        f"checkpoints/{public_id}",
        headers=read_headers(
            tenant_id="tenant-beta",
            scope="scientific-authority:read-checkpoint",
        ),
    )

    assert response.status_code == 404


def test_unknown_public_id_returns_404(tmp_path):
    client = build_client(tmp_path)

    response = client.get(
        "/tenant-namespaced-scientific-authority/"
        + "executions/"
        + ("0" * 64),
        headers=read_headers(),
    )

    assert response.status_code == 404


def test_untrusted_device_is_denied_before_resolution(
    tmp_path,
):
    client = build_client(tmp_path)
    created = create_execution(client)

    public_id = created["public_artifacts"][
        "execution_id"
    ]
    headers = read_headers()
    headers["x-device-trusted"] = "false"

    response = client.get(
        "/tenant-namespaced-scientific-authority/"
        f"executions/{public_id}",
        headers=headers,
    )

    assert response.status_code == 403
    assert response.json()["detail"]["decision"][
        "checks"
    ]["device_trusted"] is False


def test_wrong_scope_is_denied(tmp_path):
    client = build_client(tmp_path)
    created = create_execution(client)

    public_id = created["public_artifacts"][
        "authority_receipt_id"
    ]

    response = client.get(
        "/tenant-namespaced-scientific-authority/"
        f"receipts/{public_id}",
        headers=read_headers(
            scope="scientific-authority:read-execution"
        ),
    )

    assert response.status_code == 403


def test_observer_cannot_evaluate(tmp_path):
    client = build_client(tmp_path)
    headers = evaluation_headers()
    headers["x-role-id"] = "scientific-observer"

    response = client.post(
        "/tenant-namespaced-scientific-authority/evaluate",
        headers=headers,
        json=evaluation_payload(),
    )

    assert response.status_code == 403


def test_unknown_contract_returns_404(tmp_path):
    client = build_client(tmp_path)
    payload = evaluation_payload()
    payload["calculation_id"] = "unknown-calculation"

    response = client.post(
        "/tenant-namespaced-scientific-authority/evaluate",
        headers=evaluation_headers(),
        json=payload,
    )

    assert response.status_code == 404
