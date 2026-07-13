from pathlib import Path

from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def setup_function():
    db_path = Path("gagf_kernel.db")

    if db_path.exists():
        db_path.unlink()


def test_entra_ingestion_endpoint_accepts_valid_payload():
    payload = {
        "events": [
            {
                "id": "entra-api-001",
                "activityDisplayName": "User sign-in failed",
                "createdDateTime": "2026-07-08T12:00:00Z",
                "status": {
                    "errorCode": 50126,
                    "failureReason": "Invalid username or password failure",
                },
            },
            {
                "id": "entra-api-002",
                "activityDisplayName": "User sign-in",
                "createdDateTime": "2026-07-08T12:05:00Z",
                "conditionalAccessStatus": "success",
                "riskState": "none",
                "riskLevelAggregated": "none",
                "status": {
                    "errorCode": 0,
                },
            },
        ],
    }

    response = client.post("/ingest/entra", json=payload)

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ingested"
    assert data["source_system"] == "entra"
    assert data["events_normalized"] == 2
    assert data["snapshot_id"].startswith("entra-")
    assert data["snapshot_status"] == "VALID"
    assert data["selected_strategy"] == "Normal"


def test_entra_ingestion_endpoint_rejects_missing_events_field():
    payload = {}

    response = client.post("/ingest/entra", json=payload)

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "failed"
    assert data["source_system"] == "entra"
    assert data["events_normalized"] == 0
    assert "missing_events_field" in data["errors"]


def test_entra_ingestion_endpoint_rejects_empty_events_list():
    payload = {
        "events": [],
    }

    response = client.post("/ingest/entra", json=payload)

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "failed"
    assert data["source_system"] == "entra"
    assert data["events_normalized"] == 0
    assert "events_list_is_empty" in data["errors"]


def test_entra_ingestion_endpoint_rejects_events_not_list():
    payload = {
        "events": "not-a-list",
    }

    response = client.post("/ingest/entra", json=payload)

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "failed"
    assert data["source_system"] == "entra"
    assert data["events_normalized"] == 0
    assert "events_must_be_a_list" in data["errors"]


def test_entra_ingestion_endpoint_rejects_event_missing_required_fields():
    payload = {
        "events": [
            {
                "id": "",
                "activityDisplayName": "",
                "createdDateTime": "",
            },
        ],
    }

    response = client.post("/ingest/entra", json=payload)

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "failed"
    assert data["source_system"] == "entra"
    assert data["events_normalized"] == 0
    assert "event_0_missing_id" in data["errors"]
    assert "event_0_missing_activityDisplayName" in data["errors"]
    assert "event_0_missing_createdDateTime" in data["errors"]


