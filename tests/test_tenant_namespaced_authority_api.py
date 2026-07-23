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
        "0.4.0"
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

    assert alpha["public_artifacts"]["execution_id"] != (
        beta["public_artifacts"]["execution_id"]
    )

    assert alpha["public_artifacts"]["checkpoint_id"] != (
        beta["public_artifacts"]["checkpoint_id"]
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
    assert second["execution"]["resumed"] is True


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



def _collect_response_strings(value):
    values = []

    if isinstance(value, str):
        values.append(value)

    elif isinstance(value, dict):
        for item in value.values():
            values.extend(
                _collect_response_strings(item)
            )

    elif isinstance(value, list):
        for item in value:
            values.extend(
                _collect_response_strings(item)
            )

    return values


def test_evaluation_uses_redacted_public_execution_view(
    tmp_path,
):
    client = build_client(tmp_path)

    response = client.post(
        "/tenant-namespaced-scientific-authority/evaluate",
        headers=evaluation_headers(),
        json=evaluation_payload(),
    )

    assert response.status_code == 200

    execution = response.json()["execution"]

    assert execution["view_id"] == (
        "tenant-public-scientific-execution-view"
    )
    assert execution["view_version"] == "0.1.0"
    assert execution["decision_allowed"] is True
    assert execution["checkpoint_valid"] is True
    assert execution["public_artifacts"] == (
        response.json()["public_artifacts"]
    )
    assert len(execution["view_hash"]) == 64


def test_evaluation_response_exposes_no_canonical_fields(
    tmp_path,
):
    client = build_client(tmp_path)

    body = create_execution(client)
    visible_keys = set()

    def collect_keys(value):
        if isinstance(value, dict):
            visible_keys.update(value.keys())

            for item in value.values():
                collect_keys(item)

        elif isinstance(value, list):
            for item in value:
                collect_keys(item)

    collect_keys(body)

    forbidden_keys = {
        "canonical_artifact_id",
        "authority_receipt_hash",
        "audit_receipt_hash",
        "checkpoint_hash",
        "execution_receipt_hash",
        "binding_hash",
    }

    assert forbidden_keys.isdisjoint(visible_keys)





def _collect_artifact_response_keys(value):
    keys = set()

    if isinstance(value, dict):
        keys.update(value.keys())

        for item in value.values():
            keys.update(
                _collect_artifact_response_keys(item)
            )

    elif isinstance(value, list):
        for item in value:
            keys.update(
                _collect_artifact_response_keys(item)
            )

    return keys


def test_artifact_resolution_uses_public_view(tmp_path):
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

    body = response.json()

    assert body["view_id"] == (
        "tenant-public-scientific-artifact-view"
    )
    assert body["public_artifact_id"] == public_id
    assert body["artifact_type"] == "checkpoint"
    assert len(body["view_hash"]) == 64


def test_artifact_resolution_exposes_no_canonical_fields(
    tmp_path,
):
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

    body = response.json()

    public_view = {
        key: value
        for key, value in body.items()
        if key not in {
            "api_id",
            "api_version",
            "authorization",
        }
    }

    keys = _collect_artifact_response_keys(
        public_view
    )

    forbidden = {
        "canonical_artifact_id",
        "artifact_id",
        "binding_hash",
        "receipt_hash",
        "execution_receipt_hash",
        "authority_receipt_hash",
        "audit_receipt_hash",
        "checkpoint_hash",
        "context_hash",
    }

    assert forbidden.isdisjoint(keys)

    assert len(
        body["authorization"]["receipt"][
            "public_receipt_id"
        ]
    ) == 64

    assert "receipt_hash" not in (
        body["authorization"]["receipt"]
    )




def test_successful_authorization_uses_public_view(
    tmp_path,
):
    client = build_client(tmp_path)

    body = create_execution(client)
    authorization = body["authorization"]

    assert authorization["view_id"] == (
        "tenant-public-scientific-authorization-view"
    )
    assert authorization["decision"]["allowed"] is True
    assert authorization["decision"]["tenant_id"] == (
        "tenant-alpha"
    )
    assert len(
        authorization["receipt"]["public_receipt_id"]
    ) == 64
    assert len(authorization["view_hash"]) == 64


def test_authorization_response_exposes_no_identity_secrets(
    tmp_path,
):
    client = build_client(tmp_path)

    body = create_execution(client)
    authorization = body["authorization"]

    keys = _collect_artifact_response_keys(
        authorization
    )

    forbidden = {
        "actor_id",
        "credential_id",
        "session_id",
        "request_id",
        "correlation_id",
        "trust_signals",
        "receipt_hash",
    }

    assert forbidden.isdisjoint(keys)


def test_denied_authorization_uses_public_view(tmp_path):
    client = build_client(tmp_path)
    headers = evaluation_headers()
    headers["x-role-id"] = "scientific-observer"

    response = client.post(
        "/tenant-namespaced-scientific-authority/evaluate",
        headers=headers,
        json=evaluation_payload(),
    )

    assert response.status_code == 403

    detail = response.json()["detail"]

    assert detail["view_id"] == (
        "tenant-public-scientific-authorization-view"
    )
    assert detail["decision"]["allowed"] is False
    assert (
        detail["decision"]["checks"]["action_permitted"]
        is False
    )
    assert "authorization_receipt" not in detail
