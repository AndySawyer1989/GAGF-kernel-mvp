class AssessmentFactoryLiteBuyerWalkthroughScriptService:
    """Build the buyer-facing walkthrough script for Assessment Factory Lite."""

    def build_script(self) -> dict:
        return {
            "status": "ok",
            "script_type": "assessment_factory_lite_buyer_walkthrough_script",
            "package_name": "Assessment Factory Lite Demo Package",
            "release": "assessment-factory-lite-demo-delivery-packaging",
            "version": "1.7.0",
            "script_stage": "buyer_demo_conversion",
            "script_summary": self._script_summary(),
            "opening_script": self._opening_script(),
            "problem_frame": self._problem_frame(),
            "scenario_script": self._scenario_script(),
            "finding_script": self._finding_script(),
            "intervention_script": self._intervention_script(),
            "boundary_script": self._boundary_script(),
            "buyer_questions": self._buyer_questions(),
            "close_script": self._close_script(),
            "objection_responses": self._objection_responses(),
            "success_criteria": self._success_criteria(),
            "demo_boundary": self._demo_boundary(),
            "operator_message": (
                "Assessment Factory Lite buyer walkthrough script is ready "
                "for repeatable buyer-facing demo conversations."
            ),
            "recommended_action": "use_buyer_walkthrough_script",
        }

    def _script_summary(self) -> dict:
        return {
            "purpose": (
                "Give the operator a plain-language buyer-facing script for "
                "presenting the Assessment Factory Lite demo."
            ),
            "primary_operator": "founder_operator",
            "target_audience": [
                "operations_leader",
                "it_manager",
                "workflow_owner",
                "early_buyer",
            ],
            "delivery_mode": "guided_buyer_walkthrough",
            "estimated_duration": "10_to_20_minutes",
            "conversion_goal": "move_from_demo_interest_to_paid_assessment_conversation",
            "positioning": (
                "Assessment Factory Lite shows where work gets stuck, why it "
                "creates drag, and what small operational test to try first."
            ),
        }

    def _opening_script(self) -> dict:
        return {
            "section": "opening",
            "title": "Open with operational friction",
            "operator_script": (
                "This is a sample-data-only demo of Assessment Factory Lite. "
                "The goal is to show how workflow evidence can reveal where "
                "work gets stuck, explain the top source of drag, and suggest "
                "a focused intervention to test first."
            ),
            "buyer_takeaway": (
                "The buyer should understand that the product diagnoses workflow "
                "drag without needing production data for the demo."
            ),
            "duration": "1_to_2_minutes",
        }

    def _problem_frame(self) -> dict:
        return {
            "section": "problem_frame",
            "title": "Frame the buyer problem",
            "operator_script": (
                "Most teams feel delays before they can prove them. Work waits "
                "on approvals, ownership, dependencies, or unclear handoffs. "
                "Assessment Factory Lite turns those workflow signals into a "
                "clear friction finding."
            ),
            "buyer_takeaway": (
                "The demo is about making hidden operational drag visible."
            ),
            "proof_point": "sample workflow events become a ranked friction finding",
        }

    def _scenario_script(self) -> list[dict]:
        return [
            {
                "scenario": "standard",
                "label": "Approval Delay and Blocked Work",
                "when_to_use": "default_buyer_demo",
                "operator_script": (
                    "I will start with the standard scenario. It uses synthetic "
                    "workflow rows showing approval delay and blocked work. "
                    "This lets us demonstrate the diagnostic flow safely."
                ),
                "buyer_takeaway": (
                    "Approval delay can be detected from workflow evidence."
                ),
                "expected_friction": "approval_delay",
            },
            {
                "scenario": "invalid",
                "label": "Unsafe Data Boundary Test",
                "when_to_use": "trust_and_safety_explanation",
                "operator_script": (
                    "This scenario intentionally contains unsafe sample rows. "
                    "The system rejects them before producing buyer-facing findings."
                ),
                "buyer_takeaway": (
                    "The demo protects the sample-data-only boundary."
                ),
                "expected_friction": "none",
            },
            {
                "scenario": "empty",
                "label": "Empty Demo Starting State",
                "when_to_use": "screen_initialization_explanation",
                "operator_script": (
                    "This scenario shows the empty starting state before sample "
                    "rows are loaded."
                ),
                "buyer_takeaway": (
                    "The operator can show the demo state before evidence is added."
                ),
                "expected_friction": "none",
            },
        ]

    def _finding_script(self) -> dict:
        return {
            "section": "finding",
            "title": "Explain the top friction finding",
            "operator_script": (
                "In this sample scenario, the top friction point is approval delay. "
                "That means the workflow is not mainly blocked by execution effort; "
                "it is slowed by waiting for a required decision or approval path."
            ),
            "buyer_takeaway": (
                "The buyer should see that the product identifies the constraint, "
                "not just the symptoms."
            ),
            "example_finding": "Approval delays are creating workflow drag.",
            "evidence_link": "synthetic approval and blocked-work events",
        }

    def _intervention_script(self) -> dict:
        return {
            "section": "intervention",
            "title": "Explain the recommended intervention",
            "operator_script": (
                "The recommended intervention is to streamline the approval path. "
                "That does not mean removing accountability. It means testing a "
                "narrow improvement such as clearer ownership, faster routing, "
                "or a smaller approval threshold."
            ),
            "buyer_takeaway": (
                "The product moves from diagnosis to a practical next test."
            ),
            "recommended_intervention": "streamline_approval_path",
            "buyer_value": "reduce waiting time and make approval ownership clearer",
        }

    def _boundary_script(self) -> dict:
        return {
            "section": "boundary",
            "title": "Explain the demo-only boundary",
            "operator_script": (
                "This demo uses synthetic sample data only. We should not upload "
                "real customer data, regulated data, federal data, secrets, or live "
                "security telemetry into this demo path."
            ),
            "buyer_takeaway": (
                "The buyer should trust that the demo does not require sensitive data."
            ),
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
        }

    def _buyer_questions(self) -> list[dict]:
        return [
            {
                "question_type": "workflow_similarity",
                "question": (
                    "Which part of this sample workflow most resembles where "
                    "your team gets stuck?"
                ),
                "purpose": "connect the demo to the buyer's real workflow",
            },
            {
                "question_type": "evidence_source",
                "question": (
                    "What safe, non-sensitive workflow evidence could we inspect first?"
                ),
                "purpose": "identify possible assessment inputs",
            },
            {
                "question_type": "first_test",
                "question": (
                    "If approval delay is the issue, what is the smallest "
                    "approval-path test worth trying?"
                ),
                "purpose": "move toward a focused assessment or pilot",
            },
            {
                "question_type": "buyer_value",
                "question": (
                    "If we could show your top workflow constraint clearly, "
                    "who would need to see that result?"
                ),
                "purpose": "identify stakeholders and buying path",
            },
        ]

    def _close_script(self) -> dict:
        return {
            "section": "close",
            "title": "Close with the assessment offer",
            "operator_script": (
                "The next step would not be a big deployment. It would be a small, "
                "bounded assessment using safe evidence to identify one or two "
                "high-friction workflow constraints and recommend a focused test."
            ),
            "buyer_takeaway": (
                "The buyer should understand the next step as low-risk, bounded, "
                "and evidence-driven."
            ),
            "call_to_action": "schedule_paid_assessment_conversation",
        }

    def _objection_responses(self) -> list[dict]:
        return [
            {
                "objection": "we_do_not_want_to_upload_sensitive_data",
                "response": (
                    "That is the right concern. This demo is sample-data-only, "
                    "and a real assessment should start by defining safe evidence "
                    "boundaries before any data is reviewed."
                ),
            },
            {
                "objection": "we_already_know_where_the_problem_is",
                "response": (
                    "That may be true. The value here is turning that belief into "
                    "traceable evidence, ranking the constraint, and choosing the "
                    "smallest useful intervention."
                ),
            },
            {
                "objection": "this_looks_like_project_management",
                "response": (
                    "Project management tracks work. Assessment Factory Lite focuses "
                    "on governance friction: approvals, ownership gaps, handoffs, "
                    "dependencies, and decision delays."
                ),
            },
            {
                "objection": "is_this_production_ready",
                "response": (
                    "This package is a sample-data-only buyer demo. Production use, "
                    "regulated data, compliance claims, and live integrations are "
                    "outside this demo boundary."
                ),
            },
        ]

    def _success_criteria(self) -> list[str]:
        return [
            "buyer_understands_sample_data_only_boundary",
            "buyer_understands_operational_friction_problem",
            "buyer_understands_standard_scenario",
            "buyer_understands_top_friction_finding",
            "buyer_understands_recommended_intervention",
            "buyer_identifies_workflow_similarity",
            "buyer_can_name_possible_safe_evidence_source",
            "operator_can_transition_to_assessment_offer",
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