class AssessmentFactoryLiteDeliveryManifestService:
    """Build the delivery manifest for the Assessment Factory Lite demo package."""

    def build_manifest(self) -> dict:
        return {
            "status": "ok",
            "manifest_type": "assessment_factory_lite_demo_delivery_manifest",
            "package_name": "Assessment Factory Lite Demo Package",
            "release": "assessment-factory-lite-demo-styling-export",
            "version": "1.6.0",
            "delivery_stage": "demo_delivery_packaging",
            "package_summary": self._package_summary(),
            "included_capabilities": self._included_capabilities(),
            "included_endpoints": self._included_endpoints(),
            "included_documents": self._included_documents(),
            "operator_assets": self._operator_assets(),
            "buyer_demo_assets": self._buyer_demo_assets(),
            "delivery_inputs": self._delivery_inputs(),
            "delivery_outputs": self._delivery_outputs(),
            "excluded_scope": self._excluded_scope(),
            "demo_boundary": self._demo_boundary(),
            "readiness_inputs": self._readiness_inputs(),
            "operator_message": (
                "Assessment Factory Lite delivery manifest is ready for "
                "operator packaging."
            ),
            "recommended_action": "prepare_demo_delivery_package",
        }

    def _package_summary(self) -> dict:
        return {
            "purpose": (
                "Package the Assessment Factory Lite demo into a repeatable "
                "delivery unit for discovery calls and early buyer walkthroughs."
            ),
            "primary_audience": [
                "founder_operator",
                "operations_leader",
                "it_manager",
                "workflow_owner",
            ],
            "delivery_mode": "sample_data_only_demo",
            "commercial_use": "early_buyer_discovery_and_paid_assessment_setup",
            "positioning": (
                "A sample-data-only operational friction diagnostic demo that "
                "shows where work gets stuck and what to test first."
            ),
        }

    def _included_capabilities(self) -> list[dict]:
        return [
            {
                "capability": "sample_rows",
                "description": "Provides canned synthetic workflow rows.",
                "status": "included",
            },
            {
                "capability": "scenario_menu",
                "description": "Provides UI-ready scenario choices.",
                "status": "included",
            },
            {
                "capability": "dataset_contract_validation",
                "description": "Rejects unsafe or invalid demo rows.",
                "status": "included",
            },
            {
                "capability": "demo_diagnostics",
                "description": "Finds friction in accepted sample rows.",
                "status": "included",
            },
            {
                "capability": "styled_html_screen",
                "description": "Renders the Operator Workstation demo screen.",
                "status": "included",
            },
            {
                "capability": "buyer_export_polish",
                "description": "Creates buyer-facing findings and next steps.",
                "status": "included",
            },
        ]

    def _included_endpoints(self) -> list[dict]:
        return [
            {
                "method": "GET",
                "path": "/products/assessment-factory-lite/demo-samples/rows",
                "purpose": "Load default sample rows.",
            },
            {
                "method": "GET",
                "path": "/products/assessment-factory-lite/demo-samples/rows/{scenario}",
                "purpose": "Load sample rows for a named scenario.",
            },
            {
                "method": "GET",
                "path": "/products/assessment-factory-lite/demo-scenario-menu",
                "purpose": "Fetch UI-ready scenario menu items.",
            },
            {
                "method": "GET",
                "path": "/products/assessment-factory-lite/demo-style-tokens",
                "purpose": "Fetch deterministic buyer-facing style tokens.",
            },
            {
                "method": "POST",
                "path": "/products/assessment-factory-lite/demo-ui/html",
                "purpose": "Render the styled demo HTML screen.",
            },
            {
                "method": "POST",
                "path": "/products/assessment-factory-lite/buyer-export/polish",
                "purpose": "Generate polished buyer-facing export copy.",
            },
        ]

    def _included_documents(self) -> list[str]:
        return [
            "ASSESSMENT_FACTORY_LITE_DEMO_PACKAGE_CLOSEOUT.md",
            "ASSESSMENT_FACTORY_LITE_DEMO_SCREEN_CLOSEOUT.md",
            "ASSESSMENT_FACTORY_LITE_DEMO_LOADER_CLOSEOUT.md",
            "ASSESSMENT_FACTORY_LITE_DEMO_USABILITY_CLOSEOUT.md",
            "ASSESSMENT_FACTORY_LITE_DEMO_STYLING_EXPORT_CLOSEOUT.md",
            "ASSESSMENT_FACTORY_LITE_DEMO_SAMPLE_ROWS.md",
            "ASSESSMENT_FACTORY_LITE_DEMO_SCENARIO_MENU.md",
            "ASSESSMENT_FACTORY_LITE_DEMO_STYLE_TOKENS.md",
            "ASSESSMENT_FACTORY_LITE_BUYER_EXPORT_POLISH.md",
        ]

    def _operator_assets(self) -> list[dict]:
        return [
            {
                "asset": "scenario_menu",
                "purpose": "Let the operator choose standard, invalid, or empty scenarios.",
                "required": True,
            },
            {
                "asset": "sample_loader",
                "purpose": "Load canned sample rows into the visible demo screen.",
                "required": True,
            },
            {
                "asset": "styled_html_screen",
                "purpose": "Show a buyer-readable Operator Workstation screen.",
                "required": True,
            },
            {
                "asset": "buyer_export_polish",
                "purpose": "Present clearer buyer-facing findings and next steps.",
                "required": True,
            },
        ]

    def _buyer_demo_assets(self) -> list[dict]:
        return [
            {
                "asset": "standard_demo_scenario",
                "label": "Approval Delay and Blocked Work",
                "buyer_value": "Shows how approval delays create workflow drag.",
            },
            {
                "asset": "invalid_boundary_test",
                "label": "Unsafe Data Boundary Test",
                "buyer_value": "Shows that unsafe rows are rejected before findings are shown.",
            },
            {
                "asset": "empty_starting_state",
                "label": "Empty Demo Starting State",
                "buyer_value": "Shows the screen before sample rows are loaded.",
            },
            {
                "asset": "polished_buyer_export",
                "label": "Buyer-Facing Export Preview",
                "buyer_value": "Shows findings, intervention, next steps, and safety boundary.",
            },
        ]

    def _delivery_inputs(self) -> list[str]:
        return [
            "sample_scenario",
            "synthetic_rows",
            "diagnostics_result",
            "export_summary",
            "include_scenario_menu",
            "include_style_tokens",
        ]

    def _delivery_outputs(self) -> list[str]:
        return [
            "scenario_menu",
            "sample_rows_result",
            "styled_html",
            "buyer_headline",
            "buyer_summary",
            "key_findings",
            "recommended_intervention",
            "next_steps",
            "trust_and_boundary_note",
        ]

    def _excluded_scope(self) -> list[str]:
        return [
            "production_customer_data_processing",
            "regulated_data_processing",
            "federal_data_processing",
            "fedramp_or_hipaa_certification_claims",
            "soc_2_audit_claims",
            "wcag_certification_claims",
            "autonomous_remediation",
            "live_customer_integrations",
            "production_customer_deployment",
            "formal_security_authorization",
            "third_party_audit_claims",
            "persistent_file_upload_storage",
            "customer_tenant_storage",
            "pdf_generation",
            "payment_processing",
        ]

    def _demo_boundary(self) -> dict:
        return {
            "boundary_type": "demo_only_sample_data",
            "allowed_data": [
                "sample_csv",
                "synthetic_workflow_events",
                "mock_approval_events",
                "mock_delay_events",
            ],
            "prohibited_data": [
                "real_customer_data",
                "regulated_data",
                "federal_data",
                "production_customer_data",
                "customer_secrets",
                "live_security_telemetry",
            ],
            "certification_claims_allowed": False,
        }

    def _readiness_inputs(self) -> list[dict]:
        return [
            {
                "check": "sample_rows_available",
                "required": True,
                "reason": "The demo needs canned rows for repeatable walkthroughs.",
            },
            {
                "check": "scenario_menu_available",
                "required": True,
                "reason": "The operator needs visible scenario choices.",
            },
            {
                "check": "styled_html_available",
                "required": True,
                "reason": "The buyer needs a polished visible screen.",
            },
            {
                "check": "buyer_export_polish_available",
                "required": True,
                "reason": "The buyer needs clear findings and next steps.",
            },
            {
                "check": "demo_boundary_visible",
                "required": True,
                "reason": "The operator must keep the demo inside sample-data-only limits.",
            },
        ]