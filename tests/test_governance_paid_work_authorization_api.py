from __future__ import annotations

from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException
from backend.app.gagf.governance_assessment_auth import AssessmentActorContext
from fastapi.testclient import TestClient

from backend.app.gagf.governance_paid_work_authorization_api import (
    PAID_WORK_AUTHORIZATION_API_PREFIX,
    PAID_WORK_AUTHORIZATION_API_VERSION,
    create_governance_paid_work_authorization_router,
)
from backend.app.gagf.governance_paid_work_authorization_issuance_service import (
    GovernancePaidWorkAuthorizationIssuanceService,
)
from backend.app.gagf.governance_paid_work_authorization_record_store import (
    GovernancePaidWorkAuthorizationRecordStore,
)
from backend.app.gagf.governance_paid_work_prerequisite_record import (
    AUTHORIZATION_PACKAGE_KIND,
    CONTRACT_EXECUTION_EVENT_KIND,
    PAYMENT_CONFIRMATION_EVENT_KIND,
    build_paid_work_prerequisite_record,
)
from backend.app.gagf.governance_paid_work_prerequisite_record_store import (
    GovernancePaidWorkPrerequisiteRecordStore,
)
from backend.app.gagf.governance_paid_work_prerequisite_resolver import (
    GovernancePaidWorkPrerequisiteResolver,
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
        "prepared_at": "2026-10-14T20:00:00+00:00",
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


def contract_execution_event() -> dict:
    return {
        "status": "ok",
        "event_type": (
            "assessment_factory_lite_contract_execution_event"
        ),
        "event_status": "contract_executed",
        "contract_execution_event_id": "contract-event-001",
        "recorded_at": "2026-10-14T20:10:00+00:00",
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


def payment_confirmation_event() -> dict:
    return {
        "status": "ok",
        "event_type": (
            "assessment_factory_lite_payment_confirmation_event"
        ),
        "event_status": "payment_confirmed",
        "payment_confirmation_event_id": "payment-event-001",
        "recorded_at": "2026-10-14T20:20:00+00:00",
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


def issue_payload() -> dict[str, str]:
    return {
        "tenant_id": TENANT_ID,
        "client_id": CLIENT_ID,
        "engagement_id": ENGAGEMENT_ID,
        "assessment_id": ASSESSMENT_ID,
        "authorization_package_id": "authorization-package-001",
        "contract_execution_event_id": "contract-event-001",
        "payment_confirmation_event_id": "payment-event-001",
    }


def seed_prerequisites(
    store: GovernancePaidWorkPrerequisiteRecordStore,
) -> None:
    artifacts = (
        (
            AUTHORIZATION_PACKAGE_KIND,
            ready_authorization_package(),
        ),
        (
            CONTRACT_EXECUTION_EVENT_KIND,
            contract_execution_event(),
        ),
        (
            PAYMENT_CONFIRMATION_EVENT_KIND,
            payment_confirmation_event(),
        ),
    )

    for prerequisite_kind, artifact in artifacts:
        record = build_paid_work_prerequisite_record(
            prerequisite_kind=prerequisite_kind,
            tenant_id=TENANT_ID,
            client_id=CLIENT_ID,
            engagement_id=ENGAGEMENT_ID,
            assessment_id=ASSESSMENT_ID,
            artifact=artifact,
        )
        store.save(
            record=record
        )


async def verify_test_identity(request):
    tenant_id = request.headers.get("X-Tenant-ID")
    actor_id = request.headers.get("X-Actor-ID")
    roles_header = request.headers.get("X-Actor-Roles")

    if not tenant_id or not actor_id or not roles_header:
        raise HTTPException(
            status_code=401,
            detail={"code": "ASSESSMENT_AUTH_REQUIRED"},
        )

    return AssessmentActorContext(
        tenant_id=tenant_id,
        actor_id=actor_id,
        roles=tuple(
            role.strip()
            for role in roles_header.split(",")
            if role.strip()
        ),
    )

def build_client(
    tmp_path,
    *,
    seed: bool = True,
):
    prerequisite_store = GovernancePaidWorkPrerequisiteRecordStore(
        database_path=(
            tmp_path
            / "governance_paid_work_prerequisites.sqlite3"
        )
    )

    authorization_store = GovernancePaidWorkAuthorizationRecordStore(
        database_path=(
            tmp_path
            / "governance_paid_work_authorizations.sqlite3"
        )
    )

    issuance_service = GovernancePaidWorkAuthorizationIssuanceService(
        record_store=authorization_store,
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

    resolver = GovernancePaidWorkPrerequisiteResolver(
        prerequisite_store=prerequisite_store,
        issuance_service=issuance_service,
    )

    if seed:
        seed_prerequisites(
            prerequisite_store
        )

    app = FastAPI()
    # Test-only verifier; never configure this in production.
    app.state.assessment_identity_verifier = verify_test_identity
    app.include_router(
        create_governance_paid_work_authorization_router(
            prerequisite_resolver=resolver
        )
    )

    return (
        TestClient(app),
        prerequisite_store,
        authorization_store,
    )


def test_admin_can_issue_server_owned_pa001_from_ids(tmp_path):
    client, _, authorization_store = build_client(
        tmp_path
    )

    response = client.post(
        ISSUE_URL,
        json=issue_payload(),
        headers=admin_headers(),
    )

    assert response.status_code == 201

    payload = response.json()

    assert payload["status"] == "issued"
    assert payload["api_version"] == PAID_WORK_AUTHORIZATION_API_VERSION
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

    resolution = payload["prerequisite_resolution"]

    assert (
        resolution["authorization_package"]["artifact_id"]
        == "authorization-package-001"
    )
    assert (
        resolution["contract_execution_event"]["artifact_id"]
        == "contract-event-001"
    )
    assert (
        resolution["payment_confirmation_event"]["artifact_id"]
        == "payment-event-001"
    )

    stored = authorization_store.get(
        authorization_id=payload["authorization_id"]
    )

    assert stored.authorized_by == "operator-admin-001"


def test_request_cannot_supply_prerequisite_artifact_bodies(tmp_path):
    client, _, _ = build_client(
        tmp_path
    )

    payload = issue_payload()
    payload["authorization_package"] = ready_authorization_package()
    payload["contract_execution_event"] = contract_execution_event()
    payload["payment_confirmation_event"] = payment_confirmation_event()

    response = client.post(
        ISSUE_URL,
        json=payload,
        headers=admin_headers(),
    )

    assert response.status_code == 422


def test_request_cannot_supply_authoritative_pa001_fields(tmp_path):
    client, _, _ = build_client(
        tmp_path
    )

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


def test_missing_server_prerequisite_returns_409(tmp_path):
    client, _, _ = build_client(
        tmp_path,
        seed=False,
    )

    response = client.post(
        ISSUE_URL,
        json=issue_payload(),
        headers=admin_headers(),
    )

    assert response.status_code == 409
    assert response.json()["detail"]["code"] == (
        "PA001_PREREQUISITE_RESOLUTION_BLOCKED"
    )


def test_cross_hierarchy_prerequisite_resolution_returns_409(tmp_path):
    client, prerequisite_store, _ = build_client(
        tmp_path,
        seed=False,
    )

    wrong_hierarchy = {
        "tenant_id": TENANT_ID,
        "client_id": CLIENT_ID,
        "engagement_id": ENGAGEMENT_ID,
        "assessment_id": "assessment-other",
    }

    artifacts = (
        (
            AUTHORIZATION_PACKAGE_KIND,
            ready_authorization_package(),
        ),
        (
            CONTRACT_EXECUTION_EVENT_KIND,
            contract_execution_event(),
        ),
        (
            PAYMENT_CONFIRMATION_EVENT_KIND,
            payment_confirmation_event(),
        ),
    )

    for prerequisite_kind, artifact in artifacts:
        record = build_paid_work_prerequisite_record(
            prerequisite_kind=prerequisite_kind,
            artifact=artifact,
            **wrong_hierarchy,
        )
        prerequisite_store.save(
            record=record
        )

    response = client.post(
        ISSUE_URL,
        json=issue_payload(),
        headers=admin_headers(),
    )

    assert response.status_code == 409
    assert response.json()["detail"]["code"] == (
        "PA001_PREREQUISITE_RESOLUTION_BLOCKED"
    )


def test_executor_cannot_issue_pa001(tmp_path):
    client, _, _ = build_client(
        tmp_path
    )

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
    client, _, _ = build_client(
        tmp_path
    )

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
    client, _, _ = build_client(
        tmp_path
    )

    payload = issue_payload()
    payload["tenant_id"] = "tenant-other"

    response = client.post(
        ISSUE_URL,
        json=payload,
        headers=admin_headers(),
    )

    assert response.status_code == 403
    assert response.json()["detail"]["code"] == (
        "ASSESSMENT_TENANT_MISMATCH"
    )


def test_unauthenticated_request_is_rejected(tmp_path):
    client, _, _ = build_client(
        tmp_path
    )

    response = client.post(
        ISSUE_URL,
        json=issue_payload(),
    )

    assert response.status_code == 401
    assert response.json()["detail"]["code"] == (
        "ASSESSMENT_AUTH_REQUIRED"
    )


def test_issue_from_ids_is_idempotent(tmp_path):
    client, _, _ = build_client(
        tmp_path
    )

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

    assert (
        first.json()["authorization_id"]
        == second.json()["authorization_id"]
    )
    assert (
        first.json()["issuance"]["record"]["record_hash"]
        == second.json()["issuance"]["record"]["record_hash"]
    )


def test_response_declares_server_resolution_boundaries(tmp_path):
    client, _, _ = build_client(
        tmp_path
    )

    response = client.post(
        ISSUE_URL,
        json=issue_payload(),
        headers=admin_headers(),
    )

    assert response.status_code == 201

    boundaries = response.json()["boundaries"]

    assert boundaries["browser_supplies_prerequisite_ids_only"] is True
    assert boundaries["browser_does_not_supply_prerequisite_artifacts"] is True
    assert boundaries["prerequisites_resolved_server_side"] is True
    assert boundaries["browser_does_not_self_authorize"] is True
    assert boundaries["admin_issuance_required"] is True
    assert boundaries["pa001_is_not_execution"] is True
    assert boundaries["pa001_is_not_delivery"] is True
    assert boundaries["pa001_is_not_intervention_authority"] is True
