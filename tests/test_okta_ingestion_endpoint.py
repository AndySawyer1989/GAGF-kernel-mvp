from pathlib import Path

from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def setup_function():
    db_path = Path("gagf_kernel.db")

    if db_path.exists():
        db_path.unlink()


def test_okta_ingestion_endpoint_accepts_valid_payload():
    payload = {
        "events": [
            {
                "uuid": "okta-api-001",
                "eventType": "user.authentication.failed",
                "published": "2026-07-08T12:00:00Z",
                "outcome": {
                    "result": "FAILURE",
                },
            },
            {
                "uuid": "okta-api-002",
                "eventType": "user.session.start",
                "published": "2026-07-08T12:05:00Z",
                "outcome": {
                    "result": "SUCCESS",
                },
            },
        ],
    }

    response = client.post("/ingest/okta", json=payload)

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ingested"
    assert data["source_system"] == "okta"
    assert data["events_normalized"] == 2
    assert data["snapshot_id"].startswith("okta-")
    assert data["snapshot_status"] == "VALID"
    assert data["selected_strategy"] == "Normal"


def test_okta_ingestion_endpoint_rejects_missing_events_field():
    payload = {}

    response = client.post("/ingest/okta", json=payload)

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "failed"
    assert data["source_system"] == "okta"
    assert data["events_normalized"] == 0
    assert "missing_events_field" in data["errors"]


def test_okta_ingestion_endpoint_rejects_empty_events_list():
    payload = {
        "events": [],
    }

    response = client.post("/ingest/okta", json=payload)

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "failed"
    assert data["source_system"] == "okta"
    assert data["events_normalized"] == 0
    assert "events_list_is_empty" in data["errors"]


def test_okta_ingestion_endpoint_rejects_events_not_list():
    payload = {
        "events": "not-a-list",
    }

    response = client.post("/ingest/okta", json=payload)

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "failed"
    assert data["source_system"] == "okta"
    assert data["events_normalized"] == 0
    assert "events_must_be_a_list" in data["errors"]


def test_okta_ingestion_endpoint_rejects_event_missing_required_fields():
    payload = {
        "events": [
            {
                "uuid": "",
                "eventType": "",
                "published": "",
            },
        ],
    }

    response = client.post("/ingest/okta", json=payload)

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "failed"
    assert data["source_system"] == "okta"
    assert data["events_normalized"] == 0
    assert "event_0_missing_uuid" in data["errors"]
    assert "event_0_missing_eventType" in data["errors"]
    assert "event_0_missing_published" in data["errors"]





