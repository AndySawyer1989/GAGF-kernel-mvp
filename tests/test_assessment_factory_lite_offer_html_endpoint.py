from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def test_assessment_factory_lite_offer_html_endpoint_returns_contract():
    response = client.post(
        "/products/assessment-factory-lite/assessment-offer/html",
        json={},
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["status"] == "ok"
    assert payload["view_type"] == (
        "assessment_factory_lite_paid_assessment_offer_html_view"
    )
    assert payload["package_name"] == "Assessment Factory Lite Demo Package"
    assert payload["release"] == "assessment-factory-lite-buyer-conversion"
    assert payload["version"] == "1.8.0"
    assert payload["view_stage"] == "paid_assessment_conversion"
    assert payload["recommended_action"] == "present_paid_assessment_offer_html_view"


def test_assessment_factory_lite_offer_html_endpoint_returns_source_offer_and_sections():
    response = client.post(
        "/products/assessment-factory-lite/assessment-offer/html",
        json={},
    )

    payload = response.json()

    assert payload["source_offer"]["offer_type"] == (
        "assessment_factory_lite_paid_assessment_offer"
    )

    assert payload["view_sections"] == [
        "offer_header",
        "target_buyer",
        "problem_statement",
        "safe_evidence_request",
        "assessment_scope",
        "deliverable",
        "recommended_price_band",
        "buyer_commitment",
        "qualification_questions",
        "risk_controls",
        "next_action",
        "demo_boundary",
        "excluded_scope",
    ]


def test_assessment_factory_lite_offer_html_endpoint_contains_document_structure():
    response = client.post(
        "/products/assessment-factory-lite/assessment-offer/html",
        json={},
    )

    html = response.json()["html"]

    assert "<!doctype html>" in html
    assert '<html lang="en">' in html
    assert "<title>Assessment Factory Lite Paid Assessment Offer</title>" in html
    assert (
        'data-view="assessment-factory-lite-paid-assessment-offer-html-view"'
        in html
    )
    assert "Assessment Factory Lite Demo Package" in html
    assert "paid_assessment_conversion" in html


def test_assessment_factory_lite_offer_html_endpoint_contains_sections():
    response = client.post(
        "/products/assessment-factory-lite/assessment-offer/html",
        json={},
    )

    html = response.json()["html"]

    assert 'data-section="target_buyer"' in html
    assert 'data-section="problem_statement"' in html
    assert 'data-section="safe_evidence_request"' in html
    assert 'data-section="assessment_scope"' in html
    assert 'data-section="deliverable"' in html
    assert 'data-section="recommended_price_band"' in html
    assert 'data-section="buyer_commitment"' in html
    assert 'data-section="qualification_questions"' in html
    assert 'data-section="risk_controls"' in html
    assert 'data-section="next_action"' in html
    assert 'data-section="demo_boundary"' in html
    assert 'data-section="excluded_scope"' in html


def test_assessment_factory_lite_offer_html_endpoint_contains_offer_content():
    response = client.post(
        "/products/assessment-factory-lite/assessment-offer/html",
        json={},
    )

    html = response.json()["html"]

    assert "operations_leader" in html
    assert "approval and handoff workflow" in html
    assert "approval_delay" in html
    assert "safe_non_sensitive_workflow_evidence" in html
    assert "bounded_friction_assessment" in html
    assert "assessment_factory_lite_buyer_summary" in html
    assert "fixed_fee_discovery_assessment" in html
    assert "schedule_paid_assessment_conversation" in html


def test_assessment_factory_lite_offer_html_endpoint_contains_questions_and_risk_controls():
    response = client.post(
        "/products/assessment-factory-lite/assessment-offer/html",
        json={},
    )

    html = response.json()["html"]

    assert 'data-question-type="workflow_similarity"' in html
    assert 'data-question-type="evidence_source"' in html
    assert 'data-question-type="first_test"' in html
    assert 'data-question-type="buyer_value"' in html

    assert 'data-control="sample_or_redacted_data_only"' in html
    assert 'data-control="operator_price_approval"' in html
    assert 'data-control="excluded_scope_visibility"' in html
    assert 'data-control="human_review_before_delivery"' in html


def test_assessment_factory_lite_offer_html_endpoint_preserves_boundaries_and_accepts_custom_context():
    response = client.post(
        "/products/assessment-factory-lite/assessment-offer/html",
        json={
            "buyer_context": {
                "primary_buyer": "founder_operator",
                "workflow_area": "security review workflow",
                "price_low": 1500,
                "price_high": 3500,
            }
        },
    )

    assert response.status_code == 200

    html = response.json()["html"]

    assert "founder_operator" in html
    assert "security review workflow" in html
    assert "USD 1500 - 3500" in html

    assert "Demo and Assessment Intake Boundary" in html
    assert "demo_and_assessment_intake_boundary" in html
    assert "sanitized_csv" in html
    assert "redacted_workflow_export" in html
    assert "manual_workflow_summary" in html
    assert "regulated_health_data" in html
    assert "federal_sensitive_data" in html
    assert "live_security_telemetry" in html
    assert "Certification claims allowed:" in html
    assert "Binding price quote allowed:" in html
    assert "False" in html

    assert "production_customer_data_processing" in html
    assert "guaranteed_operational_outcomes" in html
    assert "binding_legal_or_compliance_advice" in html


def test_assessment_factory_lite_offer_html_endpoint_route_exists_and_preserves_release_marker():
    actual_routes = {route.path for route in app.routes}

    assert "/products/assessment-factory-lite/assessment-offer/html" in actual_routes

    response = client.get("/version")

    assert response.status_code == 200
    assert response.json() == {
        "version": "2.2.0",
        "release": "assessment-factory-lite-buyer-delivery-follow-up",
        "sprint": "5.0",
        "status": "complete",
    }



