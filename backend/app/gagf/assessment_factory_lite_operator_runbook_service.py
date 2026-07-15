class AssessmentFactoryLiteOperatorRunbookService:
    """Build the live-demo operator runbook for Assessment Factory Lite."""

    def build_runbook(self) -> dict:
        return {
            "status": "ok",
            "runbook_type": "assessment_factory_lite_demo_operator_runbook",
            "package_name": "Assessment Factory Lite Demo Package",
            "release": "assessment-factory-lite-demo-styling-export",
            "version": "1.6.0",
            "runbook_stage": "demo_delivery_packaging",
            "runbook_summary": self._runbook_summary(),
            "pre_demo_checklist": self._pre_demo_checklist(),
            "live_demo_sequence": self._live_demo_sequence(),
            "scenario_talking_points": self._scenario_talking_points(),
            "operator_safety_rules": self._operator_safety_rules(),
            "stop_conditions": self._stop_conditions(),
            "buyer_follow_up": self._buyer_follow_up(),
            "success_criteria": self._success_criteria(),
            "demo_boundary": self._demo_boundary(),
            "operator_message": (
                "Assessment Factory Lite operator runbook is ready for "
                "repeatable live demo delivery."
            ),
            "recommended_action": "use_operator_runbook_for_demo_delivery",
        }

    def _runbook_summary(self) -> dict:
        return {
            "purpose": (
                "Guide the operator through a repeatable Assessment Factory "
                "Lite demo using synthetic sample data only."
            ),
            "primary_operator": "founder_operator",
            "target_audience": [
                "operations_leader",
                "it_manager",
                "workflow_owner",
                "early_buyer",
            ],
            "delivery_mode": "live_walkthrough",
            "estimated_duration": "10_to_20_minutes",
            "positioning": (
                "Show how FIP identifies operational friction, explains the "
                "top constraint, recommends a focused intervention, and "
                "presents buyer-ready findings."
            ),
        }

    def _pre_demo_checklist(self) -> list[dict]:
        return [
            {
                "check": "version_endpoint_ready",
                "instruction": "Confirm the system version endpoint responds successfully.",
                "expected": "1.6.0 assessment-factory-lite-demo-styling-export",
                "required": True,
            },
            {
                "check": "delivery_manifest_available",
                "instruction": "Open the delivery manifest before the walkthrough.",
                "expected": "delivery manifest returns status ok",
                "required": True,
            },
            {
                "check": "scenario_menu_available",
                "instruction": "Confirm the scenario menu shows standard, invalid, and empty choices.",
                "expected": "three primary scenarios are visible",
                "required": True,
            },
            {
                "check": "styled_html_screen_available",
                "instruction": "Render the standard scenario in the HTML screen.",
                "expected": "styled screen includes Demo Scenario Menu and Sample Data Loader",
                "required": True,
            },
            {
                "check": "buyer_export_polish_available",
                "instruction": "Generate polished buyer export copy from the standard sample rows.",
                "expected": "buyer export polish returns present_polished_buyer_export",
                "required": True,
            },
            {
                "check": "demo_boundary_visible",
                "instruction": "Confirm the demo-only sample-data boundary is visible.",
                "expected": "real customer, regulated, and federal data are prohibited",
                "required": True,
            },
        ]

    def _live_demo_sequence(self) -> list[dict]:
        return [
            {
                "step": 1,
                "title": "Open with the problem",
                "operator_action": "Explain that the demo identifies where work gets stuck.",
                "buyer_message": (
                    "This demo shows how workflow evidence can reveal operational "
                    "drag and suggest what to test first."
                ),
                "endpoint_or_asset": "delivery_manifest",
            },
            {
                "step": 2,
                "title": "Show the scenario menu",
                "operator_action": "Show the standard, invalid, and empty scenario choices.",
                "buyer_message": (
                    "The demo uses synthetic scenarios so we can show the workflow "
                    "without touching real customer data."
                ),
                "endpoint_or_asset": "GET /products/assessment-factory-lite/demo-scenario-menu",
            },
            {
                "step": 3,
                "title": "Load the standard demo",
                "operator_action": "Render the standard sample_scenario in the HTML screen.",
                "buyer_message": (
                    "The standard scenario demonstrates approval delay and blocked work."
                ),
                "endpoint_or_asset": "POST /products/assessment-factory-lite/demo-ui/html",
            },
            {
                "step": 4,
                "title": "Explain the finding",
                "operator_action": "Point to the top friction finding and recommended intervention.",
                "buyer_message": (
                    "The system turns sample workflow events into a clear friction "
                    "finding and a focused next step."
                ),
                "endpoint_or_asset": "styled_html_screen",
            },
            {
                "step": 5,
                "title": "Show buyer export polish",
                "operator_action": "Show the polished buyer-facing export summary.",
                "buyer_message": (
                    "This turns the diagnostic output into language that is easier "
                    "for a buyer or manager to act on."
                ),
                "endpoint_or_asset": "POST /products/assessment-factory-lite/buyer-export/polish",
            },
            {
                "step": 6,
                "title": "Show boundary protection",
                "operator_action": "Demonstrate or explain the invalid boundary test.",
                "buyer_message": (
                    "Unsafe rows are rejected before buyer-facing findings are generated."
                ),
                "endpoint_or_asset": "invalid_boundary_test",
            },
            {
                "step": 7,
                "title": "Close with next evidence question",
                "operator_action": "Ask whether the sample friction resembles the buyer's workflow.",
                "buyer_message": (
                    "If this resembles your workflow, the next step is deciding what "
                    "safe evidence we would collect first."
                ),
                "endpoint_or_asset": "buyer_follow_up",
            },
        ]

    def _scenario_talking_points(self) -> list[dict]:
        return [
            {
                "scenario": "standard",
                "label": "Approval Delay and Blocked Work",
                "when_to_use": "default buyer demo",
                "operator_talk_track": (
                    "Use this scenario to show the core value: finding approval "
                    "drag and recommending a focused intervention."
                ),
                "expected_message": "Approval delays are creating workflow drag.",
                "recommended_intervention": "streamline_approval_path",
            },
            {
                "scenario": "invalid",
                "label": "Unsafe Data Boundary Test",
                "when_to_use": "trust and safety explanation",
                "operator_talk_track": (
                    "Use this scenario to show that unsafe or non-demo data is "
                    "blocked before findings are presented."
                ),
                "expected_message": "Sample data needs repair before buyer presentation.",
                "recommended_intervention": "repair_sample_csv_before_demo",
            },
            {
                "scenario": "empty",
                "label": "Empty Demo Starting State",
                "when_to_use": "screen initialization explanation",
                "operator_talk_track": (
                    "Use this scenario to show the starting state before demo rows "
                    "are loaded."
                ),
                "expected_message": "Add synthetic sample rows before running the demo.",
                "recommended_intervention": "add_demo_rows",
            },
        ]

    def _operator_safety_rules(self) -> list[dict]:
        return [
            {
                "rule": "use_sample_data_only",
                "instruction": "Do not use real customer, regulated, federal, or secret data.",
                "severity": "critical",
            },
            {
                "rule": "avoid_certification_claims",
                "instruction": (
                    "Do not claim FedRAMP High, HIPAA, SOC 2, WCAG, or production readiness."
                ),
                "severity": "critical",
            },
            {
                "rule": "do_not_overstate_automation",
                "instruction": (
                    "Do not say the demo autonomously remediates customer workflows."
                ),
                "severity": "high",
            },
            {
                "rule": "preserve_traceability",
                "instruction": (
                    "Keep polished buyer language tied to the source export summary."
                ),
                "severity": "high",
            },
            {
                "rule": "ask_for_workflow_similarity",
                "instruction": (
                    "Ask whether the sample scenario resembles the buyer's real workflow "
                    "before proposing next evidence collection."
                ),
                "severity": "medium",
            },
        ]

    def _stop_conditions(self) -> list[dict]:
        return [
            {
                "condition": "buyer_requests_real_data_upload",
                "operator_response": (
                    "Pause and explain that this demo is sample-data-only."
                ),
                "required_action": "do_not_accept_real_customer_data",
            },
            {
                "condition": "regulated_or_federal_data_is_offered",
                "operator_response": (
                    "Stop the demo data flow and restate the prohibited data boundary."
                ),
                "required_action": "reject_regulated_or_federal_data",
            },
            {
                "condition": "certification_claim_requested",
                "operator_response": (
                    "Clarify that this demo does not make compliance certification claims."
                ),
                "required_action": "avoid_certification_claim",
            },
            {
                "condition": "unsafe_sample_rows_detected",
                "operator_response": (
                    "Use the invalid scenario behavior to show boundary rejection."
                ),
                "required_action": "repair_sample_csv_before_demo",
            },
        ]

    def _buyer_follow_up(self) -> list[dict]:
        return [
            {
                "follow_up": "workflow_similarity_question",
                "prompt": (
                    "Which part of this sample workflow most resembles where your team gets stuck?"
                ),
                "purpose": "connect demo finding to buyer context",
            },
            {
                "follow_up": "evidence_source_question",
                "prompt": (
                    "What safe, non-sensitive workflow evidence could we inspect first?"
                ),
                "purpose": "identify possible assessment inputs",
            },
            {
                "follow_up": "first_intervention_question",
                "prompt": (
                    "If approval delay is the issue, what is the smallest approval-path test worth trying?"
                ),
                "purpose": "move toward a paid assessment or pilot",
            },
        ]

    def _success_criteria(self) -> list[str]:
        return [
            "operator_can_explain_problem_in_plain_language",
            "scenario_menu_is_visible",
            "standard_demo_renders_successfully",
            "buyer_understands_top_friction_point",
            "buyer_export_polish_is_presented",
            "demo_boundary_is_explained",
            "buyer_identifies_possible_real_workflow_parallel",
            "no_real_customer_data_is_used",
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