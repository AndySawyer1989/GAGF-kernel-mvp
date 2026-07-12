from backend.app.connectors.entra_connector import EntraConnector


def test_entra_connector_maps_failed_sign_in_to_failed_auth_burst():
    connector = EntraConnector()

    event = {
        "id": "entra-001",
        "activityDisplayName": "User sign-in failed",
        "createdDateTime": "2026-07-08T12:00:00Z",
        "status": {
            "errorCode": 50126,
            "failureReason": "Invalid username or password failure",
        },
    }

    normalized = connector.normalize_event(event)

    assert normalized.event_id == "entra-001"
    assert normalized.source_system == "entra"
    assert normalized.event_type == "failed_auth_burst"
    assert normalized.kernel_eligible is True


def test_entra_connector_maps_conditional_access_failure_to_unauthorized_api_call():
    connector = EntraConnector()

    event = {
        "id": "entra-002",
        "activityDisplayName": "User sign-in",
        "createdDateTime": "2026-07-08T12:05:00Z",
        "conditionalAccessStatus": "failure",
        "status": {
            "errorCode": 0,
        },
    }

    normalized = connector.normalize_event(event)

    assert normalized.event_id == "entra-002"
    assert normalized.source_system == "entra"
    assert normalized.event_type == "unauthorized_api_call"


def test_entra_connector_maps_risky_sign_in_to_unauthorized_api_call():
    connector = EntraConnector()

    event = {
        "id": "entra-003",
        "activityDisplayName": "User sign-in",
        "createdDateTime": "2026-07-08T12:10:00Z",
        "riskState": "atRisk",
        "riskLevelAggregated": "high",
        "status": {
            "errorCode": 0,
        },
    }

    normalized = connector.normalize_event(event)

    assert normalized.event_id == "entra-003"
    assert normalized.source_system == "entra"
    assert normalized.event_type == "unauthorized_api_call"


def test_entra_connector_maps_successful_sign_in_to_verification_passed():
    connector = EntraConnector()

    event = {
        "id": "entra-004",
        "activityDisplayName": "User sign-in",
        "createdDateTime": "2026-07-08T12:15:00Z",
        "conditionalAccessStatus": "success",
        "riskState": "none",
        "riskLevelAggregated": "none",
        "status": {
            "errorCode": 0,
        },
    }

    normalized = connector.normalize_event(event)

    assert normalized.event_id == "entra-004"
    assert normalized.source_system == "entra"
    assert normalized.event_type == "verification_passed"


def test_entra_connector_normalizes_multiple_events():
    connector = EntraConnector()

    events = [
        {
            "id": "entra-005",
            "activityDisplayName": "User sign-in failed",
            "createdDateTime": "2026-07-08T12:20:00Z",
            "status": {
                "errorCode": 50126,
                "failureReason": "Invalid credentials failure",
            },
        },
        {
            "id": "entra-006",
            "activityDisplayName": "User sign-in",
            "createdDateTime": "2026-07-08T12:25:00Z",
            "conditionalAccessStatus": "success",
            "riskState": "none",
            "riskLevelAggregated": "none",
            "status": {
                "errorCode": 0,
            },
        },
    ]

    normalized = connector.normalize_events(events)

    assert len(normalized) == 2
    assert normalized[0].event_type == "failed_auth_burst"
    assert normalized[1].event_type == "verification_passed"


def test_entra_connector_uses_missing_id_fallback():
    connector = EntraConnector()

    event = {
        "activityDisplayName": "Update user",
        "category": "UserManagement",
        "createdDateTime": "2026-07-08T12:30:00Z",
        "status": {
            "errorCode": 0,
        },
    }

    normalized = connector.normalize_event(event)

    assert normalized.event_id == "entra-event-missing-id"
    assert normalized.source_system == "entra"
    assert normalized.event_type == "historically_valid_control"

