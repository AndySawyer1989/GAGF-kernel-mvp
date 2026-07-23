from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.app.gagf.tenant_boundary_audit_query_api import (
    TENANT_BOUNDARY_AUDIT_QUERY_API_ID,
    TENANT_BOUNDARY_AUDIT_QUERY_API_VERSION,
    create_tenant_boundary_audit_query_router,
)
from backend.app.gagf.tenant_public_boundary_audit_ledger import (
    TenantPublicBoundaryAuditLedger,
)
from backend.app.gagf.tenant_public_boundary_auditor import (
    TenantPublicBoundaryAuditor,
)


def safe_audit(*, tenant_id):
    return TenantPublicBoundaryAuditor().audit(
        response={
            "tenant_id": tenant_id,
            "public_artifact_id": "a" * 64,
            "view_hash": "b" * 64,
        }
    )


def build_client(tmp_path):
    database_path = tmp_path / "boundary-audit.db"

    app = FastAPI()
    app.include_router(
        create_tenant_boundary_audit_query_router(
            database_path=database_path
        )
    )

    return (
        TestClient(app),
        TenantPublicBoundaryAuditLedger(
            database_path
        ),
    )


def trusted_headers(
    *,
    tenant_id="tenant-alpha",
    role_id="scientific-reviewer",
    scope="boundary-audit:read",
):
    return {
        "x-tenant-id": tenant_id,
        "x-role-id": role_id,
        "x-policy-scope": scope,
        "x-credential-verified": "true",
        "x-session-verified": "true",
        "x-device-trusted": "true",
        "x-tenant-membership-verified": "true",
    }


def append_record(
    ledger,
    *,
    tenant_id="tenant-alpha",
    response_kind="evaluation",
):
    return ledger.append(
        tenant_id=tenant_id,
        response_kind=response_kind,
        released=True,
        audit=safe_audit(
            tenant_id=tenant_id
        ),
    )


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


def test_api_has_stable_identity():
    assert TENANT_BOUNDARY_AUDIT_QUERY_API_ID == (
        "tenant-boundary-audit-evidence-query-api"
    )
    assert TENANT_BOUNDARY_AUDIT_QUERY_API_VERSION == (
        "0.2.0"
    )


def test_tenant_can_list_own_records(tmp_path):
    client, ledger = build_client(tmp_path)

    append_record(ledger)
    append_record(
        ledger,
        response_kind="checkpoint-read",
    )

    response = client.get(
        "/tenant-boundary-audit/records",
        headers=trusted_headers(),
    )

    assert response.status_code == 200

    body = response.json()

    assert body["api_id"] == (
        TENANT_BOUNDARY_AUDIT_QUERY_API_ID
    )
    assert body["result"]["tenant_id"] == (
        "tenant-alpha"
    )
    assert body["result"]["record_count"] == 2
    assert body["boundary_audit"]["valid"] is True


def test_cross_tenant_records_are_excluded(tmp_path):
    client, ledger = build_client(tmp_path)

    append_record(
        ledger,
        tenant_id="tenant-alpha",
    )
    append_record(
        ledger,
        tenant_id="tenant-beta",
    )

    response = client.get(
        "/tenant-boundary-audit/records",
        headers=trusted_headers(
            tenant_id="tenant-alpha"
        ),
    )

    assert response.status_code == 200
    assert (
        response.json()["result"]["record_count"]
        == 1
    )
    assert (
        response.json()["result"]["records"][0][
            "tenant_id"
        ]
        == "tenant-alpha"
    )


def test_tenant_can_get_own_public_record(tmp_path):
    client, ledger = build_client(tmp_path)

    append_record(ledger)

    listed = client.get(
        "/tenant-boundary-audit/records",
        headers=trusted_headers(),
    ).json()

    public_record_id = listed["result"]["records"][0][
        "public_record_id"
    ]

    response = client.get(
        "/tenant-boundary-audit/records/"
        f"{public_record_id}",
        headers=trusted_headers(),
    )

    assert response.status_code == 200
    assert response.json()["record"][
        "public_record_id"
    ] == public_record_id


def test_other_tenant_gets_not_found(tmp_path):
    client, ledger = build_client(tmp_path)

    append_record(
        ledger,
        tenant_id="tenant-alpha",
    )

    listed = client.get(
        "/tenant-boundary-audit/records",
        headers=trusted_headers(
            tenant_id="tenant-alpha"
        ),
    ).json()

    public_record_id = listed["result"]["records"][0][
        "public_record_id"
    ]

    response = client.get(
        "/tenant-boundary-audit/records/"
        f"{public_record_id}",
        headers=trusted_headers(
            tenant_id="tenant-beta"
        ),
    )

    assert response.status_code == 404


def test_unknown_record_returns_not_found(tmp_path):
    client, _ = build_client(tmp_path)

    response = client.get(
        "/tenant-boundary-audit/records/"
        f"{'f' * 64}",
        headers=trusted_headers(),
    )

    assert response.status_code == 404


def test_tenant_auditor_role_is_allowed(tmp_path):
    client, ledger = build_client(tmp_path)
    append_record(ledger)

    response = client.get(
        "/tenant-boundary-audit/records",
        headers=trusted_headers(
            role_id="tenant-auditor"
        ),
    )

    assert response.status_code == 200


