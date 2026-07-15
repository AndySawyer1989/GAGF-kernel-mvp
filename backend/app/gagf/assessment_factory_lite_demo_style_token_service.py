class AssessmentFactoryLiteDemoStyleTokenService:
    """Build deterministic style tokens for the Assessment Factory Lite demo."""

    def build_tokens(self) -> dict:
        return {
            "status": "ok",
            "token_type": "assessment_factory_lite_demo_style_tokens",
            "package_name": "Assessment Factory Lite Demo Package",
            "release": "assessment-factory-lite-demo-usability",
            "version": "1.5.0",
            "brand_identity": self._brand_identity(),
            "color_tokens": self._color_tokens(),
            "typography_tokens": self._typography_tokens(),
            "spacing_tokens": self._spacing_tokens(),
            "layout_tokens": self._layout_tokens(),
            "component_tokens": self._component_tokens(),
            "accessibility_tokens": self._accessibility_tokens(),
            "demo_boundary": self._demo_boundary(),
            "operator_message": (
                "Assessment Factory Lite demo style tokens are ready for "
                "buyer-facing screen polish."
            ),
            "recommended_action": "apply_demo_style_tokens_to_html_screen",
        }

    def _brand_identity(self) -> dict:
        return {
            "style_name": "assessment_factory_lite_buyer_demo",
            "visual_intent": "clean_efficient_trustworthy_operator_screen",
            "primary_audience": "operations_leaders_and_it_managers",
            "tone": "practical_clear_confident",
            "identity_colors": [
                "orange",
                "white",
                "gold",
                "purple",
            ],
        }

    def _color_tokens(self) -> dict:
        return {
            "background": "#FFFFFF",
            "surface": "#FFF8EF",
            "surface_alt": "#F7F2FF",
            "text_primary": "#241A12",
            "text_secondary": "#5C4A3D",
            "brand_orange": "#F97316",
            "brand_gold": "#D6A21E",
            "brand_purple": "#6D28D9",
            "border_subtle": "#E8D8C8",
            "success": "#166534",
            "warning": "#B45309",
            "danger": "#B91C1C",
            "info": "#1D4ED8",
        }

    def _typography_tokens(self) -> dict:
        return {
            "font_family": (
                "Inter, ui-sans-serif, system-ui, -apple-system, "
                "BlinkMacSystemFont, Segoe UI, sans-serif"
            ),
            "display_size": "2.25rem",
            "heading_size": "1.35rem",
            "body_size": "1rem",
            "caption_size": "0.875rem",
            "display_weight": "750",
            "heading_weight": "700",
            "body_weight": "450",
            "line_height": "1.55",
        }

    def _spacing_tokens(self) -> dict:
        return {
            "space_xs": "0.25rem",
            "space_sm": "0.5rem",
            "space_md": "1rem",
            "space_lg": "1.5rem",
            "space_xl": "2rem",
            "space_2xl": "3rem",
        }

    def _layout_tokens(self) -> dict:
        return {
            "screen_max_width": "1180px",
            "screen_padding": "2rem",
            "section_gap": "1.5rem",
            "card_grid_min": "260px",
            "card_grid_gap": "1rem",
            "header_radius": "1.25rem",
            "card_radius": "1rem",
        }

    def _component_tokens(self) -> dict:
        return {
            "header_gradient": (
                "linear-gradient(135deg, #F97316 0%, #D6A21E 55%, "
                "#6D28D9 100%)"
            ),
            "header_text_color": "#FFFFFF",
            "card_background": "#FFFFFF",
            "card_border": "1px solid #E8D8C8",
            "card_shadow": "0 10px 28px rgba(36, 26, 18, 0.08)",
            "warning_background": "#FFF7ED",
            "warning_border": "1px solid #FDBA74",
            "scenario_card_background": "#F7F2FF",
            "scenario_card_border": "1px solid #C4B5FD",
            "sample_loader_background": "#FFF8EF",
            "sample_loader_border": "1px solid #FDBA74",
        }

    def _accessibility_tokens(self) -> dict:
        return {
            "minimum_contrast_goal": "WCAG_AA",
            "focus_outline": "3px solid #6D28D9",
            "focus_offset": "3px",
            "reduced_motion_safe": True,
            "color_alone_required": False,
        }

    def _demo_boundary(self) -> dict:
        return {
            "boundary_type": "demo_only_sample_data",
            "allowed_data": [
                "sample_csv",
                "synthetic_workflow_events",
                "mock_approval_events",
                "mock_delay_events",
            ],
            "prohibited_data": [
                "real_customer_data",
                "regulated_data",
                "federal_data",
                "production_customer_data",
                "customer_secrets",
                "live_security_telemetry",
            ],
            "certification_claims_allowed": False,
        }