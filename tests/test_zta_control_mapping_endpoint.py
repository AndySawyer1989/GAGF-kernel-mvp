from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def build_product_security_result(
    product_name="fip_governance_diagnostics_saas",
    security_tier="tier_2_enterprise_secure",
):
    return {
        "status": "ok",
        "classification_type": "product_security_tier",
        "product_name": product_name,
        "security_tier": security_tier,
    }


def test_zta_control_mapping_endpoint_maps_tier_1_as_not_required():
    response = client.post(
        "/products/zta-controls",
        json=build_product_security_result(
            product_name="assessment_factory_lite",
            security_tier="tier_1_standard_commercial",
        ),
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["status"] == "ok"
    assert payload["mapping_type"] == "zta_control_mapping"
    assert payload["product_name"] == "assessment_factory_lite"
    assert payload["security_tier"] == "tier_1_standard_commercial"
    assert payload["zta_required"] is False
    assert payload["zta_requirement_level"] == "not_required"
    assert payload["recommended_next_action"] == (
        "apply_standard_security_baseline"
    )


def test_zta_control_mapping_endpoint_maps_tier_2_as_recommended():
    response = client.post(
        "/products/zta-controls",
        json=build_product_security_result(
            security_tier="tier_2_enterprise_secure",
        ),
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["zta_required"] is False
    assert payload["zta_requirement_level"] == "recommended"
    assert "role_based_access_control" in payload["identity_controls"]
    assert "tenant_isolation" in payload["access_enforcement_controls"]
    assert "tenant_boundary_required" in payload["deployment_implications"]
    assert payload["recommended_next_action"] == (
        "evaluate_zero_trust_readiness_for_enterprise_use"
    )


def test_zta_control_mapping_endpoint_requires_zta_for_tier_3():
    response = client.post(
        "/products/zta-controls",
        json=build_product_security_result(
            product_name="fip_healthcare_readiness_diagnostic",
            security_tier="tier_3_regulated_sensitive",
        ),
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["zta_required"] is True
    assert payload["zta_requirement_level"] == "required_regulated"
    assert "strong_identity_boundary" in payload["identity_controls"]
    assert "least_privilege_access" in payload["identity_controls"]
    assert "policy_based_access_control" in (
        payload["access_enforcement_controls"]
    )
    assert "continuous_session_verification" in (
        payload["session_and_device_controls"]
    )
    assert "regulated_data_boundary" in payload["segmentation_controls"]
    assert "minimum_necessary_access_evidence" in (
        payload["telemetry_and_evidence_requirements"]
    )
    assert payload["recommended_next_action"] == (
        "implement_regulated_zero_trust_control_plan"
    )


def test_zta_control_mapping_endpoint_requires_federal_zta_for_tier_4():
    response = client.post(
        "/products/zta-controls",
        json=build_product_security_result(
            product_name="fip_secure",
            security_tier="tier_4_federal_critical",
        ),
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["zta_required"] is True
    assert payload["zta_requirement_level"] == "required_federal_high"
    assert "hardware_backed_identity" in payload["identity_controls"]
    assert "mfa_or_passkeys" in payload["identity_controls"]
    assert "policy_decision_point" in (
        payload["access_enforcement_controls"]
    )
    assert "policy_enforcement_point" in (
        payload["access_enforcement_controls"]
    )
    assert "default_deny_access" in (
        payload["access_enforcement_controls"]
    )
    assert "device_posture_validation" in (
        payload["session_and_device_controls"]
    )
    assert "microsegmentation" in payload["segmentation_controls"]
    assert "immutable_access_evidence" in (
        payload["telemetry_and_evidence_requirements"]
    )
    assert "zta_control_mapping_record" in (
        payload["telemetry_and_evidence_requirements"]
    )
    assert payload["recommended_next_action"] == (
        "implement_federal_zero_trust_architecture_plan"
    )


def test_zta_control_mapping_endpoint_route_exists():
    actual_routes = {route.path for route in app.routes}

    assert "/products/zta-controls" in actual_routes


def test_zta_control_mapping_endpoint_preserves_release_marker():
    response = client.get("/version")

    assert response.status_code == 200
    assert response.json() == {
        "version": "1.2.0",
        "release": "assessment-factory-lite-demo-ui",
        "sprint": "4.1",
        "status": "complete",
    }





