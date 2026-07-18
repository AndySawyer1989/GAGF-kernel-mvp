from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def test_assessment_factory_lite_proposal_export_package_release_marker():
    response = client.get("/version")

    assert response.status_code == 200
    assert response.json() == {
        "version": "2.2.0",
        "release": "assessment-factory-lite-buyer-delivery-follow-up",
        "sprint": "5.0",
        "status": "complete",
    }


def test_assessment_factory_lite_proposal_export_package_release_routes_exist():
    actual_routes = {route.path for route in app.routes}

    assert "/products/assessment-factory-lite/proposal/export-package" in actual_routes
    assert "/products/assessment-factory-lite/proposal/document/pdf" in actual_routes
    assert "/products/assessment-factory-lite/proposal/document/pdf-readiness" in actual_routes
    assert "/products/assessment-factory-lite/proposal/document/markdown" in actual_routes
    assert "/products/assessment-factory-lite/proposal/document" in actual_routes


def test_assessment_factory_lite_proposal_export_package_object_contract_remains_on_proposal_package_release():
    response = client.post(
        "/products/assessment-factory-lite/proposal/export-package",
        json={},
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["package_type"] == "assessment_factory_lite_proposal_export_package"
    assert payload["release"] == "assessment-factory-lite-proposal-package"
    assert payload["version"] == "2.0.0"
    assert payload["package_stage"] == "proposal_export_package"
    assert payload["package_status"] == "ready"
    assert payload["recommended_action"] == "review_proposal_export_package"


def test_assessment_factory_lite_proposal_export_package_release_preserves_export_object_contracts():
    markdown_response = client.post(
        "/products/assessment-factory-lite/proposal/document/markdown",
        json={},
    )
    readiness_response = client.post(
        "/products/assessment-factory-lite/proposal/document/pdf-readiness",
        json={},
    )
    pdf_response = client.post(
        "/products/assessment-factory-lite/proposal/document/pdf",
        json={},
    )

    assert markdown_response.status_code == 200
    assert readiness_response.status_code == 200
    assert pdf_response.status_code == 200

    markdown = markdown_response.json()
    readiness = readiness_response.json()
    pdf = pdf_response.json()

    assert markdown["export_type"] == (
        "assessment_factory_lite_formal_proposal_markdown_export"
    )
    assert markdown["release"] == "assessment-factory-lite-proposal-package"
    assert markdown["version"] == "2.0.0"
    assert markdown["export_stage"] == "formal_proposal_markdown_export"

    assert readiness["readiness_type"] == (
        "assessment_factory_lite_formal_proposal_pdf_readiness"
    )
    assert readiness["release"] == "assessment-factory-lite-proposal-package"
    assert readiness["version"] == "2.0.0"
    assert readiness["readiness_stage"] == "formal_proposal_pdf_readiness_check"

    assert pdf["export_type"] == "assessment_factory_lite_formal_proposal_pdf_export"
    assert pdf["release"] == "assessment-factory-lite-proposal-package"
    assert pdf["version"] == "2.0.0"
    assert pdf["export_stage"] == "formal_proposal_pdf_export"


def test_assessment_factory_lite_proposal_export_package_release_contains_export_chain():
    response = client.post(
        "/products/assessment-factory-lite/proposal/export-package",
        json={},
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["markdown_export"]["format"] == "markdown"
    assert payload["markdown_export"]["markdown_present"] is True
    assert payload["markdown_export"]["section_count"] == 14

    assert payload["pdf_readiness"]["ready_for_pdf"] is True
    assert payload["pdf_readiness"]["readiness_score"] == 1.0
    assert payload["pdf_readiness"]["blocking_issues"] == []

    assert payload["pdf_export"]["status"] == "ok"
    assert payload["pdf_export"]["format"] == "pdf"
    assert payload["pdf_export"]["content_type"] == "application/pdf"

    assert payload["export_manifest"]["package_manifest_type"] == (
        "proposal_export_package_manifest"
    )
    assert payload["operator_approval"]["approval_status"] == (
        "operator_review_required"
    )
    assert payload["next_action"]["action"] == (
        "review_and_prepare_buyer_delivery_package"
    )
