class ZTAControlMappingService:
    def map_product_tier(self, product_security_result: dict) -> dict:
        tier = product_security_result.get(
            "security_tier",
            "tier_1_standard_commercial",
        )

        zta_required = self.zta_required_for_tier(tier)

        return {
            "status": "ok",
            "mapping_type": "zta_control_mapping",
            "product_name": product_security_result.get(
                "product_name",
                "unknown_product",
            ),
            "security_tier": tier,
            "zta_required": zta_required,
            "zta_requirement_level": self.get_requirement_level(tier),
            "identity_controls": self.get_identity_controls(tier),
            "access_enforcement_controls": (
                self.get_access_enforcement_controls(tier)
            ),
            "session_and_device_controls": (
                self.get_session_and_device_controls(tier)
            ),
            "segmentation_controls": self.get_segmentation_controls(tier),
            "telemetry_and_evidence_requirements": (
                self.get_telemetry_and_evidence_requirements(tier)
            ),
            "deployment_implications": self.get_deployment_implications(tier),
            "recommended_next_action": self.get_recommended_next_action(tier),
        }

    def zta_required_for_tier(self, tier: str) -> bool:
        return tier in {
            "tier_3_regulated_sensitive",
            "tier_4_federal_critical",
        }

    def get_requirement_level(self, tier: str) -> str:
        levels = {
            "tier_1_standard_commercial": "not_required",
            "tier_2_enterprise_secure": "recommended",
            "tier_3_regulated_sensitive": "required_regulated",
            "tier_4_federal_critical": "required_federal_high",
        }

        return levels.get(tier, "unknown")

    def get_identity_controls(self, tier: str) -> list[str]:
        if tier == "tier_4_federal_critical":
            return [
                "hardware_backed_identity",
                "mfa_or_passkeys",
                "privileged_access_step_up",
                "strong_service_identity",
                "short_lived_signed_tokens",
                "identity_access_chain_evidence",
            ]

        if tier == "tier_3_regulated_sensitive":
            return [
                "strong_identity_boundary",
                "mfa_or_passkeys",
                "least_privilege_access",
                "role_based_access_control",
                "access_lifecycle_management",
                "identity_access_chain_evidence",
            ]

        if tier == "tier_2_enterprise_secure":
            return [
                "mfa_recommended",
                "role_based_access_control",
                "access_lifecycle_management",
            ]

        return [
            "authentication",
            "basic_authorization",
        ]

    def get_access_enforcement_controls(self, tier: str) -> list[str]:
        if tier == "tier_4_federal_critical":
            return [
                "policy_decision_point",
                "policy_enforcement_point",
                "default_deny_access",
                "continuous_policy_evaluation",
                "mutual_tls",
                "privileged_action_approval",
                "tenant_isolation_enforcement",
            ]

        if tier == "tier_3_regulated_sensitive":
            return [
                "policy_based_access_control",
                "least_privilege_access",
                "continuous_session_verification",
                "tenant_isolation_enforcement",
                "minimum_necessary_access",
                "sensitive_action_approval",
            ]

        if tier == "tier_2_enterprise_secure":
            return [
                "role_based_access_control",
                "tenant_isolation",
                "audit_logging",
            ]

        return [
            "basic_authorization",
        ]

    def get_session_and_device_controls(self, tier: str) -> list[str]:
        if tier == "tier_4_federal_critical":
            return [
                "device_posture_validation",
                "continuous_verification",
                "session_risk_scoring",
                "short_session_lifetime",
                "managed_device_requirement",
                "privileged_session_recording",
            ]

        if tier == "tier_3_regulated_sensitive":
            return [
                "device_trust_evaluation",
                "continuous_session_verification",
                "session_timeout",
                "risk_based_reauthentication",
            ]

        if tier == "tier_2_enterprise_secure":
            return [
                "session_timeout",
                "risk_based_reauthentication_recommended",
            ]

        return [
            "standard_session_management",
        ]

    def get_segmentation_controls(self, tier: str) -> list[str]:
        if tier == "tier_4_federal_critical":
            return [
                "microsegmentation",
                "network_policy_enforcement",
                "workload_identity_segmentation",
                "tenant_boundary_segmentation",
                "environment_boundary_enforcement",
            ]

        if tier == "tier_3_regulated_sensitive":
            return [
                "tenant_boundary_segmentation",
                "regulated_data_boundary",
                "environment_boundary_enforcement",
            ]

        if tier == "tier_2_enterprise_secure":
            return [
                "tenant_isolation",
                "environment_separation",
            ]

        return [
            "basic_environment_separation",
        ]

    def get_telemetry_and_evidence_requirements(self, tier: str) -> list[str]:
        if tier == "tier_4_federal_critical":
            return [
                "immutable_access_evidence",
                "policy_decision_evidence",
                "policy_enforcement_evidence",
                "device_posture_evidence",
                "privileged_access_evidence",
                "mutual_tls_session_evidence",
                "continuous_monitoring_record",
                "zta_control_mapping_record",
            ]

        if tier == "tier_3_regulated_sensitive":
            return [
                "audit_evidence_for_access_decisions",
                "identity_access_chain_evidence",
                "session_verification_evidence",
                "regulated_data_access_evidence",
                "minimum_necessary_access_evidence",
                "zta_control_mapping_record",
            ]

        if tier == "tier_2_enterprise_secure":
            return [
                "access_review_evidence",
                "audit_log_export",
                "tenant_access_evidence",
            ]

        return [
            "basic_security_log",
        ]

    def get_deployment_implications(self, tier: str) -> list[str]:
        if tier == "tier_4_federal_critical":
            return [
                "private_cloud_or_on_prem_preferred",
                "air_gapped_supported_when_required",
                "government_authorized_cloud_supported",
                "strict_control_boundary_required",
                "continuous_monitoring_required",
            ]

        if tier == "tier_3_regulated_sensitive":
            return [
                "private_tenant_saas_preferred",
                "customer_controlled_environment_supported",
                "regulated_data_boundary_required",
                "enhanced_audit_boundary_required",
            ]

        if tier == "tier_2_enterprise_secure":
            return [
                "enterprise_saas_supported",
                "private_tenant_saas_supported",
                "tenant_boundary_required",
            ]

        return [
            "public_saas_or_demo_environment_supported",
        ]

    def get_recommended_next_action(self, tier: str) -> str:
        actions = {
            "tier_1_standard_commercial": (
                "apply_standard_security_baseline"
            ),
            "tier_2_enterprise_secure": (
                "evaluate_zero_trust_readiness_for_enterprise_use"
            ),
            "tier_3_regulated_sensitive": (
                "implement_regulated_zero_trust_control_plan"
            ),
            "tier_4_federal_critical": (
                "implement_federal_zero_trust_architecture_plan"
            ),
        }

        return actions.get(tier, "review_zero_trust_requirements")