from fastapi.testclient import TestClient

from backend.app.gagf.assessment_factory_lite_demo_ui_html_service import (
    AssessmentFactoryLiteDemoUIHTMLService,
)
from backend.app.main import app


client = TestClient(app)


def service():
    return AssessmentFactoryLiteDemoUIHTMLService()


def test_assessment_factory_lite_demo_html_service_includes_scenario_menu_by_default():
    result = service().render_html(sample_scenario="standard")

    assert result["status"] == "ok"
    assert result["scenario_menu"]["menu_type"] == (
        "assessment_factory_lite_demo_scenario_menu"
    )
    assert result["scenario_menu"]["default_scenario"] == "standard"
    assert [item["scenario"] for item in result["scenario_menu"]["menu_items"]] == [
        "standard",
        "invalid",
        "empty",
    ]
    assert "Demo Scenario Menu" in result["html"]
    assert 'data-scenario="standard"' in result["html"]
    assert 'data-scenario="invalid"' in result["html"]
    assert 'data-scenario="empty"' in result["html"]


def test_assessment_factory_lite_demo_html_service_renders_menu_item_payloads():
    result = service().render_html(sample_scenario="standard")

    assert "HTML payload: sample_scenario=standard" in result["html"]
    assert "HTML payload: sample_scenario=invalid" in result["html"]
    assert "HTML payload: sample_scenario=empty" in result["html"]
    assert "load_standard_demo_scenario" in result["html"]
    assert "load_invalid_boundary_test_scenario" in result["html"]
    assert "load_empty_demo_scenario" in result["html"]


def test_assessment_factory_lite_demo_html_service_can_disable_scenario_menu():
    result = service().render_html(
        sample_scenario="standard",
        include_scenario_menu=False,
    )

    assert result["scenario_menu"] is None
    assert "Scenario menu was not included for this render." in result["html"]
    assert 'data-scenario="standard"' not in result["html"]


def test_assessment_factory_lite_demo_html_endpoint_includes_scenario_menu_by_default():
    response = client.post(
        "/products/assessment-factory-lite/demo-ui/html",
        json={"sample_scenario": "standard"},
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["status"] == "ok"
    assert payload["scenario_menu"]["default_scenario"] == "standard"
    assert [item["scenario"] for item in payload["scenario_menu"]["menu_items"]] == [
        "standard",
        "invalid",
        "empty",
    ]
    assert "Demo Scenario Menu" in payload["html"]
    assert 'data-scenario="standard"' in payload["html"]
    assert "HTML payload: sample_scenario=standard" in payload["html"]


def test_assessment_factory_lite_demo_html_endpoint_can_disable_scenario_menu():
    response = client.post(
        "/products/assessment-factory-lite/demo-ui/html",
        json={
            "sample_scenario": "standard",
            "include_scenario_menu": False,
        },
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["scenario_menu"] is None
    assert "Scenario menu was not included for this render." in payload["html"]
    assert 'data-scenario="standard"' not in payload["html"]


def test_assessment_factory_lite_demo_html_endpoint_preserves_sample_loader():
    response = client.post(
        "/products/assessment-factory-lite/demo-ui/html",
        json={"sample_scenario": "invalid"},
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["sample_rows_result"]["scenario"] == "invalid"
    assert payload["sample_rows_result"]["is_valid_sample"] is False
    assert "Sample Data Loader" in payload["html"]
    assert 'data-sample-scenario="invalid"' in payload["html"]
    assert "Demo Scenario Menu" in payload["html"]


def test_assessment_factory_lite_demo_html_endpoint_route_preserves_release_marker():
    response = client.get("/version")

    assert response.status_code == 200
    assert response.json() == {
        "version": "1.7.0",
        "release": "assessment-factory-lite-demo-delivery-packaging",
        "sprint": "4.6",
        "status": "complete",
    }


def test_assessment_factory_lite_demo_html_screen_response_contract_includes_scenario_menu():
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




