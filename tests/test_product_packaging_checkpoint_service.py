from backend.app.gagf.product_packaging_checkpoint_service import (
    ProductPackagingCheckpointService,
)
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


def build_packaging_dashboard():
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
    portfolio_dashboard = (
        ProductSecurityPortfolioDashboardService().build_summary(portfolio)
    )
    recommendation = ProductPackagingRecommendationService().recommend(
        portfolio_dashboard
    )

    return ProductPackagingDashboardService().build_summary(recommendation)


def build_checkpoint():
    return ProductPackagingCheckpointService().build_checkpoint(
        build_packaging_dashboard()
    )


def test_product_packaging_checkpoint_builds_checkpoint():
    checkpoint = build_checkpoint()

    assert checkpoint["status"] == "ok"
    assert checkpoint["checkpoint_type"] == "product_packaging_checkpoint"
    assert checkpoint["selected_product"] == "assessment_factory_lite"
    assert checkpoint["selected_track"] == "fast_productization"
    assert checkpoint["package_name"] == (
        "Assessment Factory Lite Demo Package"
    )


def test_product_packaging_checkpoint_builds_buyer_profile():
    checkpoint = build_checkpoint()

    assert checkpoint["buyer_profile"] == {
        "buyer_type": "small_to_mid_size_operations_leader",
        "economic_buyer": "founder_operations_lead_or_it_manager",
        "user": "operator_or_process_owner",
        "primary_pain": "approval_delay_and_operational_drag",
        "sales_motion": "demo_first_consultative_sale",
    }


def test_product_packaging_checkpoint_builds_minimum_deliverable():
    checkpoint = build_checkpoint()

    assert checkpoint["minimum_deliverable"] == {
        "deliverable_type": "demo_assessment",
        "inputs": [
            "sample_csv",
            "workflow_events",
            "approval_or_delay_examples",
        ],
        "outputs": [
            "governance_drag_summary",
            "top_friction_points",
            "simple_recommendation_report",
            "operator_dashboard_view",
        ],
        "success_criteria": [
            "loads_sample_data",
            "detects_friction",
            "shows_recommendation",
            "produces_demo_ready_summary",
        ],
    }


def test_product_packaging_checkpoint_builds_demo_workflow_and_revenue_hypothesis():
    checkpoint = build_checkpoint()

    assert checkpoint["demo_workflow"] == [
        "upload_sample_csv",
        "run_governance_diagnostics",
        "review_friction_summary",
        "show_top_constraints",
        "display_recommended_intervention",
        "export_demo_summary",
    ]
    assert checkpoint["revenue_hypothesis"] == {
        "pricing_motion": "fixed_fee_demo_assessment",
        "starter_price_hypothesis": "$500-$2500",
        "expansion_path": "governance_diagnostics_saas_or_consulting",
        "time_to_value": "same_day_to_one_week",
    }


def test_product_packaging_checkpoint_sets_build_and_security_boundaries():
    checkpoint = build_checkpoint()

    assert checkpoint["build_boundary"] == {
        "scope": "demo_only",
        "allowed": [
            "sample_data",
            "local_demo",
            "operator_dashboard",
            "summary_report",
        ],
        "excluded": [
            "regulated_data",
            "production_customer_data",
            "federal_data",
            "autonomous_actions",
        ],
    }
    assert checkpoint["security_boundary"] == {
        "has_packaging_blocker": True,
        "has_federal_blocker": True,
        "has_regulated_blocker": True,
        "has_zta_blocker": True,
        "boundary_required_before_launch": False,
        "certification_claims_allowed": False,
    }


def test_product_packaging_checkpoint_sets_go_decision_for_fast_candidate():
    checkpoint = build_checkpoint()

    assert checkpoint["go_no_go"] == {
        "decision": "go",
        "reason": "fast_demo_candidate_available",
    }
    assert checkpoint["recommended_action"] == "build_demo_package"
    assert checkpoint["operator_message"] == (
        "Proceed with assessment_factory_lite as the first demo or "
        "early-revenue package. Next action: build_demo_package."
    )


def test_product_packaging_checkpoint_handles_empty_dashboard():
    checkpoint = ProductPackagingCheckpointService().build_checkpoint({})

    assert checkpoint["status"] == "ok"
    assert checkpoint["selected_product"] == "none"
    assert checkpoint["selected_track"] == "none"
    assert checkpoint["package_name"] == "No package selected"
    assert checkpoint["go_no_go"] == {
        "decision": "no_go",
        "reason": "no_packaging_candidate_available",
    }
    assert checkpoint["operator_message"] == (
        "No product is ready for packaging."
    )


