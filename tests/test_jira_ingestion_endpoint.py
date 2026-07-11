import sys
from pathlib import Path

from fastapi.testclient import TestClient


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.main import app


client = TestClient(app)


def test_jira_ingestion_endpoint_accepts_valid_payload():
    response = client.post(
        "/ingest/jira",
        json={
            "events": [
                {
                    "id": "jira-test-001",
                    "key": "FIP-101",
                    "issue_type": "Story",
                    "status": "Blocked",
                    "priority": "Medium",
                    "blocked": True,
                    "created": "2026-07-07T12:00:00Z",
                    "updated": "2026-07-07T12:30:00Z",
                },
                {
                    "id": "jira-test-002",
                    "key": "FIP-202",
                    "issue_type": "Bug",
                    "status": "Open",
                    "priority": "Critical",
                    "created": "2026-07-07T13:00:00Z",
                    "updated": "2026-07-07T13:15:00Z",
                },
            ]
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ingested"
    assert data["source_system"] == "jira"
    assert data["events_normalized"] == 2
    assert data["snapshot_status"] == "VALID"
    assert data["snapshot_id"].startswith("jira-")
    assert data["selected_strategy"] in ["Normal", "Contain", "Probe"]
    assert "kernel_decision" in data
    assert "decision_id" in data


def test_jira_ingestion_rejects_missing_events():
    response = client.post("/ingest/jira", json={})

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "failed"
    assert data["source_system"] == "jira"
    assert data["events_normalized"] == 0
    assert "missing_events_field" in data["errors"]


def test_jira_ingestion_rejects_empty_events():
    response = client.post("/ingest/jira", json={"events": []})

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "failed"
    assert data["events_normalized"] == 0
    assert "events_list_is_empty" in data["errors"]


def test_jira_ingestion_rejects_events_not_list():
    response = client.post("/ingest/jira", json={"events": "not-a-list"})

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "failed"
    assert data["events_normalized"] == 0
    assert "events_must_be_a_list" in data["errors"]


def test_jira_ingestion_rejects_event_missing_required_fields():
    response = client.post(
        "/ingest/jira",
        json={
            "events": [
                {
                    "id": "bad-jira-event-001",
                }
            ]
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "failed"
    assert data["events_normalized"] == 0
    assert "event_0_missing_key" in data["errors"]
    assert "event_0_missing_status" in data["errors"]
    assert "event_0_missing_timestamp" in data["errors"]
