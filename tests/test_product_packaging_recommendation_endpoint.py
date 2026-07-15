from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


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


def test_product_packaging_recommendation_endpoint_builds_from_profiles():
    response = client.post(
        "/products/packaging/recommendation",
        json={"product_profiles": build_portfolio_profiles()},
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["status"] == "ok"
    assert payload["recommendation_type"] == (
        "product_packaging_recommendation"
    )
    assert payload["first_packaging_candidate"] == {
        "product_name": "assessment_factory_lite",
        "track": "fast_productization",
        "reason": "lowest_security_burden",
    }


def test_product_packaging_recommendation_endpoint_selects_demo_track():
    response = client.post(
        "/products/packaging/recommendation",
        json={"product_profiles": build_portfolio_profiles()},
    )

    payload = response.json()

    assert payload["primary_packaging_track"] == (
        "demo_or_early_revenue"
    )
    assert payload["packaging_recommendation"] == (
        "package_fast_demo_or_assessment_product_first"
    )
    assert payload["next_action"] == "build_demo_package"


def test_product_packaging_recommendation_endpoint_preserves_candidate_tracks():
    response = client.post(
        "/products/packaging/recommendation",
        json={"product_profiles": build_portfolio_profiles()},
    )

    payload = response.json()

    assert payload["demo_candidates"] == [
        "assessment_factory_lite",
    ]
    assert payload["enterprise_candidates"] == [
        "fip_governance_diagnostics_saas",
    ]
    assert payload["regulated_candidates"] == [
        "fip_healthcare_readiness_diagnostic",
    ]
    assert payload["hardened_candidates"] == [
        "fip_secure",
    ]


def test_product_packaging_recommendation_endpoint_reports_security_blockers():
    response = client.post(
        "/products/packaging/recommendation",
        json={"product_profiles": build_portfolio_profiles()},
    )

    payload = response.json()

    assert payload["security_blockers"] == [
        "federal_hardened_track_required",
        "regulated_compliance_boundary_required",
        "zta_required_for_some_products",
        "hardened_products_not_fast_packaging_candidates",
        "regulated_products_need_boundary_definition",
    ]


def test_product_packaging_recommendation_endpoint_accepts_existing_dashboard():
    dashboard_response = client.post(
        "/products/security-portfolio/dashboard",
        json={"product_profiles": build_portfolio_profiles()},
    )

    assert dashboard_response.status_code == 200

    response = client.post(
        "/products/packaging/recommendation",
        json={"portfolio_dashboard": dashboard_response.json()},
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["operator_message"] == (
        "Package assessment_factory_lite first as the fastest demo or "
        "early-revenue candidate."
    )
    assert payload["next_action"] == "build_demo_package"


def test_product_packaging_recommendation_endpoint_route_exists():
    actual_routes = {route.path for route in app.routes}

    assert "/products/packaging/recommendation" in actual_routes






