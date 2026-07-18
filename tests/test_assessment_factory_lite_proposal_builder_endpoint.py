from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def test_assessment_factory_lite_proposal_builder_endpoint_returns_contract():
    response = client.post("/products/assessment-factory-lite/proposal", json={})

    assert response.status_code == 200

    payload = response.json()

    assert payload["status"] == "ok"
    assert payload["proposal_type"] == (
        "assessment_factory_lite_paid_assessment_proposal"
    )
    assert payload["package_name"] == "Assessment Factory Lite Demo Package"
    assert payload["release"] == "assessment-factory-lite-commercial-offer"
    assert payload["version"] == "1.9.0"
    assert payload["proposal_stage"] == "proposal_ready_artifact"
    assert payload["recommended_action"] == "review_proposal_ready_artifact"


def test_assessment_factory_lite_proposal_builder_endpoint_returns_title_buyer_and_problem():
    response = client.post("/products/assessment-factory-lite/proposal", json={})

    payload = response.json()

    assert payload["proposal_title"] == (
        "Assessment Factory Lite Proposal for approval and handoff workflow"
    )

    assert payload["buyer_context"]["primary_buyer"] == "operations_leader"
    assert payload["buyer_context"]["secondary_buyers"] == [
        "it_manager",
        "workflow_owner",
        "founder_operator",
    ]
    assert "workflow drag" in payload["buyer_context"]["buyer_pain"]

    assert payload["problem_statement"]["workflow_area"] == (
        "approval and handoff workflow"
    )
    assert payload["problem_statement"]["default_friction_hypothesis"] == (
        "approval_delay"
    )


def test_assessment_factory_lite_proposal_builder_endpoint_returns_scope_and_evidence_boundary():
    response = client.post("/products/assessment-factory-lite/proposal", json={})

    payload = response.json()

    scope = payload["proposed_scope"]
    evidence = payload["evidence_boundary"]

    assert scope["scope_type"] == "bounded_friction_assessment"
    assert scope["duration"] == "3_to_5_business_days"
    assert "review_safe_workflow_evidence" in scope["included_work"]
    assert "recommend_one_focused_intervention" in scope["included_work"]
    assert "one bounded workflow assessment" in scope["scope_boundary"]

    assert evidence["request_type"] == "safe_non_sensitive_workflow_evidence"
    assert "sanitized_workflow_export" in evidence["requested_sources"]
    assert "sanitized_csv" in evidence["allowed_format"]
    assert "redacted_workflow_export" in evidence["allowed_data"]
    assert "regulated_health_data" in evidence["prohibited_data"]
    assert "federal_sensitive_data" in evidence["prohibited_data"]
    assert evidence["certification_claims_allowed"] is False
    assert evidence["binding_price_quote_allowed"] is False


def test_assessment_factory_lite_proposal_builder_endpoint_returns_deliverables_and_timeline():
    response = client.post("/products/assessment-factory-lite/proposal", json={})

    payload = response.json()

    deliverables = {
        item["deliverable"]: item for item in payload["deliverables"]
    }

    assert set(deliverables) == {
        "assessment_summary",
        "recommended_next_test",
    }

    assert deliverables["assessment_summary"]["format"] == (
        "markdown_or_pdf_ready_summary"
    )
    assert "workflow_friction_finding" in deliverables["assessment_summary"]["sections"]
    assert "recommended_intervention" in deliverables["assessment_summary"]["sections"]

    assert deliverables["recommended_next_test"]["format"] == "short_action_plan"
    assert "next_test" in deliverables["recommended_next_test"]["sections"]

    timeline = payload["timeline"]

    assert timeline["estimated_duration"] == "3_to_5_business_days"
    assert [phase["phase"] for phase in timeline["phases"]] == [
        "intake",
        "evidence_review",
        "diagnostic_summary",
        "recommendation_review",
    ]


