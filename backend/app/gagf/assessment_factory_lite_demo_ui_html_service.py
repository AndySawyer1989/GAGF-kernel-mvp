from html import escape

from backend.app.gagf.assessment_factory_lite_demo_sample_rows_service import (
    AssessmentFactoryLiteDemoSampleRowsService,
)
from backend.app.gagf.assessment_factory_lite_demo_scenario_menu_service import (
    AssessmentFactoryLiteDemoScenarioMenuService,
)
from backend.app.gagf.assessment_factory_lite_demo_style_token_service import (
    AssessmentFactoryLiteDemoStyleTokenService,
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
        style_token_service: AssessmentFactoryLiteDemoStyleTokenService | None = None,
    ):
        self.ui_view_service = ui_view_service or AssessmentFactoryLiteDemoUIViewService()
        self.sample_rows_service = (
            sample_rows_service or AssessmentFactoryLiteDemoSampleRowsService()
        )
        self.scenario_menu_service = (
            scenario_menu_service or AssessmentFactoryLiteDemoScenarioMenuService()
        )
        self.style_token_service = (
            style_token_service or AssessmentFactoryLiteDemoStyleTokenService()
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
        include_style_tokens: bool = True,
    ) -> dict:
        sample_rows_result = None
        scenario_menu = (
            self.scenario_menu_service.build_menu()
            if include_scenario_menu
            else None
        )
        style_tokens = (
            self.style_token_service.build_tokens()
            if include_style_tokens
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
            style_tokens=style_tokens,
        )

        return {
            "status": "ok",
            "screen_type": "assessment_factory_lite_demo_ui_html_screen",
            "package_name": "Assessment Factory Lite Demo Package",
            "release": "assessment-factory-lite-demo-ui",
            "version": "1.2.0",
            "sample_rows_result": sample_rows_result,
            "scenario_menu": scenario_menu,
            "style_tokens": style_tokens,
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
        style_tokens: dict | None = None,
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

        css_html = self._render_style_block(style_tokens)
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
  {css_html}
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

    def _render_style_block(self, style_tokens: dict | None) -> str:
        if style_tokens is None:
            return "<!-- Style tokens were not included for this render. -->"

        colors = style_tokens.get("color_tokens", {})
        typography = style_tokens.get("typography_tokens", {})
        spacing = style_tokens.get("spacing_tokens", {})
        layout = style_tokens.get("layout_tokens", {})
        components = style_tokens.get("component_tokens", {})
        accessibility = style_tokens.get("accessibility_tokens", {})

        return f"""<style data-style-token-type="{escape(style_tokens.get("token_type", ""))}">
:root {{
  --afl-background: {escape(colors.get("background", "#FFFFFF"))};
  --afl-surface: {escape(colors.get("surface", "#FFF8EF"))};
  --afl-surface-alt: {escape(colors.get("surface_alt", "#F7F2FF"))};
  --afl-text-primary: {escape(colors.get("text_primary", "#241A12"))};
  --afl-text-secondary: {escape(colors.get("text_secondary", "#5C4A3D"))};
  --afl-brand-orange: {escape(colors.get("brand_orange", "#F97316"))};
  --afl-brand-gold: {escape(colors.get("brand_gold", "#D6A21E"))};
  --afl-brand-purple: {escape(colors.get("brand_purple", "#6D28D9"))};
  --afl-border-subtle: {escape(colors.get("border_subtle", "#E8D8C8"))};
  --afl-danger: {escape(colors.get("danger", "#B91C1C"))};
  --afl-warning: {escape(colors.get("warning", "#B45309"))};
  --afl-success: {escape(colors.get("success", "#166534"))};
  --afl-info: {escape(colors.get("info", "#1D4ED8"))};
  --afl-font-family: {escape(typography.get("font_family", "system-ui"))};
  --afl-display-size: {escape(typography.get("display_size", "2.25rem"))};
  --afl-heading-size: {escape(typography.get("heading_size", "1.35rem"))};
  --afl-body-size: {escape(typography.get("body_size", "1rem"))};
  --afl-caption-size: {escape(typography.get("caption_size", "0.875rem"))};
  --afl-display-weight: {escape(typography.get("display_weight", "750"))};
  --afl-heading-weight: {escape(typography.get("heading_weight", "700"))};
  --afl-line-height: {escape(typography.get("line_height", "1.55"))};
  --afl-space-sm: {escape(spacing.get("space_sm", "0.5rem"))};
  --afl-space-md: {escape(spacing.get("space_md", "1rem"))};
  --afl-space-lg: {escape(spacing.get("space_lg", "1.5rem"))};
  --afl-space-xl: {escape(spacing.get("space_xl", "2rem"))};
  --afl-screen-max-width: {escape(layout.get("screen_max_width", "1180px"))};
  --afl-screen-padding: {escape(layout.get("screen_padding", "2rem"))};
  --afl-section-gap: {escape(layout.get("section_gap", "1.5rem"))};
  --afl-card-grid-min: {escape(layout.get("card_grid_min", "260px"))};
  --afl-card-grid-gap: {escape(layout.get("card_grid_gap", "1rem"))};
  --afl-header-radius: {escape(layout.get("header_radius", "1.25rem"))};
  --afl-card-radius: {escape(layout.get("card_radius", "1rem"))};
  --afl-header-gradient: {escape(components.get("header_gradient", "linear-gradient(135deg, #F97316 0%, #D6A21E 55%, #6D28D9 100%)"))};
  --afl-header-text-color: {escape(components.get("header_text_color", "#FFFFFF"))};
  --afl-card-background: {escape(components.get("card_background", "#FFFFFF"))};
  --afl-card-border: {escape(components.get("card_border", "1px solid #E8D8C8"))};
  --afl-card-shadow: {escape(components.get("card_shadow", "0 10px 28px rgba(36, 26, 18, 0.08)"))};
  --afl-warning-background: {escape(components.get("warning_background", "#FFF7ED"))};
  --afl-warning-border: {escape(components.get("warning_border", "1px solid #FDBA74"))};
  --afl-scenario-card-background: {escape(components.get("scenario_card_background", "#F7F2FF"))};
  --afl-scenario-card-border: {escape(components.get("scenario_card_border", "1px solid #C4B5FD"))};
  --afl-sample-loader-background: {escape(components.get("sample_loader_background", "#FFF8EF"))};
  --afl-sample-loader-border: {escape(components.get("sample_loader_border", "1px solid #FDBA74"))};
  --afl-focus-outline: {escape(accessibility.get("focus_outline", "3px solid #6D28D9"))};
  --afl-focus-offset: {escape(accessibility.get("focus_offset", "3px"))};
}}

* {{
  box-sizing: border-box;
}}

body {{
  margin: 0;
  background: var(--afl-background);
  color: var(--afl-text-primary);
  font-family: var(--afl-font-family);
  font-size: var(--afl-body-size);
  line-height: var(--afl-line-height);
}}

a:focus,
button:focus,
[tabindex]:focus {{
  outline: var(--afl-focus-outline);
  outline-offset: var(--afl-focus-offset);
}}

.afl-demo-screen {{
  max-width: var(--afl-screen-max-width);
  margin: 0 auto;
  padding: var(--afl-screen-padding);
  display: grid;
  gap: var(--afl-section-gap);
}}

.afl-demo-header {{
  background: var(--afl-header-gradient);
  color: var(--afl-header-text-color);
  border-radius: var(--afl-header-radius);
  padding: var(--afl-space-xl);
  box-shadow: var(--afl-card-shadow);
}}

.afl-demo-header h1 {{
  margin: 0;
  font-size: var(--afl-display-size);
  font-weight: var(--afl-display-weight);
}}

.afl-kicker,
.afl-subtitle,
.afl-release {{
  margin: 0 0 var(--afl-space-sm) 0;
}}

.afl-scenario-menu,
.afl-sample-loader,
.afl-warning-strip,
.afl-card-grid,
.afl-export-preview,
.afl-next-actions {{
  background: var(--afl-card-background);
  border: var(--afl-card-border);
  border-radius: var(--afl-card-radius);
  padding: var(--afl-space-lg);
  box-shadow: var(--afl-card-shadow);
}}

.afl-scenario-menu-grid,
.afl-card-grid {{
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(var(--afl-card-grid-min), 1fr));
  gap: var(--afl-card-grid-gap);
}}

.afl-scenario-card {{
  background: var(--afl-scenario-card-background);
  border: var(--afl-scenario-card-border);
  border-radius: var(--afl-card-radius);
  padding: var(--afl-space-md);
}}

.afl-sample-scenario {{
  background: var(--afl-sample-loader-background);
  border: var(--afl-sample-loader-border);
  border-radius: var(--afl-card-radius);
  padding: var(--afl-space-md);
}}

.afl-warning {{
  background: var(--afl-warning-background);
  border: var(--afl-warning-border);
  border-radius: var(--afl-card-radius);
  padding: var(--afl-space-md);
}}

.afl-card {{
  background: var(--afl-card-background);
  border: var(--afl-card-border);
  border-radius: var(--afl-card-radius);
  padding: var(--afl-space-md);
}}

.afl-card-status,
.afl-card-primary,
.afl-card-action,
.afl-disclaimer {{
  color: var(--afl-text-secondary);
}}

h2,
h3 {{
  font-size: var(--afl-heading-size);
  font-weight: var(--afl-heading-weight);
}}

@media (prefers-reduced-motion: reduce) {{
  *,
  *::before,
  *::after {{
    scroll-behavior: auto !important;
  }}
}}
</style>"""

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