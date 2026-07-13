from backend.app.gagf.assessment_factory_lite_demo_profile_service import (
    AssessmentFactoryLiteDemoProfileService,
)
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


def build_checkpoint():
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
    packaging_dashboard = ProductPackagingDashboardService().build_summary(
        recommendation
    )

    return ProductPackagingCheckpointService().build_checkpoint(
        packaging_dashboard
    )


def build_profile():
    return AssessmentFactoryLiteDemoProfileService().build_profile(
        build_checkpoint()
    )


def test_assessment_factory_lite_demo_profile_builds_profile():
    profile = build_profile()

    assert profile["status"] == "ok"
    assert profile["profile_type"] == "assessment_factory_lite_demo_profile"
    assert profile["selected_product"] == "assessment_factory_lite"
    assert profile["package_name"] == "Assessment Factory Lite Demo Package"
    assert profile["selected_track"] == "fast_productization"
    assert profile["is_assessment_factory_lite"] is True


def test_assessment_factory_lite_demo_profile_marks_demo_ready():
    profile = build_profile()

    assert profile["demo_readiness"] == {
        "ready_for_demo_package": True,
        "decision": "go",
        "reason": "fast_demo_candidate_available",
        "requires_customer_data": False,
        "requires_regulated_data": False,
        "requires_federal_data": False,
        "requires_production_access": False,
    }


def test_assessment_factory_lite_demo_profile_sets_demo_boundary():
    profile = build_profile()

    assert profile["demo_boundary"] == {
        "boundary_type": "demo_only_sample_data",
        "allowed_data": [
            "sample_csv",
            "synthetic_workflow_events",
            "mock_approval_events",
            "mock_delay_events",
        ],
        "allowed_runtime": [
            "local_demo",
            "operator_workstation",
            "non_production_environment",
        ],
        "prohibited_data": [
            "regulated_data",
            "federal_data",
            "production_customer_data",
            "customer_secrets",
            "live_security_telemetry",
        ],
        "certification_claims_allowed": False,
    }


def test_assessment_factory_lite_demo_profile_sets_workflow_and_sections():
    profile = build_profile()

    assert profile["demo_workflow"] == [
        "load_demo_profile",
        "upload_sample_csv",
        "run_governance_diagnostics",
        "review_governance_drag_summary",
        "review_top_friction_points",
        "display_recommended_intervention",
        "export_demo_summary",
    ]
    assert "governance_drag_summary" in profile["dashboard_sections"]
    assert "recommended_intervention" in profile["dashboard_sections"]
    assert "executive_summary" in profile["report_sections"]
    assert "compliance_disclaimer" in profile["report_sections"]


def test_assessment_factory_lite_demo_profile_sets_success_criteria():
    profile = build_profile()

    assert profile["success_criteria"] == [
        "demo_profile_loads",
        "sample_csv_boundary_is_enforced",
        "governance_diagnostics_run",
        "friction_summary_is_displayed",
        "recommended_intervention_is_displayed",
        "demo_summary_can_be_exported",
        "no_regulated_or_federal_data_required",
    ]


def test_assessment_factory_lite_demo_profile_excludes_high_risk_scope():
    profile = build_profile()

    assert profile["excluded_scope"] == [
        "production_customer_data_processing",
        "regulated_data_processing",
        "federal_data_processing",
        "fedramp_or_hipaa_certification_claims",
        "autonomous_remediation",
        "live_customer_integrations",
    ]


def test_assessment_factory_lite_demo_profile_handles_non_ready_checkpoint():
    profile = AssessmentFactoryLiteDemoProfileService().build_profile({})

    assert profile["selected_product"] == "none"
    assert profile["is_assessment_factory_lite"] is False
    assert profile["demo_readiness"]["ready_for_demo_package"] is False
    assert profile["recommended_action"] == (
        "review_product_packaging_checkpoint"
    )

