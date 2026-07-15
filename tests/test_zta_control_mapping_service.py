from backend.app.gagf.zta_control_mapping_service import (
    ZTAControlMappingService,
)


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


def test_zta_control_mapping_service_marks_tier_1_as_not_required():
    service = ZTAControlMappingService()

    result = service.map_product_tier(
        build_product_security_result(
            product_name="assessment_factory_lite",
            security_tier="tier_1_standard_commercial",
        )
    )

    assert result["status"] == "ok"
    assert result["mapping_type"] == "zta_control_mapping"
    assert result["product_name"] == "assessment_factory_lite"
    assert result["security_tier"] == "tier_1_standard_commercial"
    assert result["zta_required"] is False
    assert result["zta_requirement_level"] == "not_required"
    assert result["recommended_next_action"] == (
        "apply_standard_security_baseline"
    )


def test_zta_control_mapping_service_marks_tier_2_as_recommended():
    service = ZTAControlMappingService()

    result = service.map_product_tier(
        build_product_security_result(
            security_tier="tier_2_enterprise_secure",
        )
    )

    assert result["zta_required"] is False
    assert result["zta_requirement_level"] == "recommended"
    assert "role_based_access_control" in result["identity_controls"]
    assert "tenant_isolation" in result["access_enforcement_controls"]
    assert "tenant_boundary_required" in result["deployment_implications"]
    assert result["recommended_next_action"] == (
        "evaluate_zero_trust_readiness_for_enterprise_use"
    )


def test_zta_control_mapping_service_requires_zta_for_tier_3():
    service = ZTAControlMappingService()

    result = service.map_product_tier(
        build_product_security_result(
            product_name="fip_healthcare_readiness_diagnostic",
            security_tier="tier_3_regulated_sensitive",
        )
    )

    assert result["zta_required"] is True
    assert result["zta_requirement_level"] == "required_regulated"
    assert "strong_identity_boundary" in result["identity_controls"]
    assert "least_privilege_access" in result["identity_controls"]
    assert "policy_based_access_control" in (
        result["access_enforcement_controls"]
    )
    assert "continuous_session_verification" in (
        result["session_and_device_controls"]
    )
    assert "regulated_data_boundary" in result["segmentation_controls"]
    assert "minimum_necessary_access_evidence" in (
        result["telemetry_and_evidence_requirements"]
    )
    assert result["recommended_next_action"] == (
        "implement_regulated_zero_trust_control_plan"
    )


def test_zta_control_mapping_service_requires_federal_zta_for_tier_4():
    service = ZTAControlMappingService()

    result = service.map_product_tier(
        build_product_security_result(
            product_name="fip_secure",
            security_tier="tier_4_federal_critical",
        )
    )

    assert result["zta_required"] is True
    assert result["zta_requirement_level"] == "required_federal_high"
    assert "hardware_backed_identity" in result["identity_controls"]
    assert "mfa_or_passkeys" in result["identity_controls"]
    assert "policy_decision_point" in (
        result["access_enforcement_controls"]
    )
    assert "policy_enforcement_point" in (
        result["access_enforcement_controls"]
    )
    assert "default_deny_access" in (
        result["access_enforcement_controls"]
    )
    assert "device_posture_validation" in (
        result["session_and_device_controls"]
    )
    assert "microsegmentation" in result["segmentation_controls"]
    assert "immutable_access_evidence" in (
        result["telemetry_and_evidence_requirements"]
    )
    assert "zta_control_mapping_record" in (
        result["telemetry_and_evidence_requirements"]
    )
    assert result["recommended_next_action"] == (
        "implement_federal_zero_trust_architecture_plan"
    )


def test_zta_control_mapping_service_maps_tier_3_deployment_implications():
    service = ZTAControlMappingService()

    result = service.map_product_tier(
        build_product_security_result(
            security_tier="tier_3_regulated_sensitive",
        )
    )

    assert result["deployment_implications"] == [
        "private_tenant_saas_preferred",
        "customer_controlled_environment_supported",
        "regulated_data_boundary_required",
        "enhanced_audit_boundary_required",
    ]


def test_zta_control_mapping_service_maps_tier_4_deployment_implications():
    service = ZTAControlMappingService()

    result = service.map_product_tier(
        build_product_security_result(
            security_tier="tier_4_federal_critical",
        )
    )

    assert result["deployment_implications"] == [
        "private_cloud_or_on_prem_preferred",
        "air_gapped_supported_when_required",
        "government_authorized_cloud_supported",
        "strict_control_boundary_required",
        "continuous_monitoring_required",
    ]


def test_zta_control_mapping_service_defaults_unknown_to_tier_1_behavior():
    service = ZTAControlMappingService()

    result = service.map_product_tier({})

    assert result["product_name"] == "unknown_product"
    assert result["security_tier"] == "tier_1_standard_commercial"
    assert result["zta_required"] is False
    assert result["zta_requirement_level"] == "not_required"
    assert result["identity_controls"] == [
        "authentication",
        "basic_authorization",
    ]





