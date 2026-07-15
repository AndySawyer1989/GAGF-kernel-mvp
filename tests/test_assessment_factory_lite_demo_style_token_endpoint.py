from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def test_assessment_factory_lite_demo_style_tokens_endpoint_returns_contract():
    response = client.get(
        "/products/assessment-factory-lite/demo-style-tokens"
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["status"] == "ok"
    assert payload["token_type"] == "assessment_factory_lite_demo_style_tokens"
    assert payload["package_name"] == "Assessment Factory Lite Demo Package"
    assert payload["release"] == "assessment-factory-lite-demo-usability"
    assert payload["version"] == "1.5.0"
    assert payload["recommended_action"] == "apply_demo_style_tokens_to_html_screen"


def test_assessment_factory_lite_demo_style_tokens_endpoint_returns_brand_identity():
    response = client.get(
        "/products/assessment-factory-lite/demo-style-tokens"
    )

    payload = response.json()

    assert payload["brand_identity"]["style_name"] == (
        "assessment_factory_lite_buyer_demo"
    )
    assert payload["brand_identity"]["visual_intent"] == (
        "clean_efficient_trustworthy_operator_screen"
    )
    assert payload["brand_identity"]["primary_audience"] == (
        "operations_leaders_and_it_managers"
    )
    assert payload["brand_identity"]["identity_colors"] == [
        "orange",
        "white",
        "gold",
        "purple",
    ]


def test_assessment_factory_lite_demo_style_tokens_endpoint_returns_color_tokens():
    response = client.get(
        "/products/assessment-factory-lite/demo-style-tokens"
    )

    payload = response.json()
    colors = payload["color_tokens"]

    assert colors["background"] == "#FFFFFF"
    assert colors["surface"] == "#FFF8EF"
    assert colors["surface_alt"] == "#F7F2FF"
    assert colors["brand_orange"] == "#F97316"
    assert colors["brand_gold"] == "#D6A21E"
    assert colors["brand_purple"] == "#6D28D9"
    assert colors["danger"] == "#B91C1C"


def test_assessment_factory_lite_demo_style_tokens_endpoint_returns_typography_and_layout_tokens():
    response = client.get(
        "/products/assessment-factory-lite/demo-style-tokens"
    )

    payload = response.json()

    assert "Inter" in payload["typography_tokens"]["font_family"]
    assert payload["typography_tokens"]["display_size"] == "2.25rem"
    assert payload["layout_tokens"]["screen_max_width"] == "1180px"
    assert payload["layout_tokens"]["screen_padding"] == "2rem"
    assert payload["layout_tokens"]["card_grid_min"] == "260px"
    assert payload["layout_tokens"]["card_radius"] == "1rem"


def test_assessment_factory_lite_demo_style_tokens_endpoint_returns_component_tokens():
    response = client.get(
        "/products/assessment-factory-lite/demo-style-tokens"
    )

    payload = response.json()
    components = payload["component_tokens"]

    assert "linear-gradient" in components["header_gradient"]
    assert "#F97316" in components["header_gradient"]
    assert "#D6A21E" in components["header_gradient"]
    assert "#6D28D9" in components["header_gradient"]
    assert components["card_shadow"] == "0 10px 28px rgba(36, 26, 18, 0.08)"
    assert components["scenario_card_background"] == "#F7F2FF"
    assert components["sample_loader_background"] == "#FFF8EF"


def test_assessment_factory_lite_demo_style_tokens_endpoint_returns_accessibility_tokens():
    response = client.get(
        "/products/assessment-factory-lite/demo-style-tokens"
    )

    payload = response.json()

    assert payload["accessibility_tokens"] == {
        "minimum_contrast_goal": "WCAG_AA",
        "focus_outline": "3px solid #6D28D9",
        "focus_offset": "3px",
        "reduced_motion_safe": True,
        "color_alone_required": False,
    }


def test_assessment_factory_lite_demo_style_tokens_endpoint_preserves_demo_boundary():
    response = client.get(
        "/products/assessment-factory-lite/demo-style-tokens"
    )

    payload = response.json()
    boundary = payload["demo_boundary"]

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


def test_assessment_factory_lite_demo_style_tokens_endpoint_route_exists_and_preserves_release_marker():
    actual_routes = {route.path for route in app.routes}

    assert "/products/assessment-factory-lite/demo-style-tokens" in actual_routes

    response = client.get("/version")

    assert response.status_code == 200
    assert response.json() == {
        "version": "1.5.0",
        "release": "assessment-factory-lite-demo-usability",
        "sprint": "4.4",
        "status": "complete",
    }