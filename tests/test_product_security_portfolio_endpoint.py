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


def test_product_security_portfolio_endpoint_classifies_products():
    response = client.post(
        "/products/security-portfolio",
        json=build_portfolio_profiles(),
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["status"] == "ok"
    assert payload["classification_type"] == (
        "product_security_portfolio"
    )
    assert payload["product_count"] == 4
    assert len(payload["products"]) == 4


def test_product_security_portfolio_endpoint_counts_security_tiers():
    response = client.post(
        "/products/security-portfolio",
        json=build_portfolio_profiles(),
    )

    payload = response.json()

    assert payload["tier_counts"] == {
        "tier_1_standard_commercial": 1,
        "tier_2_enterprise_secure": 1,
        "tier_3_regulated_sensitive": 1,
        "tier_4_federal_critical": 1,
    }


def test_product_security_portfolio_endpoint_counts_zta_requirements():
    response = client.post(
        "/products/security-portfolio",
        json=build_portfolio_profiles(),
    )

    payload = response.json()

    assert payload["zta_counts"] == {
        "zta_required": 2,
        "zta_recommended": 1,
        "zta_not_required": 1,
    }


def test_product_security_portfolio_endpoint_identifies_productization_tracks():
    response = client.post(
        "/products/security-portfolio",
        json=build_portfolio_profiles(),
    )

    payload = response.json()

    assert payload["highest_security_tier"] == (
        "tier_4_federal_critical"
    )
    assert payload["highest_risk_products"] == ["fip_secure"]
    assert payload["regulated_or_federal_products"] == [
        "fip_healthcare_readiness_diagnostic",
        "fip_secure",
    ]
    assert payload["fastest_productization_candidates"] == [
        "assessment_factory_lite",
        "fip_governance_diagnostics_saas",
    ]


def test_product_security_portfolio_endpoint_route_exists():
    actual_routes = {route.path for route in app.routes}

    assert "/products/security-portfolio" in actual_routes


def test_product_security_portfolio_endpoint_preserves_release_marker():
    response = client.get("/version")

    assert response.status_code == 200
    assert response.json() == {
        "version": "1.8.0",
        "release": "assessment-factory-lite-buyer-conversion",
        "sprint": "4.7",
        "status": "complete",
    }











