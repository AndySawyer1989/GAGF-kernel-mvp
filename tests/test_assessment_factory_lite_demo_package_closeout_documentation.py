from pathlib import Path


DOC_PATH = Path("docs/ASSESSMENT_FACTORY_LITE_DEMO_PACKAGE_CLOSEOUT.md")


def test_assessment_factory_lite_demo_package_closeout_document_exists():
    assert DOC_PATH.exists()


def test_assessment_factory_lite_demo_package_closeout_document_names_release_marker():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "Release 1.1.0" in content
    assert "assessment-factory-lite-demo-package" in content
    assert "Sprint" in content
    assert "4.0" in content
    assert "complete" in content


def test_assessment_factory_lite_demo_package_closeout_document_names_capability_chain():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "Product Packaging Checkpoint" in content
    assert "Assessment Factory Lite Demo Profile" in content
    assert "Dataset Contract" in content
    assert "Dataset Validation API" in content
    assert "Demo Diagnostics Service" in content
    assert "Demo Diagnostics API" in content
    assert "Demo Export Summary Service" in content
    assert "Demo Export Summary API" in content
    assert "Release Marker" in content


def test_assessment_factory_lite_demo_package_closeout_document_names_services():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "AssessmentFactoryLiteDemoProfileService" in content
    assert "AssessmentFactoryLiteDatasetContractService" in content
    assert "AssessmentFactoryLiteDemoDiagnosticsService" in content
    assert "AssessmentFactoryLiteDemoExportService" in content


def test_assessment_factory_lite_demo_package_closeout_document_names_endpoint_inventory():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "POST /products/assessment-factory-lite/demo-profile" in content
    assert "GET /products/assessment-factory-lite/dataset-contract" in content
    assert (
        "POST /products/assessment-factory-lite/dataset-contract/validate"
        in content
    )
    assert (
        "POST /products/assessment-factory-lite/demo-diagnostics/run"
        in content
    )
    assert (
        "POST /products/assessment-factory-lite/demo-export/summary"
        in content
    )


def test_assessment_factory_lite_demo_package_closeout_document_names_buyer_demo_flow():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "Load Assessment Factory Lite demo profile" in content
    assert "Fetch dataset contract" in content
    assert "Validate synthetic sample rows" in content
    assert "Run demo diagnostics" in content
    assert "Review governance drag summary" in content
    assert "Review top friction points" in content
    assert "Review recommended intervention" in content
    assert "Generate export summary" in content


def test_assessment_factory_lite_demo_package_closeout_document_names_demo_boundary():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "demo-only sample data" in content
    assert "sample_csv" in content
    assert "synthetic_workflow_events" in content
    assert "mock_approval_events" in content
    assert "mock_delay_events" in content
    assert "real_customer_data" in content
    assert "regulated_data" in content
    assert "federal_data" in content
    assert "production_customer_data" in content
    assert "live_security_telemetry" in content
    assert "certification_claims_allowed" in content


def test_assessment_factory_lite_demo_package_closeout_document_names_next_track():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "Operator Workstation Demo UI Path" in content
    assert "US-164 Assessment Factory Lite Demo UI View Contract" in content
    assert "US-165 Assessment Factory Lite Demo UI Summary Endpoint" in content
    assert "US-166 Assessment Factory Lite Demo UI Documentation" in content
    assert "US-167 Assessment Factory Lite Demo UI Release Marker" in content


def test_assessment_factory_lite_demo_package_closeout_document_preserves_boundaries():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert (
        "The Assessment Factory Lite Demo Package does not certify products "
        "as FedRAMP High, HIPAA compliant, or SOC 2 audited."
    ) in content
    assert (
        "The deterministic GAGF Kernel remains the authoritative decision "
        "and verification layer."
    ) in content
