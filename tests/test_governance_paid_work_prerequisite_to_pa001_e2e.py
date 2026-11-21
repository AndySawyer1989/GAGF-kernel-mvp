from __future__ import annotations

from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException
from backend.app.gagf.governance_assessment_auth import AssessmentActorContext
from fastapi.testclient import TestClient

from backend.app.gagf.governance_assessment_api_registration import register_governance_assessment_api
from backend.app.gagf.governance_paid_work_prerequisite_record import (
    AUTHORIZATION_PACKAGE_KIND,
    CONTRACT_EXECUTION_EVENT_KIND,
    PAYMENT_CONFIRMATION_EVENT_KIND,
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

TENANT_ID = "tenant-alpha"
CLIENT_ID = "client-acme"
ENGAGEMENT_ID = "engagement-001"
ASSESSMENT_ID = "assessment-001"
HIERARCHY = {
    "tenant_id": TENANT_ID,
    "client_id": CLIENT_ID,
    "engagement_id": ENGAGEMENT_ID,
    "assessment_id": ASSESSMENT_ID,
}
ADMIN_HEADERS = {
    "X-Tenant-ID": TENANT_ID,
    "X-Actor-ID": "operator-admin-001",
    "X-Actor-Roles": "assessment:admin",
}
FIXED_TIME = datetime(2026, 10, 15, 0, 15, 0, tzinfo=timezone.utc)


class ReadyAuthorizationPackageService:
    def build_package(self, **kwargs):
        c = kwargs["authorization_context"]
        return {
            "status": "ok",
            "event_type": "assessment_factory_lite_paid_assessment_authorization_package",
            "package_status": "ready_for_paid_assessment_authorization",
            "authorization_id": c["authorization_id"],
            "prepared_at": c["prepared_at"],
            "package_blockers": [],
            "human_authorization": {"human_operator_authorized_package": True, "paid_assessment_authorized": False},
            "commercial_boundary": {
    "authorization_package_ready": True,
    "paid_assessment_authorized": False,
    "requires_separate_contract": True,
    "requires_separate_invoice": True,
    "requires_separate_payment_confirmation": True,
},
            "governance_boundary": {"authorization_is_package_readiness_only": True, "gagf_kernel_authoritative": True, "human_boundary_required": True, "ai_override_allowed": False},
        }


class ExecutedContractEventService:
    def record_event(self, **kwargs):
        c = kwargs["contract_execution_context"]
        return {
            "status": "ok",
            "event_type": "assessment_factory_lite_contract_execution_event",
            "event_status": "contract_executed",
            "contract_execution_event_id": c["contract_execution_event_id"],
            "recorded_at": c["recorded_at"],
            "event_blockers": [],
            "execution_evidence": {
            "contract_executed": True,
},
            "commercial_boundary": {
    "contract_executed": True,
    "paid_assessment_authorized": False,
    "requires_final_paid_work_authorization": True,
},
            "governance_boundary": {"contract_execution_event_is_not_paid_work_authorization": True, "gagf_kernel_authoritative": True, "human_boundary_required": True, "ai_override_allowed": False},
        }


class ConfirmedPaymentEventService:
    def record_event(self, **kwargs):
        c = kwargs["payment_confirmation_event_context"]
        return {
            "status": "ok",
            "event_type": "assessment_factory_lite_payment_confirmation_event",
            "event_status": "payment_confirmed",
            "payment_confirmation_event_id": c["payment_confirmation_event_id"],
            "recorded_at": c["recorded_at"],
            "event_blockers": [],
            "payment_confirmation_record": {"payment_confirmed": True},
            "reconciliation_record": {"reconciliation_recorded": True},
            "operator_confirmation": {"human_operator_confirmed_payment": True, "paid_assessment_authorized": False},
            "commercial_boundary": {
    "payment_confirmed": True,
    "paid_assessment_authorized": False,
    "requires_final_paid_work_authorization": True,
},
            "governance_boundary": {"payment_confirmation_event_is_not_paid_work_authorization": True, "gagf_kernel_authoritative": True, "human_boundary_required": True, "ai_override_allowed": False},
        }


def producer_payload(evidence=None):
    return {**HIERARCHY, "evidence": evidence or {}}


def test_registered_producer_to_id_only_pa001_issuance_end_to_end(tmp_path):
    app = FastAPI()
    # Test-only verifier; never configure this in production.
    app.state.assessment_identity_verifier = verify_test_identity
    register_governance_assessment_api(app=app, database_path=tmp_path / "assessment.sqlite3")

    producer = app.state.governance_paid_work_prerequisite_producer_service
    producer.authorization_package_service = ReadyAuthorizationPackageService()
    producer.contract_execution_event_service = ExecutedContractEventService()
    producer.payment_confirmation_event_service = ConfirmedPaymentEventService()
    producer.clock = lambda: FIXED_TIME
    ids = iter(["e2e-package-001", "e2e-contract-001", "e2e-payment-001"])
    producer.instance_id_factory = lambda: next(ids)

    client = TestClient(app)

    package = client.post(
        "/api/v1/governance-paid-work-prerequisites/authorization-package",
        json=producer_payload({"authorization_context": {"pricing_reviewed": True}}),
        headers=ADMIN_HEADERS,
    )
    assert package.status_code == 201

    contract = client.post(
        "/api/v1/governance-paid-work-prerequisites/contract-execution-event",
        json=producer_payload(),
        headers=ADMIN_HEADERS,
    )
    assert contract.status_code == 201

    payment = client.post(
        "/api/v1/governance-paid-work-prerequisites/payment-confirmation-event",
        json=producer_payload(),
        headers=ADMIN_HEADERS,
    )
    assert payment.status_code == 201

    package_record = package.json()["prerequisite"]["record"]
    contract_record = contract.json()["prerequisite"]["record"]
    payment_record = payment.json()["prerequisite"]["record"]

    for record in (package_record, contract_record, payment_record):
        provenance = record["artifact"]["governance_provenance"]
        assert provenance["producer_actor_id"] == "operator-admin-001"
        assert provenance["producer_tenant_id"] == TENANT_ID
        assert provenance["actor_context_bound"] is True

    prerequisite_store = app.state.governance_paid_work_prerequisite_store
    prerequisite_store.require_for_issuance(
        prerequisite_kind=AUTHORIZATION_PACKAGE_KIND, artifact_id=package_record["artifact_id"], **HIERARCHY
    )
    prerequisite_store.require_for_issuance(
        prerequisite_kind=CONTRACT_EXECUTION_EVENT_KIND, artifact_id=contract_record["artifact_id"], **HIERARCHY
    )
    prerequisite_store.require_for_issuance(
        prerequisite_kind=PAYMENT_CONFIRMATION_EVENT_KIND, artifact_id=payment_record["artifact_id"], **HIERARCHY
    )

    issue = client.post(
        "/api/v1/governance-paid-work-authorizations/issue",
        json={
            **HIERARCHY,
            "authorization_package_id": package_record["artifact_id"],
            "contract_execution_event_id": contract_record["artifact_id"],
            "payment_confirmation_event_id": payment_record["artifact_id"],
        },
        headers=ADMIN_HEADERS,
    )
    assert issue.status_code == 201, issue.text
    body = issue.json()
    assert body["status"] == "issued"
    assert body["paid_assessment_authorized"] is True
    assert body["boundaries"]["prerequisites_resolved_server_side"] is True
    assert body["boundaries"]["browser_does_not_supply_prerequisite_artifacts"] is True


def test_browser_terminal_claim_cannot_create_prerequisite(tmp_path):
    app = FastAPI()
    # Test-only verifier; never configure this in production.
    app.state.assessment_identity_verifier = verify_test_identity
    register_governance_assessment_api(app=app, database_path=tmp_path / "assessment.sqlite3")
    client = TestClient(app)
    response = client.post(
        "/api/v1/governance-paid-work-prerequisites/payment-confirmation-event",
        json=producer_payload({"payment_confirmation_event_context": {"payment_confirmed": True}}),
        headers=ADMIN_HEADERS,
    )
    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "PREREQUISITE_TERMINAL_CLAIM_FORBIDDEN"
