from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def test_assessment_factory_lite_buyer_delivery_follow_up_release_marker_version():
    response = client.get("/version")

    assert response.status_code == 200
    assert response.json() == {
        "version": "2.2.0",
        "release": "assessment-factory-lite-buyer-delivery-follow-up",
        "sprint": "5.0",
        "status": "complete",
    }


def test_assessment_factory_lite_buyer_delivery_follow_up_release_marker_routes_are_available():
    actual_routes = {route.path for route in app.routes}

    assert "/products/assessment-factory-lite/buyer-delivery-package" in actual_routes
    assert "/products/assessment-factory-lite/buyer-delivery-message" in actual_routes
    assert "/products/assessment-factory-lite/buyer-delivery-event-record" in actual_routes
    assert "/products/assessment-factory-lite/buyer-follow-up-tracker" in actual_routes
    assert "/products/assessment-factory-lite/buyer-follow-up-message" in actual_routes
    assert "/products/assessment-factory-lite/buyer-follow-up-event-record" in actual_routes
    assert "/products/assessment-factory-lite/assessment-scope-call-package" in actual_routes


def test_assessment_factory_lite_buyer_delivery_follow_up_release_marker_preserves_assessment_scope_call_contract_version():
    response = client.post(
        "/products/assessment-factory-lite/assessment-scope-call-package",
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

    assert payload["package_type"] == "assessment_factory_lite_assessment_scope_call_package"
    assert payload["release"] == "assessment-factory-lite-buyer-delivery-follow-up"
    assert payload["version"] == "2.2.0"
    assert payload["package_status"] == "ready"


def test_assessment_factory_lite_buyer_delivery_follow_up_release_marker_preserves_follow_up_event_record_contract_version():
    response = client.post(
        "/products/assessment-factory-lite/buyer-follow-up-event-record",
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

    assert payload["event_type"] == "assessment_factory_lite_buyer_follow_up_event_record"
    assert payload["release"] == "assessment-factory-lite-proposal-export-package"
    assert payload["version"] == "2.1.0"
    assert payload["event_status"] == "recorded"


def test_assessment_factory_lite_buyer_delivery_follow_up_release_marker_preserves_buyer_follow_up_message_contract_version():
    response = client.post(
        "/products/assessment-factory-lite/buyer-follow-up-message",
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
        },
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["message_type"] == "assessment_factory_lite_buyer_follow_up_message"
    assert payload["release"] == "assessment-factory-lite-proposal-export-package"
    assert payload["version"] == "2.1.0"
    assert payload["message_status"] == "draft_ready"
