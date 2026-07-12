from backend.app.connectors.okta_connector import OktaConnector


def test_okta_connector_maps_failed_authentication_to_failed_auth_burst():
    connector = OktaConnector()

    event = {
        "uuid": "okta-001",
        "eventType": "user.authentication.failed",
        "published": "2026-07-08T12:00:00Z",
        "outcome": {
            "result": "FAILURE",
        },
    }

    normalized = connector.normalize_event(event)

    assert normalized.event_id == "okta-001"
    assert normalized.source_system == "okta"
    assert normalized.event_type == "failed_auth_burst"
    assert normalized.kernel_eligible is True


def test_okta_connector_maps_mfa_bypass_to_unauthorized_api_call():
    connector = OktaConnector()

    event = {
        "uuid": "okta-002",
        "eventType": "user.mfa.attempt_bypass",
        "published": "2026-07-08T12:05:00Z",
        "outcome": {
            "result": "FAILURE",
        },
    }

    normalized = connector.normalize_event(event)

    assert normalized.event_id == "okta-002"
    assert normalized.source_system == "okta"
    assert normalized.event_type == "unauthorized_api_call"


def test_okta_connector_maps_successful_session_to_verification_passed():
    connector = OktaConnector()

    event = {
        "uuid": "okta-003",
        "eventType": "user.session.start",
        "published": "2026-07-08T12:10:00Z",
        "outcome": {
            "result": "SUCCESS",
        },
    }

    normalized = connector.normalize_event(event)

    assert normalized.event_id == "okta-003"
    assert normalized.source_system == "okta"
    assert normalized.event_type == "verification_passed"


def test_okta_connector_maps_lifecycle_event_to_historically_valid_control():
    connector = OktaConnector()

    event = {
        "uuid": "okta-004",
        "eventType": "user.lifecycle.activate",
        "published": "2026-07-08T12:15:00Z",
        "outcome": {
            "result": "SUCCESS",
        },
    }

    normalized = connector.normalize_event(event)

    assert normalized.event_id == "okta-004"
    assert normalized.source_system == "okta"
    assert normalized.event_type == "historically_valid_control"


def test_okta_connector_normalizes_multiple_events():
    connector = OktaConnector()

    events = [
        {
            "uuid": "okta-005",
            "eventType": "user.authentication.failed",
            "published": "2026-07-08T12:20:00Z",
            "outcome": {
                "result": "FAILURE",
            },
        },
        {
            "uuid": "okta-006",
            "eventType": "user.session.start",
            "published": "2026-07-08T12:25:00Z",
            "outcome": {
                "result": "SUCCESS",
            },
        },
    ]

    normalized = connector.normalize_events(events)

    assert len(normalized) == 2
    assert normalized[0].event_type == "failed_auth_burst"
    assert normalized[1].event_type == "verification_passed"


def test_okta_connector_uses_missing_id_fallback():
    connector = OktaConnector()

    event = {
        "eventType": "user.lifecycle.activate",
        "published": "2026-07-08T12:30:00Z",
        "outcome": {
            "result": "SUCCESS",
        },
    }

    normalized = connector.normalize_event(event)

    assert normalized.event_id == "okta-event-missing-id"
    assert normalized.source_system == "okta"
    assert normalized.event_type == "historically_valid_control"

