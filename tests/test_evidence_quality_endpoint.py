from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def make_event_payload(
    event_id="evt-1",
    source_system="defender",
    timestamp_quality="SOURCE_OCCURRED_AT",
    metadata=None,
):
    if metadata is None:
        metadata = {
            "raw_payload": {
                "id": event_id,
            },
            "severity": "high",
        }

    return {
        "event_id": event_id,
        "event_type": "unauthorized_api_call",
        "event_occurred_at": "2026-07-09T10:00:00Z",
        "timestamp_quality": timestamp_quality,
        "kernel_eligible": True,
        "source_system": source_system,
        "metadata": metadata,
    }


def test_evidence_quality_endpoint_scores_security_event():
    response = client.post(
        "/evidence/quality",
        json=[
            make_event_payload(
                event_id="evt-1",
                source_system="defender",
            )
        ],
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"
    assert data["event_count"] == 1
    assert data["average_quality_score"] == 1.0
    assert data["average_quality_band"] == "high"
    assert len(data["events"]) == 1

    scored_event = data["events"][0]

    assert scored_event["event_id"] == "evt-1"
    assert scored_event["source_system"] == "defender"
    assert scored_event["quality_score"] == 1.0
    assert scored_event["quality_band"] == "high"


def test_evidence_quality_endpoint_scores_operational_event():
    response = client.post(
        "/evidence/quality",
        json=[
            make_event_payload(
                event_id="evt-2",
                source_system="github",
            )
        ],
    )

    assert response.status_code == 200

    data = response.json()
    scored_event = data["events"][0]

    assert data["status"] == "ok"
    assert data["event_count"] == 1
    assert scored_event["source_system"] == "github"
    assert scored_event["quality_score"] == 0.985
    assert scored_event["quality_band"] == "high"
    assert scored_event["factors"]["trust_tier_weight"] == 0.85


def test_evidence_quality_endpoint_scores_mixed_batch():
    response = client.post(
        "/evidence/quality",
        json=[
            make_event_payload(
                event_id="evt-1",
                source_system="defender",
            ),
            make_event_payload(
                event_id="evt-2",
                source_system="sentinelone",
            ),
            make_event_payload(
                event_id="evt-3",
                source_system="github",
            ),
        ],
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"
    assert data["event_count"] == 3
    assert data["average_quality_score"] == 0.995
    assert data["average_quality_band"] == "high"
    assert len(data["events"]) == 3


def test_evidence_quality_endpoint_lowers_score_for_missing_timestamp():
    response = client.post(
        "/evidence/quality",
        json=[
            make_event_payload(
                event_id="evt-4",
                source_system="defender",
                timestamp_quality="MISSING_TIMESTAMP",
            )
        ],
    )

    assert response.status_code == 200

    data = response.json()
    scored_event = data["events"][0]

    assert scored_event["quality_score"] == 0.75
    assert scored_event["quality_band"] == "medium"
    assert scored_event["factors"]["timestamp_quality"] == 0.0


def test_evidence_quality_endpoint_scores_unknown_source_as_low_quality():
    response = client.post(
        "/evidence/quality",
        json=[
            make_event_payload(
                event_id="evt-5",
                source_system="unknown-source",
            )
        ],
    )

    assert response.status_code == 200

    data = response.json()
    scored_event = data["events"][0]

    assert scored_event["source_system"] == "unknown-source"
    assert scored_event["quality_score"] == 0.4
    assert scored_event["quality_band"] == "low"
    assert scored_event["factors"]["source_registered"] == 0.0
    assert scored_event["factors"]["source_enabled"] == 0.0
    assert scored_event["factors"]["kernel_role_present"] == 0.0


def test_evidence_quality_endpoint_accepts_empty_batch():
    response = client.post(
        "/evidence/quality",
        json=[],
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"
    assert data["event_count"] == 0
    assert data["average_quality_score"] == 0.0
    assert data["average_quality_band"] == "invalid"
    assert data["events"] == []


