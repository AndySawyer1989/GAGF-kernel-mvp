from pathlib import Path


DOC_PATH = Path("docs/ASSESSMENT_FACTORY_LITE_DEMO_STYLE_TOKENS.md")


def test_assessment_factory_lite_demo_style_token_document_exists():
    assert DOC_PATH.exists()


def test_assessment_factory_lite_demo_style_token_document_names_service_and_endpoint():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "AssessmentFactoryLiteDemoStyleTokenService" in content
    assert "GET /products/assessment-factory-lite/demo-style-tokens" in content
    assert "assessment_factory_lite_demo_style_tokens" in content
    assert "assessment-factory-lite-demo-usability" in content
    assert "1.5.0" in content


def test_assessment_factory_lite_demo_style_token_document_names_response_contract():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "status" in content
    assert "token_type" in content
    assert "package_name" in content
    assert "release" in content
    assert "version" in content
    assert "brand_identity" in content
    assert "color_tokens" in content
    assert "typography_tokens" in content
    assert "spacing_tokens" in content
    assert "layout_tokens" in content
    assert "component_tokens" in content
    assert "accessibility_tokens" in content
    assert "demo_boundary" in content
    assert "operator_message" in content
    assert "recommended_action" in content


def test_assessment_factory_lite_demo_style_token_document_names_brand_identity():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "assessment_factory_lite_buyer_demo" in content
    assert "clean_efficient_trustworthy_operator_screen" in content
    assert "operations_leaders_and_it_managers" in content
    assert "practical_clear_confident" in content
    assert "orange" in content
    assert "white" in content
    assert "gold" in content
    assert "purple" in content


def test_assessment_factory_lite_demo_style_token_document_names_color_tokens():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "background #FFFFFF" in content
    assert "surface #FFF8EF" in content
    assert "surface_alt #F7F2FF" in content
    assert "brand_orange #F97316" in content
    assert "brand_gold #D6A21E" in content
    assert "brand_purple #6D28D9" in content
    assert "success #166534" in content
    assert "warning #B45309" in content
    assert "danger #B91C1C" in content
    assert "info #1D4ED8" in content


def test_assessment_factory_lite_demo_style_token_document_names_typography_spacing_and_layout():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "Inter" in content
    assert "display_size 2.25rem" in content
    assert "heading_size 1.35rem" in content
    assert "body_size 1rem" in content
    assert "caption_size 0.875rem" in content
    assert "line_height 1.55" in content
    assert "space_xs 0.25rem" in content
    assert "space_2xl 3rem" in content
    assert "screen_max_width 1180px" in content
    assert "screen_padding 2rem" in content
    assert "card_grid_min 260px" in content
    assert "card_radius 1rem" in content


def test_assessment_factory_lite_demo_style_token_document_names_component_and_accessibility_tokens():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "header_gradient" in content
    assert "#F97316" in content
    assert "#D6A21E" in content
    assert "#6D28D9" in content
    assert "card_shadow 0 10px 28px rgba(36, 26, 18, 0.08)" in content
    assert "scenario_card_background #F7F2FF" in content
    assert "sample_loader_background #FFF8EF" in content
    assert "minimum_contrast_goal WCAG_AA" in content
    assert "focus_outline 3px solid #6D28D9" in content
    assert "reduced_motion_safe true" in content
    assert "color_alone_required false" in content


def test_assessment_factory_lite_demo_style_token_document_preserves_boundaries():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "demo-only" in content
    assert "sample_csv" in content
    assert "synthetic_workflow_events" in content
    assert "mock_approval_events" in content
    assert "mock_delay_events" in content
    assert "real_customer_data" in content
    assert "regulated_data" in content
    assert "federal_data" in content
    assert "live_security_telemetry" in content
    assert (
        "The Assessment Factory Lite Demo Style Tokens layer does not "
        "certify products as FedRAMP High, HIPAA compliant, SOC 2 audited, "
        "WCAG certified, or production-ready."
    ) in content
    assert (
        "The deterministic GAGF Kernel remains the authoritative decision "
        "and verification layer."
    ) in content