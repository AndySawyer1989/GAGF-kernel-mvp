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


def test_evidence_diagnostics_endpoint_returns_degraded_for_empty_batch():
    response = client.post(
        "/evidence/diagnostics",
        json=[],
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"
    assert data["event_count"] == 0
    assert data["diagnostic_score"] == 0.35
    assert data["diagnostic_band"] == "degraded"

    assert data["quality"]["event_count"] == 0
    assert data["quality"]["average_quality_score"] == 0.0
    assert data["quality"]["average_quality_band"] == "invalid"

    assert data["agreement"]["event_count"] == 0
    assert data["agreement"]["agreement_score"] == 0.0
    assert data["agreement"]["agreement_band"] == "none"

    assert data["conflicts"]["conflict_count"] == 0
    assert data["source_coverage"]["total_sources"] == 7


def test_evidence_diagnostics_endpoint_scores_strong_multi_source_evidence_as_healthy():
    response = client.post(
        "/evidence/diagnostics",
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
    assert data["diagnostic_score"] == 0.9622
    assert data["diagnostic_band"] == "healthy"

    assert data["quality"]["average_quality_score"] == 0.995
    assert data["quality"]["average_quality_band"] == "high"

    assert data["agreement"]["agreement_score"] == 0.88
    assert data["agreement"]["agreement_band"] == "strong"

    assert data["conflicts"]["conflict_count"] == 0
    assert data["source_coverage"]["coverage_gap_count"] == 0


def test_evidence_diagnostics_endpoint_recommends_more_agreement_for_single_source():
    response = client.post(
        "/evidence/diagnostics",
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

    recommendation_types = {
        recommendation["recommendation_type"]
        for recommendation in data["recommendations"]
    }

    assert data["status"] == "ok"
    assert data["event_count"] == 1
    assert data["agreement"]["agreement_score"] == 0.58
    assert data["agreement"]["agreement_band"] == "weak"
    assert "increase_cross_source_agreement" in recommendation_types
    assert "missing_kernel_roles" in recommendation_types


def test_evidence_diagnostics_endpoint_detects_conflict_recommendation():
    response = client.post(
        "/evidence/diagnostics",
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

    recommendation_types = {
        recommendation["recommendation_type"]
        for recommendation in data["recommendations"]
    }

    assert data["status"] == "ok"
    assert data["conflicts"]["conflict_count"] == 1
    assert data["conflicts"]["severity_counts"]["warning"] == 1
    assert "resolve_evidence_conflicts" in recommendation_types


def test_evidence_diagnostics_endpoint_recommends_improving_low_quality_evidence():
    response = client.post(
        "/evidence/diagnostics",
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

    recommendation_types = {
        recommendation["recommendation_type"]
        for recommendation in data["recommendations"]
    }

    assert data["status"] == "ok"
    assert data["quality"]["average_quality_score"] == 0.4
    assert data["quality"]["average_quality_band"] == "low"
    assert "improve_evidence_quality" in recommendation_types
    assert "increase_cross_source_agreement" in recommendation_types






