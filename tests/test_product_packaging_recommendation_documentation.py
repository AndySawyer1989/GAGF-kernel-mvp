from pathlib import Path


DOC_PATH = Path("docs/PRODUCT_PACKAGING_RECOMMENDATION.md")


def test_product_packaging_recommendation_document_exists():
    assert DOC_PATH.exists()


def test_product_packaging_recommendation_document_names_service_and_endpoint():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "ProductPackagingRecommendationService" in content
    assert "POST /products/packaging/recommendation" in content
    assert "product_packaging_recommendation" in content


def test_product_packaging_recommendation_document_names_input_modes():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "product_profiles" in content
    assert "portfolio_dashboard" in content
    assert "Mode 1" in content
    assert "Mode 2" in content


def test_product_packaging_recommendation_document_names_output_contract():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "first_packaging_candidate" in content
    assert "primary_packaging_track" in content
    assert "demo_candidates" in content
    assert "enterprise_candidates" in content
    assert "regulated_candidates" in content
    assert "hardened_candidates" in content
    assert "security_blockers" in content
    assert "packaging_recommendation" in content
    assert "operator_message" in content
    assert "next_action" in content


def test_product_packaging_recommendation_document_names_candidate_order():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "fast_productization" in content
    assert "enterprise_ready" in content
    assert "regulated_boundary" in content
    assert "hardened_federal" in content
    assert "lowest-security-burden candidate first" in content


def test_product_packaging_recommendation_document_names_security_blockers():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "federal_hardened_track_required" in content
    assert "regulated_compliance_boundary_required" in content
    assert "zta_required_for_some_products" in content
    assert "hardened_products_not_fast_packaging_candidates" in content
    assert "regulated_products_need_boundary_definition" in content


def test_product_packaging_recommendation_document_names_current_strategy():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "assessment_factory_lite" in content
    assert "demo_or_early_revenue" in content
    assert "build_demo_package" in content
    assert "FIP Governance Diagnostics SaaS" in content
    assert "FIP Healthcare Readiness Diagnostic" in content
    assert "FIP Secure" in content
    assert "ESY secure runtime" in content


def test_product_packaging_recommendation_document_preserves_boundaries():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert (
        "Product Packaging Recommendation does not certify products as "
        "FedRAMP High, HIPAA compliant, or SOC 2 audited."
    ) in content
    assert (
        "The deterministic GAGF Kernel remains the authoritative decision "
        "and verification layer."
    ) in content

