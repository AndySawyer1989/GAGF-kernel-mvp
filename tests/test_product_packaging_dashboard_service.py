from backend.app.gagf.product_packaging_dashboard_service import (
    ProductPackagingDashboardService,
)
from backend.app.gagf.product_packaging_recommendation_service import (
    ProductPackagingRecommendationService,
)
from backend.app.gagf.product_security_portfolio_dashboard_service import (
    ProductSecurityPortfolioDashboardService,
)
from backend.app.gagf.product_security_portfolio_service import (
    ProductSecurityPortfolioService,
)


def build_packaging_recommendation():
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
    dashboard = ProductSecurityPortfolioDashboardService().build_summary(
        portfolio
    )

    return ProductPackagingRecommendationService().recommend(dashboard)


def build_summary():
    return ProductPackagingDashboardService().build_summary(
        build_packaging_recommendation()
    )


def test_product_packaging_dashboard_builds_summary():
    summary = build_summary()

    assert summary["status"] == "ok"
    assert summary["summary_type"] == "product_packaging_dashboard"
    assert summary["packaging_recommendation"] == (
        "package_fast_demo_or_assessment_product_first"
    )
    assert summary["recommended_action"] == "build_demo_package"


def test_product_packaging_dashboard_builds_first_candidate_card():
    summary = build_summary()

    assert summary["first_candidate_card"] == {
        "product_name": "assessment_factory_lite",
        "track": "fast_productization",
        "reason": "lowest_security_burden",
        "is_available": True,
        "display_label": (
            "assessment_factory_lite - Fast Productization"
        ),
    }


def test_product_packaging_dashboard_builds_packaging_track_summary():
    summary = build_summary()

    assert summary["packaging_track_summary"] == {
        "primary_packaging_track": "demo_or_early_revenue",
        "recommendation_type": "product_packaging_recommendation",
        "is_demo_or_revenue_candidate": True,
        "requires_enterprise_review": False,
        "requires_regulated_boundary": False,
        "requires_hardened_boundary": False,
    }


def test_product_packaging_dashboard_builds_candidate_summary():
    summary = build_summary()

    assert summary["candidate_summary"]["demo_candidate_count"] == 1
    assert summary["candidate_summary"]["enterprise_candidate_count"] == 1
    assert summary["candidate_summary"]["regulated_candidate_count"] == 1
    assert summary["candidate_summary"]["hardened_candidate_count"] == 1
    assert summary["candidate_summary"]["demo_candidates"] == [
        "assessment_factory_lite",
    ]
    assert summary["candidate_summary"]["hardened_candidates"] == [
        "fip_secure",
    ]


def test_product_packaging_dashboard_builds_blocker_summary():
    summary = build_summary()

    assert summary["blocker_summary"] == {
        "blocker_count": 5,
        "security_blockers": [
            "federal_hardened_track_required",
            "regulated_compliance_boundary_required",
            "zta_required_for_some_products",
            "hardened_products_not_fast_packaging_candidates",
            "regulated_products_need_boundary_definition",
        ],
        "has_federal_blocker": True,
        "has_regulated_blocker": True,
        "has_zta_blocker": True,
        "has_packaging_blocker": True,
    }


def test_product_packaging_dashboard_builds_operator_guidance():
    summary = build_summary()

    assert summary["operator_message"] == (
        "Package assessment_factory_lite first as the fastest demo or "
        "early-revenue candidate."
    )
    assert summary["recommended_action"] == "build_demo_package"


def test_product_packaging_dashboard_handles_empty_result():
    summary = ProductPackagingDashboardService().build_summary({})

    assert summary["status"] == "ok"
    assert summary["summary_type"] == "product_packaging_dashboard"
    assert summary["first_candidate_card"] == {
        "product_name": "none",
        "track": "none",
        "reason": "no_packaging_candidate_available",
        "is_available": False,
        "display_label": "No packaging candidate",
    }
    assert summary["recommended_action"] == "add_product_candidates"
    assert summary["blocker_summary"]["blocker_count"] == 0





