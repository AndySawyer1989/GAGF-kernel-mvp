from html import escape

from backend.app.gagf.assessment_factory_lite_buyer_walkthrough_script_service import (
    AssessmentFactoryLiteBuyerWalkthroughScriptService,
)


class AssessmentFactoryLiteBuyerWalkthroughHTMLService:
    """Render the buyer walkthrough script as a UI-ready HTML view."""

    def __init__(
        self,
        script_service: AssessmentFactoryLiteBuyerWalkthroughScriptService | None = None,
    ):
        self.script_service = script_service or AssessmentFactoryLiteBuyerWalkthroughScriptService()

    def render_html(self, script: dict | None = None) -> dict:
        source_script = script or self.script_service.build_script()
        html = self._build_html(source_script)

        return {
            "status": "ok",
            "view_type": "assessment_factory_lite_buyer_walkthrough_html_view",
            "package_name": "Assessment Factory Lite Demo Package",
            "release": "assessment-factory-lite-demo-delivery-packaging",
            "version": "1.7.0",
            "view_stage": "buyer_demo_conversion",
            "html": html,
            "source_script": source_script,
            "view_sections": self._view_sections(),
            "operator_message": (
                "Assessment Factory Lite buyer walkthrough HTML view is ready "
                "for operator presentation."
            ),
            "recommended_action": "present_buyer_walkthrough_html_view",
        }

    def _view_sections(self) -> list[str]:
        return [
            "walkthrough_header",
            "opening_script",
            "problem_frame",
            "scenario_script",
            "finding_script",
            "intervention_script",
            "boundary_script",
            "buyer_questions",
            "close_script",
            "objection_responses",
            "demo_boundary",
        ]

    def _build_html(self, script: dict) -> str:
        return "\n".join(
            [
                "<!doctype html>",
                '<html lang="en">',
                "<head>",
                '  <meta charset="utf-8">',
                "  <title>Assessment Factory Lite Buyer Walkthrough</title>",
                self._style_block(),
                "</head>",
                '<body data-view="assessment-factory-lite-buyer-walkthrough-html-view">',
                self._header(script),
                self._script_summary(script),
                self._opening(script),
                self._problem_frame(script),
                self._scenarios(script),
                self._finding(script),
                self._intervention(script),
                self._boundary_script(script),
                self._buyer_questions(script),
                self._close(script),
                self._objections(script),
                self._demo_boundary(script),
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
.afl-walkthrough-header {
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
.afl-script {
  font-weight: 600;
}
.afl-boundary {
  border-color: var(--afl-brand-purple);
  background: var(--afl-surface-alt);
}
</style>
""".strip()

    def _header(self, script: dict) -> str:
        return f"""
<header class="afl-walkthrough-header">
  <p class="afl-pill">Buyer Walkthrough</p>
  <p class="afl-pill">{escape(script.get("version", ""))}</p>
  <h1>{escape(script.get("package_name", ""))}</h1>
  <p>{escape(script.get("script_stage", ""))}</p>
</header>
""".strip()

    def _script_summary(self, script: dict) -> str:
        summary = script.get("script_summary", {})
        return f"""
<section class="afl-card" data-section="script_summary">
  <h2>Script Summary</h2>
  <p>{escape(summary.get("positioning", ""))}</p>
  <p><strong>Delivery mode:</strong> {escape(summary.get("delivery_mode", ""))}</p>
  <p><strong>Conversion goal:</strong> {escape(summary.get("conversion_goal", ""))}</p>
</section>
""".strip()

    def _opening(self, script: dict) -> str:
        opening = script.get("opening_script", {})
        return self._script_card("opening_script", opening)

    def _problem_frame(self, script: dict) -> str:
        problem = script.get("problem_frame", {})
        return self._script_card("problem_frame", problem)

    def _script_card(self, section_name: str, section: dict) -> str:
        return f"""
<section class="afl-card" data-section="{escape(section_name)}">
  <h2>{escape(section.get("title", section_name))}</h2>
  <p class="afl-script">{escape(section.get("operator_script", ""))}</p>
  <p><strong>Buyer takeaway:</strong> {escape(section.get("buyer_takeaway", ""))}</p>
</section>
""".strip()

    def _scenarios(self, script: dict) -> str:
        cards = []
        for scenario in script.get("scenario_script", []):
            cards.append(
                f"""
<div class="afl-card" data-scenario="{escape(scenario.get("scenario", ""))}">
  <h3>{escape(scenario.get("label", ""))}</h3>
  <p class="afl-pill">{escape(scenario.get("when_to_use", ""))}</p>
  <p class="afl-script">{escape(scenario.get("operator_script", ""))}</p>
  <p><strong>Expected friction:</strong> {escape(scenario.get("expected_friction", ""))}</p>
  <p><strong>Buyer takeaway:</strong> {escape(scenario.get("buyer_takeaway", ""))}</p>
</div>
""".strip()
            )

        return f"""
<section class="afl-card" data-section="scenario_script">
  <h2>Scenario Script</h2>
  {"".join(cards)}
</section>
""".strip()

    def _finding(self, script: dict) -> str:
        finding = script.get("finding_script", {})
        return f"""
<section class="afl-card" data-section="finding_script">
  <h2>{escape(finding.get("title", ""))}</h2>
  <p class="afl-script">{escape(finding.get("operator_script", ""))}</p>
  <p><strong>Example finding:</strong> {escape(finding.get("example_finding", ""))}</p>
  <p><strong>Evidence link:</strong> {escape(finding.get("evidence_link", ""))}</p>
</section>
""".strip()

    def _intervention(self, script: dict) -> str:
        intervention = script.get("intervention_script", {})
        return f"""
<section class="afl-card" data-section="intervention_script">
  <h2>{escape(intervention.get("title", ""))}</h2>
  <p class="afl-script">{escape(intervention.get("operator_script", ""))}</p>
  <p><strong>Recommended intervention:</strong> {escape(intervention.get("recommended_intervention", ""))}</p>
  <p><strong>Buyer value:</strong> {escape(intervention.get("buyer_value", ""))}</p>
</section>
""".strip()

    def _boundary_script(self, script: dict) -> str:
        boundary = script.get("boundary_script", {})
        prohibited = "".join(
            f'<span class="afl-pill">{escape(item)}</span>'
            for item in boundary.get("prohibited_data", [])
        )
        return f"""
<section class="afl-card afl-boundary" data-section="boundary_script">
  <h2>{escape(boundary.get("title", ""))}</h2>
  <p class="afl-script">{escape(boundary.get("operator_script", ""))}</p>
  <p><strong>Prohibited data:</strong> {prohibited}</p>
</section>
""".strip()

    def _buyer_questions(self, script: dict) -> str:
        items = []
        for question in script.get("buyer_questions", []):
            items.append(
                f"""
<li data-question-type="{escape(question.get("question_type", ""))}">
  <strong>{escape(question.get("question", ""))}</strong>
  <br>
  <span>{escape(question.get("purpose", ""))}</span>
</li>
""".strip()
            )

        return f"""
<section class="afl-card" data-section="buyer_questions">
  <h2>Buyer Questions</h2>
  <ul>
    {"".join(items)}
  </ul>
</section>
""".strip()

    def _close(self, script: dict) -> str:
        close = script.get("close_script", {})
        return f"""
<section class="afl-card" data-section="close_script">
  <h2>{escape(close.get("title", ""))}</h2>
  <p class="afl-script">{escape(close.get("operator_script", ""))}</p>
  <p><strong>Call to action:</strong> {escape(close.get("call_to_action", ""))}</p>
</section>
""".strip()

    def _objections(self, script: dict) -> str:
        items = []
        for objection in script.get("objection_responses", []):
            items.append(
                f"""
<div class="afl-card" data-objection="{escape(objection.get("objection", ""))}">
  <h3>{escape(objection.get("objection", ""))}</h3>
  <p>{escape(objection.get("response", ""))}</p>
</div>
""".strip()
            )

        return f"""
<section class="afl-card" data-section="objection_responses">
  <h2>Objection Responses</h2>
  {"".join(items)}
</section>
""".strip()

    def _demo_boundary(self, script: dict) -> str:
        boundary = script.get("demo_boundary", {})
        prohibited = "".join(
            f'<span class="afl-pill">{escape(item)}</span>'
            for item in boundary.get("prohibited_data", [])
        )
        return f"""
<section class="afl-card afl-boundary" data-section="demo_boundary">
  <h2>Demo-Only Boundary</h2>
  <p><strong>Boundary type:</strong> {escape(boundary.get("boundary_type", ""))}</p>
  <p><strong>Certification claims allowed:</strong> {escape(str(boundary.get("certification_claims_allowed")))}</p>
  <p><strong>Prohibited data:</strong> {prohibited}</p>
</section>
""".strip()