from fastapi.testclient import TestClient

from backend.app.gagf.assessment_factory_lite_demo_ui_html_service import (
    AssessmentFactoryLiteDemoUIHTMLService,
)
from backend.app.main import app


client = TestClient(app)


def service():
    return AssessmentFactoryLiteDemoUIHTMLService()


def test_assessment_factory_lite_demo_html_service_includes_style_tokens_by_default():
    result = service().render_html(sample_scenario="standard")

    assert result["status"] == "ok"
    assert result["style_tokens"]["token_type"] == (
        "assessment_factory_lite_demo_style_tokens"
    )
    assert result["style_tokens"]["release"] == (
        "assessment-factory-lite-demo-usability"
    )
    assert result["style_tokens"]["version"] == "1.5.0"
    assert '<style data-style-token-type="assessment_factory_lite_demo_style_tokens">' in (
        result["html"]
    )


def test_assessment_factory_lite_demo_html_service_renders_brand_css_variables():
    result = service().render_html(sample_scenario="standard")
    html = result["html"]

    assert "--afl-brand-orange: #F97316;" in html
    assert "--afl-brand-gold: #D6A21E;" in html
    assert "--afl-brand-purple: #6D28D9;" in html
    assert "--afl-surface: #FFF8EF;" in html
    assert "--afl-surface-alt: #F7F2FF;" in html
    assert "--afl-font-family:" in html
    assert "--afl-screen-max-width: 1180px;" in html
    assert "--afl-card-radius: 1rem;" in html


def test_assessment_factory_lite_demo_html_service_renders_component_css():
    result = service().render_html(sample_scenario="standard")
    html = result["html"]

    assert ".afl-demo-header" in html
    assert "background: var(--afl-header-gradient);" in html
    assert ".afl-scenario-card" in html
    assert "background: var(--afl-scenario-card-background);" in html
    assert ".afl-sample-scenario" in html
    assert "background: var(--afl-sample-loader-background);" in html
    assert ".afl-warning" in html
    assert "background: var(--afl-warning-background);" in html
    assert ".afl-card" in html
    assert "box-shadow: var(--afl-card-shadow);" in html


def test_assessment_factory_lite_demo_html_service_can_disable_style_tokens():
    result = service().render_html(
        sample_scenario="standard",
        include_style_tokens=False,
    )

    assert result["style_tokens"] is None
    assert "Style tokens were not included for this render." in result["html"]
    assert '<style data-style-token-type="assessment_factory_lite_demo_style_tokens">' not in (
        result["html"]
    )


def test_assessment_factory_lite_demo_html_endpoint_includes_style_tokens_by_default():
    response = client.post(
        "/products/assessment-factory-lite/demo-ui/html",
        json={"sample_scenario": "standard"},
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["style_tokens"]["token_type"] == (
        "assessment_factory_lite_demo_style_tokens"
    )
    assert payload["style_tokens"]["brand_identity"]["identity_colors"] == [
        "orange",
        "white",
        "gold",
        "purple",
    ]
    assert "--afl-brand-orange: #F97316;" in payload["html"]
    assert "Demo Scenario Menu" in payload["html"]
    assert "Sample Data Loader" in payload["html"]


def test_assessment_factory_lite_demo_html_endpoint_can_disable_style_tokens():
    response = client.post(
        "/products/assessment-factory-lite/demo-ui/html",
        json={
            "sample_scenario": "standard",
            "include_style_tokens": False,
        },
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["style_tokens"] is None
    assert "Style tokens were not included for this render." in payload["html"]
    assert "--afl-brand-orange: #F97316;" not in payload["html"]


def test_assessment_factory_lite_demo_html_response_contract_includes_style_tokens():
    result = service().render_html(sample_scenario="empty")

    assert set(result) == {
        "status",
        "screen_type",
        "package_name",
        "release",
        "version",
        "sample_rows_result",
        "scenario_menu",
        "style_tokens",
        "html",
        "ui_view",
        "operator_message",
        "recommended_action",
    }


def test_assessment_factory_lite_demo_html_style_integration_preserves_release_marker():
    response = client.get("/version")

    assert response.status_code == 200
    assert response.json() == {
        "version": "1.5.0",
        "release": "assessment-factory-lite-demo-usability",
        "sprint": "4.4",
        "status": "complete",
    }