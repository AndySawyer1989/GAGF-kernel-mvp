from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def test_assessment_factory_lite_buyer_walkthrough_html_endpoint_returns_contract():
    response = client.get(
        "/products/assessment-factory-lite/buyer-walkthrough/html"
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["status"] == "ok"
    assert payload["view_type"] == (
        "assessment_factory_lite_buyer_walkthrough_html_view"
    )
    assert payload["package_name"] == "Assessment Factory Lite Demo Package"
    assert payload["release"] == "assessment-factory-lite-demo-delivery-packaging"
    assert payload["version"] == "1.7.0"
    assert payload["view_stage"] == "buyer_demo_conversion"
    assert payload["recommended_action"] == "present_buyer_walkthrough_html_view"


def test_assessment_factory_lite_buyer_walkthrough_html_endpoint_returns_source_script_and_sections():
    response = client.get(
        "/products/assessment-factory-lite/buyer-walkthrough/html"
    )

    payload = response.json()

    assert payload["source_script"]["script_type"] == (
        "assessment_factory_lite_buyer_walkthrough_script"
    )

    assert payload["view_sections"] == [
        "walkthrough_header",
        "opening_script",
        "problem_frame",
        "scenario_script",
        "finding_script",
        "intervention_script",
        "boundary_script",
        "buyer_questions",
        "close_script",
        "objection_responses",
        "demo_boundary",
    ]


def test_assessment_factory_lite_buyer_walkthrough_html_endpoint_contains_document_structure():
    response = client.get(
        "/products/assessment-factory-lite/buyer-walkthrough/html"
    )

    html = response.json()["html"]

    assert "<!doctype html>" in html
    assert '<html lang="en">' in html
    assert "<title>Assessment Factory Lite Buyer Walkthrough</title>" in html
    assert (
        'data-view="assessment-factory-lite-buyer-walkthrough-html-view"'
        in html
    )
    assert "Assessment Factory Lite Demo Package" in html
    assert "buyer_demo_conversion" in html


def test_assessment_factory_lite_buyer_walkthrough_html_endpoint_contains_script_sections():
    response = client.get(
        "/products/assessment-factory-lite/buyer-walkthrough/html"
    )

    html = response.json()["html"]

    assert 'data-section="script_summary"' in html
    assert 'data-section="opening_script"' in html
    assert 'data-section="problem_frame"' in html
    assert 'data-section="scenario_script"' in html
    assert 'data-section="finding_script"' in html
    assert 'data-section="intervention_script"' in html
    assert 'data-section="boundary_script"' in html
    assert 'data-section="buyer_questions"' in html
    assert 'data-section="close_script"' in html
    assert 'data-section="objection_responses"' in html
    assert 'data-section="demo_boundary"' in html


def test_assessment_factory_lite_buyer_walkthrough_html_endpoint_contains_buyer_language():
    response = client.get(
        "/products/assessment-factory-lite/buyer-walkthrough/html"
    )

    html = response.json()["html"]

    assert "This is a sample-data-only demo of Assessment Factory Lite." in html
    assert "Most teams feel delays before they can prove them." in html
    assert "Approval Delay and Blocked Work" in html
    assert "Approval delays are creating workflow drag." in html
    assert "streamline_approval_path" in html
    assert "schedule_paid_assessment_conversation" in html


def test_assessment_factory_lite_buyer_walkthrough_html_endpoint_contains_questions_and_objections():
    response = client.get(
        "/products/assessment-factory-lite/buyer-walkthrough/html"
    )

    html = response.json()["html"]

    assert 'data-question-type="workflow_similarity"' in html
    assert 'data-question-type="evidence_source"' in html
    assert 'data-question-type="first_test"' in html
    assert 'data-question-type="buyer_value"' in html
    assert (
        "Which part of this sample workflow most resembles where your team gets stuck?"
        in html
    )
    assert "What safe, non-sensitive workflow evidence could we inspect first?" in html

    assert 'data-objection="we_do_not_want_to_upload_sensitive_data"' in html
    assert 'data-objection="we_already_know_where_the_problem_is"' in html
    assert 'data-objection="this_looks_like_project_management"' in html
    assert 'data-objection="is_this_production_ready"' in html


def test_assessment_factory_lite_buyer_walkthrough_html_endpoint_preserves_demo_boundary():
    response = client.get(
        "/products/assessment-factory-lite/buyer-walkthrough/html"
    )

    html = response.json()["html"]

    assert "Demo-Only Boundary" in html
    assert "demo_only_sample_data" in html
    assert "real_customer_data" in html
    assert "regulated_data" in html
    assert "federal_data" in html
    assert "production_customer_data" in html
    assert "customer_secrets" in html
    assert "live_security_telemetry" in html
    assert "Certification claims allowed:" in html
    assert "False" in html


def test_assessment_factory_lite_buyer_walkthrough_html_endpoint_route_exists_and_preserves_release_marker():
    actual_routes = {route.path for route in app.routes}

    assert "/products/assessment-factory-lite/buyer-walkthrough/html" in actual_routes

    response = client.get("/version")

    assert response.status_code == 200
    assert response.json() == {
        "version": "1.8.0",
        "release": "assessment-factory-lite-buyer-conversion",
        "sprint": "4.7",
        "status": "complete",
    }
