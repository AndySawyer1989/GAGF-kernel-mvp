from __future__ import annotations

from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException
from backend.app.gagf.governance_assessment_auth import AssessmentActorContext
from fastapi.testclient import TestClient

from backend.app.gagf.governance_paid_work_prerequisite_persistence_bridge import GovernancePaidWorkPrerequisitePersistenceBridge
from backend.app.gagf.governance_paid_work_prerequisite_producer_api import PAID_WORK_PREREQUISITE_PRODUCER_API_PREFIX, create_governance_paid_work_prerequisite_producer_router
from backend.app.gagf.governance_paid_work_prerequisite_producer_service import GovernancePaidWorkPrerequisiteProducerService
from backend.app.gagf.governance_paid_work_prerequisite_record import AUTHORIZATION_PACKAGE_KIND
from backend.app.gagf.governance_paid_work_prerequisite_record_store import GovernancePaidWorkPrerequisiteRecordStore


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
            "commercial_boundary": {"authorization_package_ready": True, "paid_assessment_authorized": False},
            "governance_boundary": {"authorization_is_package_readiness_only": True, "gagf_kernel_authoritative": True, "human_boundary_required": True, "ai_override_allowed": False},
        }


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

def build_client(tmp_path):
    store = GovernancePaidWorkPrerequisiteRecordStore(database_path=tmp_path / "prerequisites.sqlite3")
    bridge = GovernancePaidWorkPrerequisitePersistenceBridge(prerequisite_store=store)
    ids = iter(["instance-api-001", "instance-api-002", "instance-api-003"])
    producer = GovernancePaidWorkPrerequisiteProducerService(
        persistence_bridge=bridge,
        authorization_package_service=ReadyAuthorizationPackageService(),
        clock=lambda: datetime(2026, 10, 14, 23, 55, 0, tzinfo=timezone.utc),
        instance_id_factory=lambda: next(ids),
    )
    app = FastAPI()
    # Test-only verifier; never configure this in production.
    app.state.assessment_identity_verifier = verify_test_identity
    app.include_router(create_governance_paid_work_prerequisite_producer_router(producer_service=producer))
    return TestClient(app), store


def payload(evidence=None):
    return {
        "tenant_id": "tenant-alpha",
        "client_id": "client-acme",
        "engagement_id": "engagement-001",
        "assessment_id": "assessment-001",
        "evidence": evidence or {},
    }


def admin_headers(*, tenant_id="tenant-alpha", roles="assessment:admin"):
    return {
        "X-Tenant-ID": tenant_id,
        "X-Actor-ID": "admin-001",
        "X-Actor-Roles": roles,
    }


def url():
    return f"{PAID_WORK_PREREQUISITE_PRODUCER_API_PREFIX}/authorization-package"


def test_producer_route_requires_actor(tmp_path):
    client, _ = build_client(tmp_path)
    response = client.post(url(), json=payload())
    assert response.status_code == 401
    assert response.json()["detail"]["code"] == "ASSESSMENT_AUTH_REQUIRED"


def test_producer_route_requires_admin(tmp_path):
    client, _ = build_client(tmp_path)
    response = client.post(url(), json=payload(), headers=admin_headers(roles="assessment:execute"))
    assert response.status_code == 403
    assert response.json()["detail"]["code"] == "ASSESSMENT_ADMIN_REQUIRED"


def test_producer_route_rejects_tenant_mismatch(tmp_path):
    client, _ = build_client(tmp_path)
    response = client.post(url(), json=payload(), headers=admin_headers(tenant_id="tenant-other"))
    assert response.status_code == 403
    assert response.json()["detail"]["code"] == "ASSESSMENT_TENANT_MISMATCH"


def test_browser_terminal_claim_is_rejected_recursively(tmp_path):
    client, _ = build_client(tmp_path)
    response = client.post(
        url(),
        json=payload({"nested": {"paid_assessment_authorized": True}}),
        headers=admin_headers(),
    )
    assert response.status_code == 422
    detail = response.json()["detail"]
    assert detail["code"] == "PREREQUISITE_TERMINAL_CLAIM_FORBIDDEN"
    assert detail["field"] == "evidence.nested.paid_assessment_authorized"


def test_legacy_source_field_is_not_accepted(tmp_path):
    client, _ = build_client(tmp_path)
    body = payload()
    body["source"] = {"authorization_context": {}}
    response = client.post(url(), json=body, headers=admin_headers())
    assert response.status_code == 422


def test_authorization_package_route_persists_actor_bound_server_instance(tmp_path):
    client, store = build_client(tmp_path)
    response = client.post(
        url(),
        json=payload({"authorization_context": {"pricing_reviewed": True}}),
        headers=admin_headers(),
    )
    assert response.status_code == 201
    body = response.json()
    record = body["prerequisite"]["record"]
    provenance = record["artifact"]["governance_provenance"]
    assert provenance["producer_actor_id"] == "admin-001"
    assert provenance["producer_tenant_id"] == "tenant-alpha"
    assert provenance["evidence_instance_id"] == "instance-api-001"
    stored = store.require_for_issuance(
        prerequisite_kind=AUTHORIZATION_PACKAGE_KIND, artifact_id=record["artifact_id"],
        tenant_id="tenant-alpha", client_id="client-acme", engagement_id="engagement-001", assessment_id="assessment-001",
    )
    assert stored.record_hash == record["record_hash"]


def test_repeated_api_actions_create_distinct_immutable_instances(tmp_path):
    client, _ = build_client(tmp_path)
    first = client.post(url(), json=payload(), headers=admin_headers())
    second = client.post(url(), json=payload(), headers=admin_headers())
    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["prerequisite"]["artifact_id"] != second.json()["prerequisite"]["artifact_id"]


def test_response_declares_non_authority_boundaries(tmp_path):
    client, _ = build_client(tmp_path)
    response = client.post(url(), json=payload(), headers=admin_headers())
    boundaries = response.json()["boundaries"]
    assert boundaries["admin_action_required"] is True
    assert boundaries["browser_evidence_cannot_assert_terminal_state"] is True
    assert boundaries["producer_actor_context_is_bound"] is True
    assert boundaries["server_creates_evidence_instance_identity"] is True
    assert boundaries["producer_does_not_issue_pa001"] is True
