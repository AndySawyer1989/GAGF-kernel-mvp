from pathlib import Path
import shutil

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.gagf.governance_assessment_auth import AssessmentActorContext


@pytest.fixture
def isolated_client(tmp_path, monkeypatch):
    repo = Path(__file__).resolve().parents[1]

    source_policy = repo / "backend/app/gagf/policies/gpl_v0_1.yaml"
    target_policy = tmp_path / "backend/app/gagf/policies/gpl_v0_1.yaml"
    target_policy.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_policy, target_policy)

    (tmp_path / "data").mkdir(exist_ok=True)
    monkeypatch.chdir(tmp_path)

    # Test-only token mapping. Never use this verifier in production.
    identities = {
        "Bearer test-alpha": ("tenant-alpha", ("assessment:read", "assessment:execute")),
        "Bearer test-beta": ("tenant-beta", ("assessment:read", "assessment:execute")),
        "Bearer test-reader": ("tenant-alpha", ("assessment:read",)),
    }

    async def verify_test_identity(request):
        identity = identities.get(request.headers.get("authorization"))

        if identity is None:
            raise HTTPException(status_code=401, detail="test_credentials_required")

        tenant_id, roles = identity
        return AssessmentActorContext(
            tenant_id=tenant_id,
            actor_id="isolated-api-test",
            roles=roles,
        )

    monkeypatch.setattr(
        app.state,
        "assessment_identity_verifier",
        verify_test_identity,
        raising=False,
    )

    with TestClient(app) as client:
        yield client


def headers(token):
    return {"Authorization": f"Bearer {token}"}


def test_missing_credentials_are_denied(isolated_client):
    response = isolated_client.get("/snapshots")
    assert response.status_code == 401


def test_missing_verifier_fails_closed(isolated_client, monkeypatch):
    monkeypatch.delattr(
        app.state,
        "assessment_identity_verifier",
        raising=False,
    )

    response = isolated_client.get("/snapshots")
    assert response.status_code == 503
    assert response.json()["detail"]["code"] == (
        "ASSESSMENT_IDENTITY_VERIFIER_UNAVAILABLE"
    )


def test_reader_cannot_ingest(isolated_client):
    response = isolated_client.post(
        "/ingest/github",
        headers=headers("test-reader"),
        json={"events": []},
    )

    assert response.status_code == 403
    assert response.json()["detail"]["code"] == "ASSESSMENT_ROLE_FORBIDDEN"


def test_cross_tenant_records_are_not_disclosed(isolated_client):
    payload = {
        "events": [
            {
                "id": "tenant-alpha-github-event",
                "event_name": "pull_request",
                "action": "opened",
                "created_at": "2026-07-03T18:00:00Z",
            }
        ]
    }

    created = isolated_client.post(
        "/ingest/github",
        headers=headers("test-alpha"),
        json=payload,
    )

    assert created.status_code == 200, created.text
    result = created.json()
    assert result["status"] == "ingested"

    snapshot_id = result["snapshot_id"]
    decision_id = result["decision_id"]

    # Owner can retrieve its records.
    owner_snapshots = isolated_client.get(
        "/snapshots", headers=headers("test-alpha")
    )
    owner_decision = isolated_client.get(
        f"/decision/{decision_id}", headers=headers("test-alpha")
    )
    owner_diagnostics = isolated_client.get(
        f"/snapshot-diagnostics/{snapshot_id}",
        headers=headers("test-alpha"),
    )

    assert owner_snapshots.status_code == 200
    assert owner_decision.status_code == 200
    assert owner_diagnostics.status_code == 200
    assert owner_diagnostics.json()["status"] == "ok"

    # Another tenant cannot retrieve or enumerate those records.
    for path in (
        "/snapshots",
        "/decisions",
        "/snapshot-diagnostics",
    ):
        response = isolated_client.get(
            path, headers=headers("test-beta")
        )
        assert response.status_code == 200
        assert snapshot_id not in response.text
        assert decision_id not in response.text

    other_decision = isolated_client.get(
        f"/decision/{decision_id}", headers=headers("test-beta")
    )
    other_diagnostics = isolated_client.get(
        f"/snapshot-diagnostics/{snapshot_id}",
        headers=headers("test-beta"),
    )

    assert other_decision.status_code == 200
    assert other_decision.json() == {"error": "decision_not_found"}

    assert other_diagnostics.status_code == 200
    assert other_diagnostics.json()["status"] == "failed"
    assert other_diagnostics.json()["error"] == (
        "snapshot_diagnostics_not_found"
    )

    # Aggregate endpoints must remain accessible without exposing IDs.
    for path in (
        "/dashboard",
        "/snapshot-diagnostics/summary",
        "/snapshot-diagnostics/risk",
    ):
        response = isolated_client.get(
            path, headers=headers("test-beta")
        )
        assert response.status_code == 200
        assert snapshot_id not in response.text
        assert decision_id not in response.text


def test_two_tenants_retain_independent_records(isolated_client):
    records = {}

    for tenant, token in (
        ("alpha", "test-alpha"),
        ("beta", "test-beta"),
    ):
        response = isolated_client.post(
            "/ingest/github",
            headers=headers(token),
            json={
                "events": [
                    {
                        "id": f"event-{tenant}",
                        "event_name": "pull_request",
                        "action": "opened",
                        "created_at": "2026-07-03T18:00:00Z",
                    }
                ]
            },
        )

        assert response.status_code == 200, response.text
        data = response.json()
        assert data["status"] == "ingested"

        records[tenant] = {
            "snapshot_id": data["snapshot_id"],
            "decision_id": data["decision_id"],
        }

    assert records["alpha"]["snapshot_id"] != records["beta"]["snapshot_id"]
    assert records["alpha"]["decision_id"] != records["beta"]["decision_id"]

    for tenant, token, other in (
        ("alpha", "test-alpha", "beta"),
        ("beta", "test-beta", "alpha"),
    ):
        own = records[tenant]
        foreign = records[other]

        for path in (
            "/snapshots",
            "/decisions",
            "/snapshot-diagnostics",
        ):
            response = isolated_client.get(
                path,
                headers=headers(token),
            )

            assert response.status_code == 200, response.text

            # Own records are visible.
            assert own["snapshot_id"] in response.text or (
                path == "/decisions"
                and own["decision_id"] in response.text
            )

            # The other tenant's identifiers are not visible.
            assert foreign["snapshot_id"] not in response.text
            assert foreign["decision_id"] not in response.text

        own_decision = isolated_client.get(
            f"/decision/{own['decision_id']}",
            headers=headers(token),
        )
        foreign_decision = isolated_client.get(
            f"/decision/{foreign['decision_id']}",
            headers=headers(token),
        )

        assert own_decision.status_code == 200
        assert foreign_decision.json() == {
            "error": "decision_not_found"
        }

        own_diagnostics = isolated_client.get(
            f"/snapshot-diagnostics/{own['snapshot_id']}",
            headers=headers(token),
        )
        foreign_diagnostics = isolated_client.get(
            f"/snapshot-diagnostics/{foreign['snapshot_id']}",
            headers=headers(token),
        )

        assert own_diagnostics.json()["status"] == "ok"
        assert foreign_diagnostics.json()["error"] == (
            "snapshot_diagnostics_not_found"
        )

        for path in (
            "/dashboard",
            "/snapshot-diagnostics/summary",
            "/snapshot-diagnostics/risk",
        ):
            response = isolated_client.get(
                path,
                headers=headers(token),
            )

            assert response.status_code == 200
            assert foreign["snapshot_id"] not in response.text
            assert foreign["decision_id"] not in response.text
