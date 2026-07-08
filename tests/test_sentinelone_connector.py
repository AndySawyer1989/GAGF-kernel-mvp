from backend.app.connectors.sentinelone_connector import SentinelOneConnector


def test_sentinelone_connector_maps_active_threat_to_unauthorized_api_call():
    connector = SentinelOneConnector()

    event = {
        "id": "s1-001",
        "eventType": "threat_detected",
        "threatName": "Suspicious PowerShell",
        "classification": "malware",
        "confidenceLevel": "high",
        "mitigationStatus": "not_mitigated",
        "incidentStatus": "unresolved",
        "createdAt": "2026-07-08T12:00:00Z",
    }

    normalized = connector.normalize_event(event)

    assert normalized.event_id == "s1-001"
    assert normalized.source_system == "sentinelone"
    assert normalized.event_type == "unauthorized_api_call"
    assert normalized.kernel_eligible is True


def test_sentinelone_connector_maps_true_positive_to_unauthorized_api_call():
    connector = SentinelOneConnector()

    event = {
        "id": "s1-002",
        "eventType": "analyst_verdict_updated",
        "threatName": "Credential Theft Tool",
        "analystVerdict": "true_positive",
        "mitigationStatus": "mitigated",
        "incidentStatus": "resolved",
        "createdAt": "2026-07-08T12:05:00Z",
    }

    normalized = connector.normalize_event(event)

    assert normalized.event_id == "s1-002"
    assert normalized.source_system == "sentinelone"
    assert normalized.event_type == "unauthorized_api_call"


def test_sentinelone_connector_maps_mitigated_threat_to_verification_passed():
    connector = SentinelOneConnector()

    event = {
        "id": "s1-003",
        "eventType": "threat_mitigated",
        "threatName": "Quarantined Malware",
        "classification": "malware",
        "confidenceLevel": "medium",
        "mitigationStatus": "mitigated",
        "incidentStatus": "resolved",
        "createdAt": "2026-07-08T12:10:00Z",
    }

    normalized = connector.normalize_event(event)

    assert normalized.event_id == "s1-003"
    assert normalized.source_system == "sentinelone"
    assert normalized.event_type == "verification_passed"


def test_sentinelone_connector_maps_agent_online_to_verification_passed():
    connector = SentinelOneConnector()

    event = {
        "id": "s1-004",
        "eventType": "agent_online",
        "agentName": "workstation-001",
        "createdAt": "2026-07-08T12:15:00Z",
    }

    normalized = connector.normalize_event(event)

    assert normalized.event_id == "s1-004"
    assert normalized.source_system == "sentinelone"
    assert normalized.event_type == "verification_passed"


def test_sentinelone_connector_normalizes_multiple_events():
    connector = SentinelOneConnector()

    events = [
        {
            "id": "s1-005",
            "eventType": "threat_detected",
            "threatName": "Suspicious Script",
            "classification": "malware",
            "confidenceLevel": "high",
            "mitigationStatus": "not_mitigated",
            "incidentStatus": "unresolved",
            "createdAt": "2026-07-08T12:20:00Z",
        },
        {
            "id": "s1-006",
            "eventType": "agent_online",
            "agentName": "workstation-002",
            "createdAt": "2026-07-08T12:25:00Z",
        },
    ]

    normalized = connector.normalize_events(events)

    assert len(normalized) == 2
    assert normalized[0].event_type == "unauthorized_api_call"
    assert normalized[1].event_type == "verification_passed"


def test_sentinelone_connector_uses_missing_id_fallback():
    connector = SentinelOneConnector()

    event = {
        "eventType": "threat_note_updated",
        "threatName": "Historical Investigation",
        "mitigationStatus": "mitigated",
        "incidentStatus": "resolved",
        "createdAt": "2026-07-08T12:30:00Z",
    }

    normalized = connector.normalize_event(event)

    assert normalized.event_id == "sentinelone-event-missing-id"
    assert normalized.source_system == "sentinelone"
    assert normalized.event_type == "verification_passed"