from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def test_assessment_factory_lite_proposal_package_release_marker():
    response = client.get("/version")

    assert response.status_code == 200
    assert response.json() == {
        "version": "2.1.0",
        "release": "assessment-factory-lite-proposal-export-package",
        "sprint": "5.0",
        "status": "complete",
    }


def test_assessment_factory_lite_proposal_package_routes_exist():
    actual_routes = {route.path for route in app.routes}

    assert "/products/assessment-factory-lite/proposal" in actual_routes
    assert "/products/assessment-factory-lite/proposal/html" in actual_routes
    assert "/products/assessment-factory-lite/assessment-offer" in actual_routes
    assert "/products/assessment-factory-lite/assessment-offer/html" in actual_routes


def test_assessment_factory_lite_proposal_object_contract_remains_on_commercial_offer_release():
    response = client.post("/products/assessment-factory-lite/proposal", json={})

    assert response.status_code == 200

    payload = response.json()

    assert payload["proposal_type"] == (
        "assessment_factory_lite_paid_assessment_proposal"
    )
    assert payload["version"] == "1.9.0"
    assert payload["release"] == "assessment-factory-lite-commercial-offer"
    assert payload["proposal_stage"] == "proposal_ready_artifact"
    assert payload["recommended_action"] == "review_proposal_ready_artifact"


def test_assessment_factory_lite_proposal_html_object_contract_remains_on_commercial_offer_release():
    response = client.post("/products/assessment-factory-lite/proposal/html", json={})

    assert response.status_code == 200

    payload = response.json()

    assert payload["view_type"] == (
        "assessment_factory_lite_paid_assessment_proposal_html_view"
    )
    assert payload["version"] == "1.9.0"
    assert payload["release"] == "assessment-factory-lite-commercial-offer"
    assert payload["view_stage"] == "proposal_ready_presentation"
    assert payload["recommended_action"] == "present_proposal_html_view"


def test_assessment_factory_lite_proposal_package_contains_proposal_assets():
    proposal_response = client.post("/products/assessment-factory-lite/proposal", json={})
    html_response = client.post("/products/assessment-factory-lite/proposal/html", json={})

    assert proposal_response.status_code == 200
    assert html_response.status_code == 200

    proposal = proposal_response.json()
    html = html_response.json()["html"]

    assert proposal["proposal_title"] == (
        "Assessment Factory Lite Proposal for approval and handoff workflow"
    )
    assert proposal["proposed_scope"]["scope_type"] == "bounded_friction_assessment"
    assert proposal["evidence_boundary"]["request_type"] == (
        "safe_non_sensitive_workflow_evidence"
    )
    assert proposal["commercial_terms_placeholder"]["recommended_price_band"] == {
        "low": 500,
        "high": 2500,
    }

    assert "Assessment Factory Lite Proposal" in html
    assert "proposal_ready_artifact" in html
    assert "USD 500 - 2500" in html
    assert "Evidence Boundary" in html
    assert "Approval Requirements" in html
    assert "Proposal Risk Controls" in html
