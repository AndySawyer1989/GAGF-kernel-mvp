from pathlib import Path
import shutil

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.gagf.governance_assessment_auth import AssessmentActorContext


CSV_CONTENT = (
    b"event_id,event_type,timestamp_quality,source_system,event_occurred_at\n"
    b"evt-csv-001,honeyfile_interaction,SOURCE_OCCURRED_AT,CSV,2026-06-30T12:00:00Z\n"
    b"evt-csv-002,unauthorized_api_call,SOURCE_OCCURRED_AT,CSV,2026-06-30T12:03:00Z\n"
)


@pytest.fixture
def isolated_csv_client(tmp_path, monkeypatch):
    repo = Path(__file__).resolve().parents[1]

    source_policy = repo / "backend/app/gagf/policies/gpl_v0_1.yaml"
    target_policy = tmp_path / "backend/app/gagf/policies/gpl_v0_1.yaml"

    target_policy.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_policy, target_policy)
    (tmp_path / "data").mkdir(exist_ok=True)

    identities = {
        "Bearer csv-alpha": "tenant-csv-alpha",
        "Bearer csv-beta": "tenant-csv-beta",
    }

    async def verify_test_identity(request):
        tenant_id = identities.get(
            request.headers.get("authorization")
        )

        if tenant_id is None:
            raise HTTPException(
                status_code=401,
                detail="test_credentials_required",
            )

        return AssessmentActorContext(
            tenant_id=tenant_id,
            actor_id="csv-e2e-test-actor",
            roles=("assessment:read", "assessment:execute"),
        )

    monkeypatch.setattr(
        app.state,
        "assessment_identity_verifier",
        verify_test_identity,
        raising=False,
    )

    monkeypatch.chdir(tmp_path)

    with TestClient(app) as client:
        yield client, tmp_path


def auth(token):
    return {"Authorization": f"Bearer {token}"}


def test_real_csv_pipeline_preserves_tenant_isolation(isolated_csv_client):
    client, tmp_path = isolated_csv_client
    records = {}

    for tenant, token in (
        ("alpha", "csv-alpha"),
        ("beta", "csv-beta"),
    ):
        response = client.post(
            "/upload-csv",
            headers=auth(token),
            files={
                "file": (
                    "sample_events.csv",
                    CSV_CONTENT,
                    "text/csv",
                ),
            },
        )

        assert response.status_code == 200, response.text

        data = response.json()

        assert data["status"] == "ingested"
        assert data["rows_received"] == 2
        assert data["events_normalized"] == 2

        records[tenant] = {
            "snapshot_id": data["snapshot_id"],
            "decision_id": data["decision_id"],
        }

    assert records["alpha"]["snapshot_id"] != records["beta"]["snapshot_id"]
    assert records["alpha"]["decision_id"] != records["beta"]["decision_id"]

    for tenant, token, other in (
        ("alpha", "csv-alpha", "beta"),
        ("beta", "csv-beta", "alpha"),
    ):
        own = records[tenant]
        foreign = records[other]

        snapshots = client.get(
            "/snapshots",
            headers=auth(token),
        )
        decisions = client.get(
            "/decisions",
            headers=auth(token),
        )
        own_decision = client.get(
            f"/decision/{own['decision_id']}",
            headers=auth(token),
        )
        foreign_decision = client.get(
            f"/decision/{foreign['decision_id']}",
            headers=auth(token),
        )

        for response in (
            snapshots,
            decisions,
            own_decision,
            foreign_decision,
        ):
            assert response.status_code == 200, response.text

        assert own["snapshot_id"] in snapshots.text
        assert foreign["snapshot_id"] not in snapshots.text

        assert own["decision_id"] in decisions.text
        assert foreign["decision_id"] not in decisions.text

        assert foreign_decision.json() == {
            "error": "decision_not_found"
        }

        assert own["decision_id"] in own_decision.text

    # Real ledger files must exist only in the disposable directory.
    assert (tmp_path / "gagf.db").is_file()
    assert not (tmp_path / "uploads").exists()

    # CSV temporary files are removed after processing.
    assert not list(tmp_path.glob("gagf_csv_*"))
