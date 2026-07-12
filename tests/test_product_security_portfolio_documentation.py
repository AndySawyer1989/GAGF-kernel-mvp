from pathlib import Path


DOC_PATH = Path("docs/PRODUCT_SECURITY_PORTFOLIO.md")


def test_product_security_portfolio_document_exists():
    assert DOC_PATH.exists()


def test_product_security_portfolio_document_names_service_and_endpoint():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "ProductSecurityPortfolioService" in content
    assert "POST /products/security-portfolio" in content
    assert "product_security_portfolio" in content


def test_product_security_portfolio_document_names_output_contract():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "tier_counts" in content
    assert "zta_counts" in content
    assert "highest_security_tier" in content
    assert "highest_risk_products" in content
    assert "regulated_or_federal_products" in content
    assert "fastest_productization_candidates" in content
    assert "portfolio_recommendation" in content


def test_product_security_portfolio_document_names_tiers_and_zta_counts():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "tier_1_standard_commercial" in content
    assert "tier_2_enterprise_secure" in content
    assert "tier_3_regulated_sensitive" in content
    assert "tier_4_federal_critical" in content
    assert "zta_required" in content
    assert "zta_recommended" in content
    assert "zta_not_required" in content


def test_product_security_portfolio_document_names_recommendations():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "add_product_profiles_to_classify_portfolio" in content
    assert "prioritize_standard_commercial_productization" in content
    assert "prioritize_enterprise_products_with_zta_readiness_review" in content
    assert "separate_regulated_products_into_compliance_ready_track" in content
    assert "separate_federal_critical_products_into_hardened_track" in content


def test_product_security_portfolio_document_names_product_examples():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "Assessment Factory Lite" in content
    assert "FIP Governance Diagnostics SaaS" in content
    assert "FIP Healthcare Readiness Diagnostic" in content
    assert "FIP Secure" in content
    assert "ESY secure runtime" in content
    assert "Personal Friction Assistant" in content
    assert "Game Adaptive Intelligence API" in content


def test_product_security_portfolio_document_names_productization_checkpoint():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "Product Security Portfolio Classification is a product checkpoint." in content
    assert "Do not burden every product with Tier 4 controls." in content
    assert (
        "Do not expose sensitive or regulated products before defining the "
        "correct security and compliance boundary."
    ) in content


def test_product_security_portfolio_document_preserves_compliance_boundary():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert (
        "Product Security Portfolio Classification does not certify products "
        "as FedRAMP High, HIPAA compliant, or SOC 2 audited."
    ) in content
    assert (
        "The deterministic GAGF Kernel remains the authoritative decision "
        "and verification layer."
    ) in content

