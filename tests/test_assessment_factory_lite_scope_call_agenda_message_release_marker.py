from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def test_assessment_factory_lite_scope_call_agenda_message_release_marker_version_endpoint():
    response = client.get("/version")

    assert response.status_code == 200
    assert response.json() == {
        "version": "2.3.0",
        "release": "assessment-factory-lite-scope-call-conversion",
        "sprint": "5.0",
        "status": "complete",
    }


def test_assessment_factory_lite_scope_call_agenda_message_release_marker_route_available():
    actual_routes = {route.path for route in app.routes}

    assert "/products/assessment-factory-lite/scope-call-agenda-message" in actual_routes


def test_assessment_factory_lite_scope_call_agenda_message_release_marker_preserves_scope_call_object_contract():
    response = client.post(
        "/products/assessment-factory-lite/scope-call-agenda-message",
        json={
            "operator_approval": {
                "approval_status": "operator_approved",
                "scope_approved": True,
                "evidence_boundary_approved": True,
                "commercial_terms_approved": True,
                "buyer_language_approved": True,
            },
            "event_context": {
                "event_id": "buyer-delivery-event-001",
                "recorded_at": "2026-07-17T12:00:00+00:00",
                "human_operator_confirmed": True,
                "delivery_completed": True,
            },
            "follow_up_context": {
                "buyer_response_status": "interested",
                "response_received_at": "2026-07-18T09:00:00+00:00",
                "response_summary": "Buyer wants to schedule a scope call.",
                "buyer_questions": ["Can we start next week?"],
            },
            "follow_up_event_context": {
                "event_id": "buyer-follow-up-event-001",
                "recorded_at": "2026-07-21T12:00:00+00:00",
                "human_operator_confirmed": True,
                "follow_up_completed": True,
            },
            "scope_call_context": {
                "package_id": "assessment-scope-call-package-001",
                "created_at": "2026-07-21T12:30:00+00:00",
            },
        },
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["release"] == "assessment-factory-lite-scope-call-conversion"
    assert payload["version"] == "2.3.0"
    assert payload["message_status"] == "draft_ready"


def test_assessment_factory_lite_scope_call_agenda_message_release_marker_preserves_source_package_layer():
    response = client.post(
        "/products/assessment-factory-lite/scope-call-agenda-message",
        json={
            "operator_approval": {
                "approval_status": "operator_approved",
                "scope_approved": True,
                "evidence_boundary_approved": True,
                "commercial_terms_approved": True,
                "buyer_language_approved": True,
            },
            "event_context": {
                "event_id": "buyer-delivery-event-001",
                "recorded_at": "2026-07-17T12:00:00+00:00",
                "human_operator_confirmed": True,
                "delivery_completed": True,
            },
            "follow_up_context": {
                "buyer_response_status": "interested",
                "response_received_at": "2026-07-18T09:00:00+00:00",
                "response_summary": "Buyer wants to schedule a scope call.",
                "buyer_questions": ["Can we start next week?"],
            },
            "follow_up_event_context": {
                "event_id": "buyer-follow-up-event-001",
                "recorded_at": "2026-07-21T12:00:00+00:00",
                "human_operator_confirmed": True,
                "follow_up_completed": True,
            },
            "scope_call_context": {
                "package_id": "assessment-scope-call-package-001",
                "created_at": "2026-07-21T12:30:00+00:00",
            },
        },
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["source_scope_call_package"]["release"] == (
        "assessment-factory-lite-buyer-delivery-follow-up"
    )
    assert payload["source_scope_call_package"]["version"] == "2.2.0"
    assert payload["source_scope_call_package"]["package_status"] == "ready"


def test_assessment_factory_lite_scope_call_agenda_message_release_marker_preserves_human_boundaries():
    response = client.post(
        "/products/assessment-factory-lite/scope-call-agenda-message",
        json={
            "operator_approval": {
                "approval_status": "operator_approved",
                "scope_approved": True,
                "evidence_boundary_approved": True,
                "commercial_terms_approved": True,
                "buyer_language_approved": True,
            },
            "event_context": {
                "event_id": "buyer-delivery-event-001",
                "recorded_at": "2026-07-17T12:00:00+00:00",
                "human_operator_confirmed": True,
                "delivery_completed": True,
            },
            "follow_up_context": {
                "buyer_response_status": "interested",
                "response_received_at": "2026-07-18T09:00:00+00:00",
                "response_summary": "Buyer wants to schedule a scope call.",
            },
            "follow_up_event_context": {
                "event_id": "buyer-follow-up-event-001",
                "recorded_at": "2026-07-21T12:00:00+00:00",
                "human_operator_confirmed": True,
                "follow_up_completed": True,
            },
        },
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["send_policy"]["send_allowed"] is False
    assert payload["send_policy"]["automated_send_allowed"] is False
    assert payload["send_policy"]["calendar_invite_allowed"] is False
    assert payload["send_policy"]["automatic_scheduling_allowed"] is False
    assert payload["send_policy"]["requires_human_operator"] is True
    assert payload["operator_review"]["approved_for_sending"] is False
    assert payload["operator_review"]["approved_for_scheduling"] is False


