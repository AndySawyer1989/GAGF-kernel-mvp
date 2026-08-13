from __future__ import annotations

from dataclasses import replace

from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.app.gagf.governance_intervention_verification_api import (
    GOVERNANCE_INTERVENTION_VERIFICATION_API_ID,
    GOVERNANCE_INTERVENTION_VERIFICATION_API_VERSION,
    GOVERNANCE_INTERVENTION_VERIFICATION_READ_SCOPE,
    create_governance_intervention_verification_router,
)
from backend.app.gagf.governance_intervention_verification_ledger import (
    GovernanceInterventionVerificationLedger,
    GovernanceInterventionVerificationRecordBuilder,
)
from backend.app.gagf.governance_intervention_verification_lifecycle import (
    GovernanceInterventionVerificationLifecycleLedger,
)
from backend.app.gagf.governance_intervention_verification_summary import (
    GovernanceInterventionVerificationSummary,
    GovernanceInterventionVerificationSummaryDisposition,
)
from backend.app.gagf.scientific_authority_guard import (
    canonical_json,
    sha256_hex,
)
from backend.app.gagf.tenant_application_router_registry import (
    TENANT_APPLICATION_ROUTER_REGISTRY_ID,
    TENANT_APPLICATION_ROUTER_REGISTRY_VERSION,
    TenantApplicationDatabasePaths,
    register_tenant_application_routers,
)


def make_summary(
    *,
    tenant_id: str = "tenant-a",
    intervention_id: str = "intervention-1",
    verification_set_hash: str = "verification-set-1",
    disposition=(
        GovernanceInterventionVerificationSummaryDisposition.VERIFIED
    ),
    required_count: int = 3,
    verified_count: int = 3,
    not_verified_count: int = 0,
    inconclusive_count: int = 0,
) -> GovernanceInterventionVerificationSummary:
    payload = {
        "verification_summary_id": (
            "governance-intervention-verification-summary"
        ),
        "version": "0.1.0",
        "schema_version": "1.0.0",
        "tenant_id": tenant_id,
        "contract_hash": f"contract-{intervention_id}",
        "intervention_id": intervention_id,
        "intervention_type": "POLICY_CHANGE",
        "verification_set_hash": verification_set_hash,
        "required_count": required_count,
        "verified_count": verified_count,
        "not_verified_count": not_verified_count,
        "inconclusive_count": inconclusive_count,
        "verification_disposition": disposition.value,
    }

    return GovernanceInterventionVerificationSummary(
        verification_summary_id=payload[
            "verification_summary_id"
        ],
        version=payload["version"],
        schema_version=payload["schema_version"],
        tenant_id=payload["tenant_id"],
        contract_hash=payload["contract_hash"],
        intervention_id=payload["intervention_id"],
        intervention_type=payload["intervention_type"],
        verification_set_hash=payload[
            "verification_set_hash"
        ],
        required_count=payload["required_count"],
        verified_count=payload["verified_count"],
        not_verified_count=payload[
            "not_verified_count"
        ],
        inconclusive_count=payload[
            "inconclusive_count"
        ],
        verification_disposition=disposition,
        verification_summary_hash=sha256_hex(
            canonical_json(payload)
        ),
    )


def append_record(
    database_path,
    *,
    tenant_id: str = "tenant-a",
    intervention_id: str = "intervention-1",
    verification_set_hash: str = "verification-set-1",
    disposition=(
        GovernanceInterventionVerificationSummaryDisposition.VERIFIED
    ),
    required_count: int = 3,
    verified_count: int = 3,
    not_verified_count: int = 0,
    inconclusive_count: int = 0,
):
    summary = make_summary(
        tenant_id=tenant_id,
        intervention_id=intervention_id,
        verification_set_hash=verification_set_hash,
        disposition=disposition,
        required_count=required_count,
        verified_count=verified_count,
        not_verified_count=not_verified_count,
        inconclusive_count=inconclusive_count,
    )

    record = GovernanceInterventionVerificationRecordBuilder.build(
        summary=summary
    )

    ledger = GovernanceInterventionVerificationLedger(
        database_path
    )

    ledger.append(record=record)

    return summary, record


