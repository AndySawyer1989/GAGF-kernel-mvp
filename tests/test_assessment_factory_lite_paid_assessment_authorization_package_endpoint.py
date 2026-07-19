from fastapi.testclient import TestClient

from backend.app.gagf.assessment_factory_lite_formal_proposal_markdown_export_service import (
    AssessmentFactoryLiteFormalProposalMarkdownExportService,
)
from backend.app.main import app


client = TestClient(app)


APPROVAL = {
    "approval_status": "operator_approved",
    "scope_approved": True,
    "evidence_boundary_approved": True,
    "commercial_terms_approved": True,
    "buyer_language_approved": True,
}


EVENT_CONTEXT = {
    "event_id": "buyer-delivery-event-001",
    "recorded_at": "2026-07-17T12:00:00+00:00",
    "human_operator_confirmed": True,
    "delivery_completed": True,
}


FOLLOW_UP_EVENT_CONTEXT = {
    "event_id": "buyer-follow-up-event-001",
    "recorded_at": "2026-07-21T12:00:00+00:00",
    "human_operator_confirmed": True,
    "follow_up_completed": True,
}


INTERESTED_CONTEXT = {
    "buyer_response_status": "interested",
    "response_received_at": "2026-07-18T09:00:00+00:00",
    "response_summary": "Buyer wants to schedule a scope call.",
    "buyer_questions": ["Can we start next week?"],
}


AGENDA_EVENT_CONTEXT = {
    "event_id": "scope-call-agenda-message-event-001",
    "recorded_at": "2026-07-22T12:00:00+00:00",
    "human_operator_confirmed": True,
    "agenda_message_sent": True,
    "recipient_confirmed": True,
    "email_status": "operator_confirmed",
    "delivery_channel": "manual_email",
}


SCOPE_CALL_EVENT_CONTEXT = {
    "scope_call_id": "scope-call-event-package-001",
    "prepared_at": "2026-07-23T12:00:00+00:00",
}


SCOPE_CALL_RECORD_CONTEXT = {
    "event_id": "scope-call-event-record-001",
    "recorded_at": "2026-07-24T12:00:00+00:00",
    "human_operator_confirmed": True,
    "call_completed": True,
    "call_confirmed": True,
    "outcome_status": "completed",
    "outcome_summary": "Buyer confirmed the workflow problem and wants paid assessment review.",
    "buyer_needs_summary": "Buyer needs help identifying governance bottlenecks.",
    "assessment_fit": "good_fit",
    "next_step_requested": "paid_assessment_review",
    "buyer_decision_status": "requested_paid_assessment",
    "operator_name": "Andy Sawyer II",
    "operator_notes": ["Buyer confirmed scope-call outcome."],
}


AUTHORIZATION_CONTEXT = {
    "authorization_id": "paid-assessment-authorization-package-001",
    "prepared_at": "2026-07-25T12:00:00+00:00",
    "buyer_request_summary": "Buyer requested paid assessment review after scope call.",
    "pricing_reviewed": True,
    "scope_reviewed": True,
    "terms_reviewed": True,
    "evidence_reviewed": True,
    "evidence_boundary_approved": True,
    "human_operator_authorized_package": True,
    "authorization_status": "package_authorized_for_agreement_review",
}


def ready_payload():
    return {
        "operator_approval": APPROVAL,
        "event_context": EVENT_CONTEXT,
        "follow_up_context": INTERESTED_CONTEXT,
        "follow_up_event_context": FOLLOW_UP_EVENT_CONTEXT,
        "scope_call_message_event_context": AGENDA_EVENT_CONTEXT,
        "scope_call_event_context": SCOPE_CALL_EVENT_CONTEXT,
        "scope_call_record_context": SCOPE_CALL_RECORD_CONTEXT,
        "authorization_context": AUTHORIZATION_CONTEXT,
    }


