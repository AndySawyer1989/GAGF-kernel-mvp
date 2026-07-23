from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.app.gagf.tenant_application_router_registry import (
    TenantApplicationDatabasePaths,
    register_tenant_application_routers,
)
from backend.app.gagf.tenant_public_boundary_auditor import (
    TenantPublicBoundaryAuditor,
)
from tests.test_tenant_boundary_audit_query_api import (
    trusted_headers as audit_headers,
)
from tests.test_tenant_namespaced_authority_api import (
    create_execution,
    read_headers,
)


def build_integrated_client(tmp_path):
    app = FastAPI()

    database_paths = (
        TenantApplicationDatabasePaths.from_directory(
            database_directory=(
                tmp_path / "tenant-application"
            )
        )
    )

    registration = register_tenant_application_routers(
        app=app,
        database_paths=database_paths,
    )

    return (
        TestClient(app),
        database_paths,
        registration,
    )


def assert_public_response_is_safe(response_body):
    audit = TenantPublicBoundaryAuditor().audit(
        response=response_body
    )

    assert audit.valid is True
    assert audit.violation_count == 0


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


def test_two_tenants_receive_distinct_public_executions(
    tmp_path,
):
    client, _, _ = build_integrated_client(tmp_path)

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

    assert alpha["tenant_id"] == "tenant-alpha"
    assert beta["tenant_id"] == "tenant-beta"

    assert alpha["public_artifacts"]["execution_id"] != (
        beta["public_artifacts"]["execution_id"]
    )
    assert alpha["public_artifacts"]["checkpoint_id"] != (
        beta["public_artifacts"]["checkpoint_id"]
    )
    assert (
        alpha["public_artifacts"]["context_binding_id"]
        != beta["public_artifacts"]["context_binding_id"]
    )

    assert_public_response_is_safe(alpha)
    assert_public_response_is_safe(beta)


def test_each_tenant_retrieves_own_execution(
    tmp_path,
):
    client, _, _ = build_integrated_client(tmp_path)

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

    alpha_public_id = alpha["public_artifacts"][
        "execution_id"
    ]
    beta_public_id = beta["public_artifacts"][
        "execution_id"
    ]

    alpha_response = client.get(
        "/tenant-namespaced-scientific-authority/"
        f"executions/{alpha_public_id}",
        headers=read_headers(
            tenant_id="tenant-alpha"
        ),
    )
    beta_response = client.get(
        "/tenant-namespaced-scientific-authority/"
        f"executions/{beta_public_id}",
        headers=read_headers(
            tenant_id="tenant-beta"
        ),
    )

    assert alpha_response.status_code == 200
    assert beta_response.status_code == 200

    assert alpha_response.json()["tenant_id"] == (
        "tenant-alpha"
    )
    assert beta_response.json()["tenant_id"] == (
        "tenant-beta"
    )

    assert (
        alpha_response.json()["public_artifact_id"]
        == alpha_public_id
    )
    assert (
        beta_response.json()["public_artifact_id"]
        == beta_public_id
    )

    assert_public_response_is_safe(
        alpha_response.json()
    )
    assert_public_response_is_safe(
        beta_response.json()
    )


def test_cross_tenant_execution_access_returns_not_found(
    tmp_path,
):
    client, _, _ = build_integrated_client(tmp_path)

    alpha = create_execution(
        client,
        tenant_id="tenant-alpha",
        request_id="request-alpha",
    )

    alpha_public_id = alpha["public_artifacts"][
        "execution_id"
    ]

    response = client.get(
        "/tenant-namespaced-scientific-authority/"
        f"executions/{alpha_public_id}",
        headers=read_headers(
            tenant_id="tenant-beta"
        ),
    )

    assert response.status_code == 404

    serialized = str(response.json())

    assert alpha_public_id not in serialized
    assert "canonical_artifact_id" not in serialized


