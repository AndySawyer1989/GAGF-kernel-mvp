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


def test_product_packaging_dashboard_endpoint_builds_from_profiles():
    response = client.post(
        "/products/packaging/dashboard",
        json={"product_profiles": build_portfolio_profiles()},
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["status"] == "ok"
    assert payload["summary_type"] == "product_packaging_dashboard"
    assert payload["packaging_recommendation"] == (
        "package_fast_demo_or_assessment_product_first"
    )
    assert payload["recommended_action"] == "build_demo_package"


def test_product_packaging_dashboard_endpoint_builds_first_candidate_card():
    response = client.post(
        "/products/packaging/dashboard",
        json={"product_profiles": build_portfolio_profiles()},
    )

    payload = response.json()

    assert payload["first_candidate_card"] == {
        "product_name": "assessment_factory_lite",
        "track": "fast_productization",
        "reason": "lowest_security_burden",
        "is_available": True,
        "display_label": (
            "assessment_factory_lite - Fast Productization"
        ),
    }


def test_product_packaging_dashboard_endpoint_builds_candidate_and_blocker_summary():
    response = client.post(
        "/products/packaging/dashboard",
        json={"product_profiles": build_portfolio_profiles()},
    )

    payload = response.json()

    assert payload["candidate_summary"]["demo_candidate_count"] == 1
    assert payload["candidate_summary"]["enterprise_candidate_count"] == 1
    assert payload["candidate_summary"]["regulated_candidate_count"] == 1
    assert payload["candidate_summary"]["hardened_candidate_count"] == 1
    assert payload["blocker_summary"]["blocker_count"] == 5
    assert payload["blocker_summary"]["has_federal_blocker"] is True
    assert payload["blocker_summary"]["has_regulated_blocker"] is True
    assert payload["blocker_summary"]["has_zta_blocker"] is True


def test_product_packaging_dashboard_endpoint_accepts_existing_recommendation():
    recommendation_response = client.post(
        "/products/packaging/recommendation",
        json={"product_profiles": build_portfolio_profiles()},
    )

    assert recommendation_response.status_code == 200

    response = client.post(
        "/products/packaging/dashboard",
        json={"packaging_recommendation": recommendation_response.json()},
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["operator_message"] == (
        "Package assessment_factory_lite first as the fastest demo or "
        "early-revenue candidate."
    )
    assert payload["recommended_action"] == "build_demo_package"


def test_product_packaging_dashboard_endpoint_accepts_existing_portfolio_dashboard():
    dashboard_response = client.post(
        "/products/security-portfolio/dashboard",
        json={"product_profiles": build_portfolio_profiles()},
    )

    assert dashboard_response.status_code == 200

    response = client.post(
        "/products/packaging/dashboard",
        json={"portfolio_dashboard": dashboard_response.json()},
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["packaging_track_summary"][
        "primary_packaging_track"
    ] == "demo_or_early_revenue"
    assert payload["packaging_track_summary"][
        "is_demo_or_revenue_candidate"
    ] is True


def test_product_packaging_dashboard_endpoint_route_exists():
    actual_routes = {route.path for route in app.routes}

    assert "/products/packaging/dashboard" in actual_routes




