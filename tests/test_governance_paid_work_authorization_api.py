from __future__ import annotations

from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.app.gagf.governance_paid_work_authorization_api import (
    PAID_WORK_AUTHORIZATION_API_PREFIX,
    create_governance_paid_work_authorization_router,
)
from backend.app.gagf.governance_paid_work_authorization_issuance_service import (
    GovernancePaidWorkAuthorizationIssuanceService,
)
from backend.app.gagf.governance_paid_work_authorization_record_store import (
    GovernancePaidWorkAuthorizationRecordStore,
)


TENANT_ID = "tenant-alpha"
CLIENT_ID = "client-alpha"
ENGAGEMENT_ID = "engagement-001"
ASSESSMENT_ID = "assessment-001"

ISSUE_URL = (
    f"{PAID_WORK_AUTHORIZATION_API_PREFIX}/issue"
)


def admin_headers(
    *,
    tenant_id: str = TENANT_ID,
    actor_id: str = "operator-admin-001",
    roles: str = "assessment:admin",
) -> dict[str, str]:
    return {
        "X-Tenant-ID": tenant_id,
        "X-Actor-ID": actor_id,
        "X-Actor-Roles": roles,
    }


def ready_authorization_package() -> dict:
    return {
        "status": "ok",
        "event_type": (
            "assessment_factory_lite_paid_assessment_authorization_package"
        ),
        "package_status": "ready_for_paid_assessment_authorization",
        "authorization_id": "authorization-package-001",
        "package_blockers": [],
        "human_authorization": {
            "human_operator_authorized_package": True,
            "paid_assessment_authorized": False,
        },
        "commercial_boundary": {
            "authorization_package_ready": True,
            "paid_assessment_authorized": False,
            "requires_separate_contract": True,
            "requires_separate_invoice": True,
            "requires_separate_payment_confirmation": True,
        },
        "governance_boundary": {
            "gagf_kernel_authoritative": True,
            "human_boundary_required": True,
            "ai_override_allowed": False,
            "authorization_is_package_readiness_only": True,
        },
    }


def executed_contract_event() -> dict:
    return {
        "status": "ok",
        "event_type": (
            "assessment_factory_lite_contract_execution_event"
        ),
        "event_status": "contract_executed",
        "contract_execution_event_id": "contract-event-001",
        "event_blockers": [],
        "execution_evidence": {
            "contract_executed": True,
        },
        "commercial_boundary": {
            "contract_executed": True,
            "paid_assessment_authorized": False,
            "requires_final_paid_work_authorization": True,
        },
        "governance_boundary": {
            "gagf_kernel_authoritative": True,
            "human_boundary_required": True,
            "ai_override_allowed": False,
            "contract_execution_event_is_not_paid_work_authorization": True,
        },
    }


def confirmed_payment_event() -> dict:
    return {
        "status": "ok",
        "event_type": (
            "assessment_factory_lite_payment_confirmation_event"
        ),
        "event_status": "payment_confirmed",
        "payment_confirmation_event_id": "payment-confirmation-001",
        "event_blockers": [],
        "payment_confirmation_record": {
            "payment_confirmed": True,
        },
        "reconciliation_record": {
            "reconciliation_recorded": True,
        },
        "operator_confirmation": {
            "human_operator_confirmed_payment": True,
            "paid_assessment_authorized": False,
        },
        "commercial_boundary": {
            "payment_confirmed": True,
            "paid_assessment_authorized": False,
            "requires_final_paid_work_authorization": True,
        },
        "governance_boundary": {
            "gagf_kernel_authoritative": True,
            "human_boundary_required": True,
            "ai_override_allowed": False,
            "payment_confirmation_event_is_not_paid_work_authorization": True,
        },
    }


def issue_payload() -> dict:
    return {
        "tenant_id": TENANT_ID,
        "client_id": CLIENT_ID,
        "engagement_id": ENGAGEMENT_ID,
        "assessment_id": ASSESSMENT_ID,
        "authorization_package": ready_authorization_package(),
        "contract_execution_event": executed_contract_event(),
        "payment_confirmation_event": confirmed_payment_event(),
    }


def build_client(tmp_path) -> tuple[
    TestClient,
    GovernancePaidWorkAuthorizationRecordStore,
]:
    store = GovernancePaidWorkAuthorizationRecordStore(
        database_path=(
            tmp_path
            / "paid-work-authorizations.sqlite3"
        )
    )

    issuance_service = (
        GovernancePaidWorkAuthorizationIssuanceService(
            record_store=store,
            clock=lambda: datetime(
                2026,
                10,
                14,
                21,
                0,
                0,
                tzinfo=timezone.utc,
            ),
        )
    )

    app = FastAPI()
    app.include_router(
        create_governance_paid_work_authorization_router(
            issuance_service=issuance_service
        )
    )

    return TestClient(app), store


def test_admin_can_issue_server_owned_pa001(tmp_path):
    client, store = build_client(tmp_path)

    response = client.post(
        ISSUE_URL,
        json=issue_payload(),
        headers=admin_headers(),
    )

    assert response.status_code == 201

    payload = response.json()

    assert payload["status"] == "issued"
    assert payload["authorization_id"].startswith("pa-001-")
    assert (
        payload["hierarchy_key"]
        == "tenant-alpha/client-alpha/engagement-001/assessment-001"
    )
    assert payload["paid_assessment_authorized"] is True

    authorization = payload["issuance"]["authorization"]

    assert authorization["authorized_by"] == "operator-admin-001"
    assert (
        authorization["authorized_at"]
        == "2026-10-14T21:00:00+00:00"
    )

    stored = store.get(
        authorization_id=payload["authorization_id"]
    )

    assert stored.authorized_by == "operator-admin-001"


