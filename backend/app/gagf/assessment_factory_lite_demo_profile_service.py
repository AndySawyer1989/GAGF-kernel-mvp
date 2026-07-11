class AssessmentFactoryLiteDemoProfileService:
    """Build the demo profile for the Assessment Factory Lite package."""

    def build_profile(self, checkpoint: dict) -> dict:
        checkpoint = checkpoint or {}

        selected_product = checkpoint.get("selected_product", "none")
        package_name = checkpoint.get("package_name", "No package selected")
        selected_track = checkpoint.get("selected_track", "none")
        go_no_go = checkpoint.get("go_no_go", {})

        return {
            "status": "ok",
            "profile_type": "assessment_factory_lite_demo_profile",
            "selected_product": selected_product,
            "package_name": package_name,
            "selected_track": selected_track,
            "is_assessment_factory_lite": (
                selected_product == "assessment_factory_lite"
            ),
            "demo_readiness": self._demo_readiness(
                selected_product=selected_product,
                selected_track=selected_track,
                go_no_go=go_no_go,
            ),
            "demo_boundary": self._demo_boundary(),
            "demo_inputs": self._demo_inputs(),
            "demo_workflow": self._demo_workflow(),
            "dashboard_sections": self._dashboard_sections(),
            "report_sections": self._report_sections(),
            "success_criteria": self._success_criteria(),
            "excluded_scope": self._excluded_scope(),
            "operator_message": self._operator_message(
                selected_product=selected_product,
                package_name=package_name,
                go_no_go=go_no_go,
            ),
            "recommended_action": self._recommended_action(
                selected_product=selected_product,
                go_no_go=go_no_go,
            ),
        }

    def _demo_readiness(
        self,
        selected_product: str,
        selected_track: str,
        go_no_go: dict,
    ) -> dict:
        is_ready = (
            selected_product == "assessment_factory_lite"
            and selected_track == "fast_productization"
            and go_no_go.get("decision") == "go"
        )

        return {
            "ready_for_demo_package": is_ready,
            "decision": go_no_go.get("decision", "no_go"),
            "reason": go_no_go.get(
                "reason",
                "no_packaging_candidate_available",
            ),
            "requires_customer_data": False,
            "requires_regulated_data": False,
            "requires_federal_data": False,
            "requires_production_access": False,
        }

    def _demo_boundary(self) -> dict:
        return {
            "boundary_type": "demo_only_sample_data",
            "allowed_data": [
                "sample_csv",
                "synthetic_workflow_events",
                "mock_approval_events",
                "mock_delay_events",
            ],
            "allowed_runtime": [
                "local_demo",
                "operator_workstation",
                "non_production_environment",
            ],
            "prohibited_data": [
                "regulated_data",
                "federal_data",
                "production_customer_data",
                "customer_secrets",
                "live_security_telemetry",
            ],
            "certification_claims_allowed": False,
        }

    def _demo_inputs(self) -> list[dict]:
        return [
            {
                "input_name": "sample_csv",
                "description": "Synthetic workflow event CSV.",
                "required": True,
            },
            {
                "input_name": "approval_or_delay_examples",
                "description": "Example approval, delay, blocked, or handoff events.",
                "required": True,
            },
            {
                "input_name": "demo_context",
                "description": "Plain-language scenario context for the operator.",
                "required": False,
            },
        ]

    def _demo_workflow(self) -> list[str]:
        return [
            "load_demo_profile",
            "upload_sample_csv",
            "run_governance_diagnostics",
            "review_governance_drag_summary",
            "review_top_friction_points",
            "display_recommended_intervention",
            "export_demo_summary",
        ]

    def _dashboard_sections(self) -> list[str]:
        return [
            "demo_readiness_card",
            "sample_data_boundary_card",
            "governance_drag_summary",
            "top_friction_points",
            "recommended_intervention",
            "demo_export_status",
        ]

    def _report_sections(self) -> list[str]:
        return [
            "executive_summary",
            "sample_data_boundary",
            "governance_drag_findings",
            "top_constraints",
            "recommended_intervention",
            "next_steps",
            "compliance_disclaimer",
        ]

    def _success_criteria(self) -> list[str]:
        return [
            "demo_profile_loads",
            "sample_csv_boundary_is_enforced",
            "governance_diagnostics_run",
            "friction_summary_is_displayed",
            "recommended_intervention_is_displayed",
            "demo_summary_can_be_exported",
            "no_regulated_or_federal_data_required",
        ]

    def _excluded_scope(self) -> list[str]:
        return [
            "production_customer_data_processing",
            "regulated_data_processing",
            "federal_data_processing",
            "fedramp_or_hipaa_certification_claims",
            "autonomous_remediation",
            "live_customer_integrations",
        ]

    def _operator_message(
        self,
        selected_product: str,
        package_name: str,
        go_no_go: dict,
    ) -> str:
        if (
            selected_product == "assessment_factory_lite"
            and go_no_go.get("decision") == "go"
        ):
            return (
                f"{package_name} is ready to configure as a demo-only "
                "sample-data package."
            )

        return (
            "Assessment Factory Lite demo profile is not ready because the "
            "checkpoint did not select a go decision for assessment_factory_lite."
        )

    def _recommended_action(
        self,
        selected_product: str,
        go_no_go: dict,
    ) -> str:
        if (
            selected_product == "assessment_factory_lite"
            and go_no_go.get("decision") == "go"
        ):
            return "build_assessment_factory_lite_demo"

        return "review_product_packaging_checkpoint"