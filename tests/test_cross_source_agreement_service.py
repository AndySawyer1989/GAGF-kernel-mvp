from backend.app.gagf.cross_source_agreement_service import CrossSourceAgreementService
from backend.app.gagf.schemas import RawSecurityEvent, TimestampQuality


def make_event(
    event_id="evt-1",
    source_system="defender",
    event_type="unauthorized_api_call",
):
    return RawSecurityEvent(
        event_id=event_id,
        event_type=event_type,
        event_occurred_at="2026-07-09T10:00:00Z",
        timestamp_quality=TimestampQuality.SOURCE_OCCURRED_AT,
        kernel_eligible=True,
        source_system=source_system,
        metadata={
            "raw_payload": {
                "id": event_id,
            },
        },
    )


def test_cross_source_agreement_service_scores_empty_event_list_as_none():
    result = CrossSourceAgreementService().evaluate_agreement([])

    assert result["status"] == "ok"
    assert result["event_count"] == 0
    assert result["source_count"] == 0
    assert result["agreement_score"] == 0.0
    assert result["agreement_band"] == "none"
    assert result["supporting_sources"] == []
    assert result["kernel_roles_present"] == []
    assert result["event_types"] == []


def test_cross_source_agreement_service_scores_single_source_as_weak():
    events = [
        make_event(
            event_id="evt-1",
            source_system="defender",
            event_type="unauthorized_api_call",
        )
    ]

    result = CrossSourceAgreementService().evaluate_agreement(events)

    assert result["status"] == "ok"
    assert result["event_count"] == 1
    assert result["source_count"] == 1
    assert result["agreement_score"] == 0.58
    assert result["agreement_band"] == "weak"
    assert result["supporting_sources"] == ["defender"]
    assert result["kernel_roles_present"] == ["threat_evidence"]
    assert "identity_evidence" in result["missing_roles"]


def test_cross_source_agreement_service_scores_two_security_sources_as_moderate():
    events = [
        make_event(
            event_id="evt-1",
            source_system="defender",
            event_type="unauthorized_api_call",
        ),
        make_event(
            event_id="evt-2",
            source_system="sentinelone",
            event_type="unauthorized_api_call",
        ),
    ]

    result = CrossSourceAgreementService().evaluate_agreement(events)

    assert result["status"] == "ok"
    assert result["event_count"] == 2
    assert result["source_count"] == 2
    assert result["agreement_score"] == 0.685
    assert result["agreement_band"] == "moderate"
    assert result["supporting_sources"] == ["defender", "sentinelone"]
    assert result["kernel_roles_present"] == ["threat_evidence"]
    assert result["event_types"] == ["unauthorized_api_call"]


def test_cross_source_agreement_service_scores_multi_role_evidence_as_moderate():
    events = [
        make_event(
            event_id="evt-1",
            source_system="okta",
            event_type="unauthorized_api_call",
        ),
        make_event(
            event_id="evt-2",
            source_system="defender",
            event_type="unauthorized_api_call",
        ),
        make_event(
            event_id="evt-3",
            source_system="jira",
            event_type="unauthorized_api_call",
        ),
    ]

    result = CrossSourceAgreementService().evaluate_agreement(events)

    assert result["status"] == "ok"
    assert result["event_count"] == 3
    assert result["source_count"] == 3
    assert result["agreement_score"] == 0.88
    assert result["agreement_band"] == "strong"
    assert result["supporting_sources"] == ["defender", "jira", "okta"]

    assert "identity_evidence" in result["kernel_roles_present"]
    assert "threat_evidence" in result["kernel_roles_present"]
    assert "workflow_evidence" in result["kernel_roles_present"]


def test_cross_source_agreement_service_lowers_score_for_misaligned_event_types():
    events = [
        make_event(
            event_id="evt-1",
            source_system="okta",
            event_type="unauthorized_api_call",
        ),
        make_event(
            event_id="evt-2",
            source_system="defender",
            event_type="security_review",
        ),
        make_event(
            event_id="evt-3",
            source_system="jira",
            event_type="work_blocked",
        ),
    ]

    result = CrossSourceAgreementService().evaluate_agreement(events)

    assert result["status"] == "ok"
    assert result["event_count"] == 3
    assert result["source_count"] == 3
    assert result["agreement_score"] == 0.78
    assert result["agreement_band"] == "moderate"
    assert result["factors"]["event_type_alignment"] == 0.5


def test_cross_source_agreement_service_lowers_score_for_unknown_source():
    events = [
        make_event(
            event_id="evt-1",
            source_system="defender",
            event_type="unauthorized_api_call",
        ),
        make_event(
            event_id="evt-2",
            source_system="unknown-source",
            event_type="unauthorized_api_call",
        ),
    ]

    result = CrossSourceAgreementService().evaluate_agreement(events)

    assert result["status"] == "ok"
    assert result["event_count"] == 2
    assert result["source_count"] == 2
    assert result["agreement_score"] == 0.585
    assert result["agreement_band"] == "weak"
    assert result["supporting_sources"] == ["defender", "unknown-source"]
    assert result["factors"]["registered_sources"] == 0.5


def test_cross_source_agreement_service_detects_missing_roles():
    events = [
        make_event(
            event_id="evt-1",
            source_system="defender",
            event_type="unauthorized_api_call",
        )
    ]

    result = CrossSourceAgreementService().evaluate_agreement(events)

    assert "identity_evidence" in result["missing_roles"]
    assert "delivery_evidence" in result["missing_roles"]
    assert "workflow_evidence" in result["missing_roles"]
    assert "incident_evidence" in result["missing_roles"]
    assert "threat_evidence" not in result["missing_roles"]




