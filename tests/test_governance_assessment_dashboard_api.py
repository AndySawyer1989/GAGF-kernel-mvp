from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.app.gagf.governance_assessment_audit import (
    AssessmentAuditLedger,
)
from backend.app.gagf.governance_assessment_audit_checkpoint import (
    AssessmentAuditCheckpointStore,
)
from backend.app.gagf.governance_assessment_audit_checkpoint_signature_store import (
    SignedAssessmentAuditCheckpointStore,
)
from backend.app.gagf.governance_assessment_checkpoint_key_audit import (
    AssessmentCheckpointKeyAuditStore,
)
from backend.app.gagf.governance_assessment_checkpoint_key_store import (
    AssessmentCheckpointSigningKeyMetadataStore,
)
from backend.app.gagf.governance_assessment_dashboard import (
    GovernanceAssessmentDashboardService,
)
from backend.app.gagf.governance_assessment_dashboard_api import (
    create_governance_assessment_dashboard_router,
)


def headers(
    *,
    tenant_id="tenant-alpha",
    roles="assessment:admin",
):
    return {
        "X-Tenant-ID": tenant_id,
        "X-Actor-ID": "actor-001",
        "X-Actor-Roles": roles,
    }


def build_client(tmp_path, *, with_keys=True):
    audit_ledger = AssessmentAuditLedger(
        tmp_path / "audit.sqlite3"
    )
    checkpoint_store = AssessmentAuditCheckpointStore(
        tmp_path / "checkpoints.sqlite3"
    )
    signed_store = SignedAssessmentAuditCheckpointStore(
        tmp_path / "signed.sqlite3"
    )

    key_store = None
    key_audit_store = None

    if with_keys:
        key_store = AssessmentCheckpointSigningKeyMetadataStore(
            tmp_path / "keys.sqlite3"
        )
        key_audit_store = AssessmentCheckpointKeyAuditStore(
            tmp_path / "key-audit.sqlite3"
        )

    service = GovernanceAssessmentDashboardService(
        audit_ledger=audit_ledger,
        checkpoint_store=checkpoint_store,
        signed_checkpoint_store=signed_store,
        key_metadata_store=key_store,
        key_audit_store=key_audit_store,
    )

    app = FastAPI()
    app.include_router(
        create_governance_assessment_dashboard_router(
            dashboard_service=service
        )
    )

    return TestClient(app)


def test_authenticated_actor_can_read_dashboard_summary(tmp_path):
    client = build_client(tmp_path)

    response = client.get(
        (
            "/api/v1/governance-assessments"
            "/dashboard-summary"
        ),
        params={"tenant_id": "tenant-alpha"},
        headers=headers(),
    )

    assert response.status_code == 200
    assert response.json() == {
        "tenant_id": "tenant-alpha",
        "audit_event_count": 0,
        "audit_chain_valid": True,
        "checkpoint_count": 0,
        "signed_checkpoint_count": 0,
        "active_signing_key_id": None,
        "signing_key_count": 0,
        "key_activation_event_count": 0,
    }


def test_dashboard_rejects_cross_tenant_access(tmp_path):
    client = build_client(tmp_path)

    response = client.get(
        (
            "/api/v1/governance-assessments"
            "/dashboard-summary"
        ),
        params={"tenant_id": "tenant-beta"},
        headers=headers(tenant_id="tenant-alpha"),
    )

    assert response.status_code == 403
    assert response.json()["detail"]["code"] == (
        "ASSESSMENT_TENANT_MISMATCH"
    )


def test_dashboard_requires_authentication(tmp_path):
    client = build_client(tmp_path)

    response = client.get(
        (
            "/api/v1/governance-assessments"
            "/dashboard-summary"
        ),
        params={"tenant_id": "tenant-alpha"},
    )

    assert response.status_code in {401, 422}


def test_dashboard_supports_signing_disabled_environment(tmp_path):
    client = build_client(
        tmp_path,
        with_keys=False,
    )

    response = client.get(
        (
            "/api/v1/governance-assessments"
            "/dashboard-summary"
        ),
        params={"tenant_id": "tenant-alpha"},
        headers=headers(),
    )

    assert response.status_code == 200
    assert response.json()["active_signing_key_id"] is None
    assert response.json()["signing_key_count"] == 0


def test_dashboard_response_contains_no_secret_fields(tmp_path):
    client = build_client(tmp_path)

    response = client.get(
        (
            "/api/v1/governance-assessments"
            "/dashboard-summary"
        ),
        params={"tenant_id": "tenant-alpha"},
        headers=headers(),
    )

    assert response.status_code == 200
    assert "secret" not in response.text.lower()
