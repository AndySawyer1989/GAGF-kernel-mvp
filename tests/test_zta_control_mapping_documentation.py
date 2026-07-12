from pathlib import Path


DOC_PATH = Path("docs/ZTA_CONTROL_MAPPING.md")


def test_zta_control_mapping_document_exists():
    assert DOC_PATH.exists()


def test_zta_control_mapping_document_names_requirement_levels():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "not_required" in content
    assert "recommended" in content
    assert "required_regulated" in content
    assert "required_federal_high" in content


def test_zta_control_mapping_document_names_tier_3_controls():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "tier_3_regulated_sensitive" in content
    assert "strong_identity_boundary" in content
    assert "least_privilege_access" in content
    assert "policy_based_access_control" in content
    assert "continuous_session_verification" in content
    assert "regulated_data_boundary" in content
    assert "minimum_necessary_access_evidence" in content


def test_zta_control_mapping_document_names_tier_4_controls():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "tier_4_federal_critical" in content
    assert "hardware_backed_identity" in content
    assert "policy_decision_point" in content
    assert "policy_enforcement_point" in content
    assert "default_deny_access" in content
    assert "mutual_tls" in content
    assert "device_posture_validation" in content
    assert "microsegmentation" in content
    assert "immutable_access_evidence" in content


def test_zta_control_mapping_document_names_service_and_endpoint():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "ZTAControlMappingService" in content
    assert "POST /products/zta-controls" in content
    assert "mapping_type" in content
    assert "zta_required" in content
    assert "zta_requirement_level" in content


def test_zta_control_mapping_document_names_product_examples():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "Assessment Factory Lite" in content
    assert "FIP Governance Diagnostics SaaS" in content
    assert "FIP Healthcare Readiness Diagnostic" in content
    assert "FIP Secure" in content
    assert "ESY secure runtime" in content


def test_zta_control_mapping_document_preserves_compliance_boundary():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert (
        "ZTA Control Mapping does not certify a product as FedRAMP High, "
        "HIPAA compliant, or SOC 2 audited."
    ) in content
    assert (
        "The deterministic GAGF Kernel remains the authoritative decision "
        "and verification layer."
    ) in content

