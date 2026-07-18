from backend.app.gagf.assessment_factory_lite_demo_style_token_service import (
    AssessmentFactoryLiteDemoStyleTokenService,
)


def service():
    return AssessmentFactoryLiteDemoStyleTokenService()


def test_assessment_factory_lite_demo_style_tokens_build_contract():
    result = service().build_tokens()

    assert result["status"] == "ok"
    assert result["token_type"] == "assessment_factory_lite_demo_style_tokens"
    assert result["package_name"] == "Assessment Factory Lite Demo Package"
    assert result["release"] == "assessment-factory-lite-demo-usability"
    assert result["version"] == "1.5.0"
    assert result["recommended_action"] == "apply_demo_style_tokens_to_html_screen"


def test_assessment_factory_lite_demo_style_tokens_brand_identity():
    result = service().build_tokens()

    assert result["brand_identity"] == {
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


def test_assessment_factory_lite_demo_style_tokens_color_palette():
    result = service().build_tokens()
    colors = result["color_tokens"]

    assert colors["background"] == "#FFFFFF"
    assert colors["surface"] == "#FFF8EF"
    assert colors["surface_alt"] == "#F7F2FF"
    assert colors["brand_orange"] == "#F97316"
    assert colors["brand_gold"] == "#D6A21E"
    assert colors["brand_purple"] == "#6D28D9"
    assert colors["success"] == "#166534"
    assert colors["warning"] == "#B45309"
    assert colors["danger"] == "#B91C1C"


def test_assessment_factory_lite_demo_style_tokens_typography():
    result = service().build_tokens()
    typography = result["typography_tokens"]

    assert "Inter" in typography["font_family"]
    assert typography["display_size"] == "2.25rem"
    assert typography["heading_size"] == "1.35rem"
    assert typography["body_size"] == "1rem"
    assert typography["caption_size"] == "0.875rem"
    assert typography["display_weight"] == "750"
    assert typography["heading_weight"] == "700"
    assert typography["line_height"] == "1.55"


def test_assessment_factory_lite_demo_style_tokens_spacing_and_layout():
    result = service().build_tokens()

    assert result["spacing_tokens"] == {
        "space_xs": "0.25rem",
        "space_sm": "0.5rem",
        "space_md": "1rem",
        "space_lg": "1.5rem",
        "space_xl": "2rem",
        "space_2xl": "3rem",
    }

    assert result["layout_tokens"]["screen_max_width"] == "1180px"
    assert result["layout_tokens"]["screen_padding"] == "2rem"
    assert result["layout_tokens"]["card_grid_min"] == "260px"
    assert result["layout_tokens"]["card_radius"] == "1rem"


def test_assessment_factory_lite_demo_style_tokens_component_tokens():
    result = service().build_tokens()
    components = result["component_tokens"]

    assert "linear-gradient" in components["header_gradient"]
    assert "#F97316" in components["header_gradient"]
    assert "#D6A21E" in components["header_gradient"]
    assert "#6D28D9" in components["header_gradient"]
    assert components["header_text_color"] == "#FFFFFF"
    assert components["card_background"] == "#FFFFFF"
    assert components["warning_background"] == "#FFF7ED"
    assert components["scenario_card_background"] == "#F7F2FF"
    assert components["sample_loader_background"] == "#FFF8EF"


def test_assessment_factory_lite_demo_style_tokens_accessibility():
    result = service().build_tokens()

    assert result["accessibility_tokens"] == {
        "minimum_contrast_goal": "WCAG_AA",
        "focus_outline": "3px solid #6D28D9",
        "focus_offset": "3px",
        "reduced_motion_safe": True,
        "color_alone_required": False,
    }


def test_assessment_factory_lite_demo_style_tokens_preserve_demo_boundary():
    result = service().build_tokens()
    boundary = result["demo_boundary"]

    assert boundary["boundary_type"] == "demo_only_sample_data"
    assert boundary["allowed_data"] == [
        "sample_csv",
        "synthetic_workflow_events",
        "mock_approval_events",
        "mock_delay_events",
    ]
    assert boundary["prohibited_data"] == [
        "real_customer_data",
        "regulated_data",
        "federal_data",
        "production_customer_data",
        "customer_secrets",
        "live_security_telemetry",
    ]
    assert boundary["certification_claims_allowed"] is False

