from fastapi.testclient import TestClient

from backend.app.gagf.assessment_factory_lite_demo_export_service import (
    AssessmentFactoryLiteDemoExportService,
)
from backend.app.gagf.assessment_factory_lite_demo_sample_rows_service import (
    AssessmentFactoryLiteDemoSampleRowsService,
)
from backend.app.main import app


client = TestClient(app)


def sample_rows(scenario="standard"):
    return AssessmentFactoryLiteDemoSampleRowsService().get_sample_rows(
        scenario
    )["rows"]


def test_assessment_factory_lite_buyer_export_polish_endpoint_returns_contract_from_rows():
    response = client.post(
        "/products/assessment-factory-lite/buyer-export/polish",
        json={"rows": sample_rows()},
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["status"] == "ok"
    assert payload["polish_type"] == (
        "assessment_factory_lite_buyer_export_polish"
    )
    assert payload["package_name"] == "Assessment Factory Lite Demo Package"
    assert payload["release"] == "assessment-factory-lite-demo-usability"
    assert payload["version"] == "1.5.0"
    assert payload["recommended_action"] == "present_polished_buyer_export"


def test_assessment_factory_lite_buyer_export_polish_endpoint_returns_buyer_copy():
    response = client.post(
        "/products/assessment-factory-lite/buyer-export/polish",
        json={"rows": sample_rows()},
    )

    payload = response.json()

    assert "workflow" in payload["buyer_headline"].lower()
    assert "buyer-facing findings" in payload["buyer_summary"]
    assert payload["key_findings"][0]["title"] == (
        "Approval delays are creating workflow drag"
    )
    assert payload["key_findings"][0]["friction_label"] == "approval_delay"


def test_assessment_factory_lite_buyer_export_polish_endpoint_returns_intervention_and_next_steps():
    response = client.post(
        "/products/assessment-factory-lite/buyer-export/polish",
        json={"rows": sample_rows()},
    )

    payload = response.json()

    assert payload["recommended_intervention"]["intervention_type"] == (
        "streamline_approval_path"
    )
    assert payload["recommended_intervention"]["title"] == (
        "Streamline the approval path"
    )
    assert payload["recommended_intervention"]["buyer_value"] == (
        "Reduce waiting time and make approval ownership clearer."
    )
    assert payload["next_steps"] == [
        "Review the top friction point with the workflow owner.",
        "Choose one narrow intervention to test first.",
        "Use the demo output to decide what evidence should be collected next.",
    ]


def test_assessment_factory_lite_buyer_export_polish_endpoint_accepts_export_summary():
    export_summary = AssessmentFactoryLiteDemoExportService().build_export_summary(
        rows=sample_rows()
    )

    response = client.post(
        "/products/assessment-factory-lite/buyer-export/polish",
        json={"export_summary": export_summary},
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["status"] == "ok"
    assert payload["source_export_summary"]["export_type"] == (
        "assessment_factory_lite_demo_export_summary"
    )
    assert payload["recommended_intervention"]["intervention_type"] == (
        "streamline_approval_path"
    )


def test_assessment_factory_lite_buyer_export_polish_endpoint_rejects_invalid_rows():
    response = client.post(
        "/products/assessment-factory-lite/buyer-export/polish",
        json={"rows": sample_rows("invalid")},
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["status"] == "rejected"
    assert payload["buyer_headline"] == (
        "Sample data needs repair before buyer presentation."
    )
    assert payload["key_findings"][0]["finding_type"] == (
        "sample_data_boundary_failure"
    )
    assert payload["recommended_intervention"]["action"] == (
        "repair_sample_csv_before_demo"
    )
    assert payload["recommended_action"] == "repair_sample_csv_before_demo"


def test_assessment_factory_lite_buyer_export_polish_endpoint_preserves_demo_boundary():
    response = client.post(
        "/products/assessment-factory-lite/buyer-export/polish",
        json={"rows": sample_rows()},
    )

    payload = response.json()
    boundary = payload["trust_and_boundary_note"]

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


def test_assessment_factory_lite_buyer_export_polish_endpoint_route_exists():
    actual_routes = {route.path for route in app.routes}

    assert (
        "/products/assessment-factory-lite/buyer-export/polish"
        in actual_routes
    )


def test_assessment_factory_lite_buyer_export_polish_endpoint_preserves_release_marker():
    response = client.get("/version")

    assert response.status_code == 200
    assert response.json() == {
        "version": "1.8.0",
        "release": "assessment-factory-lite-buyer-conversion",
        "sprint": "4.7",
        "status": "complete",
    }


