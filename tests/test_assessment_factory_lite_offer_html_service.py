from backend.app.gagf.assessment_factory_lite_offer_html_service import (
    AssessmentFactoryLiteOfferHTMLService,
)


def service():
    return AssessmentFactoryLiteOfferHTMLService()


def test_assessment_factory_lite_offer_html_builds_contract():
    result = service().render_html()

    assert result["status"] == "ok"
    assert result["view_type"] == (
        "assessment_factory_lite_paid_assessment_offer_html_view"
    )
    assert result["package_name"] == "Assessment Factory Lite Demo Package"
    assert result["release"] == "assessment-factory-lite-buyer-conversion"
    assert result["version"] == "1.8.0"
    assert result["view_stage"] == "paid_assessment_conversion"
    assert result["recommended_action"] == "present_paid_assessment_offer_html_view"


def test_assessment_factory_lite_offer_html_returns_source_offer_and_sections():
    result = service().render_html()

    assert result["source_offer"]["offer_type"] == (
        "assessment_factory_lite_paid_assessment_offer"
    )

    assert result["view_sections"] == [
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


def test_assessment_factory_lite_offer_html_contains_document_structure():
    html = service().render_html()["html"]

    assert "<!doctype html>" in html
    assert '<html lang="en">' in html
    assert "<title>Assessment Factory Lite Paid Assessment Offer</title>" in html
    assert (
        'data-view="assessment-factory-lite-paid-assessment-offer-html-view"'
        in html
    )
    assert "Assessment Factory Lite Demo Package" in html
    assert "paid_assessment_conversion" in html


def test_assessment_factory_lite_offer_html_contains_sections():
    html = service().render_html()["html"]

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


def test_assessment_factory_lite_offer_html_contains_offer_content():
    html = service().render_html()["html"]

    assert "operations_leader" in html
    assert "approval and handoff workflow" in html
    assert "approval_delay" in html
    assert "safe_non_sensitive_workflow_evidence" in html
    assert "bounded_friction_assessment" in html
    assert "assessment_factory_lite_buyer_summary" in html
    assert "fixed_fee_discovery_assessment" in html
    assert "schedule_paid_assessment_conversation" in html


def test_assessment_factory_lite_offer_html_contains_questions_and_risk_controls():
    html = service().render_html()["html"]

    assert 'data-question-type="workflow_similarity"' in html
    assert 'data-question-type="evidence_source"' in html
    assert 'data-question-type="first_test"' in html
    assert 'data-question-type="buyer_value"' in html

    assert 'data-control="sample_or_redacted_data_only"' in html
    assert 'data-control="operator_price_approval"' in html
    assert 'data-control="excluded_scope_visibility"' in html
    assert 'data-control="human_review_before_delivery"' in html


def test_assessment_factory_lite_offer_html_preserves_boundaries_and_exclusions():
    html = service().render_html()["html"]

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


def test_assessment_factory_lite_offer_html_accepts_custom_context_and_escapes_values():
    result = service().render_html(
        buyer_context={
            "primary_buyer": "<Founder>",
            "workflow_area": "<Security Review>",
            "price_low": 1500,
            "price_high": 3500,
        }
    )

    html = result["html"]

    assert "&lt;Founder&gt;" in html
    assert "&lt;Security Review&gt;" in html
    assert "USD 1500 - 3500" in html
    assert "<Founder>" not in html
    assert "<Security Review>" not in html