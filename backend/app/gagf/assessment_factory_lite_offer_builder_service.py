from backend.app.gagf.assessment_factory_lite_buyer_walkthrough_script_service import (
    AssessmentFactoryLiteBuyerWalkthroughScriptService,
)


class AssessmentFactoryLiteOfferBuilderService:
    """Build a bounded paid-assessment offer for Assessment Factory Lite."""

    def __init__(
        self,
        script_service: AssessmentFactoryLiteBuyerWalkthroughScriptService | None = None,
    ):
        self.script_service = script_service or AssessmentFactoryLiteBuyerWalkthroughScriptService()

    def build_offer(
        self,
        buyer_context: dict | None = None,
        walkthrough_script: dict | None = None,
    ) -> dict:
        context = buyer_context or {}
        script = walkthrough_script or self.script_service.build_script()

        target_buyer = self._target_buyer(context)
        problem_statement = self._problem_statement(context)
        safe_evidence_request = self._safe_evidence_request(context)
        assessment_scope = self._assessment_scope(context)
        excluded_scope = self._excluded_scope()
        deliverable = self._deliverable(context)
        recommended_price_band = self._recommended_price_band(context)
        next_action = self._next_action(context)

        return {
            "status": "ok",
            "offer_type": "assessment_factory_lite_paid_assessment_offer",
            "package_name": "Assessment Factory Lite Demo Package",
            "release": "assessment-factory-lite-buyer-conversion",
            "version": "1.8.0",
            "offer_stage": "paid_assessment_conversion",
            "target_buyer": target_buyer,
            "problem_statement": problem_statement,
            "safe_evidence_request": safe_evidence_request,
            "assessment_scope": assessment_scope,
            "excluded_scope": excluded_scope,
            "deliverable": deliverable,
            "recommended_price_band": recommended_price_band,
            "buyer_commitment": self._buyer_commitment(),
            "qualification_questions": self._qualification_questions(script),
            "risk_controls": self._risk_controls(),
            "next_action": next_action,
            "source_script": {
                "script_type": script.get("script_type"),
                "script_stage": script.get("script_stage"),
                "recommended_action": script.get("recommended_action"),
            },
            "demo_boundary": self._demo_boundary(),
            "operator_message": (
                "Assessment Factory Lite paid-assessment offer is ready for "
                "buyer follow-up."
            ),
            "recommended_action": "present_paid_assessment_offer",
        }

    def _target_buyer(self, context: dict) -> dict:
        return {
            "primary_buyer": context.get("primary_buyer", "operations_leader"),
            "secondary_buyers": context.get(
                "secondary_buyers",
                ["it_manager", "workflow_owner", "founder_operator"],
            ),
            "buyer_pain": context.get(
                "buyer_pain",
                "approval delays, ownership gaps, handoff delays, and workflow drag",
            ),
            "best_fit_context": (
                "A team that feels operational delay but needs clearer evidence "
                "before choosing an intervention."
            ),
        }

    def _problem_statement(self, context: dict) -> dict:
        workflow_area = context.get("workflow_area", "approval and handoff workflow")

        return {
            "workflow_area": workflow_area,
            "statement": (
                f"The buyer appears to have friction in the {workflow_area}. "
                "The assessment will identify the highest-friction constraint, "
                "explain its operational impact, and recommend a focused test."
            ),
            "default_friction_hypothesis": "approval_delay",
            "buyer_value": (
                "Move from suspected workflow drag to traceable evidence and a "
                "small intervention candidate."
            ),
        }

    def _safe_evidence_request(self, context: dict) -> dict:
        requested_sources = context.get(
            "requested_sources",
            [
                "sanitized_workflow_export",
                "approval_timestamps",
                "handoff_log",
                "blocked_work_items",
            ],
        )

        return {
            "request_type": "safe_non_sensitive_workflow_evidence",
            "requested_sources": requested_sources,
            "allowed_format": [
                "sanitized_csv",
                "synthetic_sample",
                "redacted_export",
                "manual_summary",
            ],
            "prohibited_data": [
                "real_customer_secrets",
                "regulated_health_data",
                "federal_sensitive_data",
                "credentials",
                "live_security_telemetry",
            ],
            "collection_rule": (
                "Collect the minimum safe evidence needed to diagnose one workflow."
            ),
        }

    def _assessment_scope(self, context: dict) -> dict:
        workflow_area = context.get("workflow_area", "approval and handoff workflow")

        return {
            "scope_type": "bounded_friction_assessment",
            "workflow_area": workflow_area,
            "duration": context.get("duration", "3_to_5_business_days"),
            "included_work": [
                "review_safe_workflow_evidence",
                "validate_sample_or_redacted_rows",
                "identify_top_friction_point",
                "summarize_governance_drag",
                "recommend_one_focused_intervention",
                "prepare_buyer_summary",
            ],
            "success_definition": (
                "Buyer receives one clear friction finding, one evidence-backed "
                "intervention recommendation, and one practical next test."
            ),
        }

    def _excluded_scope(self) -> list[str]:
        return [
            "production_customer_data_processing",
            "regulated_data_processing",
            "federal_data_processing",
            "live_system_integration",
            "autonomous_remediation",
            "security_certification",
            "compliance_audit",
            "soc_2_audit_claims",
            "fedramp_or_hipaa_certification_claims",
            "payment_processing",
            "customer_portal_access",
            "persistent_customer_storage",
            "guaranteed_operational_outcomes",
            "binding_legal_or_compliance_advice",
        ]

    def _deliverable(self, context: dict) -> dict:
        return {
            "deliverable_type": "assessment_factory_lite_buyer_summary",
            "format": context.get("deliverable_format", "markdown_or_pdf_ready_summary"),
            "sections": [
                "executive_summary",
                "evidence_boundary",
                "workflow_friction_finding",
                "top_constraint",
                "recommended_intervention",
                "next_test",
                "excluded_scope",
            ],
            "buyer_value": (
                "A concise evidence-backed summary that can be reviewed with "
                "operations, IT, or workflow owners."
            ),
        }

    def _recommended_price_band(self, context: dict) -> dict:
        return {
            "currency": "USD",
            "low": int(context.get("price_low", 500)),
            "high": int(context.get("price_high", 2500)),
            "pricing_model": "fixed_fee_discovery_assessment",
            "pricing_note": (
                "Final pricing is operator-approved and should not be treated as "
                "an automated binding quote."
            ),
        }

    def _buyer_commitment(self) -> dict:
        return {
            "commitment_type": "small_bounded_assessment",
            "buyer_provides": [
                "one_workflow_to_assess",
                "safe_non_sensitive_evidence",
                "workflow_owner_contact",
                "review_time_for_findings",
            ],
            "operator_provides": [
                "evidence_boundary_review",
                "friction_diagnostic_summary",
                "recommended_intervention",
                "next_test_summary",
            ],
        }

    def _qualification_questions(self, script: dict) -> list[dict]:
        questions = script.get("buyer_questions", [])

        return [
            {
                "question_type": item.get("question_type"),
                "question": item.get("question"),
                "purpose": item.get("purpose"),
                "used_for_offer": item.get("question_type")
                in {
                    "workflow_similarity",
                    "evidence_source",
                    "first_test",
                    "buyer_value",
                },
            }
            for item in questions
        ]

    def _risk_controls(self) -> list[dict]:
        return [
            {
                "control": "sample_or_redacted_data_only",
                "purpose": "keep assessment intake within safe evidence boundaries",
                "required": True,
            },
            {
                "control": "operator_price_approval",
                "purpose": "prevent automated binding pricing commitments",
                "required": True,
            },
            {
                "control": "excluded_scope_visibility",
                "purpose": "make production, compliance, and regulated-data exclusions explicit",
                "required": True,
            },
            {
                "control": "human_review_before_delivery",
                "purpose": "ensure the buyer summary is reviewed before presentation",
                "required": True,
            },
        ]

    def _next_action(self, context: dict) -> dict:
        return {
            "action": "schedule_paid_assessment_conversation",
            "recommended_message": context.get(
                "recommended_message",
                (
                    "Based on the demo, the next step is a small bounded assessment "
                    "focused on one workflow and safe non-sensitive evidence."
                ),
            ),
            "operator_instruction": (
                "Confirm buyer interest, define the workflow boundary, confirm safe "
                "evidence sources, and approve final price before sending the offer."
            ),
        }

    def _demo_boundary(self) -> dict:
        return {
            "boundary_type": "demo_and_assessment_intake_boundary",
            "allowed_data": [
                "sample_csv",
                "synthetic_workflow_events",
                "sanitized_csv",
                "redacted_workflow_export",
                "manual_workflow_summary",
            ],
            "prohibited_data": [
                "real_customer_secrets",
                "regulated_health_data",
                "federal_sensitive_data",
                "production_customer_data_without_review",
                "credentials",
                "live_security_telemetry",
            ],
            "certification_claims_allowed": False,
            "binding_price_quote_allowed": False,
        }