def test_observer_role_is_denied(tmp_path):
    client, _ = build_client(tmp_path)

    response = client.get(
        "/tenant-boundary-audit/records",
        headers=trusted_headers(
            role_id="scientific-observer"
        ),
    )

    assert response.status_code == 403

    detail = response.json()["detail"]

    assert detail["authorization"]["allowed"] is False
    assert (
        detail["authorization"]["checks"][
            "role_permitted"
        ]
        is False
    )
    assert detail["boundary_audit"]["valid"] is True


def test_wrong_scope_is_denied(tmp_path):
    client, _ = build_client(tmp_path)

    response = client.get(
        "/tenant-boundary-audit/records",
        headers=trusted_headers(
            scope="scientific-authority:evaluate"
        ),
    )

    assert response.status_code == 403
    assert (
        response.json()["detail"][
            "authorization"
        ]["checks"]["scope_permitted"]
        is False
    )


def test_untrusted_device_is_denied(tmp_path):
    client, _ = build_client(tmp_path)

    headers = trusted_headers()
    headers["x-device-trusted"] = "false"

    response = client.get(
        "/tenant-boundary-audit/records",
        headers=headers,
    )

    assert response.status_code == 403
    assert (
        response.json()["detail"][
            "authorization"
        ]["checks"]["device_trusted"]
        is False
    )


def test_invalid_boolean_header_returns_400(tmp_path):
    client, _ = build_client(tmp_path)

    headers = trusted_headers()
    headers["x-session-verified"] = "unknown"

    response = client.get(
        "/tenant-boundary-audit/records",
        headers=headers,
    )

    assert response.status_code == 400


def test_response_hides_global_ledger_fields(tmp_path):
    client, ledger = build_client(tmp_path)
    append_record(ledger)

    response = client.get(
        "/tenant-boundary-audit/records",
        headers=trusted_headers(),
    )

    assert response.status_code == 200

    body = response.json()
    result_keys = collect_keys(body["result"])

    forbidden = {
        "sequence_number",
        "previous_record_hash",
        "record_hash",
        "boundary_audit_hash",
        "ledger_id",
        "ledger_version",
        "credential_id",
        "session_id",
        "request_id",
        "correlation_id",
    }

    assert forbidden.isdisjoint(result_keys)

    release_record = body["boundary_audit_record"]

    assert release_record["response_kind"] == (
        "boundary-audit-list"
    )
    assert release_record["released"] is True
    assert release_record["audit_valid"] is True

def test_response_passes_runtime_boundary_gate(
    tmp_path,
):
    client, ledger = build_client(tmp_path)
    append_record(ledger)

    response = client.get(
        "/tenant-boundary-audit/records",
        headers=trusted_headers(),
    )

    assert response.status_code == 200
    assert (
        response.json()["boundary_audit"]["valid"]
        is True
    )
    assert (
        response.json()["boundary_audit"][
            "violation_count"
        ]
        == 0
    )



def test_list_access_is_recorded(tmp_path):
    client, ledger = build_client(tmp_path)

    append_record(ledger)

    response = client.get(
        "/tenant-boundary-audit/records",
        headers=trusted_headers(),
    )

    assert response.status_code == 200

    records = ledger.list_records(
        tenant_id="tenant-alpha"
    )

    assert records[-1].response_kind == (
        "boundary-audit-list"
    )
    assert records[-1].released is True
    assert records[-1].audit_valid is True


def test_record_read_access_is_recorded(tmp_path):
    client, ledger = build_client(tmp_path)

    append_record(ledger)

    listed = client.get(
        "/tenant-boundary-audit/records",
        headers=trusted_headers(),
    ).json()

    public_record_id = listed["result"]["records"][0][
        "public_record_id"
    ]

    response = client.get(
        "/tenant-boundary-audit/records/"
        f"{public_record_id}",
        headers=trusted_headers(),
    )

    assert response.status_code == 200

    records = ledger.list_records(
        tenant_id="tenant-alpha"
    )

    assert records[-1].response_kind == (
        "boundary-audit-record-read"
    )
    assert records[-1].released is True


def test_denied_query_is_recorded(tmp_path):
    client, ledger = build_client(tmp_path)

    response = client.get(
        "/tenant-boundary-audit/records",
        headers=trusted_headers(
            role_id="scientific-observer"
        ),
    )

    assert response.status_code == 403

    records = ledger.list_records(
        tenant_id="tenant-alpha"
    )

    assert len(records) == 1
    assert records[0].response_kind == (
        "boundary-audit-query-denial"
    )
    assert records[0].released is True
    assert records[0].audit_valid is True


def test_query_response_contains_ledger_evidence(
    tmp_path,
):
    client, ledger = build_client(tmp_path)

    append_record(ledger)

    response = client.get(
        "/tenant-boundary-audit/records",
        headers=trusted_headers(),
    )

    assert response.status_code == 200

    record = response.json()[
        "boundary_audit_record"
    ]

    assert record["response_kind"] == (
        "boundary-audit-list"
    )
    assert record["released"] is True
    assert record["audit_valid"] is True

