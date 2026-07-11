class ProductSecurityTierService:
    def classify_product(self, product_profile: dict) -> dict:
        normalized_profile = self.normalize_profile(product_profile)
        tier = self.determine_tier(normalized_profile)

        return {
            "status": "ok",
            "classification_type": "product_security_tier",
            "product_name": normalized_profile["product_name"],
            "product_category": normalized_profile["product_category"],
            "security_tier": tier,
            "security_tier_label": self.get_tier_label(tier),
            "compliance_alignment": self.get_compliance_alignment(tier),
            "required_controls": self.get_required_controls(tier),
            "deployment_models": self.get_deployment_models(tier),
            "evidence_requirements": self.get_evidence_requirements(tier),
            "recommended_next_action": self.get_recommended_next_action(tier),
            "classification_reason": self.get_classification_reason(
                normalized_profile=normalized_profile,
                tier=tier,
            ),
            "normalized_profile": normalized_profile,
        }

    def normalize_profile(self, product_profile: dict) -> dict:
        return {
            "product_name": self.normalize_string(
                product_profile.get("product_name", "unknown_product")
            ),
            "product_category": self.normalize_string(
                product_profile.get("product_category", "unknown")
            ),
            "handles_customer_data": bool(
                product_profile.get("handles_customer_data", False)
            ),
            "handles_sensitive_data": bool(
                product_profile.get("handles_sensitive_data", False)
            ),
            "handles_security_telemetry": bool(
                product_profile.get("handles_security_telemetry", False)
            ),
            "handles_health_data": bool(
                product_profile.get("handles_health_data", False)
            ),
            "targets_enterprise": bool(
                product_profile.get("targets_enterprise", False)
            ),
            "targets_healthcare": bool(
                product_profile.get("targets_healthcare", False)
            ),
            "targets_federal": bool(
                product_profile.get("targets_federal", False)
            ),
            "requires_air_gap": bool(
                product_profile.get("requires_air_gap", False)
            ),
            "requires_on_prem": bool(
                product_profile.get("requires_on_prem", False)
            ),
            "is_public_demo": bool(
                product_profile.get("is_public_demo", False)
            ),
            "is_internal_only": bool(
                product_profile.get("is_internal_only", False)
            ),
        }

    def determine_tier(self, profile: dict) -> str:
        if (
            profile["targets_federal"]
            or profile["requires_air_gap"]
            or profile["requires_on_prem"]
        ):
            return "tier_4_federal_critical"

        if (
            profile["targets_healthcare"]
            or profile["handles_health_data"]
            or (
                profile["handles_security_telemetry"]
                and profile["handles_sensitive_data"]
            )
        ):
            return "tier_3_regulated_sensitive"

        if (
            profile["targets_enterprise"]
            or profile["handles_customer_data"]
            or profile["handles_sensitive_data"]
            or profile["handles_security_telemetry"]
        ):
            return "tier_2_enterprise_secure"

        return "tier_1_standard_commercial"

    def get_tier_label(self, tier: str) -> str:
        labels = {
            "tier_1_standard_commercial": "Standard Commercial",
            "tier_2_enterprise_secure": "Enterprise Secure",
            "tier_3_regulated_sensitive": "Regulated / Sensitive",
            "tier_4_federal_critical": "Federal / Critical Infrastructure",
        }

        return labels.get(tier, "Unknown")

    def get_compliance_alignment(self, tier: str) -> list[str]:
        alignments = {
            "tier_1_standard_commercial": [
                "secure_coding_baseline",
                "basic_privacy_practices",
            ],
            "tier_2_enterprise_secure": [
                "soc_2_readiness",
                "enterprise_security_baseline",
                "tenant_isolation",
            ],
            "tier_3_regulated_sensitive": [
                "soc_2_readiness",
                "hipaa_security_rule_alignment",
                "enhanced_auditability",
                "data_protection_controls",
            ],
            "tier_4_federal_critical": [
                "fedramp_high_alignment",
                "nist_800_53_alignment",
                "soc_2_readiness",
                "continuous_monitoring",
                "air_gapped_or_private_deployment_readiness",
            ],
        }

        return alignments.get(tier, [])

    def get_required_controls(self, tier: str) -> list[str]:
        controls = {
            "tier_1_standard_commercial": [
                "authentication",
                "basic_authorization",
                "secure_logging",
                "backup_and_recovery",
                "secure_development_practices",
            ],
            "tier_2_enterprise_secure": [
                "role_based_access_control",
                "tenant_isolation",
                "encryption_in_transit",
                "encryption_at_rest",
                "audit_logging",
                "change_management",
                "incident_response",
                "access_lifecycle_management",
            ],
            "tier_3_regulated_sensitive": [
                "role_based_access_control",
                "tenant_isolation",
                "encryption_in_transit",
                "encryption_at_rest",
                "immutable_audit_logging",
                "minimum_necessary_access",
                "risk_analysis",
                "risk_management",
                "incident_response",
                "data_retention_and_disposal",
                "enhanced_access_review",
            ],
            "tier_4_federal_critical": [
                "hardware_backed_authentication",
                "mfa_or_passkeys",
                "mutual_tls",
                "default_deny_access",
                "immutable_evidence_ledgers",
                "strict_tenant_isolation",
                "continuous_monitoring",
                "vulnerability_management",
                "configuration_baselines",
                "incident_response",
                "poam_tracking",
                "supply_chain_risk_management",
                "secure_boot_or_chain_of_trust",
            ],
        }

        return controls.get(tier, [])

    def get_deployment_models(self, tier: str) -> list[str]:
        models = {
            "tier_1_standard_commercial": [
                "public_saas",
                "demo_environment",
            ],
            "tier_2_enterprise_secure": [
                "enterprise_saas",
                "private_tenant_saas",
                "managed_private_cloud",
            ],
            "tier_3_regulated_sensitive": [
                "private_tenant_saas",
                "managed_private_cloud",
                "customer_controlled_environment",
            ],
            "tier_4_federal_critical": [
                "private_cloud",
                "on_prem",
                "air_gapped",
                "government_authorized_cloud",
            ],
        }

        return models.get(tier, [])

    def get_evidence_requirements(self, tier: str) -> list[str]:
        requirements = {
            "tier_1_standard_commercial": [
                "release_marker",
                "test_results",
                "basic_security_log",
            ],
            "tier_2_enterprise_secure": [
                "release_marker",
                "test_results",
                "access_review_evidence",
                "audit_log_export",
                "change_management_record",
                "incident_response_record",
            ],
            "tier_3_regulated_sensitive": [
                "release_marker",
                "test_results",
                "access_review_evidence",
                "immutable_audit_log_export",
                "risk_analysis_record",
                "risk_management_record",
                "data_retention_record",
                "incident_response_record",
                "privacy_boundary_record",
            ],
            "tier_4_federal_critical": [
                "release_marker",
                "test_results",
                "control_mapping_record",
                "continuous_monitoring_record",
                "configuration_baseline_record",
                "vulnerability_scan_record",
                "poam_record",
                "chain_of_trust_record",
                "immutable_evidence_ledger_export",
                "incident_response_record",
                "authorization_boundary_record",
            ],
        }

        return requirements.get(tier, [])

    def get_recommended_next_action(self, tier: str) -> str:
        actions = {
            "tier_1_standard_commercial": (
                "prepare_standard_commercial_launch_checklist"
            ),
            "tier_2_enterprise_secure": (
                "prepare_soc_2_readiness_and_enterprise_security_controls"
            ),
            "tier_3_regulated_sensitive": (
                "prepare_regulated_data_boundary_and_enhanced_controls"
            ),
            "tier_4_federal_critical": (
                "prepare_fedramp_high_or_private_deployment_control_plan"
            ),
        }

        return actions.get(tier, "review_product_security_requirements")

    def get_classification_reason(
        self,
        normalized_profile: dict,
        tier: str,
    ) -> str:
        if tier == "tier_4_federal_critical":
            return (
                "Product requires federal, on-prem, air-gapped, or critical "
                "infrastructure security posture."
            )

        if tier == "tier_3_regulated_sensitive":
            return (
                "Product handles regulated, healthcare, sensitive, or "
                "high-risk security data."
            )

        if tier == "tier_2_enterprise_secure":
            return (
                "Product targets enterprise use or handles customer, "
                "sensitive, or security telemetry data."
            )

        if normalized_profile["is_public_demo"]:
            return (
                "Product appears suitable for standard commercial or demo "
                "security baseline."
            )

        return (
            "Product does not currently require elevated compliance controls."
        )

    def normalize_string(self, value) -> str:
        if value is None:
            return "unknown"

        normalized = str(value).strip().lower().replace(" ", "_")

        return normalized or "unknown"