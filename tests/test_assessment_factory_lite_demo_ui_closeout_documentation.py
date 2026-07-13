from pathlib import Path


DOC_PATH = Path("docs/ASSESSMENT_FACTORY_LITE_DEMO_UI_CLOSEOUT.md")


def test_assessment_factory_lite_demo_ui_closeout_document_exists():
    assert DOC_PATH.exists()


def test_assessment_factory_lite_demo_ui_closeout_document_names_release_marker():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "Release 1.2.0" in content
    assert "assessment-factory-lite-demo-ui" in content
    assert "Sprint" in content
    assert "4.1" in content
    assert "complete" in content


def test_assessment_factory_lite_demo_ui_closeout_document_names_capability_chain():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "Assessment Factory Lite Demo Package" in content
    assert "Demo Profile" in content
    assert "Dataset Contract" in content
    assert "Dataset Validation API" in content
    assert "Demo Diagnostics API" in content
    assert "Demo Export Summary API" in content
    assert "Demo UI View Service" in content
    assert "Demo UI View API" in content
    assert "Demo UI Release Marker" in content


def test_assessment_factory_lite_demo_ui_closeout_document_names_service_and_endpoint():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "AssessmentFactoryLiteDemoUIViewService" in content
    assert "POST /products/assessment-factory-lite/demo-ui/view" in content
    assert "assessment_factory_lite_demo_ui_view" in content


def test_assessment_factory_lite_demo_ui_closeout_document_names_ui_sections_and_cards():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "demo_readiness" in content
    assert "sample_data_boundary" in content
    assert "dataset_contract" in content
    assert "dataset_validation" in content
    assert "governance_drag_summary" in content
    assert "top_friction_points" in content
    assert "recommended_intervention" in content
    assert "export_summary_preview" in content
    assert "demo_readiness_card" in content
    assert "sample_data_boundary_card" in content
    assert "dataset_contract_card" in content
    assert "dataset_validation_card" in content
    assert "governance_drag_summary_card" in content
    assert "top_friction_points_card" in content
    assert "recommended_intervention_card" in content
    assert "export_summary_preview_card" in content


def test_assessment_factory_lite_demo_ui_closeout_document_names_operator_actions():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "review_demo_readiness" in content
    assert "review_sample_data_boundary" in content
    assert "review_governance_drag_summary" in content
    assert "review_top_friction_points" in content
    assert "review_recommended_intervention" in content
    assert "review_demo_export_summary" in content
    assert "repair_sample_csv_before_demo" in content
    assert "rerun_dataset_validation" in content
    assert "rerun_demo_diagnostics" in content
    assert "add_synthetic_sample_rows" in content


def test_assessment_factory_lite_demo_ui_closeout_document_names_warnings_and_boundary():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "demo_only_boundary" in content
    assert "no_certification_claims" in content
    assert "demo_only_sample_data" in content
    assert "sample_csv" in content
    assert "synthetic_workflow_events" in content
    assert "mock_approval_events" in content
    assert "mock_delay_events" in content
    assert "real_customer_data" in content
    assert "regulated_data" in content
    assert "federal_data" in content
    assert "live_security_telemetry" in content
    assert "certification_claims_allowed" in content


def test_assessment_factory_lite_demo_ui_closeout_document_names_next_track():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "Operator Workstation Demo Screen Implementation" in content
    assert "US-169 Assessment Factory Lite Demo UI HTML Screen" in content
    assert "US-170 Assessment Factory Lite Demo UI Sample Data Loader" in content
    assert "US-171 Assessment Factory Lite Demo UI Export Preview Panel" in content
    assert "US-172 Assessment Factory Lite Demo UI Documentation" in content
    assert "US-173 Assessment Factory Lite Demo UI Screen Release Marker" in content


def test_assessment_factory_lite_demo_ui_closeout_document_preserves_boundaries():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert (
        "The Assessment Factory Lite Demo UI path does not certify products "
        "as FedRAMP High, HIPAA compliant, or SOC 2 audited."
    ) in content
    assert (
        "The deterministic GAGF Kernel remains the authoritative decision "
        "and verification layer."
    ) in content

