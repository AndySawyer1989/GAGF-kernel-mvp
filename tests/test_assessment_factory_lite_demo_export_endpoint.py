from fastapi.testclient import TestClient

from backend.app.gagf.assessment_factory_lite_demo_diagnostics_service import (
    AssessmentFactoryLiteDemoDiagnosticsService,
)
from backend.app.main import app


client = TestClient(app)


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


def diagnostics_result():
    return AssessmentFactoryLiteDemoDiagnosticsService().run_diagnostics(
        rows()
    )


def test_assessment_factory_lite_demo_export_endpoint_builds_from_rows():
    response = client.post(
        "/products/assessment-factory-lite/demo-export/summary",
        json={"rows": rows()},
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["status"] == "ok"
    assert payload["export_type"] == (
        "assessment_factory_lite_demo_export_summary"
    )
    assert payload["package_name"] == "Assessment Factory Lite Demo Package"
    assert payload["source_diagnostic_type"] == (
        "assessment_factory_lite_demo_diagnostics"
    )
    assert payload["row_count"] == 3
    assert payload["report_title"] == "Assessment Factory Lite Demo Summary"
    assert payload["recommended_action"] == "review_demo_export_summary"


def test_assessment_factory_lite_demo_export_endpoint_builds_from_diagnostics_result():
    response = client.post(
        "/products/assessment-factory-lite/demo-export/summary",
        json={"diagnostics_result": diagnostics_result()},
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["status"] == "ok"
    assert payload["row_count"] == 3
    assert payload["export_metadata"]["validation_status"] == "passed"
    assert payload["export_metadata"]["is_export_ready"] is True


def test_assessment_factory_lite_demo_export_endpoint_returns_findings():
    response = client.post(
        "/products/assessment-factory-lite/demo-export/summary",
        json={"rows": rows()},
    )

    payload = response.json()

    assert "analyzed 3 synthetic workflow events" in payload[
        "executive_summary"
    ]
    assert payload["governance_drag_findings"] == {
        "available": True,
        "total_events": 3,
        "drag_event_count": 2,
        "critical_or_high_event_count": 2,
        "total_delay_minutes": 360,
        "governance_drag_score": 0.6833,
        "drag_level": "high",
    }


def test_assessment_factory_lite_demo_export_endpoint_returns_top_constraints():
    response = client.post(
        "/products/assessment-factory-lite/demo-export/summary",
        json={"rows": rows()},
    )

    payload = response.json()

    assert payload["top_constraints"] == [
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


def test_assessment_factory_lite_demo_export_endpoint_returns_intervention_and_next_steps():
    response = client.post(
        "/products/assessment-factory-lite/demo-export/summary",
        json={"rows": rows()},
    )

    payload = response.json()

    assert payload["recommended_intervention"] == {
        "intervention_type": "streamline_approval_path",
        "priority": "high",
        "target_friction_label": "approval_delay",
        "reason": "approval_friction_detected",
    }
    assert payload["next_steps"] == [
        "review_governance_drag_summary",
        "review_top_constraints",
        "review_recommended_intervention",
        "prepare_buyer_demo_walkthrough",
    ]


def test_assessment_factory_lite_demo_export_endpoint_preserves_demo_boundary():
    response = client.post(
        "/products/assessment-factory-lite/demo-export/summary",
        json={"rows": rows()},
    )

    payload = response.json()

    assert payload["sample_data_boundary"] == {
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
    assert "synthetic sample data" in payload["compliance_disclaimer"]
    assert "does not certify FedRAMP High" in payload[
        "compliance_disclaimer"
    ]


def test_assessment_factory_lite_demo_export_endpoint_rejects_invalid_rows():
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

    response = client.post(
        "/products/assessment-factory-lite/demo-export/summary",
        json={"rows": bad_rows},
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["status"] == "rejected"
    assert payload["governance_drag_findings"] == {
        "available": False,
        "reason": "dataset_validation_failed",
    }
    assert payload["recommended_action"] == "repair_sample_csv_before_demo"
    assert payload["export_metadata"] == {
        "is_export_ready": False,
        "source_status": "rejected",
        "validation_status": "failed",
        "demo_only": True,
    }


def test_assessment_factory_lite_demo_export_endpoint_handles_empty_payload():
    response = client.post(
        "/products/assessment-factory-lite/demo-export/summary",
        json={},
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["status"] == "ok"
    assert payload["row_count"] == 0
    assert payload["recommended_intervention"]["intervention_type"] == (
        "add_demo_rows"
    )
    assert payload["next_steps"] == [
        "add_synthetic_sample_rows",
        "rerun_demo_diagnostics",
        "generate_demo_export_summary",
    ]


def test_assessment_factory_lite_demo_export_summary_route_exists():
    actual_routes = {route.path for route in app.routes}

    assert (
        "/products/assessment-factory-lite/demo-export/summary"
        in actual_routes
    )


def test_assessment_factory_lite_demo_export_endpoint_preserves_release_marker():
    response = client.get("/version")

    assert response.status_code == 200
    assert response.json() == {
        "version": "1.5.0",
        "release": "assessment-factory-lite-demo-usability",
        "sprint": "4.4",
        "status": "complete",
    }





