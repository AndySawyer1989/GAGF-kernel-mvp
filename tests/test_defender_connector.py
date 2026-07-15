from backend.app.connectors.defender_connector import DefenderConnector


def test_defender_connector_maps_high_severity_alert_to_unauthorized_api_call():
    connector = DefenderConnector()

    event = {
        "id": "def-001",
        "title": "Suspicious PowerShell activity",
        "category": "Execution",
        "severity": "high",
        "status": "new",
        "createdTime": "2026-07-08T12:00:00Z",
    }

    normalized = connector.normalize_event(event)

    assert normalized.event_id == "def-001"
    assert normalized.source_system == "defender"
    assert normalized.event_type == "unauthorized_api_call"
    assert normalized.kernel_eligible is True


def test_defender_connector_maps_true_positive_to_unauthorized_api_call():
    connector = DefenderConnector()

    event = {
        "id": "def-002",
        "title": "Credential theft alert",
        "category": "CredentialAccess",
        "severity": "medium",
        "status": "resolved",
        "classification": "truePositive",
        "createdTime": "2026-07-08T12:05:00Z",
    }

    normalized = connector.normalize_event(event)

    assert normalized.event_id == "def-002"
    assert normalized.source_system == "defender"
    assert normalized.event_type == "unauthorized_api_call"


def test_defender_connector_maps_malware_determination_to_unauthorized_api_call():
    connector = DefenderConnector()

    event = {
        "id": "def-003",
        "title": "Malware detected",
        "category": "Malware",
        "severity": "medium",
        "status": "inProgress",
        "determination": "malware",
        "createdTime": "2026-07-08T12:10:00Z",
    }

    normalized = connector.normalize_event(event)

    assert normalized.event_id == "def-003"
    assert normalized.source_system == "defender"
    assert normalized.event_type == "unauthorized_api_call"


def test_defender_connector_maps_resolved_alert_to_verification_passed():
    connector = DefenderConnector()

    event = {
        "id": "def-004",
        "title": "Informational alert closed",
        "category": "Informational",
        "severity": "low",
        "status": "resolved",
        "createdTime": "2026-07-08T12:15:00Z",
    }

    normalized = connector.normalize_event(event)

    assert normalized.event_id == "def-004"
    assert normalized.source_system == "defender"
    assert normalized.event_type == "verification_passed"


def test_defender_connector_normalizes_multiple_events():
    connector = DefenderConnector()

    events = [
        {
            "id": "def-005",
            "title": "Ransomware behavior detected",
            "category": "Malware",
            "severity": "critical",
            "status": "new",
            "createdTime": "2026-07-08T12:20:00Z",
        },
        {
            "id": "def-006",
            "title": "Device healthy",
            "category": "DeviceHealth",
            "severity": "informational",
            "status": "resolved",
            "createdTime": "2026-07-08T12:25:00Z",
        },
    ]

    normalized = connector.normalize_events(events)

    assert len(normalized) == 2
    assert normalized[0].event_type == "unauthorized_api_call"
    assert normalized[1].event_type == "verification_passed"


def test_defender_connector_uses_missing_id_fallback():
    connector = DefenderConnector()

    event = {
        "title": "Device healthy",
        "category": "DeviceHealth",
        "severity": "informational",
        "status": "resolved",
        "createdTime": "2026-07-08T12:30:00Z",
    }

    normalized = connector.normalize_event(event)

    assert normalized.event_id == "defender-event-missing-id"
    assert normalized.source_system == "defender"
    assert normalized.event_type == "verification_passed"





