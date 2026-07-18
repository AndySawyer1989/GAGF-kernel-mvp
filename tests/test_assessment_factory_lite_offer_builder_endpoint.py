from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def test_assessment_factory_lite_offer_builder_endpoint_returns_contract():
    response = client.post("/products/assessment-factory-lite/assessment-offer", json={})

    assert response.status_code == 200

    payload = response.json()

    assert payload["status"] == "ok"
    assert payload["offer_type"] == "assessment_factory_lite_paid_assessment_offer"
    assert payload["package_name"] == "Assessment Factory Lite Demo Package"
    assert payload["release"] == "assessment-factory-lite-buyer-conversion"
    assert payload["version"] == "1.8.0"
    assert payload["offer_stage"] == "paid_assessment_conversion"
    assert payload["recommended_action"] == "present_paid_assessment_offer"


def test_assessment_factory_lite_offer_builder_endpoint_returns_target_buyer_and_problem_statement():
    response = client.post("/products/assessment-factory-lite/assessment-offer", json={})

    payload = response.json()

    assert payload["target_buyer"]["primary_buyer"] == "operations_leader"
    assert payload["target_buyer"]["secondary_buyers"] == [
        "it_manager",
        "workflow_owner",
        "founder_operator",
    ]
    assert "workflow drag" in payload["target_buyer"]["buyer_pain"]

    assert payload["problem_statement"]["workflow_area"] == (
        "approval and handoff workflow"
    )
    assert payload["problem_statement"]["default_friction_hypothesis"] == (
        "approval_delay"
    )
    assert "highest-friction constraint" in payload["problem_statement"]["statement"]


def test_assessment_factory_lite_offer_builder_endpoint_returns_safe_evidence_request():
    response = client.post("/products/assessment-factory-lite/assessment-offer", json={})

    payload = response.json()
    evidence = payload["safe_evidence_request"]

    assert evidence["request_type"] == "safe_non_sensitive_workflow_evidence"
    assert evidence["requested_sources"] == [
        "sanitized_workflow_export",
        "approval_timestamps",
        "handoff_log",
        "blocked_work_items",
    ]
    assert "sanitized_csv" in evidence["allowed_format"]
    assert "redacted_export" in evidence["allowed_format"]
    assert "regulated_health_data" in evidence["prohibited_data"]
    assert "federal_sensitive_data" in evidence["prohibited_data"]
    assert "credentials" in evidence["prohibited_data"]


def test_assessment_factory_lite_offer_builder_endpoint_returns_scope_and_exclusions():
    response = client.post("/products/assessment-factory-lite/assessment-offer", json={})

    payload = response.json()
    scope = payload["assessment_scope"]

    assert scope["scope_type"] == "bounded_friction_assessment"
    assert scope["duration"] == "3_to_5_business_days"
    assert "review_safe_workflow_evidence" in scope["included_work"]
    assert "identify_top_friction_point" in scope["included_work"]
    assert "recommend_one_focused_intervention" in scope["included_work"]

    assert "production_customer_data_processing" in payload["excluded_scope"]
    assert "regulated_data_processing" in payload["excluded_scope"]
    assert "federal_data_processing" in payload["excluded_scope"]
    assert "guaranteed_operational_outcomes" in payload["excluded_scope"]
    assert "binding_legal_or_compliance_advice" in payload["excluded_scope"]


def test_assessment_factory_lite_offer_builder_endpoint_returns_deliverable_and_price_band():
    response = client.post("/products/assessment-factory-lite/assessment-offer", json={})

    payload = response.json()

    deliverable = payload["deliverable"]
    price = payload["recommended_price_band"]

    assert deliverable["deliverable_type"] == (
        "assessment_factory_lite_buyer_summary"
    )
    assert deliverable["format"] == "markdown_or_pdf_ready_summary"
    assert "executive_summary" in deliverable["sections"]
    assert "workflow_friction_finding" in deliverable["sections"]
    assert "recommended_intervention" in deliverable["sections"]

    assert price == {
        "currency": "USD",
        "low": 500,
        "high": 2500,
        "pricing_model": "fixed_fee_discovery_assessment",
        "pricing_note": (
            "Final pricing is operator-approved and should not be treated as "
            "an automated binding quote."
        ),
    }


def test_assessment_factory_lite_offer_builder_endpoint_returns_commitment_questions_and_controls():
    response = client.post("/products/assessment-factory-lite/assessment-offer", json={})

    payload = response.json()

    assert payload["buyer_commitment"]["commitment_type"] == (
        "small_bounded_assessment"
    )
    assert "one_workflow_to_assess" in payload["buyer_commitment"]["buyer_provides"]
    assert (
        "safe_non_sensitive_evidence"
        in payload["buyer_commitment"]["buyer_provides"]
    )

    questions = {
        item["question_type"]: item for item in payload["qualification_questions"]
    }

    assert set(questions) == {
        "workflow_similarity",
        "evidence_source",
        "first_test",
        "buyer_value",
    }
    assert all(item["used_for_offer"] is True for item in questions.values())

    controls = {item["control"]: item for item in payload["risk_controls"]}

    assert set(controls) == {
        "sample_or_redacted_data_only",
        "operator_price_approval",
        "excluded_scope_visibility",
        "human_review_before_delivery",
    }
    assert all(item["required"] is True for item in controls.values())


def test_assessment_factory_lite_offer_builder_endpoint_accepts_custom_context():
    response = client.post(
        "/products/assessment-factory-lite/assessment-offer",
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

    assert payload["target_buyer"]["primary_buyer"] == "founder_operator"
    assert payload["problem_statement"]["workflow_area"] == "security review workflow"
    assert payload["assessment_scope"]["workflow_area"] == "security review workflow"
    assert payload["assessment_scope"]["duration"] == "5_to_7_business_days"
    assert payload["recommended_price_band"]["low"] == 1500
    assert payload["recommended_price_band"]["high"] == 3500

    boundary = payload["demo_boundary"]

    assert boundary["boundary_type"] == "demo_and_assessment_intake_boundary"
    assert "sanitized_csv" in boundary["allowed_data"]
    assert "redacted_workflow_export" in boundary["allowed_data"]
    assert "regulated_health_data" in boundary["prohibited_data"]
    assert "federal_sensitive_data" in boundary["prohibited_data"]
    assert boundary["certification_claims_allowed"] is False
    assert boundary["binding_price_quote_allowed"] is False


def test_assessment_factory_lite_offer_builder_endpoint_route_exists_and_preserves_release_marker():
    actual_routes = {route.path for route in app.routes}

    assert "/products/assessment-factory-lite/assessment-offer" in actual_routes

    response = client.get("/version")

    assert response.status_code == 200
    assert response.json() == {
        "version": "2.2.0",
        "release": "assessment-factory-lite-buyer-delivery-follow-up",
        "sprint": "5.0",
        "status": "complete",
    }



