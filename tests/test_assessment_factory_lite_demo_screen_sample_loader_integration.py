from fastapi.testclient import TestClient

from backend.app.gagf.assessment_factory_lite_demo_ui_html_service import (
    AssessmentFactoryLiteDemoUIHTMLService,
)
from backend.app.main import app


client = TestClient(app)


def service():
    return AssessmentFactoryLiteDemoUIHTMLService()


def test_assessment_factory_lite_demo_html_service_loads_standard_sample_scenario():
    result = service().render_html(sample_scenario="standard")

    assert result["status"] == "ok"
    assert result["sample_rows_result"]["scenario"] == "standard"
    assert result["sample_rows_result"]["row_count"] == 3
    assert result["sample_rows_result"]["is_valid_sample"] is True
    assert result["ui_view"]["source_payloads"]["diagnostics_result"]["status"] == (
        "ok"
    )
    assert "Sample Data Loader" in result["html"]
    assert 'data-sample-scenario="standard"' in result["html"]
    assert "Approval Delay and Blocked Work" in result["html"]


def test_assessment_factory_lite_demo_html_service_loads_invalid_sample_scenario():
    result = service().render_html(sample_scenario="invalid")

    assert result["status"] == "ok"
    assert result["sample_rows_result"]["scenario"] == "invalid"
    assert result["sample_rows_result"]["is_valid_sample"] is False
    assert result["ui_view"]["source_payloads"]["diagnostics_result"]["status"] == (
        "rejected"
    )
    assert "Unsafe Data Boundary Example" in result["html"]
    assert "repair_sample_csv_before_demo" in result["html"]


def test_assessment_factory_lite_demo_html_service_loads_empty_sample_scenario():
    result = service().render_html(sample_scenario="empty")

    assert result["status"] == "ok"
    assert result["sample_rows_result"]["scenario"] == "empty"
    assert result["sample_rows_result"]["row_count"] == 0
    assert result["ui_view"]["source_payloads"]["diagnostics_result"]["row_count"] == 0
    assert "Empty Demo Starting State" in result["html"]
    assert "add_synthetic_sample_rows" in result["html"]


def test_assessment_factory_lite_demo_html_service_direct_rows_have_no_sample_loader_result():
    rows = [
        {
            "event_id": "evt-001",
            "case_id": "case-001",
            "event_type": "approval_delayed",
            "actor": "approver",
            "team": "operations",
            "timestamp": "2026-01-01T13:00:00Z",
            "severity": "high",
            "description": "Synthetic approval delayed.",
            "constraint_label": "approval_delay",
            "duration_minutes": 240,
        }
    ]

    result = service().render_html(rows=rows)

    assert result["sample_rows_result"] is None
    assert "No canned sample scenario was loaded" in result["html"]


def test_assessment_factory_lite_demo_html_endpoint_loads_standard_sample_scenario():
    response = client.post(
        "/products/assessment-factory-lite/demo-ui/html",
        json={"sample_scenario": "standard"},
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["status"] == "ok"
    assert payload["sample_rows_result"]["scenario"] == "standard"
    assert payload["sample_rows_result"]["row_count"] == 3
    assert payload["ui_view"]["source_payloads"]["diagnostics_result"]["status"] == (
        "ok"
    )
    assert "Sample Data Loader" in payload["html"]
    assert 'data-sample-scenario="standard"' in payload["html"]


def test_assessment_factory_lite_demo_html_endpoint_loads_invalid_sample_scenario():
    response = client.post(
        "/products/assessment-factory-lite/demo-ui/html",
        json={"sample_scenario": "invalid"},
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["sample_rows_result"]["scenario"] == "invalid"
    assert payload["sample_rows_result"]["is_valid_sample"] is False
    assert payload["ui_view"]["source_payloads"]["diagnostics_result"]["status"] == (
        "rejected"
    )
    assert "repair_sample_csv_before_demo" in payload["html"]


def test_assessment_factory_lite_demo_html_endpoint_preserves_release_marker():
    response = client.get("/version")

    assert response.status_code == 200
    assert response.json() == {
        "version": "2.3.0",
        "release": "assessment-factory-lite-scope-call-conversion",
        "sprint": "5.0",
        "status": "complete",
    }











