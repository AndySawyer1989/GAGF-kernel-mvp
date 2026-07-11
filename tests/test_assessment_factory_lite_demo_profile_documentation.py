from pathlib import Path


DOC_PATH = Path("docs/ASSESSMENT_FACTORY_LITE_DEMO_PROFILE.md")


def test_assessment_factory_lite_demo_profile_document_exists():
    assert DOC_PATH.exists()


def test_assessment_factory_lite_demo_profile_document_names_service_and_endpoint():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "AssessmentFactoryLiteDemoProfileService" in content
    assert "POST /products/assessment-factory-lite/demo-profile" in content
    assert "assessment_factory_lite_demo_profile" in content


def test_assessment_factory_lite_demo_profile_document_names_input_modes():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "product_profiles" in content
    assert "portfolio_dashboard" in content
    assert "packaging_recommendation" in content
    assert "packaging_dashboard" in content
    assert "checkpoint" in content
    assert "Mode 1" in content
    assert "Mode 2" in content
    assert "Mode 3" in content
    assert "Mode 4" in content
    assert "Mode 5" in content


def test_assessment_factory_lite_demo_profile_document_names_output_contract():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "demo_readiness" in content
    assert "demo_boundary" in content
    assert "demo_inputs" in content
    assert "demo_workflow" in content
    assert "dashboard_sections" in content
    assert "report_sections" in content
    assert "success_criteria" in content
    assert "excluded_scope" in content
    assert "recommended_action" in content


def test_assessment_factory_lite_demo_profile_document_names_demo_readiness():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "ready_for_demo_package" in content
    assert "fast_demo_candidate_available" in content
    assert "requires_customer_data" in content
    assert "requires_regulated_data" in content
    assert "requires_federal_data" in content
    assert "requires_production_access" in content


def test_assessment_factory_lite_demo_profile_document_names_demo_boundary():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "demo_only_sample_data" in content
    assert "sample_csv" in content
    assert "synthetic_workflow_events" in content
    assert "mock_approval_events" in content
    assert "mock_delay_events" in content
    assert "regulated_data" in content
    assert "federal_data" in content
    assert "production_customer_data" in content
    assert "live_security_telemetry" in content


def test_assessment_factory_lite_demo_profile_document_names_workflow_and_sections():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "load_demo_profile" in content
    assert "upload_sample_csv" in content
    assert "run_governance_diagnostics" in content
    assert "review_governance_drag_summary" in content
    assert "display_recommended_intervention" in content
    assert "demo_readiness_card" in content
    assert "sample_data_boundary_card" in content
    assert "executive_summary" in content
    assert "compliance_disclaimer" in content


def test_assessment_factory_lite_demo_profile_document_preserves_boundaries():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert (
        "The Assessment Factory Lite Demo Profile does not certify products "
        "as FedRAMP High, HIPAA compliant, or SOC 2 audited."
    ) in content
    assert (
        "The deterministic GAGF Kernel remains the authoritative decision "
        "and verification layer."
    ) in content