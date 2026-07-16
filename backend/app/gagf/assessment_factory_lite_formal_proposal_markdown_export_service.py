from backend.app.gagf.assessment_factory_lite_formal_proposal_document_service import (
    AssessmentFactoryLiteFormalProposalDocumentService,
)


class AssessmentFactoryLiteFormalProposalMarkdownExportService:
    """Render a formal proposal document object as deterministic Markdown."""

    def __init__(
        self,
        document_service: AssessmentFactoryLiteFormalProposalDocumentService | None = None,
    ):
        self.document_service = (
            document_service or AssessmentFactoryLiteFormalProposalDocumentService()
        )

    def export_markdown(
        self,
        document: dict | None = None,
        proposal: dict | None = None,
        offer: dict | None = None,
        buyer_context: dict | None = None,
    ) -> dict:
        source_document = document or self.document_service.build_document(
            proposal=proposal,
            offer=offer,
            buyer_context=buyer_context,
        )

        markdown = self._build_markdown(source_document)

        return {
            "status": "ok",
            "export_type": "assessment_factory_lite_formal_proposal_markdown_export",
            "package_name": "Assessment Factory Lite Demo Package",
            "release": "assessment-factory-lite-proposal-package",
            "version": "2.0.0",
            "export_stage": "formal_proposal_markdown_export",
            "format": "markdown",
            "filename": self._filename(source_document),
            "markdown": markdown,
            "source_document": self._source_document(source_document),
            "export_sections": self._export_sections(),
            "operator_message": (
                "Assessment Factory Lite formal proposal Markdown export is "
                "ready for operator review."
            ),
            "recommended_action": "review_formal_proposal_markdown_export",
        }

    def _filename(self, document: dict) -> str:
        title = document.get("document_title", "assessment-factory-lite-proposal")
        slug = (
            title.lower()
            .replace("formal ", "")
            .replace("assessment factory lite proposal for ", "")
            .replace(" ", "-")
            .replace("_", "-")
        )
        slug = "".join(ch for ch in slug if ch.isalnum() or ch == "-")
        slug = "-".join(part for part in slug.split("-") if part)

        return f"assessment-factory-lite-proposal-{slug or 'workflow'}.md"

    def _build_markdown(self, document: dict) -> str:
        sections = [
            f"# {document.get('document_title', 'Assessment Factory Lite Proposal')}",
            self._metadata(document),
            self._buyer_summary(document),
            self._problem_statement(document),
            self._assessment_scope(document),
            self._evidence_boundary(document),
            self._deliverables(document),
            self._timeline(document),
            self._commercial_terms(document),
            self._assumptions(document),
            self._approval_requirements(document),
            self._exclusions(document),
            self._operator_notes(document),
            self._next_action(document),
            self._boundary_notice(),
        ]

        return "\n\n".join(section.strip() for section in sections if section.strip())

    def _metadata(self, document: dict) -> str:
        return "\n".join(
            [
                "## Proposal Metadata",
                "",
                f"- Document type: {document.get('document_type')}",
                f"- Package: {document.get('package_name')}",
                f"- Release: {document.get('release')}",
                f"- Version: {document.get('version')}",
                f"- Stage: {document.get('document_stage')}",
                f"- Recommended action: {document.get('recommended_action')}",
            ]
        )

    def _buyer_summary(self, document: dict) -> str:
        buyer = document.get("buyer_summary", {})

        return "\n".join(
            [
                "## Buyer Summary",
                "",
                f"- Primary buyer: {buyer.get('primary_buyer')}",
                f"- Secondary buyers: {self._csv(buyer.get('secondary_buyers', []))}",
                f"- Buyer pain: {buyer.get('buyer_pain')}",
                f"- Best fit context: {buyer.get('best_fit_context')}",
                "",
                str(buyer.get("summary", "")),
            ]
        )

    def _problem_statement(self, document: dict) -> str:
        problem = document.get("problem_statement", {})

        return "\n".join(
            [
                "## Problem Statement",
                "",
                f"- Workflow area: {problem.get('workflow_area')}",
                f"- Default friction hypothesis: {problem.get('default_friction_hypothesis')}",
                f"- Buyer value: {problem.get('buyer_value')}",
                "",
                str(problem.get("statement", "")),
            ]
        )

    def _assessment_scope(self, document: dict) -> str:
        scope = document.get("assessment_scope", {})

        return "\n".join(
            [
                "## Assessment Scope",
                "",
                f"- Scope type: {scope.get('scope_type')}",
                f"- Workflow area: {scope.get('workflow_area')}",
                f"- Duration: {scope.get('duration')}",
                f"- Scope boundary: {scope.get('scope_boundary')}",
                "",
                "### Included Work",
                self._bullets(scope.get("included_work", [])),
                "",
                "### Success Definition",
                str(scope.get("success_definition", "")),
            ]
        )

    def _evidence_boundary(self, document: dict) -> str:
        evidence = document.get("evidence_boundary", {})

        return "\n".join(
            [
                "## Evidence Boundary",
                "",
                f"- Request type: {evidence.get('request_type')}",
                f"- Requested sources: {self._csv(evidence.get('requested_sources', []))}",
                f"- Allowed formats: {self._csv(evidence.get('allowed_format', []))}",
                f"- Allowed data: {self._csv(evidence.get('allowed_data', []))}",
                f"- Prohibited data: {self._csv(evidence.get('prohibited_data', []))}",
                f"- Certification claims allowed: {evidence.get('certification_claims_allowed')}",
                f"- Binding price quote allowed: {evidence.get('binding_price_quote_allowed')}",
                f"- Collection rule: {evidence.get('collection_rule')}",
            ]
        )

    def _deliverables(self, document: dict) -> str:
        lines = ["## Deliverables"]

        for item in document.get("deliverables", []):
            lines.extend(
                [
                    "",
                    f"### {item.get('deliverable')}",
                    "",
                    f"- Format: {item.get('format')}",
                    f"- Sections: {self._csv(item.get('sections', []))}",
                    f"- Buyer value: {item.get('buyer_value')}",
                ]
            )

        return "\n".join(lines)

    def _timeline(self, document: dict) -> str:
        timeline = document.get("timeline", {})
        lines = [
            "## Timeline",
            "",
            f"- Estimated duration: {timeline.get('estimated_duration')}",
        ]

        for phase in timeline.get("phases", []):
            lines.extend(
                [
                    "",
                    f"### {phase.get('phase')}",
                    "",
                    str(phase.get("description", "")),
                ]
            )

        return "\n".join(lines)

    def _commercial_terms(self, document: dict) -> str:
        terms = document.get("commercial_terms", {})
        band = terms.get("recommended_price_band", {})

        return "\n".join(
            [
                "## Commercial Terms",
                "",
                f"- Pricing model: {terms.get('pricing_model')}",
                f"- Currency: {terms.get('currency')}",
                f"- Recommended price band: {terms.get('currency')} {band.get('low')} - {band.get('high')}",
                f"- Payment terms: {terms.get('payment_terms')}",
                f"- Proposal expiration: {terms.get('proposal_expiration')}",
                f"- Binding quote: {terms.get('binding_quote')}",
                f"- Terms status: {terms.get('terms_status')}",
                f"- Pricing note: {terms.get('pricing_note')}",
            ]
        )

    def _assumptions(self, document: dict) -> str:
        return "\n".join(
            [
                "## Assumptions",
                "",
                self._bullets(document.get("assumptions", [])),
            ]
        )

    def _approval_requirements(self, document: dict) -> str:
        lines = ["## Approval Requirements"]

        for item in document.get("approval_requirements", []):
            lines.extend(
                [
                    "",
                    f"### {item.get('approval')}",
                    "",
                    f"- Required by: {item.get('required_by')}",
                    f"- Purpose: {item.get('purpose')}",
                    f"- Required: {item.get('required')}",
                ]
            )

        return "\n".join(lines)

    def _exclusions(self, document: dict) -> str:
        return "\n".join(
            [
                "## Exclusions",
                "",
                self._bullets(document.get("exclusions", [])),
            ]
        )

    def _operator_notes(self, document: dict) -> str:
        lines = ["## Operator Notes"]

        for item in document.get("operator_notes", []):
            lines.extend(
                [
                    "",
                    f"### {item.get('note')}",
                    "",
                    f"- Message: {item.get('message')}",
                    f"- Required: {item.get('required')}",
                ]
            )

        return "\n".join(lines)

    def _next_action(self, document: dict) -> str:
        action = document.get("next_action", {})

        return "\n".join(
            [
                "## Next Action",
                "",
                f"- Action: {action.get('action')}",
                f"- Operator instruction: {action.get('operator_instruction')}",
                f"- Future action: {action.get('future_action')}",
            ]
        )

    def _boundary_notice(self) -> str:
        return "\n".join(
            [
                "## Boundary Notice",
                "",
                "This Markdown export is not a binding quote, sales contract, invoice, "
                "legal agreement, production onboarding plan, or compliance certification.",
                "",
                "The operator must review scope, pricing, evidence boundaries, "
                "commercial terms, exclusions, and buyer-facing language before use.",
                "",
                "The deterministic GAGF Kernel remains the authoritative decision "
                "and verification layer.",
            ]
        )

    def _source_document(self, document: dict) -> dict:
        return {
            "document_type": document.get("document_type"),
            "document_stage": document.get("document_stage"),
            "release": document.get("release"),
            "version": document.get("version"),
            "recommended_action": document.get("recommended_action"),
        }

    def _export_sections(self) -> list[str]:
        return [
            "proposal_metadata",
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
            "boundary_notice",
        ]

    def _bullets(self, items: list) -> str:
        return "\n".join(f"- {item}" for item in items)

    def _csv(self, items: list) -> str:
        return ", ".join(str(item) for item in items)