from backend.app.gagf.evidence_conflict_service import EvidenceConflictService
from backend.app.gagf.schemas import RawSecurityEvent, TimestampQuality


def make_event(
    event_id="evt-1",
    source_system="defender",
    event_type="unauthorized_api_call",
    metadata=None,
):
    if metadata is None:
        metadata = {
            "raw_payload": {
                "id": event_id,
            },
        }

    return RawSecurityEvent(
        event_id=event_id,
        event_type=event_type,
        event_occurred_at="2026-07-09T10:00:00Z",
        timestamp_quality=TimestampQuality.SOURCE_OCCURRED_AT,
        kernel_eligible=True,
        source_system=source_system,
        metadata=metadata,
    )


def test_evidence_conflict_service_returns_no_conflicts_for_empty_batch():
    result = EvidenceConflictService().detect_conflicts([])

    assert result["status"] == "ok"
    assert result["event_count"] == 0
    assert result["conflict_count"] == 0
    assert result["severity_counts"]["critical"] == 0
    assert result["severity_counts"]["warning"] == 0
    assert result["severity_counts"]["info"] == 0
    assert result["conflicts"] == []


def test_evidence_conflict_service_returns_no_conflicts_for_aligned_security_events():
    events = [
        make_event(
            event_id="evt-1",
            source_system="defender",
            event_type="unauthorized_api_call",
            metadata={
                "severity": "high",
                "status": "active",
            },
        ),
        make_event(
            event_id="evt-2",
            source_system="sentinelone",
            event_type="unauthorized_api_call",
            metadata={
                "classification": "malware",
                "analyst_verdict": "true_positive",
            },
        ),
    ]

    result = EvidenceConflictService().detect_conflicts(events)

    assert result["status"] == "ok"
    assert result["event_count"] == 2
    assert result["conflict_count"] == 0
    assert result["conflicts"] == []


def test_evidence_conflict_service_detects_security_resolution_mismatch():
    events = [
        make_event(
            event_id="evt-1",
            source_system="defender",
            event_type="unauthorized_api_call",
            metadata={
                "severity": "high",
                "status": "active",
            },
        ),
        make_event(
            event_id="evt-2",
            source_system="sentinelone",
            event_type="verification_passed",
            metadata={
                "mitigation_status": "mitigated",
            },
        ),
    ]

    result = EvidenceConflictService().detect_conflicts(events)

    assert result["status"] == "ok"
    assert result["event_count"] == 2
    assert result["conflict_count"] == 1
    assert result["severity_counts"]["warning"] == 1

    conflict = result["conflicts"][0]

    assert conflict["conflict_type"] == "security_resolution_mismatch"
    assert conflict["severity"] == "warning"
    assert conflict["sources"] == ["defender", "sentinelone"]


def test_evidence_conflict_service_detects_workflow_state_mismatch():
    events = [
        make_event(
            event_id="evt-1",
            source_system="jira",
            event_type="work_blocked",
            metadata={
                "status": "blocked",
            },
        ),
        make_event(
            event_id="evt-2",
            source_system="github",
            event_type="verification_passed",
            metadata={
                "state": "merged",
            },
        ),
    ]

    result = EvidenceConflictService().detect_conflicts(events)

    assert result["status"] == "ok"
    assert result["event_count"] == 2
    assert result["conflict_count"] == 1

    conflict = result["conflicts"][0]

    assert conflict["conflict_type"] == "workflow_state_mismatch"
    assert conflict["severity"] == "warning"
    assert conflict["sources"] == ["github", "jira"]


def test_evidence_conflict_service_detects_identity_outcome_mismatch():
    events = [
        make_event(
            event_id="evt-1",
            source_system="okta",
            event_type="login_failed",
            metadata={
                "outcome": "failure",
            },
        ),
        make_event(
            event_id="evt-2",
            source_system="entra",
            event_type="login_success",
            metadata={
                "outcome": "success",
            },
        ),
    ]

    result = EvidenceConflictService().detect_conflicts(events)

    assert result["status"] == "ok"
    assert result["event_count"] == 2
    assert result["conflict_count"] == 1

    conflict = result["conflicts"][0]

    assert conflict["conflict_type"] == "identity_outcome_mismatch"
    assert conflict["severity"] == "warning"
    assert conflict["sources"] == ["entra", "okta"]


def test_evidence_conflict_service_detects_multiple_conflicts():
    events = [
        make_event(
            event_id="evt-1",
            source_system="defender",
            event_type="unauthorized_api_call",
            metadata={
                "severity": "high",
                "status": "active",
            },
        ),
        make_event(
            event_id="evt-2",
            source_system="sentinelone",
            event_type="verification_passed",
            metadata={
                "mitigation_status": "mitigated",
            },
        ),
        make_event(
            event_id="evt-3",
            source_system="jira",
            event_type="work_blocked",
            metadata={
                "status": "blocked",
            },
        ),
        make_event(
            event_id="evt-4",
            source_system="github",
            event_type="verification_passed",
            metadata={
                "state": "merged",
            },
        ),
    ]

    result = EvidenceConflictService().detect_conflicts(events)

    conflict_types = {
        conflict["conflict_type"]
        for conflict in result["conflicts"]
    }

    assert result["status"] == "ok"
    assert result["event_count"] == 4
    assert result["conflict_count"] == 2
    assert result["severity_counts"]["warning"] == 2
    assert "security_resolution_mismatch" in conflict_types
    assert "workflow_state_mismatch" in conflict_types


def test_evidence_conflict_service_builds_custom_severity_counts():
    service = EvidenceConflictService()

    conflicts = [
        {"severity": "critical"},
        {"severity": "warning"},
        {"severity": "warning"},
        {"severity": "info"},
    ]

    counts = service.build_severity_counts(conflicts)

    assert counts["critical"] == 1
    assert counts["warning"] == 2
    assert counts["info"] == 1


def test_evidence_conflict_service_ignores_unknown_metadata_shape():
    event = make_event(
        event_id="evt-1",
        source_system="defender",
        event_type="unauthorized_api_call",
        metadata=None,
    )

    result = EvidenceConflictService().detect_conflicts([event])

    assert result["status"] == "ok"
    assert result["event_count"] == 1
    assert result["conflict_count"] == 0
    assert result["conflicts"] == []

