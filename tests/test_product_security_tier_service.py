from backend.app.gagf.product_security_tier_service import (
    ProductSecurityTierService,
)


def test_product_security_tier_service_classifies_public_demo_as_tier_1():
    service = ProductSecurityTierService()

    result = service.classify_product(
        {
            "product_name": "Assessment Factory Lite",
            "product_category": "demo",
            "is_public_demo": True,
        }
    )

    assert result["status"] == "ok"
    assert result["classification_type"] == "product_security_tier"
    assert result["product_name"] == "assessment_factory_lite"
    assert result["security_tier"] == "tier_1_standard_commercial"
    assert result["security_tier_label"] == "Standard Commercial"
    assert result["recommended_next_action"] == (
        "prepare_standard_commercial_launch_checklist"
    )


def test_product_security_tier_service_classifies_enterprise_saas_as_tier_2():
    service = ProductSecurityTierService()

    result = service.classify_product(
        {
            "product_name": "FIP Governance Diagnostics SaaS",
            "product_category": "governance_diagnostics",
            "targets_enterprise": True,
            "handles_customer_data": True,
        }
    )

    assert result["security_tier"] == "tier_2_enterprise_secure"
    assert result["security_tier_label"] == "Enterprise Secure"
    assert "soc_2_readiness" in result["compliance_alignment"]
    assert "tenant_isolation" in result["required_controls"]
    assert "enterprise_saas" in result["deployment_models"]


def test_product_security_tier_service_classifies_healthcare_as_tier_3():
    service = ProductSecurityTierService()

    result = service.classify_product(
        {
            "product_name": "FIP Healthcare Readiness Diagnostic",
            "product_category": "compliance",
            "targets_healthcare": True,
            "handles_health_data": True,
        }
    )

    assert result["security_tier"] == "tier_3_regulated_sensitive"
    assert result["security_tier_label"] == "Regulated / Sensitive"
    assert "hipaa_security_rule_alignment" in result["compliance_alignment"]
    assert "minimum_necessary_access" in result["required_controls"]
    assert "privacy_boundary_record" in result["evidence_requirements"]


def test_product_security_tier_service_classifies_security_telemetry_sensitive_as_tier_3():
    service = ProductSecurityTierService()

    result = service.classify_product(
        {
            "product_name": "Security Telemetry Diagnostic",
            "product_category": "security",
            "handles_security_telemetry": True,
            "handles_sensitive_data": True,
        }
    )

    assert result["security_tier"] == "tier_3_regulated_sensitive"
    assert result["recommended_next_action"] == (
        "prepare_regulated_data_boundary_and_enhanced_controls"
    )


def test_product_security_tier_service_classifies_federal_or_airgap_as_tier_4():
    service = ProductSecurityTierService()

    result = service.classify_product(
        {
            "product_name": "FIP Secure",
            "product_category": "secure_enterprise",
            "targets_federal": True,
            "requires_air_gap": True,
            "requires_on_prem": True,
        }
    )

    assert result["security_tier"] == "tier_4_federal_critical"
    assert result["security_tier_label"] == (
        "Federal / Critical Infrastructure"
    )
    assert "fedramp_high_alignment" in result["compliance_alignment"]
    assert "mutual_tls" in result["required_controls"]
    assert "air_gapped" in result["deployment_models"]
    assert "authorization_boundary_record" in result["evidence_requirements"]


def test_product_security_tier_service_tier_4_overrides_lower_tiers():
    service = ProductSecurityTierService()

    result = service.classify_product(
        {
            "product_name": "Federal Healthcare Security Product",
            "targets_enterprise": True,
            "targets_healthcare": True,
            "handles_health_data": True,
            "targets_federal": True,
        }
    )

    assert result["security_tier"] == "tier_4_federal_critical"
    assert result["classification_reason"] == (
        "Product requires federal, on-prem, air-gapped, or critical "
        "infrastructure security posture."
    )


def test_product_security_tier_service_normalizes_profile():
    service = ProductSecurityTierService()

    result = service.classify_product(
        {
            "product_name": " Personal Friction Assistant ",
            "product_category": " Personal Productivity ",
            "handles_customer_data": False,
            "is_internal_only": True,
        }
    )

    assert result["normalized_profile"]["product_name"] == (
        "personal_friction_assistant"
    )
    assert result["normalized_profile"]["product_category"] == (
        "personal_productivity"
    )
    assert result["normalized_profile"]["is_internal_only"] is True
