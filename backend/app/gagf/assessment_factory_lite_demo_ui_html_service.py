from html import escape

from backend.app.gagf.assessment_factory_lite_demo_sample_rows_service import (
    AssessmentFactoryLiteDemoSampleRowsService,
)
from backend.app.gagf.assessment_factory_lite_demo_scenario_menu_service import (
    AssessmentFactoryLiteDemoScenarioMenuService,
)
from backend.app.gagf.assessment_factory_lite_demo_ui_view_service import (
    AssessmentFactoryLiteDemoUIViewService,
)


class AssessmentFactoryLiteDemoUIHTMLService:
    """Render the Assessment Factory Lite demo UI view as deterministic HTML."""

    def __init__(
        self,
        ui_view_service: AssessmentFactoryLiteDemoUIViewService | None = None,
        sample_rows_service: AssessmentFactoryLiteDemoSampleRowsService | None = None,
        scenario_menu_service: (
            AssessmentFactoryLiteDemoScenarioMenuService | None
        ) = None,
    ):
        self.ui_view_service = ui_view_service or AssessmentFactoryLiteDemoUIViewService()
        self.sample_rows_service = (
            sample_rows_service or AssessmentFactoryLiteDemoSampleRowsService()
        )
        self.scenario_menu_service = (
            scenario_menu_service or AssessmentFactoryLiteDemoScenarioMenuService()
        )

    def render_html(
        self,
        checkpoint: dict | None = None,
        rows: list[dict] | None = None,
        diagnostics_result: dict | None = None,
        export_summary: dict | None = None,
        ui_view: dict | None = None,
        sample_scenario: str | None = None,
        include_scenario_menu: bool = True,
    ) -> dict:
        sample_rows_result = None
        scenario_menu = (
            self.scenario_menu_service.build_menu()
            if include_scenario_menu
            else None
        )

        if ui_view is None and rows is None and sample_scenario:
            sample_rows_result = self.sample_rows_service.get_sample_rows(
                sample_scenario
            )
            rows = sample_rows_result.get("rows", [])

        if ui_view is None:
            ui_view = self.ui_view_service.build_view(
                checkpoint=checkpoint,
                rows=rows,
                diagnostics_result=diagnostics_result,
                export_summary=export_summary,
            )

        html = self._build_html(
            ui_view=ui_view,
            sample_rows_result=sample_rows_result,
            scenario_menu=scenario_menu,
        )

        return {
            "status": "ok",
            "screen_type": "assessment_factory_lite_demo_ui_html_screen",
            "package_name": "Assessment Factory Lite Demo Package",
            "release": "assessment-factory-lite-demo-ui",
            "version": "1.2.0",
            "sample_rows_result": sample_rows_result,
            "scenario_menu": scenario_menu,
            "html": html,
            "ui_view": ui_view,
            "operator_message": (
                "Assessment Factory Lite demo HTML screen rendered for the "
                "Operator Workstation."
            ),
            "recommended_action": "display_assessment_factory_lite_demo_screen",
        }

    def _build_html(
        self,
        ui_view: dict,
        sample_rows_result: dict | None = None,
        scenario_menu: dict | None = None,
    ) -> str:
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

        scenario_menu_html = self._render_scenario_menu(scenario_menu)
        sample_loader_html = self._render_sample_loader(sample_rows_result)

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

    <section class="afl-scenario-menu" aria-label="Demo scenario menu">
      <h2>Demo Scenario Menu</h2>
      {scenario_menu_html}
    </section>

    <section class="afl-sample-loader" aria-label="Sample data loader">
      <h2>Sample Data Loader</h2>
      {sample_loader_html}
    </section>

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

    def _render_scenario_menu(self, scenario_menu: dict | None) -> str:
        if scenario_menu is None:
            return "<p>Scenario menu was not included for this render.</p>"

        items_html = "\n".join(
            self._render_scenario_menu_item(item)
            for item in scenario_menu.get("menu_items", [])
        )

        default_scenario = escape(str(scenario_menu.get("default_scenario", "")))
        action = escape(str(scenario_menu.get("recommended_action", "")))

        return f"""<div class="afl-scenario-menu-summary">
  <p>Default scenario: {default_scenario}</p>
  <p>Action: {action}</p>
</div>
<div class="afl-scenario-menu-grid">
  {items_html}
</div>"""

    def _render_scenario_menu_item(self, item: dict) -> str:
        scenario = escape(str(item.get("scenario", "")))
        label = escape(str(item.get("label", "")))
        description = escape(str(item.get("description", "")))
        recommended_use = escape(str(item.get("recommended_use", "")))
        row_count = escape(str(item.get("row_count", 0)))
        expected_intervention = escape(str(item.get("expected_intervention", "")))
        ui_action = escape(str(item.get("ui_action", "")))
        sample_scenario = escape(
            str(item.get("html_payload", {}).get("sample_scenario", ""))
        )

        return f"""<article class="afl-scenario-card" data-scenario="{scenario}">
  <h3>{label}</h3>
  <p>{description}</p>
  <p>Recommended use: {recommended_use}</p>
  <p>Rows: {row_count}</p>
  <p>Expected intervention: {expected_intervention}</p>
  <p>UI action: {ui_action}</p>
  <p>HTML payload: sample_scenario={sample_scenario}</p>
</article>"""

    def _render_sample_loader(
        self,
        sample_rows_result: dict | None,
    ) -> str:
        if sample_rows_result is None:
            return (
                "<p>No canned sample scenario was loaded. "
                "Rows may have been provided directly.</p>"
            )

        scenario = escape(str(sample_rows_result.get("scenario", "")))
        label = escape(str(sample_rows_result.get("scenario_label", "")))
        row_count = escape(str(sample_rows_result.get("row_count", 0)))
        action = escape(str(sample_rows_result.get("recommended_action", "")))
        boundary = escape(str(sample_rows_result.get("boundary_type", "")))

        return f"""<article class="afl-sample-scenario" data-sample-scenario="{scenario}">
  <h3>{label}</h3>
  <p>Scenario: {scenario}</p>
  <p>Rows loaded: {row_count}</p>
  <p>Boundary: {boundary}</p>
  <p>Action: {action}</p>
</article>"""

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