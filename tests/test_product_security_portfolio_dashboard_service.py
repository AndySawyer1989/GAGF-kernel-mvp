from backend.app.gagf.product_security_portfolio_dashboard_service import (
    ProductSecurityPortfolioDashboardService,
)
from backend.app.gagf.product_security_portfolio_service import (
    ProductSecurityPortfolioService,
)


def build_portfolio_profiles():
    return [
        {
            "product_name": "Assessment Factory Lite",
            "product_category": "demo",
            "is_public_demo": True,
        },
        {
            "product_name": "FIP Governance Diagnostics SaaS",
            "product_category": "governance_diagnostics",
            "targets_enterprise": True,
            "handles_customer_data": True,
        },
        {
            "product_name": "FIP Healthcare Readiness Diagnostic",
            "product_category": "compliance",
            "targets_healthcare": True,
            "handles_health_data": True,
        },
        {
            "product_name": "FIP Secure",
            "product_category": "secure_enterprise",
            "targets_federal": True,
            "requires_air_gap": True,
            "requires_on_prem": True,
        },
    ]


def build_summary():
    portfolio = ProductSecurityPortfolioService().classify_portfolio(
        build_portfolio_profiles()
    )
    return ProductSecurityPortfolioDashboardService().build_summary(
        portfolio
    )


def test_product_security_portfolio_dashboard_builds_summary():
    summary = build_summary()

    assert summary["status"] == "ok"
    assert summary["summary_type"] == (
        "product_security_portfolio_dashboard"
    )
    assert summary["product_count"] == 4
    assert summary["portfolio_recommendation"] == (
        "separate_federal_critical_products_into_hardened_track"
    )


def test_product_security_portfolio_dashboard_builds_tier_distribution():
    summary = build_summary()

    assert summary["tier_distribution"] == {
        "standard_commercial": 1,
        "enterprise_secure": 1,
        "regulated_sensitive": 1,
        "federal_critical": 1,
    }


def test_product_security_portfolio_dashboard_builds_zta_distribution():
    summary = build_summary()

    assert summary["zta_distribution"] == {
        "required": 2,
        "recommended": 1,
        "not_required": 1,
    }


def test_product_security_portfolio_dashboard_builds_productization_tracks():
    summary = build_summary()

    assert summary["productization_tracks"]["fast_productization"] == [
        "assessment_factory_lite",
    ]
    assert summary["productization_tracks"]["enterprise_ready"] == [
        "fip_governance_diagnostics_saas",
    ]
    assert summary["productization_tracks"]["regulated_boundary"] == [
        "fip_healthcare_readiness_diagnostic",
    ]
    assert summary["productization_tracks"]["hardened_federal"] == [
        "fip_secure",
    ]


def test_product_security_portfolio_dashboard_builds_risk_summary():
    summary = build_summary()

    assert summary["risk_summary"] == {
        "highest_security_tier": "tier_4_federal_critical",
        "highest_risk_product_count": 1,
        "regulated_or_federal_product_count": 2,
        "requires_hardened_track": True,
        "requires_regulated_track": True,
    }


def test_product_security_portfolio_dashboard_builds_operator_guidance():
    summary = build_summary()

    assert summary["operator_message"] == (
        "Separate federal or critical products into a hardened track."
    )
    assert summary["recommended_action"] == (
        "define_federal_hardened_product_track"
    )


def test_product_security_portfolio_dashboard_handles_empty_result():
    summary = ProductSecurityPortfolioDashboardService().build_summary({})

    assert summary["status"] == "ok"
    assert summary["product_count"] == 0
    assert summary["portfolio_recommendation"] == (
        "add_product_profiles_to_classify_portfolio"
    )
    assert summary["tier_distribution"] == {
        "standard_commercial": 0,
        "enterprise_secure": 0,
        "regulated_sensitive": 0,
        "federal_critical": 0,
    }
    assert summary["zta_distribution"] == {
        "required": 0,
        "recommended": 0,
        "not_required": 0,
    }
    assert summary["recommended_action"] == "add_product_profiles"