def make_app(database_path):
    app = FastAPI()

    app.include_router(
        create_governance_intervention_verification_router(
            database_path=database_path
        )
    )

    return app


def authorized_headers(
    *,
    tenant_id: str = "tenant-a",
    role_id: str = "tenant-auditor",
    policy_scope: str = (
        GOVERNANCE_INTERVENTION_VERIFICATION_READ_SCOPE
    ),
    credential_verified: str = "true",
    session_verified: str = "true",
    device_trusted: str = "true",
    tenant_membership_verified: str = "true",
):
    return {
        "x-tenant-id": tenant_id,
        "x-role-id": role_id,
        "x-policy-scope": policy_scope,
        "x-credential-verified": credential_verified,
        "x-session-verified": session_verified,
        "x-device-trusted": device_trusted,
        "x-tenant-membership-verified": (
            tenant_membership_verified
        ),
    }


def test_api_constants_are_stable():
    assert (
        GOVERNANCE_INTERVENTION_VERIFICATION_API_ID
        == "governance-intervention-verification-api"
    )
    assert (
        GOVERNANCE_INTERVENTION_VERIFICATION_API_VERSION
        == "0.2.0"
    )
    assert (
        GOVERNANCE_INTERVENTION_VERIFICATION_READ_SCOPE
        == "intervention-verification:read"
    )


def test_get_intervention_history_returns_records(tmp_path):
    database_path = tmp_path / "verification.db"

    _, first = append_record(
        database_path,
        intervention_id="intervention-1",
        verification_set_hash="set-1",
    )

    _, second = append_record(
        database_path,
        intervention_id="intervention-1",
        verification_set_hash="set-2",
        disposition=(
            GovernanceInterventionVerificationSummaryDisposition
            .INCONCLUSIVE
        ),
        verified_count=2,
        inconclusive_count=1,
    )

    client = TestClient(
        make_app(database_path)
    )

    response = client.get(
        (
            "/tenant-intervention-verification/"
            "interventions/intervention-1"
        ),
        headers=authorized_headers(),
    )

    assert response.status_code == 200

    payload = response.json()

    assert (
        payload["api_id"]
        == GOVERNANCE_INTERVENTION_VERIFICATION_API_ID
    )
    assert payload["record_count"] == 2

    assert payload["records"][0]["record_hash"] == (
        first.record_hash
    )
    assert payload["records"][1]["record_hash"] == (
        second.record_hash
    )


def test_intervention_history_is_tenant_scoped(tmp_path):
    database_path = tmp_path / "verification.db"

    append_record(
        database_path,
        tenant_id="tenant-a",
        intervention_id="shared-intervention",
        verification_set_hash="tenant-a-set",
    )

    append_record(
        database_path,
        tenant_id="tenant-b",
        intervention_id="shared-intervention",
        verification_set_hash="tenant-b-set",
    )

    client = TestClient(
        make_app(database_path)
    )

    response = client.get(
        (
            "/tenant-intervention-verification/"
            "interventions/shared-intervention"
        ),
        headers=authorized_headers(
            tenant_id="tenant-a"
        ),
    )

    assert response.status_code == 200

    records = response.json()["records"]

    assert len(records) == 1
    assert records[0]["tenant_id"] == "tenant-a"


def test_intervention_history_missing_returns_empty_collection(
    tmp_path,
):
    database_path = tmp_path / "verification.db"

    client = TestClient(
        make_app(database_path)
    )

    response = client.get(
        (
            "/tenant-intervention-verification/"
            "interventions/missing"
        ),
        headers=authorized_headers(),
    )

    assert response.status_code == 200
    assert response.json()["record_count"] == 0
    assert response.json()["records"] == []


