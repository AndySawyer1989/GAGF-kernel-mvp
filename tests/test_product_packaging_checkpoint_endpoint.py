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


def test_product_packaging_checkpoint_endpoint_builds_from_profiles():
    response = client.post(
        "/products/packaging/checkpoint",
        json={"product_profiles": build_portfolio_profiles()},
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["status"] == "ok"
    assert payload["checkpoint_type"] == "product_packaging_checkpoint"
    assert payload["selected_product"] == "assessment_factory_lite"
    assert payload["selected_track"] == "fast_productization"
    assert payload["package_name"] == "Assessment Factory Lite Demo Package"


def test_product_packaging_checkpoint_endpoint_builds_buyer_and_deliverable():
    response = client.post(
        "/products/packaging/checkpoint",
        json={"product_profiles": build_portfolio_profiles()},
    )

    payload = response.json()

    assert payload["buyer_profile"]["buyer_type"] == (
        "small_to_mid_size_operations_leader"
    )
    assert payload["buyer_profile"]["sales_motion"] == (
        "demo_first_consultative_sale"
    )
    assert payload["minimum_deliverable"]["deliverable_type"] == (
        "demo_assessment"
    )
    assert "governance_drag_summary" in (
        payload["minimum_deliverable"]["outputs"]
    )


def test_product_packaging_checkpoint_endpoint_sets_go_decision():
    response = client.post(
        "/products/packaging/checkpoint",
        json={"product_profiles": build_portfolio_profiles()},
    )

    payload = response.json()

    assert payload["go_no_go"] == {
        "decision": "go",
        "reason": "fast_demo_candidate_available",
    }
    assert payload["recommended_action"] == "build_demo_package"
    assert payload["operator_message"] == (
        "Proceed with assessment_factory_lite as the first demo or "
        "early-revenue package. Next action: build_demo_package."
    )


def test_product_packaging_checkpoint_endpoint_accepts_existing_dashboard():
    dashboard_response = client.post(
        "/products/packaging/dashboard",
        json={"product_profiles": build_portfolio_profiles()},
    )

    assert dashboard_response.status_code == 200

    response = client.post(
        "/products/packaging/checkpoint",
        json={"packaging_dashboard": dashboard_response.json()},
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["selected_product"] == "assessment_factory_lite"
    assert payload["build_boundary"]["scope"] == "demo_only"
    assert payload["security_boundary"]["certification_claims_allowed"] is False


def test_product_packaging_checkpoint_endpoint_accepts_existing_recommendation():
    recommendation_response = client.post(
        "/products/packaging/recommendation",
        json={"product_profiles": build_portfolio_profiles()},
    )

    assert recommendation_response.status_code == 200

    response = client.post(
        "/products/packaging/checkpoint",
        json={"packaging_recommendation": recommendation_response.json()},
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["package_name"] == "Assessment Factory Lite Demo Package"
    assert payload["revenue_hypothesis"]["pricing_motion"] == (
        "fixed_fee_demo_assessment"
    )


def test_product_packaging_checkpoint_endpoint_route_exists():
    actual_routes = {route.path for route in app.routes}

    assert "/products/packaging/checkpoint" in actual_routes


