from backend.app.connectors.github_connector import GitHubConnector


def test_github_connector_normalizes_single_event():
    connector = GitHubConnector()

    github_event = {
        "id": "gh-001",
        "event_name": "pull_request",
        "action": "opened",
        "created_at": "2026-07-03T18:00:00Z",
    }

    event = connector.normalize_event(github_event)

    assert event.event_id == "gh-001"
    assert event.source_system == "github"
    assert event.event_type == "unauthorized_api_call"
    assert event.kernel_eligible is True
    assert event.metadata["raw_payload"] == github_event


def test_github_connector_normalizes_multiple_events():
    connector = GitHubConnector()

    github_events = [
        {
            "id": "gh-001",
            "event_name": "pull_request",
            "action": "opened",
            "created_at": "2026-07-03T18:00:00Z",
        },
        {
            "id": "gh-002",
            "event_name": "push",
            "action": "created",
            "created_at": "2026-07-03T18:05:00Z",
        },
    ]

    events = connector.normalize_events(github_events)

    assert len(events) == 2
    assert events[0].event_type == "unauthorized_api_call"
    assert events[1].event_type == "historically_valid_control"


def test_github_connector_maps_unknown_event_to_default_signal():
    connector = GitHubConnector()

    github_event = {
        "id": "gh-unknown",
        "event_name": "unknown_event",
        "action": "unknown_action",
        "created_at": "2026-07-03T18:10:00Z",
    }

    event = connector.normalize_event(github_event)

    assert event.event_type == "failed_auth_burst"
    assert event.source_system == "github"