def test_get_summary_returns_exact_record(tmp_path):
    database_path = tmp_path / "verification.db"

    summary, record = append_record(
        database_path
    )

    client = TestClient(
        make_app(database_path)
    )

    response = client.get(
        (
            "/tenant-intervention-verification/"
            "summaries/"
            f"{summary.verification_summary_hash}"
        ),
        headers=authorized_headers(),
    )

    assert response.status_code == 200

    payload = response.json()

    assert (
        payload["record"]["record_hash"]
        == record.record_hash
    )
    assert (
        payload["record"]["verification_summary_hash"]
        == summary.verification_summary_hash
    )


def test_get_summary_missing_returns_404(tmp_path):
    database_path = tmp_path / "verification.db"

    client = TestClient(
        make_app(database_path)
    )

    response = client.get(
        (
            "/tenant-intervention-verification/"
            "summaries/missing-summary"
        ),
        headers=authorized_headers(),
    )

    assert response.status_code == 404


def test_get_summary_cannot_cross_tenant_boundary(tmp_path):
    database_path = tmp_path / "verification.db"

    summary, _ = append_record(
        database_path,
        tenant_id="tenant-a",
    )

    client = TestClient(
        make_app(database_path)
    )

    response = client.get(
        (
            "/tenant-intervention-verification/"
            "summaries/"
            f"{summary.verification_summary_hash}"
        ),
        headers=authorized_headers(
            tenant_id="tenant-b"
        ),
    )

    assert response.status_code == 404


def test_integrity_endpoint_returns_tenant_chain_state(
    tmp_path,
):
    database_path = tmp_path / "verification.db"

    append_record(
        database_path,
        intervention_id="one",
        verification_set_hash="set-one",
    )

    append_record(
        database_path,
        intervention_id="two",
        verification_set_hash="set-two",
    )

    client = TestClient(
        make_app(database_path)
    )

    response = client.get(
        (
            "/tenant-intervention-verification/"
            "ledger/integrity"
        ),
        headers=authorized_headers(),
    )

    assert response.status_code == 200

    integrity = response.json()["integrity"]

    assert integrity["tenant_id"] == "tenant-a"
    assert integrity["record_count"] == 2
    assert integrity["valid"] is True
    assert len(integrity["last_chain_hash"]) == 64


def test_integrity_endpoint_empty_tenant_is_valid_genesis(
    tmp_path,
):
    database_path = tmp_path / "verification.db"

    client = TestClient(
        make_app(database_path)
    )

    response = client.get(
        (
            "/tenant-intervention-verification/"
            "ledger/integrity"
        ),
        headers=authorized_headers(),
    )

    assert response.status_code == 200

    integrity = response.json()["integrity"]

    assert integrity["record_count"] == 0
    assert integrity["valid"] is True
    assert integrity["last_chain_hash"] == "0" * 64


def test_missing_required_headers_are_rejected(tmp_path):
    client = TestClient(
        make_app(tmp_path / "verification.db")
    )

    response = client.get(
        (
            "/tenant-intervention-verification/"
            "ledger/integrity"
        )
    )

    assert response.status_code == 422


def test_blank_tenant_is_rejected(tmp_path):
    client = TestClient(
        make_app(tmp_path / "verification.db")
    )

    response = client.get(
        (
            "/tenant-intervention-verification/"
            "ledger/integrity"
        ),
        headers=authorized_headers(
            tenant_id="   "
        ),
    )

    assert response.status_code == 400


def test_unpermitted_role_is_rejected(tmp_path):
    client = TestClient(
        make_app(tmp_path / "verification.db")
    )

    response = client.get(
        (
            "/tenant-intervention-verification/"
            "ledger/integrity"
        ),
        headers=authorized_headers(
            role_id="operator"
        ),
    )

    assert response.status_code == 403
    assert (
        response.json()["detail"]["authorization"]["allowed"]
        is False
    )


