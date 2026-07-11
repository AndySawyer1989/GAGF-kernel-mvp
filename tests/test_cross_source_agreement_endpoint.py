from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def make_event_payload(
    event_id="evt-1",
    source_system="defender",
    event_type="unauthorized_api_call",
):
    return {
        "event_id": event_id,
        "event_type": event_type,
        "event_occurred_at": "2026-07-09T10:00:00Z",
        "timestamp_quality": "SOURCE_OCCURRED_AT",
        "kernel_eligible": True,
        "source_system": source_system,
        "metadata": {
            "raw_payload": {
                "id": event_id,
            },
        },
    }


def test_cross_source_agreement_endpoint_scores_empty_batch_as_none():
    response = client.post(
        "/evidence/agreement",
        json=[],
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"
    assert data["event_count"] == 0
    assert data["source_count"] == 0
    assert data["agreement_score"] == 0.0
    assert data["agreement_band"] == "none"
    assert data["supporting_sources"] == []
    assert data["kernel_roles_present"] == []
    assert data["event_types"] == []


def test_cross_source_agreement_endpoint_scores_single_source_as_weak():
    response = client.post(
        "/evidence/agreement",
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

    assert data["status"] == "ok"
    assert data["event_count"] == 1
    assert data["source_count"] == 1
    assert data["agreement_score"] == 0.58
    assert data["agreement_band"] == "weak"
    assert data["supporting_sources"] == ["defender"]
    assert data["kernel_roles_present"] == ["threat_evidence"]


def test_cross_source_agreement_endpoint_scores_two_security_sources_as_moderate():
    response = client.post(
        "/evidence/agreement",
        json=[
            make_event_payload(
                event_id="evt-1",
                source_system="defender",
                event_type="unauthorized_api_call",
            ),
            make_event_payload(
                event_id="evt-2",
                source_system="sentinelone",
                event_type="unauthorized_api_call",
            ),
        ],
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"
    assert data["event_count"] == 2
    assert data["source_count"] == 2
    assert data["agreement_score"] == 0.685
    assert data["agreement_band"] == "moderate"
    assert data["supporting_sources"] == ["defender", "sentinelone"]
    assert data["kernel_roles_present"] == ["threat_evidence"]
    assert data["event_types"] == ["unauthorized_api_call"]


def test_cross_source_agreement_endpoint_scores_multi_role_evidence_as_strong():
    response = client.post(
        "/evidence/agreement",
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
    assert data["source_count"] == 3
    assert data["agreement_score"] == 0.88
    assert data["agreement_band"] == "strong"
    assert data["supporting_sources"] == ["defender", "jira", "okta"]

    assert "identity_evidence" in data["kernel_roles_present"]
    assert "threat_evidence" in data["kernel_roles_present"]
    assert "workflow_evidence" in data["kernel_roles_present"]


def test_cross_source_agreement_endpoint_lowers_score_for_misaligned_event_types():
    response = client.post(
        "/evidence/agreement",
        json=[
            make_event_payload(
                event_id="evt-1",
                source_system="okta",
                event_type="unauthorized_api_call",
            ),
            make_event_payload(
                event_id="evt-2",
                source_system="defender",
                event_type="security_review",
            ),
            make_event_payload(
                event_id="evt-3",
                source_system="jira",
                event_type="work_blocked",
            ),
        ],
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"
    assert data["event_count"] == 3
    assert data["source_count"] == 3
    assert data["agreement_score"] == 0.78
    assert data["agreement_band"] == "moderate"
    assert data["factors"]["event_type_alignment"] == 0.5


def test_cross_source_agreement_endpoint_lowers_score_for_unknown_source():
    response = client.post(
        "/evidence/agreement",
        json=[
            make_event_payload(
                event_id="evt-1",
                source_system="defender",
                event_type="unauthorized_api_call",
            ),
            make_event_payload(
                event_id="evt-2",
                source_system="unknown-source",
                event_type="unauthorized_api_call",
            ),
        ],
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"
    assert data["event_count"] == 2
    assert data["source_count"] == 2
    assert data["agreement_score"] == 0.585
    assert data["agreement_band"] == "weak"
    assert data["supporting_sources"] == ["defender", "unknown-source"]
    assert data["factors"]["registered_sources"] == 0.5


def test_cross_source_agreement_endpoint_reports_missing_roles():
    response = client.post(
        "/evidence/agreement",
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

    assert "identity_evidence" in data["missing_roles"]
    assert "delivery_evidence" in data["missing_roles"]
    assert "workflow_evidence" in data["missing_roles"]
    assert "incident_evidence" in data["missing_roles"]
    assert "threat_evidence" not in data["missing_roles"]
