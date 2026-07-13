from backend.app.connectors.jira_connector import JiraConnector
from backend.app.gagf.schemas import TimestampQuality


def test_jira_connector_normalizes_blocked_issue():
    connector = JiraConnector()

    event = connector.normalize_event(
        {
            "id": "jira-issue-001",
            "key": "FIP-101",
            "issue_type": "Story",
            "status": "Blocked",
            "priority": "Medium",
            "blocked": True,
            "created": "2026-07-07T12:00:00Z",
            "updated": "2026-07-07T12:30:00Z",
        }
    )

    assert event.event_id == "jira-issue-001"
    assert event.source_system == "jira"
    assert event.event_type == "honeyfile_interaction"
    assert event.event_occurred_at == "2026-07-07T12:00:00Z"
    assert event.event_created_at == "2026-07-07T12:00:00Z"
    assert event.timestamp_quality == TimestampQuality.SOURCE_OCCURRED_AT
    assert event.kernel_eligible is True
    assert event.metadata["raw_payload"]["key"] == "FIP-101"


def test_jira_connector_normalizes_high_priority_bug():
    connector = JiraConnector()

    event = connector.normalize_event(
        {
            "id": "jira-bug-001",
            "key": "FIP-202",
            "issue_type": "Bug",
            "status": "Open",
            "priority": "Critical",
            "created": "2026-07-07T13:00:00Z",
            "updated": "2026-07-07T13:15:00Z",
        }
    )

    assert event.event_id == "jira-bug-001"
    assert event.source_system == "jira"
    assert event.event_type == "failed_auth_burst"
    assert event.timestamp_quality == TimestampQuality.SOURCE_OCCURRED_AT
    assert event.metadata["raw_payload"]["priority"] == "Critical"


def test_jira_connector_normalizes_done_issue():
    connector = JiraConnector()

    event = connector.normalize_event(
        {
            "id": "jira-done-001",
            "key": "FIP-303",
            "issue_type": "Task",
            "status": "Done",
            "priority": "Low",
            "created": "2026-07-07T14:00:00Z",
            "updated": "2026-07-07T16:00:00Z",
        }
    )

    assert event.event_id == "jira-done-001"
    assert event.source_system == "jira"
    assert event.event_type == "verification_passed"


def test_jira_connector_normalizes_multiple_events():
    connector = JiraConnector()

    events = connector.normalize_events(
        [
            {
                "id": "jira-001",
                "key": "FIP-1",
                "issue_type": "Story",
                "status": "In Progress",
                "priority": "Medium",
                "created": "2026-07-07T12:00:00Z",
                "updated": "2026-07-07T12:30:00Z",
            },
            {
                "id": "jira-002",
                "key": "FIP-2",
                "issue_type": "Task",
                "status": "Resolved",
                "priority": "Low",
                "created": "2026-07-07T13:00:00Z",
                "updated": "2026-07-07T14:00:00Z",
            },
        ]
    )

    assert len(events) == 2
    assert events[0].source_system == "jira"
    assert events[1].source_system == "jira"
    assert events[0].event_type == "historically_valid_control"
    assert events[1].event_type == "verification_passed"


def test_jira_connector_falls_back_to_missing_id():
    connector = JiraConnector()

    event = connector.normalize_event(
        {
            "key": "FIP-MISSING",
            "issue_type": "Task",
            "status": "Open",
            "priority": "Medium",
            "created": "2026-07-07T15:00:00Z",
            "updated": "2026-07-07T15:10:00Z",
        }
    )

    assert event.event_id == "jira-event-missing-id"
    assert event.source_system == "jira"
    assert event.event_type == "historically_valid_control"


