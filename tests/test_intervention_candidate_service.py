from backend.app.gagf.intervention_candidate_service import (
    InterventionCandidateService,
)
from backend.app.gagf.schemas import RawSecurityEvent, TimestampQuality


def make_event(
    event_id="evt-1",
    source_system="defender",
    event_type="unauthorized_api_call",
    metadata=None,
):
    if metadata is None:
        metadata = {}

    return RawSecurityEvent(
        event_id=event_id,
        event_type=event_type,
        event_occurred_at="2026-07-09T10:00:00Z",
        timestamp_quality=TimestampQuality.SOURCE_OCCURRED_AT,
        kernel_eligible=True,
        source_system=source_system,
        metadata=metadata,
    )


def test_intervention_candidate_service_returns_empty_result():
    result = InterventionCandidateService().recommend_events([])

    assert result == {
        "status": "ok",
        "event_count": 0,
        "signal_count": 0,
        "friction_signal_count": 0,
        "debt_indicator_count": 0,
        "intervention_candidate_count": 0,
        "dominant_intervention_type": "none",
        "intervention_posture": "none",
        "recommended_next_action": "none",
        "governance_debt_score": 0.0,
        "governance_debt_band": "none",
        "debt_posture": "none",
        "intervention_urgency": "none",
        "amplifier_pressure": 0.0,
        "intervention_type_counts": {
            "evidence_reconciliation": 0,
            "security_policy_review": 0,
            "access_policy_tuning": 0,
            "process_refactor": 0,
            "delivery_pipeline_review": 0,
            "operations_stabilization": 0,
        },
        "intervention_candidates": [],
    }


def test_intervention_candidate_service_recommends_security_policy_review():
    events = [
        make_event(
            event_id="evt-1",
            source_system="defender",
            event_type="unauthorized_api_call",
            metadata={
                "severity": "high",
                "status": "active",
            },
        )
    ]

    result = InterventionCandidateService().recommend_events(events)

    assert result["status"] == "ok"
    assert result["event_count"] == 1
    assert result["signal_count"] == 1
    assert result["friction_signal_count"] == 1
    assert result["debt_indicator_count"] == 1
    assert result["intervention_candidate_count"] == 1
    assert result["dominant_intervention_type"] == "security_policy_review"
    assert result["intervention_posture"] == "immediate_intervention"
    assert result["governance_debt_score"] == 0.8635
    assert result["governance_debt_band"] == "critical"
    assert result["debt_posture"] == "critical_debt"
    assert result["intervention_urgency"] == "immediate"
    assert result["amplifier_pressure"] == 0.0

    candidate = result["intervention_candidates"][0]

    assert candidate["event_id"] == "evt-1"
    assert candidate["source_system"] == "defender"
    assert candidate["source_debt_type"] == "security_governance_debt"
    assert candidate["intervention_type"] == "security_policy_review"
    assert candidate["priority_score"] == 0.8279
    assert candidate["priority_band"] == "high"
    assert "Review security policy" in candidate["recommended_action"]
    assert "Security governance debt" in candidate["governance_interpretation"]


def test_intervention_candidate_service_recommends_access_policy_tuning():
    events = [
        make_event(
            event_id="evt-1",
            source_system="okta",
            event_type="login_failed",
            metadata={
                "outcome": "failed",
            },
        )
    ]

    result = InterventionCandidateService().recommend_events(events)

    assert result["dominant_intervention_type"] == "access_policy_tuning"
    assert result["intervention_posture"] == "prioritize_intervention"
    assert result["recommended_next_action"].startswith("Tune identity policy")

    candidate = result["intervention_candidates"][0]

    assert candidate["source_debt_type"] == "identity_governance_debt"
    assert candidate["intervention_type"] == "access_policy_tuning"
    assert candidate["priority_score"] == 0.7474
    assert candidate["priority_band"] == "high"