def test_assessment_factory_lite_proposal_builder_endpoint_returns_commercial_terms_and_exclusions():
    response = client.post("/products/assessment-factory-lite/proposal", json={})

    payload = response.json()

    terms = payload["commercial_terms_placeholder"]

    assert terms == {
        "pricing_model": "fixed_fee_discovery_assessment",
        "currency": "USD",
        "recommended_price_band": {
            "low": 500,
            "high": 2500,
        },
        "payment_terms": "operator_to_define",
        "proposal_expiration": "operator_to_define",
        "pricing_note": (
            "Final pricing is operator-approved and should not be treated as "
            "an automated binding quote."
        ),
        "binding_quote": False,
    }

    assert "production_customer_data_processing" in payload["excluded_scope"]
    assert "regulated_data_processing" in payload["excluded_scope"]
    assert "federal_data_processing" in payload["excluded_scope"]
    assert "guaranteed_operational_outcomes" in payload["excluded_scope"]
    assert "binding_legal_or_compliance_advice" in payload["excluded_scope"]


def test_assessment_factory_lite_proposal_builder_endpoint_returns_assumptions_approvals_and_controls():
    response = client.post("/products/assessment-factory-lite/proposal", json={})

    payload = response.json()

    assert payload["assumptions"] == [
        "buyer_selects_one_workflow_for_assessment",
        "buyer_provides_safe_non_sensitive_evidence_only",
        "operator_reviews_evidence_boundary_before_analysis",
        "assessment_output_is_reviewed_before_buyer_delivery",
        "final_price_and_terms_are_operator_approved",
    ]

    approvals = {
        item["approval"]: item for item in payload["approval_requirements"]
    }

    assert set(approvals) == {
        "evidence_boundary_approval",
        "commercial_terms_approval",
        "buyer_scope_acknowledgement",
    }
    assert all(item["required"] is True for item in approvals.values())

    controls = {
        item["control"]: item for item in payload["proposal_risk_controls"]
    }

    assert set(controls) == {
        "non_binding_proposal_until_operator_approval",
        "safe_evidence_boundary_required",
        "excluded_scope_must_be_visible",
        "human_review_before_sending",
    }
    assert all(item["required"] is True for item in controls.values())


def test_assessment_factory_lite_proposal_builder_endpoint_returns_source_offer_and_next_action():
    response = client.post("/products/assessment-factory-lite/proposal", json={})

    payload = response.json()

    assert payload["source_offer"] == {
        "offer_type": "assessment_factory_lite_paid_assessment_offer",
        "offer_stage": "paid_assessment_conversion",
        "release": "assessment-factory-lite-buyer-conversion",
        "version": "1.8.0",
        "recommended_action": "present_paid_assessment_offer",
    }

    assert payload["next_action"] == {
        "action": "review_and_prepare_proposal",
        "operator_instruction": (
            "Review the proposal-ready artifact, confirm evidence boundary, "
            "approve commercial terms, and decide whether to generate a formal "
            "proposal document."
        ),
        "future_action": "generate_formal_proposal",
    }


def test_assessment_factory_lite_proposal_builder_endpoint_accepts_custom_context_and_preserves_release_marker():
    response = client.post(
        "/products/assessment-factory-lite/proposal",
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

    assert payload["proposal_title"] == (
        "Assessment Factory Lite Proposal for security review workflow"
    )
    assert payload["buyer_context"]["primary_buyer"] == "founder_operator"
    assert payload["problem_statement"]["workflow_area"] == "security review workflow"
    assert payload["proposed_scope"]["workflow_area"] == "security review workflow"
    assert payload["proposed_scope"]["duration"] == "5_to_7_business_days"
    assert payload["commercial_terms_placeholder"]["recommended_price_band"] == {
        "low": 1500,
        "high": 3500,
    }

    actual_routes = {route.path for route in app.routes}

    assert "/products/assessment-factory-lite/proposal" in actual_routes

    version_response = client.get("/version")

    assert version_response.status_code == 200
    assert version_response.json() == {
        "version": "2.2.0",
        "release": "assessment-factory-lite-buyer-delivery-follow-up",
        "sprint": "5.0",
        "status": "complete",
    }


