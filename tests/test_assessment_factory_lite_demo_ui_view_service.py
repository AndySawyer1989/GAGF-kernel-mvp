from backend.app.gagf.assessment_factory_lite_demo_ui_view_service import (
    AssessmentFactoryLiteDemoUIViewService,
)


def service():
    return AssessmentFactoryLiteDemoUIViewService()


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
    ]


def test_assessment_factory_lite_demo_ui_view_builds_contract():
    result = service().build_view(rows=rows())

    assert result["status"] == "ok"
    assert result["view_type"] == "assessment_factory_lite_demo_ui_view"
    assert result["package_name"] == "Assessment Factory Lite Demo Package"
    assert result["release"] == "assessment-factory-lite-demo-package"
    assert result["version"] == "1.1.0"
    assert result["recommended_action"] == (
        "render_assessment_factory_lite_demo_view"
    )


def test_assessment_factory_lite_demo_ui_view_names_sections():
    result = service().build_view(rows=rows())

    assert result["ui_sections"] == [
        "demo_readiness",
        "sample_data_boundary",
        "dataset_contract",
        "dataset_validation",
        "governance_drag_summary",
        "top_friction_points",
        "recommended_intervention",
        "export_summary_preview",
        "next_steps",
        "compliance_disclaimer",
    ]


def test_assessment_factory_lite_demo_ui_view_builds_cards():
    result = service().build_view(rows=rows())
    cards = {card["card_id"]: card for card in result["cards"]}

    assert set(cards) == {
        "demo_readiness_card",
        "sample_data_boundary_card",
        "dataset_contract_card",
        "dataset_validation_card",
        "governance_drag_summary_card",
        "top_friction_points_card",
        "recommended_intervention_card",
        "export_summary_preview_card",
    }
    assert cards["dataset_validation_card"]["status"] == "passed"
    assert cards["top_friction_points_card"]["primary_value"] == (
        "approval_delay"
    )
    assert cards["recommended_intervention_card"]["primary_value"] == (
        "streamline_approval_path"
    )


def test_assessment_factory_lite_demo_ui_view_preserves_data_boundary():
    result = service().build_view(rows=rows())

    assert result["data_boundary"] == {
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


def test_assessment_factory_lite_demo_ui_view_preserves_source_payloads():
    result = service().build_view(rows=rows())

    assert set(result["source_payloads"]) == {
        "profile",
        "dataset_contract",
        "diagnostics_result",
        "export_summary",
    }
    assert result["source_payloads"]["dataset_contract"]["contract_type"] == (
        "assessment_factory_lite_demo_dataset_contract"
    )
    assert result["source_payloads"]["diagnostics_result"]["status"] == "ok"
    assert result["source_payloads"]["export_summary"]["status"] == "ok"


def test_assessment_factory_lite_demo_ui_view_rejects_invalid_rows():
    bad_rows = [
        {
            "event_id": "evt-003",
            "case_id": "case-002",
            "event_type": "real_customer_incident",
            "actor": "operator",
            "team": "security",
            "timestamp": "2026-01-01T15:00:00Z",
            "severity": "urgent",
            "description": "Invalid event.",
            "contains_real_customer_data": True,
        }
    ]

    result = service().build_view(rows=bad_rows)
    cards = {card["card_id"]: card for card in result["cards"]}

    assert cards["dataset_validation_card"]["status"] == "failed"
    assert result["operator_actions"] == [
        "repair_sample_csv_before_demo",
        "rerun_dataset_validation",
        "rerun_demo_diagnostics",
    ]


def test_assessment_factory_lite_demo_ui_view_includes_warnings():
    result = service().build_view(rows=rows())

    assert result["warnings"] == [
        {
            "warning_type": "demo_only_boundary",
            "severity": "high",
            "message": (
                "Use synthetic sample data only. Do not upload real "
                "customer, regulated, federal, secret, or live telemetry data."
            ),
        },
        {
            "warning_type": "no_certification_claims",
            "severity": "high",
            "message": (
                "This demo does not certify FedRAMP High, HIPAA compliance, "
                "SOC 2, production readiness, or customer deployment readiness."
            ),
        },
    ]





