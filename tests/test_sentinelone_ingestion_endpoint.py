from pathlib import Path

from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def setup_function():
    db_path = Path("gagf_kernel.db")

    if db_path.exists():
        db_path.unlink()


def test_sentinelone_ingestion_endpoint_accepts_valid_payload():
    payload = {
        "events": [
            {
                "id": "s1-api-001",
                "eventType": "threat_detected",
                "threatName": "Suspicious PowerShell",
                "classification": "malware",
                "confidenceLevel": "high",
                "mitigationStatus": "not_mitigated",
                "incidentStatus": "unresolved",
                "createdAt": "2026-07-08T12:00:00Z",
            },
            {
                "id": "s1-api-002",
                "eventType": "agent_online",
                "agentName": "workstation-001",
                "createdAt": "2026-07-08T12:05:00Z",
            },
        ],
    }

    response = client.post("/ingest/sentinelone", json=payload)

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ingested"
    assert data["source_system"] == "sentinelone"
    assert data["events_normalized"] == 2
    assert data["snapshot_id"].startswith("sentinelone-")
    assert data["snapshot_status"] == "VALID"
    assert data["selected_strategy"] == "Normal"


def test_sentinelone_ingestion_endpoint_rejects_missing_events_field():
    payload = {}

    response = client.post("/ingest/sentinelone", json=payload)

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "failed"
    assert data["source_system"] == "sentinelone"
    assert data["events_normalized"] == 0
    assert "missing_events_field" in data["errors"]


def test_sentinelone_ingestion_endpoint_rejects_empty_events_list():
    payload = {
        "events": [],
    }

    response = client.post("/ingest/sentinelone", json=payload)

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "failed"
    assert data["source_system"] == "sentinelone"
    assert data["events_normalized"] == 0
    assert "events_list_is_empty" in data["errors"]


def test_sentinelone_ingestion_endpoint_rejects_events_not_list():
    payload = {
        "events": "not-a-list",
    }

    response = client.post("/ingest/sentinelone", json=payload)

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "failed"
    assert data["source_system"] == "sentinelone"
    assert data["events_normalized"] == 0
    assert "events_must_be_a_list" in data["errors"]


def test_sentinelone_ingestion_endpoint_rejects_event_missing_required_fields():
    payload = {
        "events": [
            {
                "id": "",
                "eventType": "",
                "createdAt": "",
            },
        ],
    }

    response = client.post("/ingest/sentinelone", json=payload)

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "failed"
    assert data["source_system"] == "sentinelone"
    assert data["events_normalized"] == 0
    assert "event_0_missing_id" in data["errors"]
    assert "event_0_missing_eventType" in data["errors"]
    assert "event_0_missing_createdAt" in data["errors"]




