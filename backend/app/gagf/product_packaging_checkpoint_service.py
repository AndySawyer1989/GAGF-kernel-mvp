class ProductPackagingCheckpointService:
    """Convert packaging dashboard output into a product packaging checkpoint."""

    def build_checkpoint(self, packaging_dashboard: dict) -> dict:
        dashboard = packaging_dashboard or {}

        first_candidate_card = dashboard.get(
            "first_candidate_card",
            {
                "product_name": "none",
                "track": "none",
                "reason": "no_packaging_candidate_available",
                "is_available": False,
            },
        )

        product_name = first_candidate_card.get("product_name", "none")
        track = first_candidate_card.get("track", "none")
        recommended_action = dashboard.get(
            "recommended_action",
            "add_product_candidates",
        )
        blocker_summary = dashboard.get("blocker_summary", {})

        return {
            "status": "ok",
            "checkpoint_type": "product_packaging_checkpoint",
            "selected_product": product_name,
            "selected_track": track,
            "package_name": self._package_name(product_name, track),
            "buyer_profile": self._buyer_profile(product_name, track),
            "minimum_deliverable": self._minimum_deliverable(
                product_name,
                track,
            ),
            "demo_workflow": self._demo_workflow(product_name, track),
            "revenue_hypothesis": self._revenue_hypothesis(
                product_name,
                track,
            ),
            "build_boundary": self._build_boundary(track),
            "security_boundary": self._security_boundary(
                track,
                blocker_summary,
            ),
            "go_no_go": self._go_no_go(
                first_candidate_card=first_candidate_card,
                blocker_summary=blocker_summary,
            ),
            "recommended_action": recommended_action,
            "operator_message": self._operator_message(
                product_name=product_name,
                track=track,
                recommended_action=recommended_action,
            ),
        }

    def _package_name(self, product_name: str, track: str) -> str:
        if product_name == "assessment_factory_lite":
            return "Assessment Factory Lite Demo Package"

        if track == "enterprise_ready":
            return "Enterprise Governance Diagnostics Pilot Package"

        if track == "regulated_boundary":
            return "Regulated Readiness Boundary Package"

        if track == "hardened_federal":
            return "Federal Hardened Readiness Package"

        if product_name == "none":
            return "No package selected"

        return f"{product_name} Package"

    def _buyer_profile(self, product_name: str, track: str) -> dict:
        if product_name == "assessment_factory_lite":
            return {
                "buyer_type": "small_to_mid_size_operations_leader",
                "economic_buyer": "founder_operations_lead_or_it_manager",
                "user": "operator_or_process_owner",
                "primary_pain": "approval_delay_and_operational_drag",
                "sales_motion": "demo_first_consultative_sale",
            }

        if track == "enterprise_ready":
            return {
                "buyer_type": "enterprise_governance_or_security_leader",
                "economic_buyer": "director_or_vp_operations_security_or_it",
                "user": "governance_operator",
                "primary_pain": "cross_team_governance_debt",
                "sales_motion": "enterprise_pilot",
            }

        if track == "regulated_boundary":
            return {
                "buyer_type": "regulated_compliance_or_risk_leader",
                "economic_buyer": "compliance_risk_or_security_director",
                "user": "compliance_operator",
                "primary_pain": "regulated_process_friction_and_audit_readiness",
                "sales_motion": "readiness_assessment",
            }

        if track == "hardened_federal":
            return {
                "buyer_type": "federal_or_critical_infrastructure_leader",
                "economic_buyer": "program_manager_or_security_authorizing_official",
                "user": "secure_operations_operator",
                "primary_pain": "high_assurance_governance_and_control_evidence",
                "sales_motion": "hardened_private_engagement",
            }

        return {
            "buyer_type": "unknown",
            "economic_buyer": "unknown",
            "user": "unknown",
            "primary_pain": "unknown",
            "sales_motion": "review_required",
        }

    def _minimum_deliverable(self, product_name: str, track: str) -> dict:
        if product_name == "assessment_factory_lite":
            return {
                "deliverable_type": "demo_assessment",
                "inputs": [
                    "sample_csv",
                    "workflow_events",
                    "approval_or_delay_examples",
                ],
                "outputs": [
                    "governance_drag_summary",
                    "top_friction_points",
                    "simple_recommendation_report",
                    "operator_dashboard_view",
                ],
                "success_criteria": [
                    "loads_sample_data",
                    "detects_friction",
                    "shows_recommendation",
                    "produces_demo_ready_summary",
                ],
            }

        if track == "enterprise_ready":
            return {
                "deliverable_type": "enterprise_pilot",
                "inputs": [
                    "customer_workflow_export",
                    "jira_or_servicenow_events",
                    "team_metadata",
                ],
                "outputs": [
                    "enterprise_governance_diagnostics",
                    "security_tier_summary",
                    "zta_readiness_review",
                ],
                "success_criteria": [
                    "maps_enterprise_events",
                    "separates_security_tiers",
                    "shows_portfolio_recommendation",
                ],
            }

        if track == "regulated_boundary":
            return {
                "deliverable_type": "regulated_boundary_assessment",
                "inputs": [
                    "regulated_workflow_sample",
                    "data_boundary_notes",
                    "compliance_constraints",
                ],
                "outputs": [
                    "regulated_boundary_summary",
                    "security_control_gap_summary",
                    "zta_required_controls",
                ],
                "success_criteria": [
                    "defines_compliance_boundary",
                    "identifies_required_controls",
                    "does_not_claim_certification",
                ],
            }

        if track == "hardened_federal":
            return {
                "deliverable_type": "hardened_readiness_assessment",
                "inputs": [
                    "federal_or_secure_workflow_sample",
                    "authorization_boundary_notes",
                    "control_requirements",
                ],
                "outputs": [
                    "hardened_track_summary",
                    "fedramp_high_alignment_notes",
                    "zta_control_map",
                ],
                "success_criteria": [
                    "defines_hardened_boundary",
                    "identifies_zero_trust_requirements",
                    "does_not_claim_authorization",
                ],
            }

        return {
            "deliverable_type": "none",
            "inputs": [],
            "outputs": [],
            "success_criteria": [],
        }

    def _demo_workflow(self, product_name: str, track: str) -> list[str]:
        if product_name == "assessment_factory_lite":
            return [
                "upload_sample_csv",
                "run_governance_diagnostics",
                "review_friction_summary",
                "show_top_constraints",
                "display_recommended_intervention",
                "export_demo_summary",
            ]

        if track == "enterprise_ready":
            return [
                "ingest_enterprise_workflow_sample",
                "classify_product_security_tier",
                "show_governance_diagnostics",
                "show_zta_readiness_review",
                "present_enterprise_pilot_scope",
            ]

        if track == "regulated_boundary":
            return [
                "define_regulated_data_boundary",
                "classify_security_tier",
                "map_zta_controls",
                "identify_audit_evidence_requirements",
                "present_boundary_readiness_summary",
            ]

        if track == "hardened_federal":
            return [
                "define_authorization_boundary",
                "classify_federal_security_tier",
                "map_federal_zta_controls",
                "identify_hardened_deployment_requirements",
                "present_hardened_track_summary",
            ]

        return []

    def _revenue_hypothesis(self, product_name: str, track: str) -> dict:
        if product_name == "assessment_factory_lite":
            return {
                "pricing_motion": "fixed_fee_demo_assessment",
                "starter_price_hypothesis": "$500-$2500",
                "expansion_path": "governance_diagnostics_saas_or_consulting",
                "time_to_value": "same_day_to_one_week",
            }

        if track == "enterprise_ready":
            return {
                "pricing_motion": "paid_enterprise_pilot",
                "starter_price_hypothesis": "$5000-$25000",
                "expansion_path": "enterprise_subscription_or_private_tenant",
                "time_to_value": "two_to_six_weeks",
            }

        if track == "regulated_boundary":
            return {
                "pricing_motion": "regulated_readiness_assessment",
                "starter_price_hypothesis": "$10000-$50000",
                "expansion_path": "regulated_saas_or_private_deployment",
                "time_to_value": "four_to_eight_weeks",
            }

        if track == "hardened_federal":
            return {
                "pricing_motion": "hardened_private_engagement",
                "starter_price_hypothesis": "$25000+",
                "expansion_path": "federal_secure_deployment",
                "time_to_value": "multi_month",
            }

        return {
            "pricing_motion": "none",
            "starter_price_hypothesis": "none",
            "expansion_path": "none",
            "time_to_value": "unknown",
        }

    def _build_boundary(self, track: str) -> dict:
        if track == "fast_productization":
            return {
                "scope": "demo_only",
                "allowed": [
                    "sample_data",
                    "local_demo",
                    "operator_dashboard",
                    "summary_report",
                ],
                "excluded": [
                    "regulated_data",
                    "production_customer_data",
                    "federal_data",
                    "autonomous_actions",
                ],
            }

        if track == "enterprise_ready":
            return {
                "scope": "enterprise_pilot",
                "allowed": [
                    "customer_approved_exports",
                    "enterprise_security_review",
                    "tenant_isolation_review",
                ],
                "excluded": [
                    "regulated_health_data_without_boundary",
                    "federal_data_without_hardened_track",
                ],
            }

        if track == "regulated_boundary":
            return {
                "scope": "compliance_boundary_definition",
                "allowed": [
                    "deidentified_samples",
                    "control_mapping",
                    "audit_evidence_planning",
                ],
                "excluded": [
                    "unbounded_health_data",
                    "certification_claims",
                    "production_access_without_controls",
                ],
            }

        if track == "hardened_federal":
            return {
                "scope": "hardened_boundary_definition",
                "allowed": [
                    "authorization_boundary_planning",
                    "zta_control_mapping",
                    "private_deployment_design",
                ],
                "excluded": [
                    "production_federal_data_without_authorization",
                    "fedramp_certification_claims",
                    "uncontrolled_public_saas",
                ],
            }

        return {
            "scope": "none",
            "allowed": [],
            "excluded": [],
        }

    def _security_boundary(
        self,
        track: str,
        blocker_summary: dict,
    ) -> dict:
        return {
            "has_packaging_blocker": blocker_summary.get(
                "has_packaging_blocker",
                False,
            ),
            "has_federal_blocker": blocker_summary.get(
                "has_federal_blocker",
                False,
            ),
            "has_regulated_blocker": blocker_summary.get(
                "has_regulated_blocker",
                False,
            ),
            "has_zta_blocker": blocker_summary.get("has_zta_blocker", False),
            "boundary_required_before_launch": track
            in {
                "regulated_boundary",
                "hardened_federal",
            },
            "certification_claims_allowed": False,
        }

    def _go_no_go(
        self,
        first_candidate_card: dict,
        blocker_summary: dict,
    ) -> dict:
        is_available = first_candidate_card.get("is_available", False)
        track = first_candidate_card.get("track", "none")

        if not is_available:
            return {
                "decision": "no_go",
                "reason": "no_packaging_candidate_available",
            }

        if track == "fast_productization":
            return {
                "decision": "go",
                "reason": "fast_demo_candidate_available",
            }

        if track == "enterprise_ready":
            return {
                "decision": "conditional_go",
                "reason": "enterprise_security_review_required",
            }

        if blocker_summary.get("has_packaging_blocker", False):
            return {
                "decision": "no_go",
                "reason": "security_boundary_required_before_packaging",
            }

        return {
            "decision": "review",
            "reason": "manual_product_packaging_review_required",
        }

    def _operator_message(
        self,
        product_name: str,
        track: str,
        recommended_action: str,
    ) -> str:
        if product_name == "none":
            return "No product is ready for packaging."

        if track == "fast_productization":
            return (
                f"Proceed with {product_name} as the first demo or "
                f"early-revenue package. Next action: {recommended_action}."
            )

        if track == "enterprise_ready":
            return (
                f"Proceed conditionally with {product_name} as an enterprise "
                f"pilot. Next action: {recommended_action}."
            )

        if track == "regulated_boundary":
            return (
                f"Do not package {product_name} until the regulated boundary "
                f"is defined. Next action: {recommended_action}."
            )

        if track == "hardened_federal":
            return (
                f"Do not package {product_name} until the hardened federal "
                f"security boundary is defined. Next action: "
                f"{recommended_action}."
            )

        return f"Review packaging path for {product_name}."