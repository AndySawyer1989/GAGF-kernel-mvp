from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def test_assessment_factory_lite_proposal_html_endpoint_returns_contract():
    response = client.post("/products/assessment-factory-lite/proposal/html", json={})

    assert response.status_code == 200

    payload = response.json()

    assert payload["status"] == "ok"
    assert payload["view_type"] == (
        "assessment_factory_lite_paid_assessment_proposal_html_view"
    )
    assert payload["package_name"] == "Assessment Factory Lite Demo Package"
    assert payload["release"] == "assessment-factory-lite-commercial-offer"
    assert payload["version"] == "1.9.0"
    assert payload["view_stage"] == "proposal_ready_presentation"
    assert payload["recommended_action"] == "present_proposal_html_view"


def test_assessment_factory_lite_proposal_html_endpoint_returns_source_proposal_and_sections():
    response = client.post("/products/assessment-factory-lite/proposal/html", json={})

    payload = response.json()

    assert payload["source_proposal"]["proposal_type"] == (
        "assessment_factory_lite_paid_assessment_proposal"
    )

    assert payload["view_sections"] == [
        "proposal_header",
        "buyer_context",
        "problem_statement",
        "proposed_scope",
        "evidence_boundary",
        "deliverables",
        "timeline",
        "commercial_terms_placeholder",
        "approval_requirements",
        "proposal_risk_controls",
        "excluded_scope",
        "next_action",
    ]


def test_assessment_factory_lite_proposal_html_endpoint_contains_document_structure():
    response = client.post("/products/assessment-factory-lite/proposal/html", json={})

    html = response.json()["html"]

    assert "<!doctype html>" in html
    assert '<html lang="en">' in html
    assert "<title>Assessment Factory Lite Proposal</title>" in html
    assert (
        'data-view="assessment-factory-lite-paid-assessment-proposal-html-view"'
        in html
    )
    assert "Assessment Factory Lite Proposal for approval and handoff workflow" in html
    assert "proposal_ready_artifact" in html


def test_assessment_factory_lite_proposal_html_endpoint_contains_sections():
    response = client.post("/products/assessment-factory-lite/proposal/html", json={})

    html = response.json()["html"]

    assert 'data-section="buyer_context"' in html
    assert 'data-section="problem_statement"' in html
    assert 'data-section="proposed_scope"' in html
    assert 'data-section="evidence_boundary"' in html
    assert 'data-section="deliverables"' in html
    assert 'data-section="timeline"' in html
    assert 'data-section="commercial_terms_placeholder"' in html
    assert 'data-section="approval_requirements"' in html
    assert 'data-section="proposal_risk_controls"' in html
    assert 'data-section="excluded_scope"' in html
    assert 'data-section="next_action"' in html


def test_assessment_factory_lite_proposal_html_endpoint_contains_proposal_content():
    response = client.post("/products/assessment-factory-lite/proposal/html", json={})

    html = response.json()["html"]

    assert "operations_leader" in html
    assert "approval and handoff workflow" in html
    assert "approval_delay" in html
    assert "bounded_friction_assessment" in html
    assert "safe_non_sensitive_workflow_evidence" in html
    assert "assessment_summary" in html
    assert "recommended_next_test" in html
    assert "fixed_fee_discovery_assessment" in html
    assert "USD 500 - 2500" in html
    assert "review_and_prepare_proposal" in html


def test_assessment_factory_lite_proposal_html_endpoint_contains_timeline_approvals_and_controls():
    response = client.post("/products/assessment-factory-lite/proposal/html", json={})

    html = response.json()["html"]

    assert 'data-phase="intake"' in html
    assert 'data-phase="evidence_review"' in html
    assert 'data-phase="diagnostic_summary"' in html
    assert 'data-phase="recommendation_review"' in html

    assert 'data-approval="evidence_boundary_approval"' in html
    assert 'data-approval="commercial_terms_approval"' in html
    assert 'data-approval="buyer_scope_acknowledgement"' in html

    assert 'data-control="non_binding_proposal_until_operator_approval"' in html
    assert 'data-control="safe_evidence_boundary_required"' in html
    assert 'data-control="excluded_scope_must_be_visible"' in html
    assert 'data-control="human_review_before_sending"' in html


def test_assessment_factory_lite_proposal_html_endpoint_preserves_boundaries_and_exclusions():
    response = client.post("/products/assessment-factory-lite/proposal/html", json={})

    html = response.json()["html"]

    assert "Evidence Boundary" in html
    assert "redacted_workflow_export" in html
    assert "manual_workflow_summary" in html
    assert "regulated_health_data" in html
    assert "federal_sensitive_data" in html
    assert "live_security_telemetry" in html
    assert "Certification claims allowed:" in html
    assert "Binding price quote allowed:" in html
    assert "False" in html

    assert "production_customer_data_processing" in html
    assert "regulated_data_processing" in html
    assert "federal_data_processing" in html
    assert "guaranteed_operational_outcomes" in html
    assert "binding_legal_or_compliance_advice" in html


def test_assessment_factory_lite_proposal_html_endpoint_accepts_custom_context_and_preserves_release_marker():
    response = client.post(
        "/products/assessment-factory-lite/proposal/html",
        json={
            "buyer_context": {
                "primary_buyer": "founder_operator",
                "workflow_area": "security review workflow",
                "duration": "5_to_7_business_days",
                "price_low": 1500,
                "price_high": 3500,
            }
        },
    )

    assert response.status_code == 200

    payload = response.json()
    html = payload["html"]

    assert "founder_operator" in html
    assert "security review workflow" in html
    assert "5_to_7_business_days" in html
    assert "USD 1500 - 3500" in html

    actual_routes = {route.path for route in app.routes}

    assert "/products/assessment-factory-lite/proposal/html" in actual_routes

    version_response = client.get("/version")

    assert version_response.status_code == 200
    assert version_response.json() == {
        "version": "1.9.0",
        "release": "assessment-factory-lite-commercial-offer",
        "sprint": "4.8",
        "status": "complete",
    }