def test_scientific_reviewer_role_is_permitted(tmp_path):
    client = TestClient(
        make_app(tmp_path / "verification.db")
    )

    response = client.get(
        (
            "/tenant-intervention-verification/"
            "ledger/integrity"
        ),
        headers=authorized_headers(
            role_id="scientific-reviewer"
        ),
    )

    assert response.status_code == 200


def test_wrong_scope_is_rejected(tmp_path):
    client = TestClient(
        make_app(tmp_path / "verification.db")
    )

    response = client.get(
        (
            "/tenant-intervention-verification/"
            "ledger/integrity"
        ),
        headers=authorized_headers(
            policy_scope="some-other:read"
        ),
    )

    assert response.status_code == 403


def test_unverified_credential_is_rejected(tmp_path):
    client = TestClient(
        make_app(tmp_path / "verification.db")
    )

    response = client.get(
        (
            "/tenant-intervention-verification/"
            "ledger/integrity"
        ),
        headers=authorized_headers(
            credential_verified="false"
        ),
    )

    assert response.status_code == 403


def test_unverified_session_is_rejected(tmp_path):
    client = TestClient(
        make_app(tmp_path / "verification.db")
    )

    response = client.get(
        (
            "/tenant-intervention-verification/"
            "ledger/integrity"
        ),
        headers=authorized_headers(
            session_verified="false"
        ),
    )

    assert response.status_code == 403


def test_untrusted_device_is_rejected(tmp_path):
    client = TestClient(
        make_app(tmp_path / "verification.db")
    )

    response = client.get(
        (
            "/tenant-intervention-verification/"
            "ledger/integrity"
        ),
        headers=authorized_headers(
            device_trusted="false"
        ),
    )

    assert response.status_code == 403


def test_unverified_membership_is_rejected(tmp_path):
    client = TestClient(
        make_app(tmp_path / "verification.db")
    )

    response = client.get(
        (
            "/tenant-intervention-verification/"
            "ledger/integrity"
        ),
        headers=authorized_headers(
            tenant_membership_verified="false"
        ),
    )

    assert response.status_code == 403


def test_invalid_boolean_header_is_rejected(tmp_path):
    client = TestClient(
        make_app(tmp_path / "verification.db")
    )

    response = client.get(
        (
            "/tenant-intervention-verification/"
            "ledger/integrity"
        ),
        headers=authorized_headers(
            device_trusted="maybe"
        ),
    )

    assert response.status_code == 400


def test_authorization_metadata_is_returned(tmp_path):
    client = TestClient(
        make_app(tmp_path / "verification.db")
    )

    response = client.get(
        (
            "/tenant-intervention-verification/"
            "ledger/integrity"
        ),
        headers=authorized_headers(),
    )

    authorization = response.json()["authorization"]

    assert authorization["tenant_id"] == "tenant-a"
    assert authorization["role_id"] == "tenant-auditor"
    assert (
        authorization["scope"]
        == GOVERNANCE_INTERVENTION_VERIFICATION_READ_SCOPE
    )
    assert authorization["allowed"] is True
    assert authorization["reasons"] == []


def test_router_contains_only_get_routes_for_verification_surface(
    tmp_path,
):
    app = make_app(
        tmp_path / "verification.db"
    )

    openapi_paths = app.openapi()["paths"]

    verification_paths = {
        path: operations
        for path, operations in openapi_paths.items()
        if path.startswith(
            "/tenant-intervention-verification"
        )
    }

    assert verification_paths

    for operations in verification_paths.values():
        assert set(operations) == {"get"}


