from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def test_product_security_tier_endpoint_classifies_public_demo_as_tier_1():
    response = client.post(
        "/products/security-tier",
        json={
            "product_name": "Assessment Factory Lite",
            "product_category": "demo",
            "is_public_demo": True,
        },
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["status"] == "ok"
    assert payload["classification_type"] == "product_security_tier"
    assert payload["product_name"] == "assessment_factory_lite"
    assert payload["security_tier"] == "tier_1_standard_commercial"
    assert payload["security_tier_label"] == "Standard Commercial"
    assert payload["recommended_next_action"] == (
        "prepare_standard_commercial_launch_checklist"
    )


def test_product_security_tier_endpoint_classifies_enterprise_saas_as_tier_2():
    response = client.post(
        "/products/security-tier",
        json={
            "product_name": "FIP Governance Diagnostics SaaS",
            "product_category": "governance_diagnostics",
            "targets_enterprise": True,
            "handles_customer_data": True,
        },
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["security_tier"] == "tier_2_enterprise_secure"
    assert payload["security_tier_label"] == "Enterprise Secure"
    assert "soc_2_readiness" in payload["compliance_alignment"]
    assert "tenant_isolation" in payload["required_controls"]
    assert "enterprise_saas" in payload["deployment_models"]


def test_product_security_tier_endpoint_classifies_healthcare_as_tier_3():
    response = client.post(
        "/products/security-tier",
        json={
            "product_name": "FIP Healthcare Readiness Diagnostic",
            "product_category": "compliance",
            "targets_healthcare": True,
            "handles_health_data": True,
        },
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["security_tier"] == "tier_3_regulated_sensitive"
    assert payload["security_tier_label"] == "Regulated / Sensitive"
    assert "hipaa_security_rule_alignment" in payload[
        "compliance_alignment"
    ]
    assert "minimum_necessary_access" in payload["required_controls"]
    assert "privacy_boundary_record" in payload["evidence_requirements"]


def test_product_security_tier_endpoint_classifies_fip_secure_as_tier_4():
    response = client.post(
        "/products/security-tier",
        json={
            "product_name": "FIP Secure",
            "product_category": "secure_enterprise",
            "targets_federal": True,
            "requires_air_gap": True,
            "requires_on_prem": True,
        },
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["security_tier"] == "tier_4_federal_critical"
    assert payload["security_tier_label"] == (
        "Federal / Critical Infrastructure"
    )
    assert "fedramp_high_alignment" in payload["compliance_alignment"]
    assert "mutual_tls" in payload["required_controls"]
    assert "air_gapped" in payload["deployment_models"]
    assert "authorization_boundary_record" in payload[
        "evidence_requirements"
    ]


def test_product_security_tier_endpoint_route_exists():
    actual_routes = {route.path for route in app.routes}

    assert "/products/security-tier" in actual_routes


def test_product_security_tier_endpoint_preserves_release_marker():
    response = client.get("/version")

    assert response.status_code == 200
    assert response.json() == {
        "version": "1.2.0",
        "release": "assessment-factory-lite-demo-ui",
        "sprint": "4.1",
        "status": "complete",
    }




