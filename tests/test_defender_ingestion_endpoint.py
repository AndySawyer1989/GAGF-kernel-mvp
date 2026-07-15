from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def test_defender_ingestion_endpoint_accepts_events():
    payload = {
        "events": [
            {
                "id": "def-api-001",
                "title": "Suspicious PowerShell activity",
                "severity": "high",
                "category": "Execution",
                "status": "new",
                "createdDateTime": "2026-07-08T20:00:00Z",
            },
            {
                "alertId": "def-api-002",
                "title": "Endpoint sensor degraded",
                "severity": "medium",
                "category": "Endpoint",
                "status": "inProgress",
                "createdDateTime": "2026-07-08T20:05:00Z",
            },
        ]
    }

    response = client.post("/ingest/defender", json=payload)

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ingested"
    assert data["source_system"] == "defender"
    assert data["events_normalized"] == 2
    assert data["snapshot_id"].startswith("defender-")
    assert data["snapshot_status"] == "VALID"
    assert data["decision_id"]
    assert data["kernel_decision"]


def test_defender_ingestion_rejects_missing_events_field():
    response = client.post("/ingest/defender", json={})

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "failed"
    assert data["source_system"] == "defender"
    assert data["events_normalized"] == 0
    assert "missing_events_field" in data["errors"]


def test_defender_ingestion_rejects_missing_required_event_fields():
    payload = {
        "events": [
            {
                "severity": "high",
                "category": "Execution",
            }
        ]
    }

    response = client.post("/ingest/defender", json=payload)

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "failed"
    assert data["source_system"] == "defender"
    assert data["events_normalized"] == 0
    assert "event_0_missing_id" in data["errors"]
    assert "event_0_missing_title" in data["errors"]
    assert "event_0_missing_timestamp" in data["errors"]





