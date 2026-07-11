from backend.app.gagf.governance_diagnostic_chain_service import (
    GovernanceDiagnosticChainService,
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


def test_governance_diagnostic_chain_service_returns_empty_chain():
    result = GovernanceDiagnosticChainService().diagnose_events([])

    assert result["status"] == "ok"
    assert result["event_count"] == 0
    assert result["chain_stage_count"] == 5
    assert result["chain_posture"] == "none"
    assert result["recommended_next_action"] == "none"

    assert result["chain_summary"] == {
        "dominant_signal": "none",
        "governance_posture": "none",
        "correlation_posture": "none",
        "dominant_friction_type": "none",
        "friction_posture": "none",
        "dominant_debt_type": "none",
        "governance_debt_score": 0.0,
        "governance_debt_band": "none",
        "debt_posture": "none",
        "intervention_urgency": "none",
        "dominant_intervention_type": "none",
        "intervention_posture": "none",
        "signal_count": 0,
        "correlation_count": 0,
        "friction_signal_count": 0,
        "debt_indicator_count": 0,
        "intervention_candidate_count": 0,
    }


def test_governance_diagnostic_chain_service_diagnoses_security_chain():
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

    result = GovernanceDiagnosticChainService().diagnose_events(events)

    assert result["status"] == "ok"
    assert result["event_count"] == 1
    assert result["chain_stage_count"] == 5
    assert result["chain_posture"] == "critical_governance_diagnosis"
    assert result["recommended_next_action"].startswith("Review security policy")

    summary = result["chain_summary"]

    assert summary["dominant_signal"] == "security_risk"
    assert summary["governance_posture"] == "urgent_attention"
    assert summary["correlation_posture"] == "none"
    assert summary["dominant_friction_type"] == "security_pressure"
    assert summary["friction_posture"] == "severe_friction"
    assert summary["dominant_debt_type"] == "security_governance_debt"
    assert summary["governance_debt_score"] == 0.8635
    assert summary["governance_debt_band"] == "critical"
    assert summary["debt_posture"] == "critical_debt"
    assert summary["intervention_urgency"] == "immediate"
    assert summary["dominant_intervention_type"] == "security_policy_review"
    assert summary["intervention_posture"] == "immediate_intervention"
    assert summary["signal_count"] == 1
    assert summary["correlation_count"] == 0
    assert summary["friction_signal_count"] == 1
    assert summary["debt_indicator_count"] == 1
    assert summary["intervention_candidate_count"] == 1


def test_governance_diagnostic_chain_service_diagnoses_process_delivery_chain():
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

    result = GovernanceDiagnosticChainService().diagnose_events(events)

    assert result["chain_posture"] == "high_governance_diagnosis"
    assert result["recommended_next_action"].startswith("Refactor approval")

    summary = result["chain_summary"]

    assert summary["dominant_signal"] == "workflow_friction"
    assert summary["correlation_posture"] == "moderate_correlation"
    assert summary["dominant_friction_type"] == "process_friction"
    assert summary["friction_posture"] == "high_friction"
    assert summary["dominant_debt_type"] == "process_governance_debt"
    assert summary["governance_debt_score"] == 0.727
    assert summary["governance_debt_band"] == "high"
    assert summary["debt_posture"] == "high_debt"
    assert summary["intervention_urgency"] == "near_term"
    assert summary["dominant_intervention_type"] == "process_refactor"
    assert summary["intervention_posture"] == "prioritize_intervention"
    assert summary["signal_count"] == 2
    assert summary["correlation_count"] == 1
    assert summary["friction_signal_count"] == 2
    assert summary["debt_indicator_count"] == 2
    assert summary["intervention_candidate_count"] == 2


def test_governance_diagnostic_chain_service_diagnoses_evidence_conflict_chain():
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

    result = GovernanceDiagnosticChainService().diagnose_events(events)

    assert result["chain_posture"] == "critical_governance_diagnosis"
    assert result["recommended_next_action"].startswith(
        "Reconcile conflicting evidence claims"
    )

    summary = result["chain_summary"]

    assert summary["dominant_signal"] == "evidence_conflict"
    assert summary["governance_posture"] == "reconcile_evidence"
    assert summary["dominant_friction_type"] == "evidence_friction"
    assert summary["dominant_debt_type"] == "evidence_debt"
    assert summary["dominant_intervention_type"] == "evidence_reconciliation"


def test_governance_diagnostic_chain_service_handles_unknown_signal_chain():
    events = [
        make_event(
            event_id="evt-1",
            source_system="unknown-source",
            event_type="unmapped_event",
            metadata={
                "note": "no known governance mapping",
            },
        )
    ]

    result = GovernanceDiagnosticChainService().diagnose_events(events)

    assert result["chain_posture"] == "low_governance_diagnosis"
    assert result["recommended_next_action"] == "none"

    summary = result["chain_summary"]

    assert summary["dominant_signal"] == "governance_unknown"
    assert summary["governance_posture"] == "classification_gap"
    assert summary["correlation_posture"] == "none"
    assert summary["dominant_friction_type"] == "none"
    assert summary["friction_posture"] == "none"
    assert summary["dominant_debt_type"] == "none"
    assert summary["governance_debt_score"] == 0.0
    assert summary["governance_debt_band"] == "none"
    assert summary["debt_posture"] == "none"
    assert summary["intervention_urgency"] == "none"
    assert summary["dominant_intervention_type"] == "none"
    assert summary["intervention_posture"] == "none"
    assert summary["signal_count"] == 1
    assert summary["correlation_count"] == 0
    assert summary["friction_signal_count"] == 0
    assert summary["debt_indicator_count"] == 0
    assert summary["intervention_candidate_count"] == 0


def test_governance_diagnostic_chain_service_exposes_full_stage_payloads():
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

    result = GovernanceDiagnosticChainService().diagnose_events(events)

    assert "signal_summary" in result
    assert "correlation_result" in result
    assert "friction_result" in result
    assert "debt_result" in result
    assert "intervention_result" in result

    assert result["signal_summary"]["dominant_signal"] == "security_risk"
    assert result["friction_result"]["dominant_friction_type"] == (
        "security_pressure"
    )
    assert result["debt_result"]["dominant_debt_type"] == (
        "security_governance_debt"
    )
    assert result["intervention_result"]["dominant_intervention_type"] == (
        "security_policy_review"
    )


def test_governance_diagnostic_chain_service_chain_posture_priority():
    service = GovernanceDiagnosticChainService()

    assert service.get_chain_posture(
        {
            "signal_count": 1,
            "debt_posture": "critical_debt",
            "intervention_posture": "prioritize_intervention",
            "governance_debt_band": "high",
            "friction_posture": "moderate_friction",
            "friction_signal_count": 1,
            "debt_indicator_count": 1,
            "intervention_candidate_count": 1,
        }
    ) == "critical_governance_diagnosis"

    assert service.get_chain_posture(
        {
            "signal_count": 1,
            "debt_posture": "high_debt",
            "intervention_posture": "monitor_intervention",
            "governance_debt_band": "high",
            "friction_posture": "high_friction",
            "friction_signal_count": 1,
            "debt_indicator_count": 1,
            "intervention_candidate_count": 1,
        }
    ) == "high_governance_diagnosis"

    assert service.get_chain_posture(
        {
            "signal_count": 1,
            "debt_posture": "none",
            "intervention_posture": "none",
            "governance_debt_band": "none",
            "friction_posture": "none",
            "friction_signal_count": 0,
            "debt_indicator_count": 0,
            "intervention_candidate_count": 0,
        }
    ) == "low_governance_diagnosis"
