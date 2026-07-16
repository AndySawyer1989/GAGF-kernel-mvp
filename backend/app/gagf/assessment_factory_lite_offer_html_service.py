from html import escape

from backend.app.gagf.assessment_factory_lite_offer_builder_service import (
    AssessmentFactoryLiteOfferBuilderService,
)


class AssessmentFactoryLiteOfferHTMLService:
    """Render the Assessment Factory Lite paid-assessment offer as HTML."""

    def __init__(
        self,
        offer_service: AssessmentFactoryLiteOfferBuilderService | None = None,
    ):
        self.offer_service = offer_service or AssessmentFactoryLiteOfferBuilderService()

    def render_html(
        self,
        offer: dict | None = None,
        buyer_context: dict | None = None,
    ) -> dict:
        source_offer = offer or self.offer_service.build_offer(
            buyer_context=buyer_context
        )

        html = self._build_html(source_offer)

        return {
            "status": "ok",
            "view_type": "assessment_factory_lite_paid_assessment_offer_html_view",
            "package_name": "Assessment Factory Lite Demo Package",
            "release": "assessment-factory-lite-buyer-conversion",
            "version": "1.8.0",
            "view_stage": "paid_assessment_conversion",
            "html": html,
            "source_offer": source_offer,
            "view_sections": self._view_sections(),
            "operator_message": (
                "Assessment Factory Lite paid-assessment offer HTML view is "
                "ready for operator review and buyer presentation."
            ),
            "recommended_action": "present_paid_assessment_offer_html_view",
        }

    def _view_sections(self) -> list[str]:
        return [
            "offer_header",
            "target_buyer",
            "problem_statement",
            "safe_evidence_request",
            "assessment_scope",
            "deliverable",
            "recommended_price_band",
            "buyer_commitment",
            "qualification_questions",
            "risk_controls",
            "next_action",
            "demo_boundary",
            "excluded_scope",
        ]

    def _build_html(self, offer: dict) -> str:
        return "\n".join(
            [
                "<!doctype html>",
                '<html lang="en">',
                "<head>",
                '  <meta charset="utf-8">',
                "  <title>Assessment Factory Lite Paid Assessment Offer</title>",
                self._style_block(),
                "</head>",
                '<body data-view="assessment-factory-lite-paid-assessment-offer-html-view">',
                self._header(offer),
                self._target_buyer(offer),
                self._problem_statement(offer),
                self._safe_evidence_request(offer),
                self._assessment_scope(offer),
                self._deliverable(offer),
                self._price_band(offer),
                self._buyer_commitment(offer),
                self._qualification_questions(offer),
                self._risk_controls(offer),
                self._next_action(offer),
                self._demo_boundary(offer),
                self._excluded_scope(offer),
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
.afl-offer-header {
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
</style>
""".strip()

    def _header(self, offer: dict) -> str:
        return f"""
<header class="afl-offer-header">
  <p class="afl-pill">Paid Assessment Offer</p>
  <p class="afl-pill">{escape(offer.get("version", ""))}</p>
  <h1>{escape(offer.get("package_name", ""))}</h1>
  <p>{escape(offer.get("offer_stage", ""))}</p>
  <p><strong>Offer type:</strong> {escape(offer.get("offer_type", ""))}</p>
</header>
""".strip()

    def _target_buyer(self, offer: dict) -> str:
        buyer = offer.get("target_buyer", {})
        secondary = self._pills(buyer.get("secondary_buyers", []))

        return f"""
<section class="afl-card" data-section="target_buyer">
  <h2>Target Buyer</h2>
  <p><strong>Primary buyer:</strong> {escape(buyer.get("primary_buyer", ""))}</p>
  <p><strong>Secondary buyers:</strong> {secondary}</p>
  <p><strong>Buyer pain:</strong> {escape(buyer.get("buyer_pain", ""))}</p>
  <p>{escape(buyer.get("best_fit_context", ""))}</p>
</section>
""".strip()

    def _problem_statement(self, offer: dict) -> str:
        problem = offer.get("problem_statement", {})

        return f"""
<section class="afl-card" data-section="problem_statement">
  <h2>Problem Statement</h2>
  <p><strong>Workflow area:</strong> {escape(problem.get("workflow_area", ""))}</p>
  <p>{escape(problem.get("statement", ""))}</p>
  <p><strong>Default friction hypothesis:</strong> {escape(problem.get("default_friction_hypothesis", ""))}</p>
  <p><strong>Buyer value:</strong> {escape(problem.get("buyer_value", ""))}</p>
</section>
""".strip()

    def _safe_evidence_request(self, offer: dict) -> str:
        evidence = offer.get("safe_evidence_request", {})

        return f"""
<section class="afl-card afl-boundary" data-section="safe_evidence_request">
  <h2>Safe Evidence Request</h2>
  <p><strong>Request type:</strong> {escape(evidence.get("request_type", ""))}</p>
  <p><strong>Requested sources:</strong> {self._pills(evidence.get("requested_sources", []))}</p>
  <p><strong>Allowed format:</strong> {self._pills(evidence.get("allowed_format", []))}</p>
  <p><strong>Prohibited data:</strong> {self._pills(evidence.get("prohibited_data", []))}</p>
  <p>{escape(evidence.get("collection_rule", ""))}</p>
</section>
""".strip()

    def _assessment_scope(self, offer: dict) -> str:
        scope = offer.get("assessment_scope", {})

        return f"""
<section class="afl-card" data-section="assessment_scope">
  <h2>Assessment Scope</h2>
  <p><strong>Scope type:</strong> {escape(scope.get("scope_type", ""))}</p>
  <p><strong>Workflow area:</strong> {escape(scope.get("workflow_area", ""))}</p>
  <p><strong>Duration:</strong> {escape(scope.get("duration", ""))}</p>
  <p><strong>Included work:</strong> {self._pills(scope.get("included_work", []))}</p>
  <p>{escape(scope.get("success_definition", ""))}</p>
</section>
""".strip()

    def _deliverable(self, offer: dict) -> str:
        deliverable = offer.get("deliverable", {})

        return f"""
<section class="afl-card" data-section="deliverable">
  <h2>Deliverable</h2>
  <p><strong>Deliverable type:</strong> {escape(deliverable.get("deliverable_type", ""))}</p>
  <p><strong>Format:</strong> {escape(deliverable.get("format", ""))}</p>
  <p><strong>Sections:</strong> {self._pills(deliverable.get("sections", []))}</p>
  <p>{escape(deliverable.get("buyer_value", ""))}</p>
</section>
""".strip()

    def _price_band(self, offer: dict) -> str:
        price = offer.get("recommended_price_band", {})
        low = escape(str(price.get("low", "")))
        high = escape(str(price.get("high", "")))
        currency = escape(price.get("currency", ""))

        return f"""
<section class="afl-card" data-section="recommended_price_band">
  <h2>Recommended Price Band</h2>
  <p class="afl-price">{currency} {low} - {high}</p>
  <p><strong>Pricing model:</strong> {escape(price.get("pricing_model", ""))}</p>
  <p>{escape(price.get("pricing_note", ""))}</p>
</section>
""".strip()

    def _buyer_commitment(self, offer: dict) -> str:
        commitment = offer.get("buyer_commitment", {})

        return f"""
<section class="afl-card" data-section="buyer_commitment">
  <h2>Buyer Commitment</h2>
  <p><strong>Commitment type:</strong> {escape(commitment.get("commitment_type", ""))}</p>
  <p><strong>Buyer provides:</strong> {self._pills(commitment.get("buyer_provides", []))}</p>
  <p><strong>Operator provides:</strong> {self._pills(commitment.get("operator_provides", []))}</p>
</section>
""".strip()

    def _qualification_questions(self, offer: dict) -> str:
        questions = []
        for question in offer.get("qualification_questions", []):
            questions.append(
                f"""
<li data-question-type="{escape(question.get("question_type", ""))}">
  <strong>{escape(question.get("question", ""))}</strong>
  <br>
  <span>{escape(question.get("purpose", ""))}</span>
</li>
""".strip()
            )

        return f"""
<section class="afl-card" data-section="qualification_questions">
  <h2>Qualification Questions</h2>
  <ul>
    {"".join(questions)}
  </ul>
</section>
""".strip()

    def _risk_controls(self, offer: dict) -> str:
        controls = []
        for control in offer.get("risk_controls", []):
            controls.append(
                f"""
<div class="afl-card" data-control="{escape(control.get("control", ""))}">
  <h3>{escape(control.get("control", ""))}</h3>
  <p>{escape(control.get("purpose", ""))}</p>
  <p><strong>Required:</strong> {escape(str(control.get("required")))}</p>
</div>
""".strip()
            )

        return f"""
<section class="afl-card" data-section="risk_controls">
  <h2>Risk Controls</h2>
  {"".join(controls)}
</section>
""".strip()

    def _next_action(self, offer: dict) -> str:
        action = offer.get("next_action", {})

        return f"""
<section class="afl-card" data-section="next_action">
  <h2>Next Action</h2>
  <p><strong>Action:</strong> {escape(action.get("action", ""))}</p>
  <p>{escape(action.get("recommended_message", ""))}</p>
  <p><strong>Operator instruction:</strong> {escape(action.get("operator_instruction", ""))}</p>
</section>
""".strip()

    def _demo_boundary(self, offer: dict) -> str:
        boundary = offer.get("demo_boundary", {})

        return f"""
<section class="afl-card afl-boundary" data-section="demo_boundary">
  <h2>Demo and Assessment Intake Boundary</h2>
  <p><strong>Boundary type:</strong> {escape(boundary.get("boundary_type", ""))}</p>
  <p><strong>Allowed data:</strong> {self._pills(boundary.get("allowed_data", []))}</p>
  <p><strong>Prohibited data:</strong> {self._pills(boundary.get("prohibited_data", []))}</p>
  <p><strong>Certification claims allowed:</strong> {escape(str(boundary.get("certification_claims_allowed")))}</p>
  <p><strong>Binding price quote allowed:</strong> {escape(str(boundary.get("binding_price_quote_allowed")))}</p>
</section>
""".strip()

    def _excluded_scope(self, offer: dict) -> str:
        return f"""
<section class="afl-card afl-boundary" data-section="excluded_scope">
  <h2>Excluded Scope</h2>
  <p>{self._pills(offer.get("excluded_scope", []))}</p>
</section>
""".strip()

    def _pills(self, items: list) -> str:
        return "".join(
            f'<span class="afl-pill">{escape(str(item))}</span>'
            for item in items
        )