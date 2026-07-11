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


def test_product_security_portfolio_service_classifies_products():
    service = ProductSecurityPortfolioService()

    result = service.classify_portfolio(build_portfolio_profiles())

    assert result["status"] == "ok"
    assert result["classification_type"] == (
        "product_security_portfolio"
    )
    assert result["product_count"] == 4
    assert len(result["products"]) == 4


def test_product_security_portfolio_service_counts_security_tiers():
    service = ProductSecurityPortfolioService()

    result = service.classify_portfolio(build_portfolio_profiles())

    assert result["tier_counts"] == {
        "tier_1_standard_commercial": 1,
        "tier_2_enterprise_secure": 1,
        "tier_3_regulated_sensitive": 1,
        "tier_4_federal_critical": 1,
    }


def test_product_security_portfolio_service_counts_zta_requirements():
    service = ProductSecurityPortfolioService()

    result = service.classify_portfolio(build_portfolio_profiles())

    assert result["zta_counts"] == {
        "zta_required": 2,
        "zta_recommended": 1,
        "zta_not_required": 1,
    }


def test_product_security_portfolio_service_identifies_highest_risk_products():
    service = ProductSecurityPortfolioService()

    result = service.classify_portfolio(build_portfolio_profiles())

    assert result["highest_security_tier"] == (
        "tier_4_federal_critical"
    )
    assert result["highest_risk_products"] == ["fip_secure"]
    assert result["regulated_or_federal_products"] == [
        "fip_healthcare_readiness_diagnostic",
        "fip_secure",
    ]


def test_product_security_portfolio_service_identifies_fastest_productization_candidates():
    service = ProductSecurityPortfolioService()

    result = service.classify_portfolio(build_portfolio_profiles())

    assert result["fastest_productization_candidates"] == [
        "assessment_factory_lite",
        "fip_governance_diagnostics_saas",
    ]


def test_product_security_portfolio_service_attaches_zta_controls():
    service = ProductSecurityPortfolioService()

    result = service.classify_portfolio(build_portfolio_profiles())

    products = {
        product["product_name"]: product
        for product in result["products"]
    }

    assert products["fip_healthcare_readiness_diagnostic"][
        "zta_required"
    ] is True
    assert products["fip_healthcare_readiness_diagnostic"][
        "zta_requirement_level"
    ] == "required_regulated"
    assert "strong_identity_boundary" in products[
        "fip_healthcare_readiness_diagnostic"
    ]["zta_controls"]["identity_controls"]

    assert products["fip_secure"]["zta_required"] is True
    assert products["fip_secure"]["zta_requirement_level"] == (
        "required_federal_high"
    )
    assert "policy_decision_point" in products["fip_secure"][
        "zta_controls"
    ]["access_enforcement_controls"]


def test_product_security_portfolio_service_recommends_federal_track_when_tier_4_exists():
    service = ProductSecurityPortfolioService()

    result = service.classify_portfolio(build_portfolio_profiles())

    assert result["portfolio_recommendation"] == (
        "separate_federal_critical_products_into_hardened_track"
    )


def test_product_security_portfolio_service_handles_empty_portfolio():
    service = ProductSecurityPortfolioService()

    result = service.classify_portfolio([])

    assert result["status"] == "ok"
    assert result["product_count"] == 0
    assert result["highest_security_tier"] == "none"
    assert result["highest_risk_products"] == []
    assert result["regulated_or_federal_products"] == []
    assert result["fastest_productization_candidates"] == []
    assert result["portfolio_recommendation"] == (
        "add_product_profiles_to_classify_portfolio"
    )
