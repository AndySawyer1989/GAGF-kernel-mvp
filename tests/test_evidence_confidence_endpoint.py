from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def make_event_payload(
    event_id="evt-1",
    source_system="defender",
    event_type="unauthorized_api_call",
    timestamp_quality="SOURCE_OCCURRED_AT",
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
        "timestamp_quality": timestamp_quality,
        "kernel_eligible": True,
        "source_system": source_system,
        "metadata": metadata,
    }


def test_evidence_confidence_endpoint_builds_confidence_for_strong_multi_source_evidence():
    response = client.post(
        "/evidence/confidence",
        json=[
            make_event_payload(
                event_id="evt-1",
                source_system="okta",
                event_type="unauthorized_api_call",
            ),
            make_event_payload(
                event_id="evt-2",
                source_system="defender",
                event_type="unauthorized_api_call",
            ),
            make_event_payload(
                event_id="evt-3",
                source_system="jira",
                event_type="unauthorized_api_call",
            ),
        ],
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"
    assert data["event_count"] == 3
    assert data["confidence_score"] == 0.9622
    assert data["confidence_band"] == "high"

    confidence = data["evidence_confidence"]

    assert confidence["score"] == 0.9622
    assert confidence["factors"]["evidence_quality"] == 0.995
    assert confidence["factors"]["cross_source_agreement"] == 0.88
    assert confidence["factors"]["conflict_health"] == 1.0
    assert confidence["factors"]["source_coverage"] == 1.0
    assert confidence["factors"]["diagnostic_score"] == 0.9622


def test_evidence_confidence_endpoint_builds_confidence_for_single_source_evidence():
    response = client.post(
        "/evidence/confidence",
        json=[
            make_event_payload(
                event_id="evt-1",
                source_system="defender",
                event_type="unauthorized_api_call",
            )
        ],
    )

    assert response.status_code == 200

    data = response.json()
    confidence = data["evidence_confidence"]

    assert data["status"] == "ok"
    assert data["event_count"] == 1
    assert data["confidence_score"] == 0.874
    assert data["confidence_band"] == "high"

    assert confidence["score"] == 0.874
    assert confidence["factors"]["evidence_quality"] == 1.0
    assert confidence["factors"]["cross_source_agreement"] == 0.58
    assert confidence["factors"]["conflict_health"] == 1.0
    assert confidence["factors"]["source_coverage"] == 1.0


def test_evidence_confidence_endpoint_lowers_confidence_for_conflicting_evidence():
    response = client.post(
        "/evidence/confidence",
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
    confidence = data["evidence_confidence"]

    assert data["status"] == "ok"
    assert data["event_count"] == 2
    assert data["confidence_score"] == 0.8074
    assert data["confidence_band"] == "medium"

    assert confidence["score"] == 0.8074
    assert confidence["factors"]["conflict_health"] == 0.65
    assert data["diagnostics"]["conflicts"]["conflict_count"] == 1


def test_evidence_confidence_endpoint_lowers_confidence_for_unknown_source():
    response = client.post(
        "/evidence/confidence",
        json=[
            make_event_payload(
                event_id="evt-1",
                source_system="unknown-source",
                event_type="unauthorized_api_call",
            )
        ],
    )

    assert response.status_code == 200

    data = response.json()
    confidence = data["evidence_confidence"]

    assert data["status"] == "ok"
    assert data["event_count"] == 1
    assert data["confidence_score"] == 0.586
    assert data["confidence_band"] == "low"

    assert confidence["score"] == 0.586
    assert confidence["factors"]["evidence_quality"] == 0.4
    assert confidence["factors"]["cross_source_agreement"] == 0.32


def test_evidence_confidence_endpoint_handles_empty_event_batch():
    response = client.post(
        "/evidence/confidence",
        json=[],
    )

    assert response.status_code == 200

    data = response.json()
    confidence = data["evidence_confidence"]

    assert data["status"] == "ok"
    assert data["event_count"] == 0
    assert data["confidence_score"] == 0.35
    assert data["confidence_band"] == "low"

    assert confidence["score"] == 0.35
    assert confidence["factors"]["evidence_quality"] == 0.0
    assert confidence["factors"]["cross_source_agreement"] == 0.0
    assert confidence["factors"]["conflict_health"] == 1.0
    assert confidence["factors"]["source_coverage"] == 1.0
