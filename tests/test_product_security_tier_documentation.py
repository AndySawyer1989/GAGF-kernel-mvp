from pathlib import Path


DOC_PATH = Path("docs/PRODUCT_SECURITY_TIERING.md")


def test_product_security_tier_document_exists():
    assert DOC_PATH.exists()


def test_product_security_tier_document_names_all_tiers():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "tier_1_standard_commercial" in content
    assert "tier_2_enterprise_secure" in content
    assert "tier_3_regulated_sensitive" in content
    assert "tier_4_federal_critical" in content
    assert "Standard Commercial" in content
    assert "Enterprise Secure" in content
    assert "Regulated / Sensitive" in content
    assert "Federal / Critical Infrastructure" in content


def test_product_security_tier_document_names_profile_fields():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "product_name" in content
    assert "product_category" in content
    assert "handles_customer_data" in content
    assert "handles_sensitive_data" in content
    assert "handles_security_telemetry" in content
    assert "handles_health_data" in content
    assert "targets_enterprise" in content
    assert "targets_healthcare" in content
    assert "targets_federal" in content
    assert "requires_air_gap" in content
    assert "requires_on_prem" in content


def test_product_security_tier_document_names_compliance_alignments():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "secure_coding_baseline" in content
    assert "soc_2_readiness" in content
    assert "hipaa_security_rule_alignment" in content
    assert "fedramp_high_alignment" in content
    assert "nist_800_53_alignment" in content


def test_product_security_tier_document_names_required_controls():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "tenant_isolation" in content
    assert "immutable_audit_logging" in content
    assert "minimum_necessary_access" in content
    assert "mutual_tls" in content
    assert "immutable_evidence_ledgers" in content
    assert "supply_chain_risk_management" in content


def test_product_security_tier_document_names_service_and_endpoint():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "ProductSecurityTierService" in content
    assert "POST /products/security-tier" in content
    assert "classification_type" in content
    assert "product_security_tier" in content


def test_product_security_tier_document_names_product_examples():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "Assessment Factory Lite" in content
    assert "FIP Governance Diagnostics SaaS" in content
    assert "FIP Healthcare Readiness Diagnostic" in content
    assert "FIP Secure" in content
    assert "ESY secure runtime" in content


def test_product_security_tier_document_preserves_compliance_boundary():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert (
        "Product Security Tiering does not certify a product as FedRAMP "
        "High, HIPAA compliant, or SOC 2 audited."
    ) in content
    assert (
        "The deterministic GAGF Kernel remains the authoritative decision "
        "and verification layer."
    ) in content






