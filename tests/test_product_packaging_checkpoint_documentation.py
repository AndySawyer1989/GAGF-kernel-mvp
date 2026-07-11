from pathlib import Path


DOC_PATH = Path("docs/PRODUCT_PACKAGING_CHECKPOINT.md")


def test_product_packaging_checkpoint_document_exists():
    assert DOC_PATH.exists()


def test_product_packaging_checkpoint_document_names_service_and_endpoint():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "ProductPackagingCheckpointService" in content
    assert "POST /products/packaging/checkpoint" in content
    assert "product_packaging_checkpoint" in content


def test_product_packaging_checkpoint_document_names_input_modes():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "product_profiles" in content
    assert "portfolio_dashboard" in content
    assert "packaging_recommendation" in content
    assert "packaging_dashboard" in content
    assert "Mode 1" in content
    assert "Mode 2" in content
    assert "Mode 3" in content
    assert "Mode 4" in content


def test_product_packaging_checkpoint_document_names_output_contract():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "selected_product" in content
    assert "selected_track" in content
    assert "package_name" in content
    assert "buyer_profile" in content
    assert "minimum_deliverable" in content
    assert "demo_workflow" in content
    assert "revenue_hypothesis" in content
    assert "build_boundary" in content
    assert "security_boundary" in content
    assert "go_no_go" in content


def test_product_packaging_checkpoint_document_names_assessment_factory_strategy():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "assessment_factory_lite" in content
    assert "Assessment Factory Lite Demo Package" in content
    assert "fixed_fee_demo_assessment" in content
    assert "$500-$2500" in content
    assert "build_demo_package" in content
    assert "fast_demo_candidate_available" in content


def test_product_packaging_checkpoint_document_names_demo_boundary():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "demo_only" in content
    assert "sample_data" in content
    assert "local_demo" in content
    assert "summary_report" in content
    assert "regulated_data" in content
    assert "production_customer_data" in content
    assert "federal_data" in content
    assert "autonomous_actions" in content


def test_product_packaging_checkpoint_document_names_product_tracks():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "FIP Governance Diagnostics SaaS" in content
    assert "FIP Healthcare Readiness Diagnostic" in content
    assert "FIP Secure" in content
    assert "ESY secure runtime" in content
    assert "enterprise pilot track" in content
    assert "regulated boundary track" in content
    assert "hardened federal track" in content


def test_product_packaging_checkpoint_document_preserves_boundaries():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert (
        "The Product Packaging Checkpoint does not certify products as "
        "FedRAMP High, HIPAA compliant, or SOC 2 audited."
    ) in content
    assert (
        "The deterministic GAGF Kernel remains the authoritative decision "
        "and verification layer."
    ) in content