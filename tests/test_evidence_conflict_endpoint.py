from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def make_event_payload(
    event_id="evt-1",
    source_system="defender",
    event_type="unauthorized_api_call",
    metadata=None,
):
    if metadata is None:
        metadata = {
            "raw_payload": {
                "id": event_id,
            },
        }

    return {
        "event_id": event_id,
        "event_type": event_type,
        "event_occurred_at": "2026-07-09T10:00:00Z",
        "timestamp_quality": "SOURCE_OCCURRED_AT",
        "kernel_eligible": True,
        "source_system": source_system,
        "metadata": metadata,
    }


def test_evidence_conflict_endpoint_returns_no_conflicts_for_empty_batch():
    response = client.post(
        "/evidence/conflicts",
        json=[],
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"
    assert data["event_count"] == 0
    assert data["conflict_count"] == 0
    assert data["severity_counts"]["critical"] == 0
    assert data["severity_counts"]["warning"] == 0
    assert data["severity_counts"]["info"] == 0
    assert data["conflicts"] == []


def test_evidence_conflict_endpoint_returns_no_conflicts_for_aligned_security_events():
    response = client.post(
        "/evidence/conflicts",
        json=[
            make_event_payload(
                event_id="evt-1",
                source_system="defender",
                event_type="unauthorized_api_call",
                metadata={
                    "severity": "high",
                    "status": "active",
                },
            ),
            make_event_payload(
                event_id="evt-2",
                source_system="sentinelone",
                event_type="unauthorized_api_call",
                metadata={
                    "classification": "malware",
                    "analyst_verdict": "true_positive",
                },
            ),
        ],
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"
    assert data["event_count"] == 2
    assert data["conflict_count"] == 0
    assert data["conflicts"] == []


def test_evidence_conflict_endpoint_detects_security_resolution_mismatch():
    response = client.post(
        "/evidence/conflicts",
        json=[
            make_event_payload(
                event_id="evt-1",
                source_system="defender",
                event_type="unauthorized_api_call",
                metadata={
                    "severity": "high",
                    "status": "active",
                },
            ),
            make_event_payload(
                event_id="evt-2",
                source_system="sentinelone",
                event_type="verification_passed",
                metadata={
                    "mitigation_status": "mitigated",
                },
            ),
        ],
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"
    assert data["event_count"] == 2
    assert data["conflict_count"] == 1
    assert data["severity_counts"]["warning"] == 1

    conflict = data["conflicts"][0]

    assert conflict["conflict_type"] == "security_resolution_mismatch"
    assert conflict["severity"] == "warning"
    assert conflict["sources"] == ["defender", "sentinelone"]


def test_evidence_conflict_endpoint_detects_workflow_state_mismatch():
    response = client.post(
        "/evidence/conflicts",
        json=[
            make_event_payload(
                event_id="evt-1",
                source_system="jira",
                event_type="work_blocked",
                metadata={
                    "status": "blocked",
                },
            ),
            make_event_payload(
                event_id="evt-2",
                source_system="github",
                event_type="verification_passed",
                metadata={
                    "state": "merged",
                },
            ),
        ],
    )

    assert response.status_code == 200

    data = response.json()
    conflict = data["conflicts"][0]

    assert data["status"] == "ok"
    assert data["event_count"] == 2
    assert data["conflict_count"] == 1
    assert conflict["conflict_type"] == "workflow_state_mismatch"
    assert conflict["severity"] == "warning"
    assert conflict["sources"] == ["github", "jira"]


def test_evidence_conflict_endpoint_detects_identity_outcome_mismatch():
    response = client.post(
        "/evidence/conflicts",
        json=[
            make_event_payload(
                event_id="evt-1",
                source_system="okta",
                event_type="login_failed",
                metadata={
                    "outcome": "failure",
                },
            ),
            make_event_payload(
                event_id="evt-2",
                source_system="entra",
                event_type="login_success",
                metadata={
                    "outcome": "success",
                },
            ),
        ],
    )

    assert response.status_code == 200

    data = response.json()
    conflict = data["conflicts"][0]

    assert data["status"] == "ok"
    assert data["event_count"] == 2
    assert data["conflict_count"] == 1
    assert conflict["conflict_type"] == "identity_outcome_mismatch"
    assert conflict["severity"] == "warning"
    assert conflict["sources"] == ["entra", "okta"]


def test_evidence_conflict_endpoint_detects_multiple_conflicts():
    response = client.post(
        "/evidence/conflicts",
        json=[
            make_event_payload(
                event_id="evt-1",
                source_system="defender",
                event_type="unauthorized_api_call",
                metadata={
                    "severity": "high",
                    "status": "active",
                },
            ),
            make_event_payload(
                event_id="evt-2",
                source_system="sentinelone",
                event_type="verification_passed",
                metadata={
                    "mitigation_status": "mitigated",
                },
            ),
            make_event_payload(
                event_id="evt-3",
                source_system="jira",
                event_type="work_blocked",
                metadata={
                    "status": "blocked",
                },
            ),
            make_event_payload(
                event_id="evt-4",
                source_system="github",
                event_type="verification_passed",
                metadata={
                    "state": "merged",
                },
            ),
        ],
    )

    assert response.status_code == 200

    data = response.json()

    conflict_types = {
        conflict["conflict_type"]
        for conflict in data["conflicts"]
    }

    assert data["status"] == "ok"
    assert data["event_count"] == 4
    assert data["conflict_count"] == 2
    assert data["severity_counts"]["warning"] == 2
    assert "security_resolution_mismatch" in conflict_types
    assert "workflow_state_mismatch" in conflict_types



