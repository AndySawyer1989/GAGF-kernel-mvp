from backend.app.connectors.servicenow_connector import ServiceNowConnector
from backend.app.gagf.schemas import TimestampQuality


def test_servicenow_connector_normalizes_incident_event():
    connector = ServiceNowConnector()

    event = connector.normalize_event(
        {
            "sys_id": "sn-incident-001",
            "table": "incident",
            "category": "security",
            "state": "new",
            "opened_at": "2026-07-06T12:00:00Z",
            "sys_created_on": "2026-07-06T12:01:00Z",
        }
    )

    assert event.event_id == "sn-incident-001"
    assert event.source_system == "servicenow"
    assert event.event_type == "failed_auth_burst"
    assert event.event_occurred_at == "2026-07-06T12:00:00Z"
    assert event.event_created_at == "2026-07-06T12:01:00Z"
    assert event.timestamp_quality == TimestampQuality.SOURCE_OCCURRED_AT
    assert event.kernel_eligible is True
    assert event.metadata["raw_payload"]["table"] == "incident"


def test_servicenow_connector_normalizes_change_request_event():
    connector = ServiceNowConnector()

    event = connector.normalize_event(
        {
            "sys_id": "sn-change-001",
            "table": "change_request",
            "state": "authorize",
            "opened_at": "2026-07-06T13:00:00Z",
            "sys_created_on": "2026-07-06T13:01:00Z",
        }
    )

    assert event.event_id == "sn-change-001"
    assert event.source_system == "servicenow"
    assert event.event_type == "unauthorized_api_call"
    assert event.timestamp_quality == TimestampQuality.SOURCE_OCCURRED_AT
    assert event.metadata["raw_payload"]["table"] == "change_request"


def test_servicenow_connector_normalizes_multiple_events():
    connector = ServiceNowConnector()

    events = connector.normalize_events(
        [
            {
                "sys_id": "sn-001",
                "table": "incident",
                "category": "security",
                "state": "new",
                "opened_at": "2026-07-06T12:00:00Z",
                "sys_created_on": "2026-07-06T12:01:00Z",
            },
            {
                "sys_id": "sn-002",
                "table": "change_request",
                "state": "closed",
                "opened_at": "2026-07-06T13:00:00Z",
                "sys_created_on": "2026-07-06T13:01:00Z",
            },
        ]
    )

    assert len(events) == 2
    assert events[0].source_system == "servicenow"
    assert events[1].source_system == "servicenow"
    assert events[0].event_type == "failed_auth_burst"
    assert events[1].event_type == "verification_passed"


def test_servicenow_connector_falls_back_to_missing_id():
    connector = ServiceNowConnector()

    event = connector.normalize_event(
        {
            "table": "incident",
            "category": "general",
            "state": "new",
            "opened_at": "2026-07-06T14:00:00Z",
            "sys_created_on": "2026-07-06T14:01:00Z",
        }
    )

    assert event.event_id == "servicenow-event-missing-id"
    assert event.source_system == "servicenow"
    assert event.event_type == "historically_valid_control"


