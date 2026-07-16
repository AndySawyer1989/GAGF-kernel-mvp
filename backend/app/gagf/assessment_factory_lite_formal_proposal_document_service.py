from backend.app.gagf.assessment_factory_lite_proposal_builder_service import (
    AssessmentFactoryLiteProposalBuilderService,
)


class AssessmentFactoryLiteFormalProposalDocumentService:
    """Build a formal proposal document object from a proposal-ready artifact."""

    def __init__(
        self,
        proposal_service: AssessmentFactoryLiteProposalBuilderService | None = None,
    ):
        self.proposal_service = (
            proposal_service or AssessmentFactoryLiteProposalBuilderService()
        )

    def build_document(
        self,
        proposal: dict | None = None,
        offer: dict | None = None,
        buyer_context: dict | None = None,
    ) -> dict:
        source_proposal = proposal or self.proposal_service.build_proposal(
            offer=offer,
            buyer_context=buyer_context,
        )

        return {
            "status": "ok",
            "document_type": "assessment_factory_lite_formal_proposal_document",
            "package_name": "Assessment Factory Lite Demo Package",
            "release": "assessment-factory-lite-proposal-package",
            "version": "2.0.0",
            "document_stage": "formal_proposal_document_draft",
            "document_title": self._document_title(source_proposal),
            "buyer_summary": self._buyer_summary(source_proposal),
            "problem_statement": self._problem_statement(source_proposal),
            "assessment_scope": self._assessment_scope(source_proposal),
            "evidence_boundary": self._evidence_boundary(source_proposal),
            "deliverables": self._deliverables(source_proposal),
            "timeline": self._timeline(source_proposal),
            "commercial_terms": self._commercial_terms(source_proposal),
            "assumptions": self._assumptions(source_proposal),
            "approval_requirements": self._approval_requirements(source_proposal),
            "exclusions": self._exclusions(source_proposal),
            "operator_notes": self._operator_notes(),
            "source_proposal": self._source_proposal(source_proposal),
            "document_sections": self._document_sections(),
            "next_action": self._next_action(),
            "operator_message": (
                "Assessment Factory Lite formal proposal document draft is ready "
                "for operator review."
            ),
            "recommended_action": "review_formal_proposal_document",
        }

    def _document_title(self, proposal: dict) -> str:
        title = proposal.get("proposal_title") or (
            "Assessment Factory Lite Proposal"
        )
        return f"Formal {title}"

    def _buyer_summary(self, proposal: dict) -> dict:
        buyer = proposal.get("buyer_context", {})
        problem = proposal.get("problem_statement", {})

        return {
            "primary_buyer": buyer.get("primary_buyer"),
            "secondary_buyers": buyer.get("secondary_buyers", []),
            "buyer_pain": buyer.get("buyer_pain"),
            "best_fit_context": buyer.get("best_fit_context"),
            "summary": (
                f"This proposal is prepared for {buyer.get('primary_buyer')} "
                f"to assess friction in the {problem.get('workflow_area')}."
            ),
        }

    def _problem_statement(self, proposal: dict) -> dict:
        problem = proposal.get("problem_statement", {})

        return {
            "workflow_area": problem.get("workflow_area"),
            "statement": problem.get("statement"),
            "default_friction_hypothesis": problem.get(
                "default_friction_hypothesis"
            ),
            "buyer_value": problem.get("buyer_value"),
        }

    def _assessment_scope(self, proposal: dict) -> dict:
        scope = proposal.get("proposed_scope", {})

        return {
            "scope_type": scope.get("scope_type"),
            "workflow_area": scope.get("workflow_area"),
            "duration": scope.get("duration"),
            "included_work": scope.get("included_work", []),
            "success_definition": scope.get("success_definition"),
            "scope_boundary": scope.get("scope_boundary"),
        }

    def _evidence_boundary(self, proposal: dict) -> dict:
        evidence = proposal.get("evidence_boundary", {})

        return {
            "request_type": evidence.get("request_type"),
            "requested_sources": evidence.get("requested_sources", []),
            "allowed_format": evidence.get("allowed_format", []),
            "allowed_data": evidence.get("allowed_data", []),
            "prohibited_data": evidence.get("prohibited_data", []),
            "collection_rule": evidence.get("collection_rule"),
            "certification_claims_allowed": evidence.get(
                "certification_claims_allowed",
                False,
            ),
            "binding_price_quote_allowed": evidence.get(
                "binding_price_quote_allowed",
                False,
            ),
        }

    def _deliverables(self, proposal: dict) -> list[dict]:
        return proposal.get("deliverables", [])

    def _timeline(self, proposal: dict) -> dict:
        return proposal.get("timeline", {})

    def _commercial_terms(self, proposal: dict) -> dict:
        terms = proposal.get("commercial_terms_placeholder", {})

        return {
            "pricing_model": terms.get("pricing_model"),
            "currency": terms.get("currency"),
            "recommended_price_band": terms.get("recommended_price_band", {}),
            "payment_terms": terms.get("payment_terms"),
            "proposal_expiration": terms.get("proposal_expiration"),
            "pricing_note": terms.get("pricing_note"),
            "binding_quote": terms.get("binding_quote", False),
            "terms_status": "operator_to_finalize",
        }

    def _assumptions(self, proposal: dict) -> list[str]:
        return proposal.get("assumptions", [])

    def _approval_requirements(self, proposal: dict) -> list[dict]:
        return proposal.get("approval_requirements", [])

    def _exclusions(self, proposal: dict) -> list[str]:
        exclusions = proposal.get("excluded_scope", [])

        required_exclusions = [
            "binding_price_quote",
            "binding_sales_contract",
            "production_service_commitment",
            "legal_or_compliance_certification",
        ]

        return sorted(set(exclusions) | set(required_exclusions))

    def _operator_notes(self) -> list[dict]:
        return [
            {
                "note": "review_scope_before_sending",
                "message": (
                    "Confirm the workflow boundary, included work, and excluded "
                    "scope before sharing with a buyer."
                ),
                "required": True,
            },
            {
                "note": "review_evidence_boundary_before_sending",
                "message": (
                    "Confirm only safe, non-sensitive evidence is requested."
                ),
                "required": True,
            },
            {
                "note": "review_terms_before_sending",
                "message": (
                    "Finalize payment terms, proposal expiration, and pricing "
                    "before buyer delivery."
                ),
                "required": True,
            },
        ]

    def _source_proposal(self, proposal: dict) -> dict:
        return {
            "proposal_type": proposal.get("proposal_type"),
            "proposal_stage": proposal.get("proposal_stage"),
            "release": proposal.get("release"),
            "version": proposal.get("version"),
            "recommended_action": proposal.get("recommended_action"),
        }

    def _document_sections(self) -> list[str]:
        return [
            "document_title",
            "buyer_summary",
            "problem_statement",
            "assessment_scope",
            "evidence_boundary",
            "deliverables",
            "timeline",
            "commercial_terms",
            "assumptions",
            "approval_requirements",
            "exclusions",
            "operator_notes",
            "next_action",
        ]

    def _next_action(self) -> dict:
        return {
            "action": "review_and_finalize_formal_proposal_document",
            "operator_instruction": (
                "Review the formal proposal document draft, finalize commercial "
                "terms, confirm evidence boundaries, and decide whether to export "
                "a buyer-facing document."
            ),
            "future_action": "export_formal_proposal_document",
        }