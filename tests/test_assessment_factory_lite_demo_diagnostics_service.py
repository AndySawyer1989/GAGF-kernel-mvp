from backend.app.gagf.assessment_factory_lite_demo_diagnostics_service import (
    AssessmentFactoryLiteDemoDiagnosticsService,
)


def service():
    return AssessmentFactoryLiteDemoDiagnosticsService()


def valid_rows():
    return [
        {
            "event_id": "evt-001",
            "case_id": "case-001",
            "event_type": "approval_requested",
            "actor": "requester",
            "team": "operations",
            "timestamp": "2026-01-01T09:00:00Z",
            "severity": "medium",
            "description": "Synthetic approval request submitted.",
            "constraint_label": "approval_required",
            "duration_minutes": 0,
        },
        {
            "event_id": "evt-002",
            "case_id": "case-001",
            "event_type": "approval_delayed",
            "actor": "approver",
            "team": "operations",
            "timestamp": "2026-01-01T13:00:00Z",
            "severity": "high",
            "description": "Synthetic approval delayed.",
            "constraint_label": "approval_delay",
            "duration_minutes": 240,
        },
        {
            "event_id": "evt-003",
            "case_id": "case-002",
            "event_type": "work_blocked",
            "actor": "operator",
            "team": "engineering",
            "timestamp": "2026-01-01T14:00:00Z",
            "severity": "critical",
            "description": "Synthetic work blocked.",
            "constraint_label": "work_blocked",
            "duration_minutes": 120,
        },
    ]


def test_assessment_factory_lite_demo_diagnostics_runs_for_valid_rows():
    result = service().run_diagnostics(valid_rows())

    assert result["status"] == "ok"
    assert result["diagnostic_type"] == (
        "assessment_factory_lite_demo_diagnostics"
    )
    assert result["row_count"] == 3
    assert result["validation"]["is_valid"] is True
    assert result["recommended_action"] == "export_demo_summary"


def test_assessment_factory_lite_demo_diagnostics_builds_drag_summary():
    result = service().run_diagnostics(valid_rows())

    assert result["governance_drag_summary"] == {
        "total_events": 3,
        "drag_event_count": 2,
        "critical_or_high_event_count": 2,
        "total_delay_minutes": 360,
        "event_type_counts": {
            "approval_requested": 1,
            "approval_delayed": 1,
            "work_blocked": 1,
        },
        "severity_counts": {
            "medium": 1,
            "high": 1,
            "critical": 1,
        },
        "governance_drag_score": 0.6833,
        "drag_level": "high",
    }


def test_assessment_factory_lite_demo_diagnostics_identifies_top_friction_points():
    result = service().run_diagnostics(valid_rows())

    assert result["top_friction_points"] == [
        {
            "friction_label": "approval_delay",
            "event_count": 1,
            "case_count": 1,
            "total_delay_minutes": 240,
            "high_or_critical_count": 1,
            "priority_score": 7.0,
        },
        {
            "friction_label": "work_blocked",
            "event_count": 1,
            "case_count": 1,
            "total_delay_minutes": 120,
            "high_or_critical_count": 1,
            "priority_score": 5.0,
        },
        {
            "friction_label": "approval_required",
            "event_count": 1,
            "case_count": 1,
            "total_delay_minutes": 0,
            "high_or_critical_count": 0,
            "priority_score": 1.0,
        },
    ]


def test_assessment_factory_lite_demo_diagnostics_recommends_intervention():
    result = service().run_diagnostics(valid_rows())

    assert result["recommended_intervention"] == {
        "intervention_type": "streamline_approval_path",
        "priority": "high",
        "target_friction_label": "approval_delay",
        "reason": "approval_friction_detected",
    }


def test_assessment_factory_lite_demo_diagnostics_builds_export_ready_summary():
    result = service().run_diagnostics(valid_rows())

    assert result["export_ready_summary"]["is_export_ready"] is True
    assert result["export_ready_summary"]["top_friction_label"] == (
        "approval_delay"
    )
    assert result["export_ready_summary"][
        "recommended_intervention_type"
    ] == "streamline_approval_path"
    assert "synthetic sample data" in result["export_ready_summary"][
        "compliance_disclaimer"
    ]


def test_assessment_factory_lite_demo_diagnostics_rejects_invalid_rows():
    rows = [
        {
            "event_id": "evt-004",
            "case_id": "case-003",
            "event_type": "real_customer_incident",
            "actor": "operator",
            "team": "security",
            "timestamp": "2026-01-01T15:00:00Z",
            "severity": "urgent",
            "description": "Invalid event.",
            "contains_real_customer_data": True,
        }
    ]

    result = service().run_diagnostics(rows)

    assert result["status"] == "rejected"
    assert result["validation"]["is_valid"] is False
    assert result["recommended_intervention"] == {
        "intervention_type": "repair_sample_csv_before_demo",
        "priority": "required",
        "reason": "dataset_validation_failed",
    }
    assert result["export_ready_summary"] == {
        "is_export_ready": False,
        "reason": "dataset_validation_failed",
    }
    assert result["recommended_action"] == "repair_sample_csv_before_demo"


def test_assessment_factory_lite_demo_diagnostics_handles_empty_rows():
    result = service().run_diagnostics([])

    assert result["status"] == "ok"
    assert result["row_count"] == 0
    assert result["governance_drag_summary"]["governance_drag_score"] == 0.0
    assert result["recommended_intervention"] == {
        "intervention_type": "add_demo_rows",
        "priority": "required",
        "reason": "no_demo_rows_available",
    }
    assert result["export_ready_summary"]["is_export_ready"] is True