def test_no_write_methods_exist_on_verification_paths(tmp_path):
    client = TestClient(
        make_app(tmp_path / "verification.db")
    )

    paths = (
        (
            "/tenant-intervention-verification/"
            "interventions/intervention-1"
        ),
        (
            "/tenant-intervention-verification/"
            "summaries/summary-1"
        ),
        (
            "/tenant-intervention-verification/"
            "ledger/integrity"
        ),
        (
            "/tenant-intervention-verification/"
            "records/record-1/lifecycle"
        ),
        (
            "/tenant-intervention-verification/"
            "records/record-1/lifecycle/history"
        ),
    )

    headers = authorized_headers()

    for path in paths:
        for method in (
            "post",
            "put",
            "patch",
            "delete",
        ):
            response = getattr(
                client,
                method,
            )(
                path,
                headers=headers,
            )

            assert response.status_code == 405


def test_registry_database_paths_include_verification_db(
    tmp_path,
):
    paths = TenantApplicationDatabasePaths.from_directory(
        database_directory=tmp_path
    )

    assert (
        paths.intervention_verification_database_path
        == tmp_path / "intervention-verification.db"
    )

    serialized = paths.to_dict()

    assert (
        serialized[
            "intervention_verification_database_path"
        ]
        == str(
            tmp_path / "intervention-verification.db"
        )
    )


def test_registry_registers_verification_router(tmp_path):
    app = FastAPI()

    paths = TenantApplicationDatabasePaths.from_directory(
        database_directory=tmp_path
    )

    registration = register_tenant_application_routers(
        app=app,
        database_paths=paths,
    )

    assert (
        registration.registry_id
        == TENANT_APPLICATION_ROUTER_REGISTRY_ID
    )
    assert (
        registration.registry_version
        == TENANT_APPLICATION_ROUTER_REGISTRY_VERSION
    )
    assert registration.registered is True

    assert (
        registration.intervention_verification_prefix
        == "/tenant-intervention-verification"
    )

    registered_paths = set(
        app.openapi()["paths"]
    )

    assert (
        "/tenant-intervention-verification/"
        "interventions/{intervention_id}"
        in registered_paths
    )

    assert (
        "/tenant-intervention-verification/"
        "summaries/{verification_summary_hash}"
        in registered_paths
    )

    assert (
        "/tenant-intervention-verification/"
        "ledger/integrity"
        in registered_paths
    )

    assert (
        "/tenant-intervention-verification/"
        "records/{verification_record_hash}/lifecycle"
        in registered_paths
    )

    assert (
        "/tenant-intervention-verification/"
        "records/{verification_record_hash}/"
        "lifecycle/history"
        in registered_paths
    )


def test_registry_ensures_verification_database_parent_exists(
    tmp_path,
):
    directory = tmp_path / "nested" / "databases"

    paths = TenantApplicationDatabasePaths.from_directory(
        database_directory=directory
    )

    paths.ensure_directories()

    assert directory.exists()


def test_read_api_does_not_change_record(tmp_path):
    database_path = tmp_path / "verification.db"

    summary, original_record = append_record(
        database_path
    )

    client = TestClient(
        make_app(database_path)
    )

    response = client.get(
        (
            "/tenant-intervention-verification/"
            "summaries/"
            f"{summary.verification_summary_hash}"
        ),
        headers=authorized_headers(),
    )

    assert response.status_code == 200

    ledger = GovernanceInterventionVerificationLedger(
        database_path
    )

    stored = ledger.get_by_summary_hash(
        tenant_id="tenant-a",
        verification_summary_hash=(
            summary.verification_summary_hash
        ),
    )

    assert stored == original_record


def test_read_api_does_not_create_new_records(tmp_path):
    database_path = tmp_path / "verification.db"

    client = TestClient(
        make_app(database_path)
    )

    response = client.get(
        (
            "/tenant-intervention-verification/"
            "interventions/intervention-1"
        ),
        headers=authorized_headers(),
    )

    assert response.status_code == 200

    ledger = GovernanceInterventionVerificationLedger(
        database_path
    )

    verification = ledger.verify_tenant_chain(
        tenant_id="tenant-a"
    )

    assert verification.record_count == 0


