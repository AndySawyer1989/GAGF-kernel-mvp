from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def test_github_ingestion_endpoint_accepts_events():
    payload = {
        "events": [
            {
                "id": "gh-api-001",
                "event_name": "pull_request",
                "action": "opened",
                "created_at": "2026-07-03T18:00:00Z",
            },
            {
                "id": "gh-api-002",
                "event_name": "push",
                "action": "created",
                "created_at": "2026-07-03T18:05:00Z",
            },
        ]
    }

    response = client.post("/ingest/github", json=payload)

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ingested"
    assert data["source_system"] == "github"
    assert data["events_normalized"] == 2
    assert data["snapshot_status"] == "VALID"
    assert "snapshot_id" in data
    assert "decision_id" in data
    assert "selected_strategy" in data
    assert "kernel_decision" in data
    assert "reason" in data