def test_intervention_candidate_service_recommends_process_and_delivery_interventions():
    events = [
        make_event(
            event_id="evt-1",
            source_system="jira",
            event_type="approval_delayed",
            metadata={
                "status": "waiting",
            },
        ),
        make_event(
            event_id="evt-2",
            source_system="github",
            event_type="pull_request_review_required",
            metadata={
                "state": "review_required",
            },
        ),
    ]

    result = InterventionCandidateService().recommend_events(events)

    assert result["intervention_candidate_count"] == 2
    assert result["dominant_intervention_type"] == "process_refactor"
    assert result["intervention_posture"] == "prioritize_intervention"
    assert result["governance_debt_score"] == 0.727
    assert result["governance_debt_band"] == "high"
    assert result["amplifier_pressure"] == 0.73

    assert result["intervention_type_counts"] == {
        "evidence_reconciliation": 0,
        "security_policy_review": 0,
        "access_policy_tuning": 0,
        "process_refactor": 1,
        "delivery_pipeline_review": 1,
        "operations_stabilization": 0,
    }

    assert [
        candidate["intervention_type"]
        for candidate in result["intervention_candidates"]
    ] == [
        "process_refactor",
        "delivery_pipeline_review",
    ]

    assert result["intervention_candidates"][0]["priority_score"] == 0.7825
    assert result["intervention_candidates"][1]["priority_score"] == 0.7055


def test_intervention_candidate_service_recommends_evidence_reconciliation():
    events = [
        make_event(
            event_id="evt-1",
            source_system="defender",
            event_type="security_resolution_mismatch",
            metadata={
                "status": "conflict",
                "severity": "high",
            },
        )
    ]

    result = InterventionCandidateService().recommend_events(events)

    assert result["dominant_intervention_type"] == "evidence_reconciliation"
    assert result["intervention_posture"] == "immediate_intervention"
    assert result["recommended_next_action"].startswith(
        "Reconcile conflicting evidence claims"
    )

    candidate = result["intervention_candidates"][0]

    assert candidate["source_debt_type"] == "evidence_debt"
    assert candidate["intervention_type"] == "evidence_reconciliation"
    assert candidate["priority_score"] == 0.8488
    assert candidate["priority_band"] == "high"


def test_intervention_candidate_service_ignores_unknown_signals():
    events = [
        make_event(
            event_id="evt-1",
            source_system="unknown-source",
            event_type="unmapped_event",
        )
    ]

    result = InterventionCandidateService().recommend_events(events)

    assert result["event_count"] == 1
    assert result["signal_count"] == 1
    assert result["friction_signal_count"] == 0
    assert result["debt_indicator_count"] == 0
    assert result["intervention_candidate_count"] == 0
    assert result["dominant_intervention_type"] == "none"
    assert result["intervention_posture"] == "none"
    assert result["recommended_next_action"] == "none"
    assert result["intervention_candidates"] == []


def test_intervention_candidate_service_uses_amplifier_pressure_for_priority():
    events = [
        make_event(
            event_id="evt-1",
            source_system="okta",
            event_type="login_failed",
            metadata={
                "outcome": "failed",
            },
        ),
        make_event(
            event_id="evt-2",
            source_system="defender",
            event_type="unauthorized_api_call",
            metadata={
                "severity": "high",
                "status": "active",
            },
        ),
    ]

    result = InterventionCandidateService().recommend_events(events)

    assert result["amplifier_pressure"] == 0.91
    assert result["intervention_posture"] == "immediate_intervention"

    assert [
        candidate["intervention_type"]
        for candidate in result["intervention_candidates"]
    ] == [
        "security_policy_review",
        "access_policy_tuning",
    ]

    assert result["intervention_candidates"][0]["priority_score"] == 0.8734
    assert result["intervention_candidates"][1]["priority_score"] == 0.8179


def test_intervention_candidate_service_dominant_intervention_uses_priority_on_tie():
    counts = {
        "evidence_reconciliation": 0,
        "security_policy_review": 1,
        "access_policy_tuning": 1,
        "process_refactor": 1,
        "delivery_pipeline_review": 0,
        "operations_stabilization": 0,
    }

    result = InterventionCandidateService().get_dominant_intervention_type(
        counts
    )

    assert result == "security_policy_review"


def test_intervention_candidate_service_calculates_priority_safely():
    service = InterventionCandidateService()

    assert service.calculate_priority_score(
        base_impact=0.85,
        debt_score=0.8635,
        intervention_urgency="immediate",
        amplifier_pressure=0.0,
    ) == 0.8279

    assert service.calculate_priority_score(
        base_impact=0.85,
        debt_score="unknown",
        intervention_urgency="near_term",
        amplifier_pressure="unknown",
    ) == 0.4575