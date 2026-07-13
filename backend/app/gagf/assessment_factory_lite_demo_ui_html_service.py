from html import escape

from backend.app.gagf.assessment_factory_lite_demo_ui_view_service import (
    AssessmentFactoryLiteDemoUIViewService,
)


class AssessmentFactoryLiteDemoUIHTMLService:
    """Render the Assessment Factory Lite demo UI view as deterministic HTML."""

    def __init__(
        self,
        ui_view_service: AssessmentFactoryLiteDemoUIViewService | None = None,
    ):
        self.ui_view_service = ui_view_service or AssessmentFactoryLiteDemoUIViewService()

    def render_html(
        self,
        checkpoint: dict | None = None,
        rows: list[dict] | None = None,
        diagnostics_result: dict | None = None,
        export_summary: dict | None = None,
        ui_view: dict | None = None,
    ) -> dict:
        if ui_view is None:
            ui_view = self.ui_view_service.build_view(
                checkpoint=checkpoint,
                rows=rows,
                diagnostics_result=diagnostics_result,
                export_summary=export_summary,
            )

        html = self._build_html(ui_view)

        return {
            "status": "ok",
            "screen_type": "assessment_factory_lite_demo_ui_html_screen",
            "package_name": "Assessment Factory Lite Demo Package",
            "release": "assessment-factory-lite-demo-ui",
            "version": "1.2.0",
            "html": html,
            "ui_view": ui_view,
            "operator_message": (
                "Assessment Factory Lite demo HTML screen rendered for the "
                "Operator Workstation."
            ),
            "recommended_action": "display_assessment_factory_lite_demo_screen",
        }

    def _build_html(self, ui_view: dict) -> str:
        cards_html = "\n".join(
            self._render_card(card) for card in ui_view.get("cards", [])
        )
        warnings_html = "\n".join(
            self._render_warning(warning)
            for warning in ui_view.get("warnings", [])
        )
        actions_html = "\n".join(
            f"<li>{escape(action)}</li>"
            for action in ui_view.get("operator_actions", [])
        )

        export_summary = ui_view.get("source_payloads", {}).get(
            "export_summary", {}
        )
        executive_summary = escape(export_summary.get("executive_summary", ""))
        compliance_disclaimer = escape(
            export_summary.get("compliance_disclaimer", "")
        )

        return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Assessment Factory Lite Demo</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
</head>
<body data-screen="assessment-factory-lite-demo-ui-html-screen">
  <main class="afl-demo-screen">
    <header class="afl-demo-header">
      <p class="afl-kicker">FIP/GAGF Operator Workstation</p>
      <h1>Assessment Factory Lite Demo</h1>
      <p class="afl-subtitle">Sample-data-only buyer demo path</p>
      <p class="afl-release">Release: {escape(ui_view.get("release", ""))} | Version: {escape(ui_view.get("version", ""))}</p>
    </header>

    <section class="afl-warning-strip" aria-label="Demo warnings">
      <h2>Demo Safety Warnings</h2>
      {warnings_html}
    </section>

    <section class="afl-card-grid" aria-label="Demo cards">
      <h2>Operator Demo Cards</h2>
      {cards_html}
    </section>

    <section class="afl-export-preview" aria-label="Export summary preview">
      <h2>Buyer-Facing Export Preview</h2>
      <p>{executive_summary}</p>
      <p class="afl-disclaimer">{compliance_disclaimer}</p>
    </section>

    <section class="afl-next-actions" aria-label="Operator actions">
      <h2>Operator Actions</h2>
      <ol>
        {actions_html}
      </ol>
    </section>
  </main>
</body>
</html>"""

    def _render_card(self, card: dict) -> str:
        card_id = escape(str(card.get("card_id", "")))
        title = escape(str(card.get("title", "")))
        status = escape(str(card.get("status", "")))
        summary = escape(str(card.get("summary", "")))
        primary_value = escape(str(card.get("primary_value", "")))
        action = escape(str(card.get("action", "")))

        return f"""<article class="afl-card" data-card-id="{card_id}">
  <h3>{title}</h3>
  <p class="afl-card-status">Status: {status}</p>
  <p class="afl-card-primary">Primary value: {primary_value}</p>
  <p>{summary}</p>
  <p class="afl-card-action">Action: {action}</p>
</article>"""

    def _render_warning(self, warning: dict) -> str:
        warning_type = escape(str(warning.get("warning_type", "")))
        severity = escape(str(warning.get("severity", "")))
        message = escape(str(warning.get("message", "")))

        return f"""<article class="afl-warning" data-warning-type="{warning_type}">
  <h3>{warning_type}</h3>
  <p>Severity: {severity}</p>
  <p>{message}</p>
</article>"""