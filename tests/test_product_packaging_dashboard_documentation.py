from pathlib import Path


DOC_PATH = Path("docs/PRODUCT_PACKAGING_DASHBOARD.md")


def test_product_packaging_dashboard_document_exists():
    assert DOC_PATH.exists()


def test_product_packaging_dashboard_document_names_service_and_endpoint():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "ProductPackagingDashboardService" in content
    assert "POST /products/packaging/dashboard" in content
    assert "product_packaging_dashboard" in content


def test_product_packaging_dashboard_document_names_input_modes():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "product_profiles" in content
    assert "portfolio_dashboard" in content
    assert "packaging_recommendation" in content
    assert "Mode 1" in content
    assert "Mode 2" in content
    assert "Mode 3" in content


def test_product_packaging_dashboard_document_names_output_contract():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "first_candidate_card" in content
    assert "packaging_track_summary" in content
    assert "candidate_summary" in content
    assert "blocker_summary" in content
    assert "dashboard_cards" in content
    assert "operator_message" in content
    assert "recommended_action" in content


def test_product_packaging_dashboard_document_names_first_candidate_card():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "product_name" in content
    assert "track" in content
    assert "reason" in content
    assert "is_available" in content
    assert "display_label" in content
    assert "assessment_factory_lite - Fast Productization" in content


def test_product_packaging_dashboard_document_names_blockers_and_actions():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "federal_hardened_track_required" in content
    assert "regulated_compliance_boundary_required" in content
    assert "zta_required_for_some_products" in content
    assert "build_demo_package" in content
    assert "package low-risk demo or assessment products first" in content.lower()


def test_product_packaging_dashboard_document_names_current_strategy():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "assessment_factory_lite" in content
    assert "demo_or_early_revenue" in content
    assert "fip_healthcare_readiness_diagnostic" in content
    assert "fip_secure" in content


def test_product_packaging_dashboard_document_preserves_boundaries():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert (
        "The Product Packaging Dashboard does not certify products as "
        "FedRAMP High, HIPAA compliant, or SOC 2 audited."
    ) in content
    assert (
        "The deterministic GAGF Kernel remains the authoritative decision "
        "and verification layer."
    ) in content







