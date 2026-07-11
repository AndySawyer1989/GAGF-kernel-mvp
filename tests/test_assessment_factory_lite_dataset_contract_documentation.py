from pathlib import Path


DOC_PATH = Path("docs/ASSESSMENT_FACTORY_LITE_DATASET_CONTRACT.md")


def test_assessment_factory_lite_dataset_contract_document_exists():
    assert DOC_PATH.exists()


def test_assessment_factory_lite_dataset_contract_document_names_service_and_endpoints():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "AssessmentFactoryLiteDatasetContractService" in content
    assert "GET /products/assessment-factory-lite/dataset-contract" in content
    assert (
        "POST /products/assessment-factory-lite/dataset-contract/validate"
        in content
    )
    assert "assessment_factory_lite_demo_dataset_contract" in content


def test_assessment_factory_lite_dataset_contract_document_names_required_fields():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "event_id" in content
    assert "case_id" in content
    assert "event_type" in content
    assert "actor" in content
    assert "team" in content
    assert "timestamp" in content
    assert "severity" in content
    assert "description" in content


def test_assessment_factory_lite_dataset_contract_document_names_allowed_values():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "approval_requested" in content
    assert "approval_delayed" in content
    assert "approval_granted" in content
    assert "work_blocked" in content
    assert "handoff_delayed" in content
    assert "ownership_gap" in content
    assert "low" in content
    assert "medium" in content
    assert "high" in content
    assert "critical" in content


def test_assessment_factory_lite_dataset_contract_document_names_validation_rules():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "all_required_fields_must_be_present" in content
    assert "event_type_must_be_allowed" in content
    assert "severity_must_be_allowed" in content
    assert "dataset_must_be_demo_only" in content
    assert "real_customer_data_is_not_allowed" in content
    assert "regulated_data_is_not_allowed" in content
    assert "federal_data_is_not_allowed" in content
    assert "certification_claims_are_not_allowed" in content


def test_assessment_factory_lite_dataset_contract_document_names_failure_modes():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "missing_required_fields" in content
    assert "invalid_event_type" in content
    assert "invalid_severity" in content
    assert "real_customer_data_not_allowed" in content
    assert "regulated_data_not_allowed" in content
    assert "federal_data_not_allowed" in content
    assert "repair_sample_csv_before_demo" in content
    assert "run_demo_diagnostics" in content


def test_assessment_factory_lite_dataset_contract_document_names_demo_boundary():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "demo_only_sample_data" in content
    assert "sample_csv" in content
    assert "synthetic_workflow_events" in content
    assert "mock_approval_events" in content
    assert "mock_delay_events" in content
    assert "production_customer_data" in content
    assert "live_security_telemetry" in content
    assert "customer_secrets" in content


def test_assessment_factory_lite_dataset_contract_document_preserves_boundaries():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert (
        "The Assessment Factory Lite Dataset Contract does not certify "
        "products as FedRAMP High, HIPAA compliant, or SOC 2 audited."
    ) in content
    assert (
        "The deterministic GAGF Kernel remains the authoritative decision "
        "and verification layer."
    ) in content