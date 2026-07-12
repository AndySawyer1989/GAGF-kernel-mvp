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


def test_product_security_portfolio_dashboard_endpoint_builds_summary_from_profiles():
    response = client.post(
        "/products/security-portfolio/dashboard",
        json={"product_profiles": build_portfolio_profiles()},
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["status"] == "ok"
    assert payload["summary_type"] == (
        "product_security_portfolio_dashboard"
    )
    assert payload["product_count"] == 4
    assert payload["portfolio_recommendation"] == (
        "separate_federal_critical_products_into_hardened_track"
    )


def test_product_security_portfolio_dashboard_endpoint_builds_tier_distribution():
    response = client.post(
        "/products/security-portfolio/dashboard",
        json={"product_profiles": build_portfolio_profiles()},
    )

    payload = response.json()

    assert payload["tier_distribution"] == {
        "standard_commercial": 1,
        "enterprise_secure": 1,
        "regulated_sensitive": 1,
        "federal_critical": 1,
    }


def test_product_security_portfolio_dashboard_endpoint_builds_zta_distribution():
    response = client.post(
        "/products/security-portfolio/dashboard",
        json={"product_profiles": build_portfolio_profiles()},
    )

    payload = response.json()

    assert payload["zta_distribution"] == {
        "required": 2,
        "recommended": 1,
        "not_required": 1,
    }


def test_product_security_portfolio_dashboard_endpoint_builds_productization_tracks():
    response = client.post(
        "/products/security-portfolio/dashboard",
        json={"product_profiles": build_portfolio_profiles()},
    )

    payload = response.json()

    assert payload["productization_tracks"]["fast_productization"] == [
        "assessment_factory_lite",
    ]
    assert payload["productization_tracks"]["enterprise_ready"] == [
        "fip_governance_diagnostics_saas",
    ]
    assert payload["productization_tracks"]["regulated_boundary"] == [
        "fip_healthcare_readiness_diagnostic",
    ]
    assert payload["productization_tracks"]["hardened_federal"] == [
        "fip_secure",
    ]


def test_product_security_portfolio_dashboard_endpoint_accepts_existing_portfolio_result():
    portfolio_response = client.post(
        "/products/security-portfolio",
        json=build_portfolio_profiles(),
    )

    assert portfolio_response.status_code == 200

    response = client.post(
        "/products/security-portfolio/dashboard",
        json={"portfolio_result": portfolio_response.json()},
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["risk_summary"] == {
        "highest_security_tier": "tier_4_federal_critical",
        "highest_risk_product_count": 1,
        "regulated_or_federal_product_count": 2,
        "requires_hardened_track": True,
        "requires_regulated_track": True,
    }
    assert payload["operator_message"] == (
        "Separate federal or critical products into a hardened track."
    )
    assert payload["recommended_action"] == (
        "define_federal_hardened_product_track"
    )


def test_product_security_portfolio_dashboard_endpoint_route_exists():
    actual_routes = {route.path for route in app.routes}

    assert "/products/security-portfolio/dashboard" in actual_routes