def test_request_cannot_supply_authoritative_fields(tmp_path):
    client, _ = build_client(tmp_path)

    payload = issue_payload()
    payload["authorization_id"] = "browser-auth-001"
    payload["authorized_by"] = "browser-user"
    payload["authorized_at"] = "2000-01-01T00:00:00+00:00"
    payload["paid_assessment_authorized"] = True

    response = client.post(
        ISSUE_URL,
        json=payload,
        headers=admin_headers(),
    )

    assert response.status_code == 422


def test_executor_cannot_issue_pa001(tmp_path):
    client, _ = build_client(tmp_path)

    response = client.post(
        ISSUE_URL,
        json=issue_payload(),
        headers=admin_headers(
            roles="assessment:execute"
        ),
    )

    assert response.status_code == 403
    assert response.json()["detail"]["code"] == (
        "PA001_ISSUANCE_ROLE_FORBIDDEN"
    )


def test_reader_cannot_reach_issuance_handler(tmp_path):
    client, _ = build_client(tmp_path)

    response = client.post(
        ISSUE_URL,
        json=issue_payload(),
        headers=admin_headers(
            roles="assessment:read"
        ),
    )

    assert response.status_code == 403
    assert response.json()["detail"]["code"] == (
        "ASSESSMENT_ROLE_FORBIDDEN"
    )


def test_body_tenant_mismatch_fails_at_auth_boundary(tmp_path):
    client, _ = build_client(tmp_path)

    response = client.post(
        ISSUE_URL,
        json=issue_payload(),
        headers=admin_headers(
            tenant_id="tenant-beta"
        ),
    )

    assert response.status_code == 403
    assert response.json()["detail"]["code"] == (
        "ASSESSMENT_TENANT_MISMATCH"
    )


def test_missing_actor_headers_returns_401(tmp_path):
    client, _ = build_client(tmp_path)

    response = client.post(
        ISSUE_URL,
        json=issue_payload(),
    )

    assert response.status_code == 401
    assert response.json()["detail"]["code"] == (
        "ASSESSMENT_AUTH_REQUIRED"
    )


def test_unready_package_returns_409(tmp_path):
    client, _ = build_client(tmp_path)

    payload = issue_payload()
    payload["authorization_package"][
        "package_status"
    ] = "pending_authorization_review"

    response = client.post(
        ISSUE_URL,
        json=payload,
        headers=admin_headers(),
    )

    assert response.status_code == 409
    assert response.json()["detail"]["code"] == (
        "PA001_ISSUANCE_BLOCKED"
    )


def test_unexecuted_contract_returns_409(tmp_path):
    client, _ = build_client(tmp_path)

    payload = issue_payload()
    payload["contract_execution_event"][
        "event_status"
    ] = "pending_contract_execution_confirmation"

    response = client.post(
        ISSUE_URL,
        json=payload,
        headers=admin_headers(),
    )

    assert response.status_code == 409


def test_unconfirmed_payment_returns_409(tmp_path):
    client, _ = build_client(tmp_path)

    payload = issue_payload()
    payload["payment_confirmation_event"][
        "event_status"
    ] = "pending_payment_confirmation"

    response = client.post(
        ISSUE_URL,
        json=payload,
        headers=admin_headers(),
    )

    assert response.status_code == 409


def test_repeat_request_is_idempotent(tmp_path):
    client, store = build_client(tmp_path)

    first = client.post(
        ISSUE_URL,
        json=issue_payload(),
        headers=admin_headers(),
    )
    second = client.post(
        ISSUE_URL,
        json=issue_payload(),
        headers=admin_headers(),
    )

    assert first.status_code == 201
    assert second.status_code == 201

    first_payload = first.json()
    second_payload = second.json()

    assert (
        first_payload["authorization_id"]
        == second_payload["authorization_id"]
    )
    assert (
        first_payload["issuance"]["record"]["record_hash"]
        == second_payload["issuance"]["record"]["record_hash"]
    )

    stored = store.get(
        authorization_id=first_payload["authorization_id"]
    )

    assert (
        stored.record_hash
        == first_payload["issuance"]["record"]["record_hash"]
    )


def test_response_preserves_constitutional_boundaries(tmp_path):
    client, _ = build_client(tmp_path)

    response = client.post(
        ISSUE_URL,
        json=issue_payload(),
        headers=admin_headers(),
    )

    assert response.status_code == 201

    boundaries = response.json()["boundaries"]

    assert boundaries["browser_does_not_supply_authorized_by"] is True
    assert boundaries["browser_does_not_supply_authorized_at"] is True
    assert boundaries["browser_does_not_supply_authorization_id"] is True
    assert boundaries["browser_does_not_self_authorize"] is True
    assert boundaries["admin_issuance_required"] is True
    assert boundaries["pa001_is_not_execution"] is True
    assert boundaries["pa001_is_not_delivery"] is True
    assert boundaries["pa001_is_not_production_onboarding"] is True
    assert boundaries["pa001_is_not_intervention_authority"] is True
