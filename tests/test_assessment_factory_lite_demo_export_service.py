from backend.app.gagf.assessment_factory_lite_demo_diagnostics_service import (
    AssessmentFactoryLiteDemoDiagnosticsService,
)
from backend.app.gagf.assessment_factory_lite_demo_export_service import (
    AssessmentFactoryLiteDemoExportService,
)


def rows():
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


def service():
    return AssessmentFactoryLiteDemoExportService()


def diagnostics_result():
    return AssessmentFactoryLiteDemoDiagnosticsService().run_diagnostics(
        rows()
    )


def test_assessment_factory_lite_demo_export_builds_summary_from_diagnostics():
    result = service().build_export_summary(
        diagnostics_result=diagnostics_result()
    )

    assert result["status"] == "ok"
    assert result["export_type"] == (
        "assessment_factory_lite_demo_export_summary"
    )
    assert result["package_name"] == "Assessment Factory Lite Demo Package"
    assert result["source_diagnostic_type"] == (
        "assessment_factory_lite_demo_diagnostics"
    )
    assert result["row_count"] == 3
    assert result["report_title"] == "Assessment Factory Lite Demo Summary"
    assert result["recommended_action"] == "review_demo_export_summary"


def test_assessment_factory_lite_demo_export_can_run_from_rows():
    result = service().build_export_summary(rows=rows())

    assert result["status"] == "ok"
    assert result["row_count"] == 3
    assert result["export_metadata"]["validation_status"] == "passed"
    assert result["export_metadata"]["is_export_ready"] is True


def test_assessment_factory_lite_demo_export_builds_executive_summary_and_findings():
    result = service().build_export_summary(
        diagnostics_result=diagnostics_result()
    )

    assert "analyzed 3 synthetic workflow events" in result[
        "executive_summary"
    ]
    assert result["governance_drag_findings"] == {
        "available": True,
        "total_events": 3,
        "drag_event_count": 2,
        "critical_or_high_event_count": 2,
        "total_delay_minutes": 360,
        "governance_drag_score": 0.6833,
        "drag_level": "high",
    }


def test_assessment_factory_lite_demo_export_builds_top_constraints():
    result = service().build_export_summary(
        diagnostics_result=diagnostics_result()
    )

    assert result["top_constraints"] == [
        {
            "rank": 1,
            "constraint_label": "approval_delay",
            "event_count": 1,
            "case_count": 1,
            "total_delay_minutes": 240,
            "priority_score": 7.0,
        },
        {
            "rank": 2,
            "constraint_label": "work_blocked",
            "event_count": 1,
            "case_count": 1,
            "total_delay_minutes": 120,
            "priority_score": 5.0,
        },
        {
            "rank": 3,
            "constraint_label": "approval_required",
            "event_count": 1,
            "case_count": 1,
            "total_delay_minutes": 0,
            "priority_score": 1.0,
        },
    ]


def test_assessment_factory_lite_demo_export_preserves_boundary_and_disclaimer():
    result = service().build_export_summary(
        diagnostics_result=diagnostics_result()
    )

    assert result["sample_data_boundary"] == {
        "boundary_type": "demo_only_sample_data",
        "allowed_data": [
            "sample_csv",
            "synthetic_workflow_events",
            "mock_approval_events",
            "mock_delay_events",
        ],
        "prohibited_data": [
            "real_customer_data",
            "regulated_data",
            "federal_data",
            "production_customer_data",
            "customer_secrets",
            "live_security_telemetry",
        ],
        "certification_claims_allowed": False,
    }
    assert "synthetic sample data" in result["compliance_disclaimer"]
    assert "does not certify FedRAMP High" in result[
        "compliance_disclaimer"
    ]


def test_assessment_factory_lite_demo_export_builds_intervention_and_next_steps():
    result = service().build_export_summary(
        diagnostics_result=diagnostics_result()
    )

    assert result["recommended_intervention"] == {
        "intervention_type": "streamline_approval_path",
        "priority": "high",
        "target_friction_label": "approval_delay",
        "reason": "approval_friction_detected",
    }
    assert result["next_steps"] == [
        "review_governance_drag_summary",
        "review_top_constraints",
        "review_recommended_intervention",
        "prepare_buyer_demo_walkthrough",
    ]


def test_assessment_factory_lite_demo_export_rejects_invalid_diagnostics():
    bad_rows = [
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

    diagnostics = AssessmentFactoryLiteDemoDiagnosticsService().run_diagnostics(
        bad_rows
    )
    result = service().build_export_summary(diagnostics_result=diagnostics)

    assert result["status"] == "rejected"
    assert result["governance_drag_findings"] == {
        "available": False,
        "reason": "dataset_validation_failed",
    }
    assert result["recommended_action"] == "repair_sample_csv_before_demo"
    assert result["export_metadata"] == {
        "is_export_ready": False,
        "source_status": "rejected",
        "validation_status": "failed",
        "demo_only": True,
    }