from backend.app.gagf.assessment_factory_lite_demo_ui_html_service import (
    AssessmentFactoryLiteDemoUIHTMLService,
)


def service():
    return AssessmentFactoryLiteDemoUIHTMLService()


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


def test_assessment_factory_lite_demo_ui_html_screen_renders_contract():
    result = service().render_html(rows=rows())

    assert result["status"] == "ok"
    assert result["screen_type"] == (
        "assessment_factory_lite_demo_ui_html_screen"
    )
    assert result["package_name"] == "Assessment Factory Lite Demo Package"
    assert result["release"] == "assessment-factory-lite-demo-ui"
    assert result["version"] == "1.2.0"
    assert result["recommended_action"] == (
        "display_assessment_factory_lite_demo_screen"
    )


def test_assessment_factory_lite_demo_ui_html_screen_contains_document_shell():
    result = service().render_html(rows=rows())
    html = result["html"]

    assert "<!doctype html>" in html
    assert '<html lang="en">' in html
    assert "<title>Assessment Factory Lite Demo</title>" in html
    assert 'data-screen="assessment-factory-lite-demo-ui-html-screen"' in html
    assert "FIP/GAGF Operator Workstation" in html
    assert "Sample-data-only buyer demo path" in html


def test_assessment_factory_lite_demo_ui_html_screen_contains_cards():
    result = service().render_html(rows=rows())
    html = result["html"]

    assert 'data-card-id="demo_readiness_card"' in html
    assert 'data-card-id="sample_data_boundary_card"' in html
    assert 'data-card-id="dataset_contract_card"' in html
    assert 'data-card-id="dataset_validation_card"' in html
    assert 'data-card-id="governance_drag_summary_card"' in html
    assert 'data-card-id="top_friction_points_card"' in html
    assert 'data-card-id="recommended_intervention_card"' in html
    assert 'data-card-id="export_summary_preview_card"' in html


def test_assessment_factory_lite_demo_ui_html_screen_contains_warnings():
    result = service().render_html(rows=rows())
    html = result["html"]

    assert 'data-warning-type="demo_only_boundary"' in html
    assert 'data-warning-type="no_certification_claims"' in html
    assert "Use synthetic sample data only" in html
    assert "does not certify FedRAMP High" in html
    assert "HIPAA compliance" in html
    assert "SOC 2" in html


def test_assessment_factory_lite_demo_ui_html_screen_contains_export_preview():
    result = service().render_html(rows=rows())
    html = result["html"]

    assert "Buyer-Facing Export Preview" in html
    assert "Assessment Factory Lite analyzed 2 synthetic workflow events" in html
    assert "governance drag events" in html
    assert "synthetic sample data" in html
    assert "production readiness" in html


def test_assessment_factory_lite_demo_ui_html_screen_contains_operator_actions():
    result = service().render_html(rows=rows())
    html = result["html"]

    assert "Operator Actions" in html
    assert "review_demo_readiness" in html
    assert "review_sample_data_boundary" in html
    assert "review_governance_drag_summary" in html
    assert "review_top_friction_points" in html
    assert "review_recommended_intervention" in html
    assert "review_demo_export_summary" in html


def test_assessment_factory_lite_demo_ui_html_screen_preserves_ui_view():
    result = service().render_html(rows=rows())

    assert result["ui_view"]["view_type"] == "assessment_factory_lite_demo_ui_view"
    assert result["ui_view"]["recommended_action"] == (
        "render_assessment_factory_lite_demo_view"
    )
    assert result["ui_view"]["data_boundary"]["boundary_type"] == (
        "demo_only_sample_data"
    )

