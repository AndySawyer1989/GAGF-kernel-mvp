from html import escape

from backend.app.gagf.assessment_factory_lite_proposal_builder_service import (
    AssessmentFactoryLiteProposalBuilderService,
)


class AssessmentFactoryLiteProposalHTMLService:
    """Render the Assessment Factory Lite proposal-ready artifact as HTML."""

    def __init__(
        self,
        proposal_service: AssessmentFactoryLiteProposalBuilderService | None = None,
    ):
        self.proposal_service = (
            proposal_service or AssessmentFactoryLiteProposalBuilderService()
        )

    def render_html(
        self,
        proposal: dict | None = None,
        offer: dict | None = None,
        buyer_context: dict | None = None,
    ) -> dict:
        source_proposal = proposal or self.proposal_service.build_proposal(
            offer=offer,
            buyer_context=buyer_context,
        )

        html = self._build_html(source_proposal)

        return {
            "status": "ok",
            "view_type": "assessment_factory_lite_paid_assessment_proposal_html_view",
            "package_name": "Assessment Factory Lite Demo Package",
            "release": "assessment-factory-lite-commercial-offer",
            "version": "1.9.0",
            "view_stage": "proposal_ready_presentation",
            "html": html,
            "source_proposal": source_proposal,
            "view_sections": self._view_sections(),
            "operator_message": (
                "Assessment Factory Lite proposal HTML view is ready for "
                "operator review and buyer presentation."
            ),
            "recommended_action": "present_proposal_html_view",
        }

    def _view_sections(self) -> list[str]:
        return [
            "proposal_header",
            "buyer_context",
            "problem_statement",
            "proposed_scope",
            "evidence_boundary",
            "deliverables",
            "timeline",
            "commercial_terms_placeholder",
            "approval_requirements",
            "proposal_risk_controls",
            "excluded_scope",
            "next_action",
        ]

    def _build_html(self, proposal: dict) -> str:
        return "\n".join(
            [
                "<!doctype html>",
                '<html lang="en">',
                "<head>",
                '  <meta charset="utf-8">',
                "  <title>Assessment Factory Lite Proposal</title>",
                self._style_block(),
                "</head>",
                '<body data-view="assessment-factory-lite-paid-assessment-proposal-html-view">',
                self._header(proposal),
                self._buyer_context(proposal),
                self._problem_statement(proposal),
                self._proposed_scope(proposal),
                self._evidence_boundary(proposal),
                self._deliverables(proposal),
                self._timeline(proposal),
                self._commercial_terms(proposal),
                self._approval_requirements(proposal),
                self._proposal_risk_controls(proposal),
                self._excluded_scope(proposal),
                self._next_action(proposal),
                "</body>",
                "</html>",
            ]
        )

    def _style_block(self) -> str:
        return """
<style>
:root {
  --afl-brand-orange: #F97316;
  --afl-brand-gold: #D6A21E;
  --afl-brand-purple: #6D28D9;
  --afl-surface: #FFF8EF;
  --afl-surface-alt: #F7F2FF;
  --afl-text-primary: #241A12;
  --afl-text-secondary: #5C4A3D;
  --afl-border-subtle: #E8D8C8;
  --afl-card-radius: 1rem;
  --afl-font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}
body {
  margin: 0;
  padding: 2rem;
  background: #FFFFFF;
  color: var(--afl-text-primary);
  font-family: var(--afl-font-family);
  line-height: 1.55;
}
.afl-proposal-header {
  border: 1px solid var(--afl-border-subtle);
  border-radius: var(--afl-card-radius);
  background: linear-gradient(135deg, var(--afl-surface), var(--afl-surface-alt));
  padding: 1.5rem;
  margin-bottom: 1rem;
}
.afl-card {
  border: 1px solid var(--afl-border-subtle);
  border-radius: var(--afl-card-radius);
  padding: 1rem;
  margin: 1rem 0;
}
.afl-card h2, .afl-card h3 {
  margin-top: 0;
}
.afl-pill {
  display: inline-block;
  border: 1px solid var(--afl-border-subtle);
  border-radius: 999px;
  padding: 0.2rem 0.65rem;
  margin: 0.15rem;
  background: #FFFFFF;
}
.afl-boundary {
  border-color: var(--afl-brand-purple);
  background: var(--afl-surface-alt);
}
.afl-price {
  font-size: 1.5rem;
  font-weight: 750;
  color: var(--afl-brand-purple);
}
.afl-phase {
  border-left: 0.25rem solid var(--afl-brand-orange);
  padding-left: 0.75rem;
  margin: 0.75rem 0;
}
</style>
""".strip()

    def _header(self, proposal: dict) -> str:
        return f"""
<header class="afl-proposal-header">
  <p class="afl-pill">Proposal-Ready Artifact</p>
  <p class="afl-pill">{escape(str(proposal.get("version", "")))}</p>
  <h1>{escape(str(proposal.get("proposal_title", "")))}</h1>
  <p><strong>Proposal type:</strong> {escape(str(proposal.get("proposal_type", "")))}</p>
  <p><strong>Stage:</strong> {escape(str(proposal.get("proposal_stage", "")))}</p>
</header>
""".strip()

    def _buyer_context(self, proposal: dict) -> str:
        buyer = proposal.get("buyer_context", {})
        return f"""
<section class="afl-card" data-section="buyer_context">
  <h2>Buyer Context</h2>
  <p><strong>Primary buyer:</strong> {escape(str(buyer.get("primary_buyer", "")))}</p>
  <p><strong>Secondary buyers:</strong> {self._pills(buyer.get("secondary_buyers", []))}</p>
  <p><strong>Buyer pain:</strong> {escape(str(buyer.get("buyer_pain", "")))}</p>
  <p>{escape(str(buyer.get("best_fit_context", "")))}</p>
</section>
""".strip()

    def _problem_statement(self, proposal: dict) -> str:
        problem = proposal.get("problem_statement", {})
        return f"""
<section class="afl-card" data-section="problem_statement">
  <h2>Problem Statement</h2>
  <p><strong>Workflow area:</strong> {escape(str(problem.get("workflow_area", "")))}</p>
  <p>{escape(str(problem.get("statement", "")))}</p>
  <p><strong>Default friction hypothesis:</strong> {escape(str(problem.get("default_friction_hypothesis", "")))}</p>
  <p><strong>Buyer value:</strong> {escape(str(problem.get("buyer_value", "")))}</p>
</section>
""".strip()

    def _proposed_scope(self, proposal: dict) -> str:
        scope = proposal.get("proposed_scope", {})
        return f"""
<section class="afl-card" data-section="proposed_scope">
  <h2>Proposed Scope</h2>
  <p><strong>Scope type:</strong> {escape(str(scope.get("scope_type", "")))}</p>
  <p><strong>Workflow area:</strong> {escape(str(scope.get("workflow_area", "")))}</p>
  <p><strong>Duration:</strong> {escape(str(scope.get("duration", "")))}</p>
  <p><strong>Included work:</strong> {self._pills(scope.get("included_work", []))}</p>
  <p><strong>Scope boundary:</strong> {escape(str(scope.get("scope_boundary", "")))}</p>
  <p>{escape(str(scope.get("success_definition", "")))}</p>
</section>
""".strip()

    def _evidence_boundary(self, proposal: dict) -> str:
        evidence = proposal.get("evidence_boundary", {})
        return f"""
<section class="afl-card afl-boundary" data-section="evidence_boundary">
  <h2>Evidence Boundary</h2>
  <p><strong>Request type:</strong> {escape(str(evidence.get("request_type", "")))}</p>
  <p><strong>Requested sources:</strong> {self._pills(evidence.get("requested_sources", []))}</p>
  <p><strong>Allowed formats:</strong> {self._pills(evidence.get("allowed_format", []))}</p>
  <p><strong>Allowed data:</strong> {self._pills(evidence.get("allowed_data", []))}</p>
  <p><strong>Prohibited data:</strong> {self._pills(evidence.get("prohibited_data", []))}</p>
  <p><strong>Certification claims allowed:</strong> {escape(str(evidence.get("certification_claims_allowed")))}</p>
  <p><strong>Binding price quote allowed:</strong> {escape(str(evidence.get("binding_price_quote_allowed")))}</p>
  <p>{escape(str(evidence.get("collection_rule", "")))}</p>
</section>
""".strip()

    def _deliverables(self, proposal: dict) -> str:
        cards = []
        for item in proposal.get("deliverables", []):
            cards.append(
                f"""
<div class="afl-card" data-deliverable="{escape(str(item.get("deliverable", "")))}">
  <h3>{escape(str(item.get("deliverable", "")))}</h3>
  <p><strong>Format:</strong> {escape(str(item.get("format", "")))}</p>
  <p><strong>Sections:</strong> {self._pills(item.get("sections", []))}</p>
  <p>{escape(str(item.get("buyer_value", "")))}</p>
</div>
""".strip()
            )
        return f"""
<section class="afl-card" data-section="deliverables">
  <h2>Deliverables</h2>
  {"".join(cards)}
</section>
""".strip()

    def _timeline(self, proposal: dict) -> str:
        timeline = proposal.get("timeline", {})
        phases = []
        for phase in timeline.get("phases", []):
            phases.append(
                f"""
<div class="afl-phase" data-phase="{escape(str(phase.get("phase", "")))}">
  <h3>{escape(str(phase.get("phase", "")))}</h3>
  <p>{escape(str(phase.get("description", "")))}</p>
</div>
""".strip()
            )
        return f"""
<section class="afl-card" data-section="timeline">
  <h2>Timeline</h2>
  <p><strong>Estimated duration:</strong> {escape(str(timeline.get("estimated_duration", "")))}</p>
  {"".join(phases)}
</section>
""".strip()

    def _commercial_terms(self, proposal: dict) -> str:
        terms = proposal.get("commercial_terms_placeholder", {})
        band = terms.get("recommended_price_band", {})
        currency = escape(str(terms.get("currency", "")))
        low = escape(str(band.get("low", "")))
        high = escape(str(band.get("high", "")))
        return f"""
<section class="afl-card" data-section="commercial_terms_placeholder">
  <h2>Commercial Terms Placeholder</h2>
  <p class="afl-price">{currency} {low} - {high}</p>
  <p><strong>Pricing model:</strong> {escape(str(terms.get("pricing_model", "")))}</p>
  <p><strong>Payment terms:</strong> {escape(str(terms.get("payment_terms", "")))}</p>
  <p><strong>Proposal expiration:</strong> {escape(str(terms.get("proposal_expiration", "")))}</p>
  <p><strong>Binding quote:</strong> {escape(str(terms.get("binding_quote")))}</p>
  <p>{escape(str(terms.get("pricing_note", "")))}</p>
</section>
""".strip()

    def _approval_requirements(self, proposal: dict) -> str:
        cards = []
        for approval in proposal.get("approval_requirements", []):
            cards.append(
                f"""
<div class="afl-card" data-approval="{escape(str(approval.get("approval", "")))}">
  <h3>{escape(str(approval.get("approval", "")))}</h3>
  <p><strong>Required by:</strong> {escape(str(approval.get("required_by", "")))}</p>
  <p>{escape(str(approval.get("purpose", "")))}</p>
  <p><strong>Required:</strong> {escape(str(approval.get("required")))}</p>
</div>
""".strip()
            )
        return f"""
<section class="afl-card" data-section="approval_requirements">
  <h2>Approval Requirements</h2>
  {"".join(cards)}
</section>
""".strip()

    def _proposal_risk_controls(self, proposal: dict) -> str:
        cards = []
        for control in proposal.get("proposal_risk_controls", []):
            cards.append(
                f"""
<div class="afl-card" data-control="{escape(str(control.get("control", "")))}">
  <h3>{escape(str(control.get("control", "")))}</h3>
  <p>{escape(str(control.get("purpose", "")))}</p>
  <p><strong>Required:</strong> {escape(str(control.get("required")))}</p>
</div>
""".strip()
            )
        return f"""
<section class="afl-card" data-section="proposal_risk_controls">
  <h2>Proposal Risk Controls</h2>
  {"".join(cards)}
</section>
""".strip()

    def _excluded_scope(self, proposal: dict) -> str:
        return f"""
<section class="afl-card afl-boundary" data-section="excluded_scope">
  <h2>Excluded Scope</h2>
  <p>{self._pills(proposal.get("excluded_scope", []))}</p>
</section>
""".strip()

    def _next_action(self, proposal: dict) -> str:
        action = proposal.get("next_action", {})
        return f"""
<section class="afl-card" data-section="next_action">
  <h2>Next Action</h2>
  <p><strong>Action:</strong> {escape(str(action.get("action", "")))}</p>
  <p><strong>Operator instruction:</strong> {escape(str(action.get("operator_instruction", "")))}</p>
  <p><strong>Future action:</strong> {escape(str(action.get("future_action", "")))}</p>
</section>
""".strip()

    def _pills(self, items: list) -> str:
        return "".join(
            f'<span class="afl-pill">{escape(str(item))}</span>'
            for item in items
        )
