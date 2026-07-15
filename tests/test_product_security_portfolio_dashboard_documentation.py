from pathlib import Path


DOC_PATH = Path("docs/PRODUCT_SECURITY_PORTFOLIO_DASHBOARD.md")


def test_product_security_portfolio_dashboard_document_exists():
    assert DOC_PATH.exists()


def test_product_security_portfolio_dashboard_document_names_service_and_endpoint():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "ProductSecurityPortfolioDashboardService" in content
    assert "POST /products/security-portfolio/dashboard" in content
    assert "product_security_portfolio_dashboard" in content


def test_product_security_portfolio_dashboard_document_names_input_modes():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "product_profiles" in content
    assert "portfolio_result" in content
    assert "Mode 1" in content
    assert "Mode 2" in content


def test_product_security_portfolio_dashboard_document_names_output_contract():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "tier_distribution" in content
    assert "zta_distribution" in content
    assert "productization_tracks" in content
    assert "risk_summary" in content
    assert "highest_risk_summary" in content
    assert "dashboard_cards" in content
    assert "operator_message" in content
    assert "recommended_action" in content


def test_product_security_portfolio_dashboard_document_names_tracks():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "fast_productization" in content
    assert "enterprise_ready" in content
    assert "regulated_boundary" in content
    assert "hardened_federal" in content
    assert "zta_planning" in content


def test_product_security_portfolio_dashboard_document_names_recommended_actions():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "add_product_profiles" in content
    assert "package_standard_commercial_product" in content
    assert "package_enterprise_product_with_zta_review" in content
    assert "define_regulated_compliance_boundary" in content
    assert "define_federal_hardened_product_track" in content


def test_product_security_portfolio_dashboard_document_names_product_examples():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "Assessment Factory Lite" in content
    assert "FIP Governance Diagnostics SaaS" in content
    assert "FIP Healthcare Readiness Diagnostic" in content
    assert "FIP Secure" in content
    assert "ESY secure runtime" in content


def test_product_security_portfolio_dashboard_document_preserves_compliance_boundary():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert (
        "The Product Security Portfolio Dashboard does not certify products "
        "as FedRAMP High, HIPAA compliant, or SOC 2 audited."
    ) in content
    assert (
        "The deterministic GAGF Kernel remains the authoritative decision "
        "and verification layer."
    ) in content





