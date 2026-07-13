from pathlib import Path


DOC_PATH = Path("docs/ASSESSMENT_FACTORY_LITE_DEMO_DIAGNOSTICS.md")


def test_assessment_factory_lite_demo_diagnostics_document_exists():
    assert DOC_PATH.exists()


def test_assessment_factory_lite_demo_diagnostics_document_names_service_and_endpoint():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "AssessmentFactoryLiteDemoDiagnosticsService" in content
    assert (
        "POST /products/assessment-factory-lite/demo-diagnostics/run"
        in content
    )
    assert "assessment_factory_lite_demo_diagnostics" in content


def test_assessment_factory_lite_demo_diagnostics_document_names_input_contract():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "event_id" in content
    assert "case_id" in content
    assert "event_type" in content
    assert "actor" in content
    assert "team" in content
    assert "timestamp" in content
    assert "severity" in content
    assert "description" in content
    assert "duration_minutes" in content
    assert "constraint_label" in content


def test_assessment_factory_lite_demo_diagnostics_document_names_output_contract():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "status" in content
    assert "diagnostic_type" in content
    assert "row_count" in content
    assert "validation" in content
    assert "governance_drag_summary" in content
    assert "top_friction_points" in content
    assert "recommended_intervention" in content
    assert "export_ready_summary" in content
    assert "operator_message" in content
    assert "recommended_action" in content


def test_assessment_factory_lite_demo_diagnostics_document_names_drag_summary():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "total_events" in content
    assert "drag_event_count" in content
    assert "critical_or_high_event_count" in content
    assert "total_delay_minutes" in content
    assert "event_type_counts" in content
    assert "severity_counts" in content
    assert "governance_drag_score" in content
    assert "drag_level" in content


def test_assessment_factory_lite_demo_diagnostics_document_names_friction_and_interventions():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "friction_label" in content
    assert "priority_score" in content
    assert "streamline_approval_path" in content
    assert "clarify_ownership_and_handoffs" in content
    assert "stabilize_operational_path" in content
    assert "review_top_constraint" in content
    assert "add_demo_rows" in content
    assert "repair_sample_csv_before_demo" in content


def test_assessment_factory_lite_demo_diagnostics_document_names_export_summary():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "is_export_ready" in content
    assert "report_sections" in content
    assert "executive_summary" in content
    assert "sample_data_boundary" in content
    assert "governance_drag_findings" in content
    assert "top_constraints" in content
    assert "next_steps" in content
    assert "compliance_disclaimer" in content


def test_assessment_factory_lite_demo_diagnostics_document_preserves_boundaries():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert (
        "The Assessment Factory Lite Demo Diagnostics Runner does not "
        "certify products as FedRAMP High, HIPAA compliant, or SOC 2 audited."
    ) in content
    assert (
        "The deterministic GAGF Kernel remains the authoritative decision "
        "and verification layer."
    ) in content