def test_assessment_factory_lite_paid_assessment_authorization_package_endpoint_builds_contract():
    response = client.post(
        "/products/assessment-factory-lite/paid-assessment-authorization-package",
        json=ready_payload(),
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["status"] == "ok"
    assert payload["event_type"] == "assessment_factory_lite_paid_assessment_authorization_package"
    assert payload["package_name"] == "Assessment Factory Lite Demo Package"
    assert payload["release"] == "assessment-factory-lite-scope-call-conversion"
    assert payload["version"] == "2.3.0"
    assert payload["package_stage"] == "paid_assessment_authorization_package"
    assert payload["package_status"] == "ready_for_paid_assessment_authorization"
    assert payload["authorization_id"] == "paid-assessment-authorization-package-001"
    assert payload["prepared_at"] == "2026-07-25T12:00:00+00:00"
    assert payload["recommended_action"] == "prepare_paid_assessment_agreement_review"


def test_assessment_factory_lite_paid_assessment_authorization_package_endpoint_summarizes_source_event():
    response = client.post(
        "/products/assessment-factory-lite/paid-assessment-authorization-package",
        json=ready_payload(),
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["source_scope_call_event_record"] == {
        "event_type": "assessment_factory_lite_scope_call_event_record",
        "event_stage": "scope_call_event_record",
        "event_status": "recorded",
        "release": "assessment-factory-lite-scope-call-conversion",
        "version": "2.3.0",
        "event_id": "scope-call-event-record-001",
        "recorded_at": "2026-07-24T12:00:00+00:00",
        "recommended_action": "prepare_paid_assessment_authorization_package",
    }


def test_assessment_factory_lite_paid_assessment_authorization_package_endpoint_tracks_buyer_request():
    response = client.post(
        "/products/assessment-factory-lite/paid-assessment-authorization-package",
        json=ready_payload(),
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["buyer_request"] == {
        "buyer_requested_paid_assessment": True,
        "buyer_decision_status": "requested_paid_assessment",
        "requested_package_type": "assessment_factory_lite_paid_assessment",
        "buyer_request_summary": "Buyer requested paid assessment review after scope call.",
        "buyer_request_is_evidence_not_authorization": True,
    }


def test_assessment_factory_lite_paid_assessment_authorization_package_endpoint_tracks_reviews_and_human_authorization():
    response = client.post(
        "/products/assessment-factory-lite/paid-assessment-authorization-package",
        json=ready_payload(),
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["commercial_review"] == {
        "pricing_reviewed": True,
        "scope_reviewed": True,
        "terms_reviewed": True,
        "commercial_terms_ready": True,
        "contract_required_before_execution": True,
        "invoice_required_before_payment": True,
        "payment_required_before_paid_work": True,
    }

    assert payload["evidence_review"] == {
        "evidence_reviewed": True,
        "evidence_boundary_approved": True,
        "production_data_approved": False,
        "secrets_approved": False,
        "credentials_approved": False,
        "evidence_ready_for_paid_assessment": True,
    }

    assert payload["human_authorization"] == {
        "human_operator_required": True,
        "human_operator_authorized_package": True,
        "authorization_status": "package_authorized_for_agreement_review",
        "paid_assessment_authorized": False,
        "contract_execution_approved": False,
        "invoice_creation_approved": False,
        "payment_request_approved": False,
        "production_onboarding_approved": False,
    }


def test_assessment_factory_lite_paid_assessment_authorization_package_endpoint_builds_checklist_and_score():
    response = client.post(
        "/products/assessment-factory-lite/paid-assessment-authorization-package",
        json=ready_payload(),
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["package_checklist"] == {
        "scope_call_event_recorded": True,
        "buyer_requested_paid_assessment": True,
        "buyer_request_is_evidence_not_authorization": True,
        "commercial_terms_ready": True,
        "evidence_ready_for_paid_assessment": True,
        "human_operator_authorized_package": True,
        "paid_assessment_not_authorized_by_package": True,
        "contract_not_executed": True,
        "invoice_not_created": True,
        "payment_not_requested": True,
        "production_onboarding_not_started": True,
    }

    assert payload["package_blockers"] == []
    assert payload["authorization_score"] == {
        "passed": 11,
        "total": 11,
        "score": 1.0,
        "ready": True,
    }


def test_assessment_factory_lite_paid_assessment_authorization_package_endpoint_preserves_boundaries():
    response = client.post(
        "/products/assessment-factory-lite/paid-assessment-authorization-package",
        json=ready_payload(),
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["commercial_boundary"] == {
        "authorization_package_ready": True,
        "paid_assessment_authorized": False,
        "contract_created": False,
        "contract_executed": False,
        "invoice_created": False,
        "payment_requested": False,
        "production_onboarding_authorized": False,
        "requires_separate_contract": True,
        "requires_separate_invoice": True,
        "requires_separate_payment_confirmation": True,
    }

    assert payload["evidence_boundary"]["production_data_requires_separate_approval"] is True
    assert "regulated_production_data" in payload["evidence_boundary"]["excluded_evidence"]

    assert payload["governance_boundary"] == {
        "deterministic_status_required": True,
        "gagf_kernel_authoritative": True,
        "ai_override_allowed": False,
        "human_boundary_required": True,
        "release_marker_preserved": True,
        "authorization_is_package_readiness_only": True,
    }

    assert payload["boundary_notices"] == [
        "paid_assessment_authorization_package_does_not_authorize_paid_work",
        "paid_assessment_authorization_package_does_not_execute_contract",
        "paid_assessment_authorization_package_does_not_create_invoice",
        "paid_assessment_authorization_package_does_not_request_payment",
        "paid_assessment_authorization_package_does_not_start_production_onboarding",
        "paid_assessment_authorization_package_requires_human_operator",
    ]


def test_assessment_factory_lite_paid_assessment_authorization_package_endpoint_includes_audit_next_action_and_message():
    response = client.post(
        "/products/assessment-factory-lite/paid-assessment-authorization-package",
        json=ready_payload(),
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["audit_notes"] == [
        "paid_assessment_authorization_package_built",
        "buyer_request_treated_as_evidence_not_authorization",
        "paid_assessment_not_authorized",
        "contract_not_executed",
        "invoice_not_created",
        "payment_not_requested",
        "production_onboarding_not_started",
        "paid_assessment_authorization_package_ready",
        "buyer_requested_paid_assessment_review",
    ]

    assert payload["next_action"] == {
        "action": "prepare_paid_assessment_agreement_review",
        "operator_instruction": (
            "Prepare the paid assessment agreement review. Do not begin "
            "paid assessment work until contract, invoice, payment, and "
            "authorization gates are completed."
        ),
        "future_action": "build_paid_assessment_agreement_review",
    }

    assert payload["operator_message"] == (
        "Paid assessment authorization package is ready for agreement "
        "review. Paid assessment work is still not authorized until "
        "contract, invoice, payment, and authorization gates are completed."
    )


def test_assessment_factory_lite_paid_assessment_authorization_package_endpoint_handles_pending_states():
    no_human = ready_payload()
    no_human["authorization_context"] = dict(AUTHORIZATION_CONTEXT)
    no_human["authorization_context"]["human_operator_authorized_package"] = False

    response = client.post(
        "/products/assessment-factory-lite/paid-assessment-authorization-package",
        json=no_human,
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["package_status"] == "pending_human_authorization"
    assert "human_operator_authorized_package" in payload["package_blockers"]
    assert payload["recommended_action"] == "resolve_paid_assessment_authorization_package_gaps"

    no_review = ready_payload()
    no_review["authorization_context"] = dict(AUTHORIZATION_CONTEXT)
    no_review["authorization_context"]["evidence_reviewed"] = False

    response = client.post(
        "/products/assessment-factory-lite/paid-assessment-authorization-package",
        json=no_review,
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["package_status"] == "pending_authorization_review"
    assert "evidence_ready_for_paid_assessment" in payload["package_blockers"]
    assert payload["next_action"]["action"] == "complete_authorization_review"

    no_request = ready_payload()
    no_request["scope_call_record_context"] = dict(SCOPE_CALL_RECORD_CONTEXT)
    no_request["scope_call_record_context"]["buyer_decision_status"] = "needs_follow_up"

    response = client.post(
        "/products/assessment-factory-lite/paid-assessment-authorization-package",
        json=no_request,
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["package_status"] == "pending_buyer_request"
    assert "buyer_requested_paid_assessment" in payload["package_blockers"]
    assert payload["next_action"]["action"] == "confirm_buyer_paid_assessment_request"


def test_assessment_factory_lite_paid_assessment_authorization_package_endpoint_blocks_invalid_upstream_export():
    export = AssessmentFactoryLiteFormalProposalMarkdownExportService().export_markdown()
    export["markdown"] = export["markdown"].replace(
        "Binding quote: False",
        "Binding quote: True",
    )

    response = client.post(
        "/products/assessment-factory-lite/paid-assessment-authorization-package",
        json={
            "export": export,
            "operator_approval": APPROVAL,
            "event_context": EVENT_CONTEXT,
            "follow_up_event_context": FOLLOW_UP_EVENT_CONTEXT,
            "scope_call_message_event_context": AGENDA_EVENT_CONTEXT,
            "scope_call_record_context": SCOPE_CALL_RECORD_CONTEXT,
            "authorization_context": AUTHORIZATION_CONTEXT,
        },
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["package_status"] == "blocked"
    assert payload["source_scope_call_event_record"]["event_status"] == "blocked"
    assert payload["recommended_action"] == "resolve_paid_assessment_authorization_package_gaps"


def test_assessment_factory_lite_paid_assessment_authorization_package_endpoint_route_exists_and_preserves_release_marker():
    actual_routes = {route.path for route in app.routes}

    assert "/products/assessment-factory-lite/paid-assessment-authorization-package" in actual_routes

    response = client.get("/version")

    assert response.status_code == 200
    assert response.json() == {
        "version": "2.3.0",
        "release": "assessment-factory-lite-scope-call-conversion",
        "sprint": "5.0",
        "status": "complete",
    }