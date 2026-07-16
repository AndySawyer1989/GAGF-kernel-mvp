from backend.app.gagf.assessment_factory_lite_offer_builder_service import (
    AssessmentFactoryLiteOfferBuilderService,
)


class AssessmentFactoryLiteProposalBuilderService:
    """Build a proposal-ready artifact from an Assessment Factory Lite offer."""

    def __init__(
        self,
        offer_service: AssessmentFactoryLiteOfferBuilderService | None = None,
    ):
        self.offer_service = offer_service or AssessmentFactoryLiteOfferBuilderService()

    def build_proposal(
        self,
        offer: dict | None = None,
        buyer_context: dict | None = None,
    ) -> dict:
        source_offer = offer or self.offer_service.build_offer(
            buyer_context=buyer_context
        )

        return {
            "status": "ok",
            "proposal_type": "assessment_factory_lite_paid_assessment_proposal",
            "package_name": "Assessment Factory Lite Demo Package",
            "release": "assessment-factory-lite-commercial-offer",
            "version": "1.9.0",
            "proposal_stage": "proposal_ready_artifact",
            "proposal_title": self._proposal_title(source_offer),
            "buyer_context": self._buyer_context(source_offer),
            "problem_statement": self._problem_statement(source_offer),
            "proposed_scope": self._proposed_scope(source_offer),
            "evidence_boundary": self._evidence_boundary(source_offer),
            "deliverables": self._deliverables(source_offer),
            "timeline": self._timeline(source_offer),
            "commercial_terms_placeholder": self._commercial_terms_placeholder(
                source_offer
            ),
            "excluded_scope": self._excluded_scope(source_offer),
            "assumptions": self._assumptions(),
            "approval_requirements": self._approval_requirements(),
            "proposal_risk_controls": self._proposal_risk_controls(),
            "source_offer": self._source_offer(source_offer),
            "next_action": self._next_action(),
            "operator_message": (
                "Assessment Factory Lite proposal-ready artifact is ready for "
                "operator review."
            ),
            "recommended_action": "review_proposal_ready_artifact",
        }

    def _proposal_title(self, offer: dict) -> str:
        workflow_area = offer.get("problem_statement", {}).get(
            "workflow_area",
            "workflow",
        )

        return f"Assessment Factory Lite Proposal for {workflow_area}"

    def _buyer_context(self, offer: dict) -> dict:
        target_buyer = offer.get("target_buyer", {})

        return {
            "primary_buyer": target_buyer.get("primary_buyer"),
            "secondary_buyers": target_buyer.get("secondary_buyers", []),
            "buyer_pain": target_buyer.get("buyer_pain"),
            "best_fit_context": target_buyer.get("best_fit_context"),
        }

    def _problem_statement(self, offer: dict) -> dict:
        problem = offer.get("problem_statement", {})

        return {
            "workflow_area": problem.get("workflow_area"),
            "statement": problem.get("statement"),
            "default_friction_hypothesis": problem.get(
                "default_friction_hypothesis"
            ),
            "buyer_value": problem.get("buyer_value"),
        }

    def _proposed_scope(self, offer: dict) -> dict:
        scope = offer.get("assessment_scope", {})

        return {
            "scope_type": scope.get("scope_type"),
            "workflow_area": scope.get("workflow_area"),
            "duration": scope.get("duration"),
            "included_work": scope.get("included_work", []),
            "success_definition": scope.get("success_definition"),
            "scope_boundary": (
                "This proposal covers one bounded workflow assessment using "
                "safe, non-sensitive evidence only."
            ),
        }

    def _evidence_boundary(self, offer: dict) -> dict:
        evidence = offer.get("safe_evidence_request", {})
        boundary = offer.get("demo_boundary", {})

        return {
            "request_type": evidence.get("request_type"),
            "requested_sources": evidence.get("requested_sources", []),
            "allowed_format": evidence.get("allowed_format", []),
            "allowed_data": boundary.get("allowed_data", []),
            "prohibited_data": sorted(
                set(evidence.get("prohibited_data", []))
                | set(boundary.get("prohibited_data", []))
            ),
            "collection_rule": evidence.get("collection_rule"),
            "certification_claims_allowed": boundary.get(
                "certification_claims_allowed",
                False,
            ),
            "binding_price_quote_allowed": boundary.get(
                "binding_price_quote_allowed",
                False,
            ),
        }

    def _deliverables(self, offer: dict) -> list[dict]:
        deliverable = offer.get("deliverable", {})

        return [
            {
                "deliverable": "assessment_summary",
                "format": deliverable.get("format"),
                "sections": deliverable.get("sections", []),
                "buyer_value": deliverable.get("buyer_value"),
            },
            {
                "deliverable": "recommended_next_test",
                "format": "short_action_plan",
                "sections": [
                    "top_constraint",
                    "recommended_intervention",
                    "next_test",
                    "owner_or_stakeholder",
                ],
                "buyer_value": (
                    "A practical next-step plan that the buyer can review with "
                    "operations, IT, or workflow owners."
                ),
            },
        ]

    def _timeline(self, offer: dict) -> dict:
        scope = offer.get("assessment_scope", {})

        return {
            "estimated_duration": scope.get("duration", "3_to_5_business_days"),
            "phases": [
                {
                    "phase": "intake",
                    "description": "Confirm workflow boundary and safe evidence sources.",
                },
                {
                    "phase": "evidence_review",
                    "description": "Review sample, sanitized, or redacted workflow evidence.",
                },
                {
                    "phase": "diagnostic_summary",
                    "description": "Identify the top friction point and governance drag.",
                },
                {
                    "phase": "recommendation_review",
                    "description": "Review recommended intervention and next test.",
                },
            ],
        }

    def _commercial_terms_placeholder(self, offer: dict) -> dict:
        price = offer.get("recommended_price_band", {})

        return {
            "pricing_model": price.get("pricing_model"),
            "currency": price.get("currency"),
            "recommended_price_band": {
                "low": price.get("low"),
                "high": price.get("high"),
            },
            "payment_terms": "operator_to_define",
            "proposal_expiration": "operator_to_define",
            "pricing_note": price.get("pricing_note"),
            "binding_quote": False,
        }

    def _excluded_scope(self, offer: dict) -> list[str]:
        return offer.get("excluded_scope", [])

    def _assumptions(self) -> list[str]:
        return [
            "buyer_selects_one_workflow_for_assessment",
            "buyer_provides_safe_non_sensitive_evidence_only",
            "operator_reviews_evidence_boundary_before_analysis",
            "assessment_output_is_reviewed_before_buyer_delivery",
            "final_price_and_terms_are_operator_approved",
        ]

    def _approval_requirements(self) -> list[dict]:
        return [
            {
                "approval": "evidence_boundary_approval",
                "required_by": "operator",
                "purpose": "confirm proposed evidence is safe for assessment intake",
                "required": True,
            },
            {
                "approval": "commercial_terms_approval",
                "required_by": "operator",
                "purpose": "confirm final price, scope, and payment terms",
                "required": True,
            },
            {
                "approval": "buyer_scope_acknowledgement",
                "required_by": "buyer",
                "purpose": "confirm workflow boundary and excluded scope",
                "required": True,
            },
        ]

    def _proposal_risk_controls(self) -> list[dict]:
        return [
            {
                "control": "non_binding_proposal_until_operator_approval",
                "purpose": "prevent automated commitment to pricing or terms",
                "required": True,
            },
            {
                "control": "safe_evidence_boundary_required",
                "purpose": "prevent regulated, federal, secret, or live telemetry intake",
                "required": True,
            },
            {
                "control": "excluded_scope_must_be_visible",
                "purpose": "make production, compliance, and legal exclusions clear",
                "required": True,
            },
            {
                "control": "human_review_before_sending",
                "purpose": "ensure proposal language is reviewed before buyer delivery",
                "required": True,
            },
        ]

    def _source_offer(self, offer: dict) -> dict:
        return {
            "offer_type": offer.get("offer_type"),
            "offer_stage": offer.get("offer_stage"),
            "release": offer.get("release"),
            "version": offer.get("version"),
            "recommended_action": offer.get("recommended_action"),
        }

    def _next_action(self) -> dict:
        return {
            "action": "review_and_prepare_proposal",
            "operator_instruction": (
                "Review the proposal-ready artifact, confirm evidence boundary, "
                "approve commercial terms, and decide whether to generate a formal "
                "proposal document."
            ),
            "future_action": "generate_formal_proposal",
        }