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
        "0.3.0"
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
    assert body["page"]["tenant_id"] == (
        "tenant-alpha"
    )
    assert body["page"]["returned_count"] == 2
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
        response.json()["page"]["returned_count"]
        == 1
    )
    assert (
        response.json()["page"]["records"][0][
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

    public_record_id = listed["page"]["records"][0][
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

    public_record_id = listed["page"]["records"][0][
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
    result_keys = collect_keys(body["page"])

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

    public_record_id = listed["page"]["records"][0][
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





def test_list_endpoint_is_bounded(tmp_path):
    client, ledger = build_client(tmp_path)

    for index in range(5):
        append_record(
            ledger,
            response_kind=f"response-{index + 1}",
        )

    response = client.get(
        "/tenant-boundary-audit/records",
        params={
            "page_size": 2,
        },
        headers=trusted_headers(),
    )

    assert response.status_code == 200

    page = response.json()["page"]

    assert page["page_size"] == 2
    assert page["returned_count"] == 2
    assert page["has_more"] is True
    assert page["next_cursor"] is not None
    assert len(page["records"]) == 2


def test_cursor_returns_next_api_page(tmp_path):
    client, ledger = build_client(tmp_path)

    for index in range(5):
        append_record(
            ledger,
            response_kind=f"response-{index + 1}",
        )

    first = client.get(
        "/tenant-boundary-audit/records",
        params={
            "page_size": 2,
        },
        headers=trusted_headers(),
    ).json()["page"]

    second_response = client.get(
        "/tenant-boundary-audit/records",
        params={
            "page_size": 2,
            "cursor": first["next_cursor"],
        },
        headers=trusted_headers(),
    )

    assert second_response.status_code == 200

    second = second_response.json()["page"]

    assert [
        record["tenant_sequence_number"]
        for record in second["records"]
    ] == [3, 4]
    assert second["has_more"] is True


def test_final_api_page_has_no_cursor(tmp_path):
    client, ledger = build_client(tmp_path)

    for index in range(3):
        append_record(
            ledger,
            response_kind=f"response-{index + 1}",
        )

    first = client.get(
        "/tenant-boundary-audit/records",
        params={
            "page_size": 2,
        },
        headers=trusted_headers(),
    ).json()["page"]

    second = client.get(
        "/tenant-boundary-audit/records",
        params={
            "page_size": 2,
            "cursor": first["next_cursor"],
        },
        headers=trusted_headers(),
    ).json()["page"]

    assert second["returned_count"] == 1
    assert second["has_more"] is False
    assert second["next_cursor"] is None


def test_cross_tenant_cursor_is_rejected_by_api(
    tmp_path,
):
    client, ledger = build_client(tmp_path)

    for tenant_id in (
        "tenant-alpha",
        "tenant-beta",
    ):
        for index in range(3):
            append_record(
                ledger,
                tenant_id=tenant_id,
                response_kind=(
                    f"{tenant_id}-response-{index + 1}"
                ),
            )

    alpha_page = client.get(
        "/tenant-boundary-audit/records",
        params={
            "page_size": 1,
        },
        headers=trusted_headers(
            tenant_id="tenant-alpha"
        ),
    ).json()["page"]

    response = client.get(
        "/tenant-boundary-audit/records",
        params={
            "page_size": 1,
            "cursor": alpha_page["next_cursor"],
        },
        headers=trusted_headers(
            tenant_id="tenant-beta"
        ),
    )

    assert response.status_code == 400
    assert "verification failed" in (
        response.json()["detail"]
    )


def test_invalid_cursor_returns_400(tmp_path):
    client, _ = build_client(tmp_path)

    response = client.get(
        "/tenant-boundary-audit/records",
        params={
            "cursor": "invalid",
        },
        headers=trusted_headers(),
    )

    assert response.status_code == 400
    assert "cursor" in response.json()["detail"]


def test_page_size_above_limit_returns_400(
    tmp_path,
):
    client, _ = build_client(tmp_path)

    response = client.get(
        "/tenant-boundary-audit/records",
        params={
            "page_size": 101,
        },
        headers=trusted_headers(),
    )

    assert response.status_code == 400
    assert "must not exceed" in (
        response.json()["detail"]
    )


def test_paginated_response_passes_boundary_gate(
    tmp_path,
):
    client, ledger = build_client(tmp_path)

    append_record(ledger)

    response = client.get(
        "/tenant-boundary-audit/records",
        params={
            "page_size": 1,
        },
        headers=trusted_headers(),
    )

    assert response.status_code == 200
    assert (
        response.json()["boundary_audit"]["valid"]
        is True
    )
    assert len(
        response.json()["page"]["page_hash"]
    ) == 64


def test_pagination_snapshot_excludes_new_query_access_records(
    tmp_path,
):
    client, ledger = build_client(tmp_path)

    for index in range(3):
        append_record(
            ledger,
            response_kind=f"response-{index + 1}",
        )

    first_response = client.get(
        "/tenant-boundary-audit/records",
        params={
            "page_size": 2,
        },
        headers=trusted_headers(),
    )

    assert first_response.status_code == 200

    first = first_response.json()["page"]

    assert first["snapshot_sequence"] == 3
    assert first["returned_count"] == 2

    second_response = client.get(
        "/tenant-boundary-audit/records",
        params={
            "page_size": 2,
            "cursor": first["next_cursor"],
        },
        headers=trusted_headers(),
    )

    assert second_response.status_code == 200

    second = second_response.json()["page"]

    assert second["snapshot_sequence"] == 3
    assert second["returned_count"] == 1
    assert [
        record["tenant_sequence_number"]
        for record in second["records"]
    ] == [3]
    assert second["has_more"] is False
    assert second["next_cursor"] is None

    assert len(
        ledger.list_records(
            tenant_id="tenant-alpha"
        )
    ) == 5
