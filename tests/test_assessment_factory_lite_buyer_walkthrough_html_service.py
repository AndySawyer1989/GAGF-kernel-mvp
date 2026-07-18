from backend.app.gagf.assessment_factory_lite_buyer_walkthrough_html_service import (
    AssessmentFactoryLiteBuyerWalkthroughHTMLService,
)


def service():
    return AssessmentFactoryLiteBuyerWalkthroughHTMLService()


def test_assessment_factory_lite_buyer_walkthrough_html_builds_contract():
    result = service().render_html()

    assert result["status"] == "ok"
    assert result["view_type"] == (
        "assessment_factory_lite_buyer_walkthrough_html_view"
    )
    assert result["package_name"] == "Assessment Factory Lite Demo Package"
    assert result["release"] == "assessment-factory-lite-demo-delivery-packaging"
    assert result["version"] == "1.7.0"
    assert result["view_stage"] == "buyer_demo_conversion"
    assert result["recommended_action"] == "present_buyer_walkthrough_html_view"


def test_assessment_factory_lite_buyer_walkthrough_html_returns_source_script_and_sections():
    result = service().render_html()

    assert result["source_script"]["script_type"] == (
        "assessment_factory_lite_buyer_walkthrough_script"
    )

    assert result["view_sections"] == [
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


def test_assessment_factory_lite_buyer_walkthrough_html_contains_document_structure():
    html = service().render_html()["html"]

    assert "<!doctype html>" in html
    assert '<html lang="en">' in html
    assert "<title>Assessment Factory Lite Buyer Walkthrough</title>" in html
    assert (
        'data-view="assessment-factory-lite-buyer-walkthrough-html-view"'
        in html
    )
    assert "Assessment Factory Lite Demo Package" in html
    assert "buyer_demo_conversion" in html


def test_assessment_factory_lite_buyer_walkthrough_html_contains_script_sections():
    html = service().render_html()["html"]

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


def test_assessment_factory_lite_buyer_walkthrough_html_contains_buyer_language():
    html = service().render_html()["html"]

    assert "This is a sample-data-only demo of Assessment Factory Lite." in html
    assert "Most teams feel delays before they can prove them." in html
    assert "Approval Delay and Blocked Work" in html
    assert "Approval delays are creating workflow drag." in html
    assert "streamline_approval_path" in html
    assert "schedule_paid_assessment_conversation" in html


def test_assessment_factory_lite_buyer_walkthrough_html_contains_questions_and_objections():
    html = service().render_html()["html"]

    assert 'data-question-type="workflow_similarity"' in html
    assert 'data-question-type="evidence_source"' in html
    assert 'data-question-type="first_test"' in html
    assert 'data-question-type="buyer_value"' in html
    assert "Which part of this sample workflow most resembles where your team gets stuck?" in html
    assert "What safe, non-sensitive workflow evidence could we inspect first?" in html

    assert 'data-objection="we_do_not_want_to_upload_sensitive_data"' in html
    assert 'data-objection="we_already_know_where_the_problem_is"' in html
    assert 'data-objection="this_looks_like_project_management"' in html
    assert 'data-objection="is_this_production_ready"' in html


def test_assessment_factory_lite_buyer_walkthrough_html_preserves_demo_boundary():
    html = service().render_html()["html"]

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


def test_assessment_factory_lite_buyer_walkthrough_html_escapes_custom_script():
    custom_script = {
        "package_name": "<Package>",
        "version": "1.7.0",
        "script_stage": "buyer_demo_conversion",
        "script_summary": {
            "positioning": "<bad>",
            "delivery_mode": "guided_buyer_walkthrough",
            "conversion_goal": "test",
        },
        "opening_script": {
            "title": "<Opening>",
            "operator_script": "<script>alert('x')</script>",
            "buyer_takeaway": "<takeaway>",
        },
        "problem_frame": {
            "title": "Problem",
            "operator_script": "Safe",
            "buyer_takeaway": "Safe",
        },
        "scenario_script": [],
        "finding_script": {},
        "intervention_script": {},
        "boundary_script": {"prohibited_data": []},
        "buyer_questions": [],
        "close_script": {},
        "objection_responses": [],
        "demo_boundary": {
            "boundary_type": "demo_only_sample_data",
            "prohibited_data": [],
            "certification_claims_allowed": False,
        },
    }

    html = service().render_html(custom_script)["html"]

    assert "&lt;Package&gt;" in html
    assert "&lt;script&gt;alert(&#x27;x&#x27;)&lt;/script&gt;" in html
    assert "<script>alert('x')</script>" not in html