def test_api_exposes_governed_disposition_without_success_claim(
    tmp_path,
):
    database_path = tmp_path / "verification.db"

    _, record = append_record(
        database_path,
        disposition=(
            GovernanceInterventionVerificationSummaryDisposition
            .NOT_VERIFIED
        ),
        verified_count=2,
        not_verified_count=1,
    )

    client = TestClient(
        make_app(database_path)
    )

    response = client.get(
        (
            "/tenant-intervention-verification/"
            "summaries/"
            f"{record.verification_summary_hash}"
        ),
        headers=authorized_headers(),
    )

    payload = response.json()["record"]

    assert (
        payload["verification_disposition"]
        == "NOT_VERIFIED"
    )

    forbidden_fields = {
        "success",
        "failure",
        "intervention_success",
        "intervention_failure",
        "causation",
        "causal_effect",
        "causal_attribution",
        "authorized",
        "rollback",
        "continue_intervention",
        "recommended_action",
        "next_action",
    }

    assert forbidden_fields.isdisjoint(payload)


def test_query_surface_cannot_mutate_tampered_record(tmp_path):
    database_path = tmp_path / "verification.db"

    summary, record = append_record(
        database_path
    )

    ledger = GovernanceInterventionVerificationLedger(
        database_path
    )

    stored = ledger.get_by_summary_hash(
        tenant_id="tenant-a",
        verification_summary_hash=(
            summary.verification_summary_hash
        ),
    )

    tampered = replace(
        stored,
        intervention_id="tampered",
    )

    assert tampered.verify() is False
    assert record.verify() is True

def test_get_lifecycle_state_returns_active_state(tmp_path):
    database_path = tmp_path / "verification.db"

    _, record = append_record(
        database_path
    )

    lifecycle = GovernanceInterventionVerificationLifecycleLedger(
        database_path=database_path
    )

    lifecycle.activate(
        tenant_id="tenant-a",
        verification_record_hash=record.record_hash,
    )

    client = TestClient(
        make_app(database_path)
    )

    response = client.get(
        (
            "/tenant-intervention-verification/"
            f"records/{record.record_hash}/lifecycle"
        ),
        headers=authorized_headers(),
    )

    assert response.status_code == 200

    payload = response.json()["lifecycle"]

    assert payload["tenant_id"] == "tenant-a"
    assert (
        payload["verification_record_hash"]
        == record.record_hash
    )
    assert payload["lifecycle_status"] == "ACTIVE"
    assert payload["superseded_by_record_hash"] is None


def test_get_lifecycle_state_returns_current_state(tmp_path):
    database_path = tmp_path / "verification.db"

    _, record = append_record(
        database_path
    )

    lifecycle = GovernanceInterventionVerificationLifecycleLedger(
        database_path=database_path
    )

    lifecycle.activate(
        tenant_id="tenant-a",
        verification_record_hash=record.record_hash,
    )

    lifecycle.mark_stale(
        tenant_id="tenant-a",
        verification_record_hash=record.record_hash,
    )

    client = TestClient(
        make_app(database_path)
    )

    response = client.get(
        (
            "/tenant-intervention-verification/"
            f"records/{record.record_hash}/lifecycle"
        ),
        headers=authorized_headers(),
    )

    assert response.status_code == 200
    assert (
        response.json()["lifecycle"]["lifecycle_status"]
        == "STALE"
    )


def test_get_lifecycle_state_missing_returns_404(tmp_path):
    database_path = tmp_path / "verification.db"

    client = TestClient(
        make_app(database_path)
    )

    response = client.get(
        (
            "/tenant-intervention-verification/"
            "records/missing-record/lifecycle"
        ),
        headers=authorized_headers(),
    )

    assert response.status_code == 404