def test_tenant_audit_queries_are_isolated(
    tmp_path,
):
    client, _, _ = build_integrated_client(tmp_path)

    create_execution(
        client,
        tenant_id="tenant-alpha",
        request_id="request-alpha",
    )
    create_execution(
        client,
        tenant_id="tenant-beta",
        request_id="request-beta",
    )

    alpha_response = client.get(
        "/tenant-boundary-audit/records",
        params={
            "page_size": 100,
        },
        headers=audit_headers(
            tenant_id="tenant-alpha"
        ),
    )
    beta_response = client.get(
        "/tenant-boundary-audit/records",
        params={
            "page_size": 100,
        },
        headers=audit_headers(
            tenant_id="tenant-beta"
        ),
    )

    assert alpha_response.status_code == 200
    assert beta_response.status_code == 200

    alpha_page = alpha_response.json()["page"]
    beta_page = beta_response.json()["page"]

    assert alpha_page["tenant_id"] == "tenant-alpha"
    assert beta_page["tenant_id"] == "tenant-beta"

    assert alpha_page["returned_count"] >= 1
    assert beta_page["returned_count"] >= 1

    assert all(
        record["tenant_id"] == "tenant-alpha"
        for record in alpha_page["records"]
    )
    assert all(
        record["tenant_id"] == "tenant-beta"
        for record in beta_page["records"]
    )

    alpha_public_ids = {
        record["public_record_id"]
        for record in alpha_page["records"]
    }
    beta_public_ids = {
        record["public_record_id"]
        for record in beta_page["records"]
    }

    assert alpha_public_ids.isdisjoint(
        beta_public_ids
    )

    assert_public_response_is_safe(
        alpha_response.json()
    )
    assert_public_response_is_safe(
        beta_response.json()
    )


def test_other_tenant_cannot_resolve_audit_record(
    tmp_path,
):
    client, _, _ = build_integrated_client(tmp_path)

    create_execution(
        client,
        tenant_id="tenant-alpha",
        request_id="request-alpha",
    )

    alpha_list = client.get(
        "/tenant-boundary-audit/records",
        params={
            "page_size": 100,
        },
        headers=audit_headers(
            tenant_id="tenant-alpha"
        ),
    )

    assert alpha_list.status_code == 200

    alpha_records = alpha_list.json()["page"][
        "records"
    ]

    assert alpha_records

    public_record_id = alpha_records[0][
        "public_record_id"
    ]

    response = client.get(
        "/tenant-boundary-audit/records/"
        f"{public_record_id}",
        headers=audit_headers(
            tenant_id="tenant-beta"
        ),
    )

    assert response.status_code == 404

    assert public_record_id not in str(
        response.json()
    )


def test_active_pagination_snapshot_excludes_new_access_records(
    tmp_path,
):
    client, _, _ = build_integrated_client(tmp_path)

    for index in range(3):
        create_execution(
            client,
            tenant_id="tenant-alpha",
            request_id=f"request-alpha-{index + 1}",
        )

    first_response = client.get(
        "/tenant-boundary-audit/records",
        params={
            "page_size": 2,
        },
        headers=audit_headers(
            tenant_id="tenant-alpha"
        ),
    )

    assert first_response.status_code == 200

    first_page = first_response.json()["page"]

    assert first_page["returned_count"] == 2
    assert first_page["next_cursor"] is not None

    frozen_snapshot = first_page[
        "snapshot_sequence"
    ]

    second_response = client.get(
        "/tenant-boundary-audit/records",
        params={
            "page_size": 2,
            "cursor": first_page["next_cursor"],
        },
        headers=audit_headers(
            tenant_id="tenant-alpha"
        ),
    )

    assert second_response.status_code == 200

    second_page = second_response.json()["page"]

    assert second_page["snapshot_sequence"] == (
        frozen_snapshot
    )

    assert all(
        record["tenant_sequence_number"]
        <= frozen_snapshot
        for record in second_page["records"]
    )


def test_complete_public_surface_exposes_no_internal_fields(
    tmp_path,
):
    client, _, _ = build_integrated_client(tmp_path)

    created = create_execution(
        client,
        tenant_id="tenant-alpha",
        request_id="request-alpha",
    )

    execution_response = client.get(
        "/tenant-namespaced-scientific-authority/"
        f"executions/"
        f"{created['public_artifacts']['execution_id']}",
        headers=read_headers(
            tenant_id="tenant-alpha"
        ),
    )

    audit_response = client.get(
        "/tenant-boundary-audit/records",
        headers=audit_headers(
            tenant_id="tenant-alpha"
        ),
    )

    assert execution_response.status_code == 200
    assert audit_response.status_code == 200

    public_payloads = (
        created,
        execution_response.json(),
        audit_response.json(),
    )

    forbidden_keys = {
        "canonical_artifact_id",
        "actor_id",
        "credential_id",
        "session_id",
        "request_id",
        "correlation_id",
        "trust_signals",
        "authorization_receipt",
        "internal_receipt_commitment",
    }

    for payload in public_payloads:
        keys = collect_keys(payload)

        assert forbidden_keys.isdisjoint(keys)
        assert_public_response_is_safe(payload)


def test_integrated_registration_uses_shared_evidence_path(
    tmp_path,
):
    _, paths, registration = (
        build_integrated_client(tmp_path)
    )

    assert registration.registered is True

    assert (
        registration.database_paths
        .boundary_audit_database_path
        == paths.boundary_audit_database_path
    )

    assert (
        paths.boundary_audit_database_path.parent
        == paths.namespace_database_path.parent
    )
