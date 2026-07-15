import sys
from pathlib import Path

from fastapi.testclient import TestClient


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.main import app


client = TestClient(app)


def test_servicenow_ingestion_endpoint_accepts_valid_payload():
    response = client.post(
        "/ingest/servicenow",
        json={
            "events": [
                {
                    "sys_id": "sn-test-001",
                    "table": "incident",
                    "category": "security",
                    "state": "new",
                    "opened_at": "2026-07-06T12:00:00Z",
                    "sys_created_on": "2026-07-06T12:01:00Z",
                },
                {
                    "sys_id": "sn-test-002",
                    "table": "change_request",
                    "state": "authorize",
                    "opened_at": "2026-07-06T13:00:00Z",
                    "sys_created_on": "2026-07-06T13:01:00Z",
                },
            ]
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ingested"
    assert data["source_system"] == "servicenow"
    assert data["events_normalized"] == 2
    assert data["snapshot_status"] == "VALID"
    assert data["snapshot_id"].startswith("servicenow-")
    assert data["selected_strategy"] in ["Normal", "Contain", "Probe"]
    assert "kernel_decision" in data
    assert "decision_id" in data


def test_servicenow_ingestion_rejects_missing_events():
    response = client.post("/ingest/servicenow", json={})

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "failed"
    assert data["source_system"] == "servicenow"
    assert data["events_normalized"] == 0
    assert "missing_events_field" in data["errors"]


def test_servicenow_ingestion_rejects_empty_events():
    response = client.post("/ingest/servicenow", json={"events": []})

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "failed"
    assert data["events_normalized"] == 0
    assert "events_list_is_empty" in data["errors"]


def test_servicenow_ingestion_rejects_events_not_list():
    response = client.post("/ingest/servicenow", json={"events": "not-a-list"})

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "failed"
    assert data["events_normalized"] == 0
    assert "events_must_be_a_list" in data["errors"]


def test_servicenow_ingestion_rejects_event_missing_required_fields():
    response = client.post(
        "/ingest/servicenow",
        json={
            "events": [
                {
                    "sys_id": "bad-sn-event-001",
                }
            ]
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "failed"
    assert data["events_normalized"] == 0
    assert "event_0_missing_table" in data["errors"]
    assert "event_0_missing_timestamp" in data["errors"]





