from backend.app.gagf.product_packaging_recommendation_service import (
    ProductPackagingRecommendationService,
)
from backend.app.gagf.product_security_portfolio_dashboard_service import (
    ProductSecurityPortfolioDashboardService,
)
from backend.app.gagf.product_security_portfolio_service import (
    ProductSecurityPortfolioService,
)


def build_dashboard():
    profiles = [
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

    portfolio = ProductSecurityPortfolioService().classify_portfolio(
        profiles
    )

    return ProductSecurityPortfolioDashboardService().build_summary(
        portfolio
    )


def test_product_packaging_recommendation_service_builds_recommendation():
    recommendation = ProductPackagingRecommendationService().recommend(
        build_dashboard()
    )

    assert recommendation["status"] == "ok"
    assert recommendation["recommendation_type"] == (
        "product_packaging_recommendation"
    )
    assert recommendation["first_packaging_candidate"] == {
        "product_name": "assessment_factory_lite",
        "track": "fast_productization",
        "reason": "lowest_security_burden",
    }


def test_product_packaging_recommendation_service_selects_demo_track_first():
    recommendation = ProductPackagingRecommendationService().recommend(
        build_dashboard()
    )

    assert recommendation["primary_packaging_track"] == (
        "demo_or_early_revenue"
    )
    assert recommendation["packaging_recommendation"] == (
        "package_fast_demo_or_assessment_product_first"
    )
    assert recommendation["next_action"] == "build_demo_package"


def test_product_packaging_recommendation_service_preserves_candidate_tracks():
    recommendation = ProductPackagingRecommendationService().recommend(
        build_dashboard()
    )

    assert recommendation["demo_candidates"] == [
        "assessment_factory_lite",
    ]
    assert recommendation["enterprise_candidates"] == [
        "fip_governance_diagnostics_saas",
    ]
    assert recommendation["regulated_candidates"] == [
        "fip_healthcare_readiness_diagnostic",
    ]
    assert recommendation["hardened_candidates"] == [
        "fip_secure",
    ]


def test_product_packaging_recommendation_service_reports_security_blockers():
    recommendation = ProductPackagingRecommendationService().recommend(
        build_dashboard()
    )

    assert recommendation["security_blockers"] == [
        "federal_hardened_track_required",
        "regulated_compliance_boundary_required",
        "zta_required_for_some_products",
        "hardened_products_not_fast_packaging_candidates",
        "regulated_products_need_boundary_definition",
    ]


def test_product_packaging_recommendation_service_builds_operator_message():
    recommendation = ProductPackagingRecommendationService().recommend(
        build_dashboard()
    )

    assert recommendation["operator_message"] == (
        "Package assessment_factory_lite first as the fastest demo or "
        "early-revenue candidate."
    )


def test_product_packaging_recommendation_service_selects_enterprise_when_no_fast_candidate():
    dashboard = {
        "productization_tracks": {
            "fast_productization": [],
            "enterprise_ready": ["fip_governance_diagnostics_saas"],
            "regulated_boundary": [],
            "hardened_federal": [],
            "zta_planning": [],
        },
        "risk_summary": {},
        "zta_distribution": {
            "required": 0,
            "recommended": 1,
            "not_required": 0,
        },
    }

    recommendation = ProductPackagingRecommendationService().recommend(
        dashboard
    )

    assert recommendation["first_packaging_candidate"] == {
        "product_name": "fip_governance_diagnostics_saas",
        "track": "enterprise_ready",
        "reason": "commercial_candidate_with_enterprise_controls",
    }
    assert recommendation["primary_packaging_track"] == "enterprise_pilot"
    assert recommendation["next_action"] == "build_enterprise_pilot_package"


def test_product_packaging_recommendation_service_handles_empty_dashboard():
    recommendation = ProductPackagingRecommendationService().recommend({})

    assert recommendation["first_packaging_candidate"] == {
        "product_name": "none",
        "track": "none",
        "reason": "no_packaging_candidate_available",
    }
    assert recommendation["primary_packaging_track"] == "none"
    assert recommendation["packaging_recommendation"] == (
        "add_or_refine_product_candidates"
    )
    assert recommendation["operator_message"] == (
        "No product packaging candidate is available yet."
    )
    assert recommendation["next_action"] == "add_product_candidates"