def test_lifecycle_state_is_tenant_scoped(tmp_path):
    database_path = tmp_path / "verification.db"

    _, record = append_record(
        database_path,
        tenant_id="tenant-a",
    )

    lifecycle = GovernanceInterventionVerificationLifecycleLedger(
        database_path=database_path
    )

    lifecycle.activate(
        tenant_id="tenant-a",
        verification_record_hash=record.record_hash,
    )

    client = TestClient(
        make_app(database_path)
    )

    response = client.get(
        (
            "/tenant-intervention-verification/"
            f"records/{record.record_hash}/lifecycle"
        ),
        headers=authorized_headers(
            tenant_id="tenant-b"
        ),
    )

    assert response.status_code == 404


def test_lifecycle_history_returns_ordered_events(tmp_path):
    database_path = tmp_path / "verification.db"

    _, record = append_record(
        database_path
    )

    lifecycle = GovernanceInterventionVerificationLifecycleLedger(
        database_path=database_path
    )

    lifecycle.activate(
        tenant_id="tenant-a",
        verification_record_hash=record.record_hash,
    )

    lifecycle.mark_stale(
        tenant_id="tenant-a",
        verification_record_hash=record.record_hash,
    )

    lifecycle.require_reverification(
        tenant_id="tenant-a",
        verification_record_hash=record.record_hash,
    )

    client = TestClient(
        make_app(database_path)
    )

    response = client.get(
        (
            "/tenant-intervention-verification/"
            f"records/{record.record_hash}/"
            "lifecycle/history"
        ),
        headers=authorized_headers(),
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["event_count"] == 3

    assert [
        event["lifecycle_status"]
        for event in payload["events"]
    ] == [
        "ACTIVE",
        "STALE",
        "REVERIFICATION_REQUIRED",
    ]


def test_lifecycle_history_missing_is_empty(tmp_path):
    database_path = tmp_path / "verification.db"

    client = TestClient(
        make_app(database_path)
    )

    response = client.get(
        (
            "/tenant-intervention-verification/"
            "records/missing-record/lifecycle/history"
        ),
        headers=authorized_headers(),
    )

    assert response.status_code == 200
    assert response.json()["event_count"] == 0
    assert response.json()["events"] == []


def test_lifecycle_history_is_tenant_scoped(tmp_path):
    database_path = tmp_path / "verification.db"

    _, record = append_record(
        database_path,
        tenant_id="tenant-a",
    )

    lifecycle = GovernanceInterventionVerificationLifecycleLedger(
        database_path=database_path
    )

    lifecycle.activate(
        tenant_id="tenant-a",
        verification_record_hash=record.record_hash,
    )

    client = TestClient(
        make_app(database_path)
    )

    response = client.get(
        (
            "/tenant-intervention-verification/"
            f"records/{record.record_hash}/"
            "lifecycle/history"
        ),
        headers=authorized_headers(
            tenant_id="tenant-b"
        ),
    )

    assert response.status_code == 200
    assert response.json()["event_count"] == 0
    assert response.json()["events"] == []


def test_lifecycle_reads_require_existing_authorization(
    tmp_path,
):
    database_path = tmp_path / "verification.db"

    client = TestClient(
        make_app(database_path)
    )

    response = client.get(
        (
            "/tenant-intervention-verification/"
            "records/record/lifecycle"
        ),
        headers=authorized_headers(
            policy_scope="wrong:scope"
        ),
    )

    assert response.status_code == 403


def test_lifecycle_routes_are_get_only(tmp_path):
    app = make_app(
        tmp_path / "verification.db"
    )

    paths = app.openapi()["paths"]

    state_path = (
        "/tenant-intervention-verification/"
        "records/{verification_record_hash}/lifecycle"
    )

    history_path = (
        "/tenant-intervention-verification/"
        "records/{verification_record_hash}/"
        "lifecycle/history"
    )

    assert state_path in paths
    assert history_path in paths

    assert set(paths[state_path]) == {"get"}
    assert set(paths[history_path]) == {"get"}


def test_lifecycle_api_does_not_mutate_history(tmp_path):
    database_path = tmp_path / "verification.db"

    _, record = append_record(
        database_path
    )

    lifecycle = GovernanceInterventionVerificationLifecycleLedger(
        database_path=database_path
    )

    lifecycle.activate(
        tenant_id="tenant-a",
        verification_record_hash=record.record_hash,
    )

    before = lifecycle.list_history(
        tenant_id="tenant-a",
        verification_record_hash=record.record_hash,
    )

    client = TestClient(
        make_app(database_path)
    )

    for _ in range(3):
        response = client.get(
            (
                "/tenant-intervention-verification/"
                f"records/{record.record_hash}/lifecycle"
            ),
            headers=authorized_headers(),
        )

        assert response.status_code == 200

    after = lifecycle.list_history(
        tenant_id="tenant-a",
        verification_record_hash=record.record_hash,
    )

    assert after == before


def test_lifecycle_api_contains_no_causal_or_action_claims(
    tmp_path,
):
    database_path = tmp_path / "verification.db"

    _, record = append_record(
        database_path
    )

    lifecycle = GovernanceInterventionVerificationLifecycleLedger(
        database_path=database_path
    )

    lifecycle.activate(
        tenant_id="tenant-a",
        verification_record_hash=record.record_hash,
    )

    lifecycle.require_reverification(
        tenant_id="tenant-a",
        verification_record_hash=record.record_hash,
    )

    client = TestClient(
        make_app(database_path)
    )

    response = client.get(
        (
            "/tenant-intervention-verification/"
            f"records/{record.record_hash}/lifecycle"
        ),
        headers=authorized_headers(),
    )

    payload = response.json()["lifecycle"]

    forbidden = {
        "success",
        "failure",
        "causation",
        "causal_effect",
        "causal_attribution",
        "authorized",
        "execute",
        "rollback",
        "continue_intervention",
        "recommended_action",
        "next_action",
    }

    assert forbidden.isdisjoint(payload)


def test_lifecycle_api_exposes_supersession_without_rewriting_record(
    tmp_path,
):
    database_path = tmp_path / "verification.db"

    original_summary, original = append_record(
        database_path,
        verification_set_hash="set-original",
    )

    _, replacement = append_record(
        database_path,
        verification_set_hash="set-replacement",
        disposition=(
            GovernanceInterventionVerificationSummaryDisposition
            .INCONCLUSIVE
        ),
        verified_count=2,
        inconclusive_count=1,
    )

    lifecycle = GovernanceInterventionVerificationLifecycleLedger(
        database_path=database_path
    )

    lifecycle.activate(
        tenant_id="tenant-a",
        verification_record_hash=original.record_hash,
    )

    lifecycle.supersede(
        tenant_id="tenant-a",
        verification_record_hash=original.record_hash,
        superseded_by_record_hash=replacement.record_hash,
    )

    client = TestClient(
        make_app(database_path)
    )

    response = client.get(
        (
            "/tenant-intervention-verification/"
            f"records/{original.record_hash}/lifecycle"
        ),
        headers=authorized_headers(),
    )

    assert response.status_code == 200

    lifecycle_payload = response.json()["lifecycle"]

    assert (
        lifecycle_payload["lifecycle_status"]
        == "SUPERSEDED"
    )
    assert (
        lifecycle_payload["superseded_by_record_hash"]
        == replacement.record_hash
    )

    verification_ledger = (
        GovernanceInterventionVerificationLedger(
            database_path
        )
    )

    stored_original = (
        verification_ledger.get_by_summary_hash(
            tenant_id="tenant-a",
            verification_summary_hash=(
                original_summary.verification_summary_hash
            ),
        )
    )

    assert stored_original == original
    assert (
        stored_original.verification_disposition
        == original.verification_disposition
    )