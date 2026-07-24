from dataclasses import FrozenInstanceError

import pytest

from backend.app.gagf.governance_assessment_domain import (
    EvidenceSourceKind,
    EvidenceSourceReference,
)
from backend.app.gagf.governance_assessment_evidence_intake import (
    AssessmentEvidenceIntakeError,
    GovernanceAssessmentEvidenceIntakeService,
)
from backend.app.gagf.governance_assessment_isolation import (
    CommercialHierarchyContext,
)


SERVICE = GovernanceAssessmentEvidenceIntakeService()


def build_context():
    return CommercialHierarchyContext(
        tenant_id="tenant-alpha",
        client_id="client-acme",
        engagement_id="engagement-001",
        assessment_id="assessment-001",
    )


def build_source(kind=EvidenceSourceKind.CSV):
    return EvidenceSourceReference(
        source_id="source-001",
        kind=kind,
        display_name="Ticket Export",
        source_location="uploads/tickets.csv",
    )


def valid_csv():
    return (
        "event_id,event_type,occurred_at,work_item_id,owner\n"
        "event-001,APPROVAL_DELAYED,"
        "2026-07-01T12:00:00Z,TICKET-1,security\n"
        "event-002,WORK_BLOCKED,"
        "2026-07-01T13:00:00+00:00,TICKET-2,operations\n"
    )


def test_ingest_csv_accepts_valid_rows():
    result = SERVICE.ingest_csv(
        context=build_context(),
        source=build_source(),
        csv_text=valid_csv(),
    )

    assert result.total_rows == 2
    assert result.accepted_count == 2
    assert result.rejected_count == 0
    assert result.valid is True


def test_records_are_bound_to_full_hierarchy():
    result = SERVICE.ingest_csv(
        context=build_context(),
        source=build_source(),
        csv_text=valid_csv(),
    )

    record = result.accepted_records[0]

    assert record.hierarchy_key == (
        "tenant-alpha/client-acme/"
        "engagement-001/assessment-001"
    )
    assert record.source_id == "source-001"


def test_ingest_csv_preserves_additional_attributes():
    result = SERVICE.ingest_csv(
        context=build_context(),
        source=build_source(),
        csv_text=valid_csv(),
    )

    first = result.accepted_records[0]

    assert first.attributes == {
        "work_item_id": "TICKET-1",
        "owner": "security",
    }


def test_timestamps_are_normalized_to_utc():
    csv_text = (
        "event_id,event_type,occurred_at\n"
        "event-001,WORK_BLOCKED,"
        "2026-07-01T08:00:00-04:00\n"
    )

    result = SERVICE.ingest_csv(
        context=build_context(),
        source=build_source(),
        csv_text=csv_text,
    )

    assert (
        result.accepted_records[0]
        .occurred_at.isoformat()
        == "2026-07-01T12:00:00+00:00"
    )


def test_evidence_hash_is_deterministic():
    first = SERVICE.ingest_csv(
        context=build_context(),
        source=build_source(),
        csv_text=valid_csv(),
    )
    second = SERVICE.ingest_csv(
        context=build_context(),
        source=build_source(),
        csv_text=valid_csv(),
    )

    assert (
        first.accepted_records[0].evidence_hash
        == second.accepted_records[0].evidence_hash
    )
    assert first.intake_hash == second.intake_hash


def test_same_event_is_distinct_across_tenants():
    alpha = SERVICE.ingest_csv(
        context=build_context(),
        source=build_source(),
        csv_text=valid_csv(),
    )
    beta = SERVICE.ingest_csv(
        context=CommercialHierarchyContext(
            tenant_id="tenant-beta",
            client_id="client-acme",
            engagement_id="engagement-001",
            assessment_id="assessment-001",
        ),
        source=build_source(),
        csv_text=valid_csv(),
    )

    assert (
        alpha.accepted_records[0].evidence_hash
        != beta.accepted_records[0].evidence_hash
    )


def test_duplicate_event_id_is_rejected():
    csv_text = (
        "event_id,event_type,occurred_at\n"
        "event-001,WORK_BLOCKED,2026-07-01T12:00:00Z\n"
        "event-001,ESCALATION,2026-07-01T13:00:00Z\n"
    )

    result = SERVICE.ingest_csv(
        context=build_context(),
        source=build_source(),
        csv_text=csv_text,
    )

    assert result.accepted_count == 1
    assert result.rejected_count == 1
    assert result.valid is False
    assert "duplicate event_id" in (
        result.rejected_rows[0].reason
    )


def test_invalid_timestamp_is_rejected():
    csv_text = (
        "event_id,event_type,occurred_at\n"
        "event-001,WORK_BLOCKED,not-a-date\n"
    )

    result = SERVICE.ingest_csv(
        context=build_context(),
        source=build_source(),
        csv_text=csv_text,
    )

    assert result.accepted_count == 0
    assert result.rejected_count == 1
    assert "ISO-8601" in result.rejected_rows[0].reason


def test_timezone_is_required():
    csv_text = (
        "event_id,event_type,occurred_at\n"
        "event-001,WORK_BLOCKED,2026-07-01T12:00:00\n"
    )

    result = SERVICE.ingest_csv(
        context=build_context(),
        source=build_source(),
        csv_text=csv_text,
    )

    assert result.rejected_count == 1
    assert "timezone" in result.rejected_rows[0].reason


def test_missing_required_header_fails_intake():
    csv_text = (
        "event_id,occurred_at\n"
        "event-001,2026-07-01T12:00:00Z\n"
    )

    with pytest.raises(
        AssessmentEvidenceIntakeError,
        match="event_type",
    ):
        SERVICE.ingest_csv(
            context=build_context(),
            source=build_source(),
            csv_text=csv_text,
        )


def test_empty_csv_fails_intake():
    with pytest.raises(
        AssessmentEvidenceIntakeError,
        match="must not be empty",
    ):
        SERVICE.ingest_csv(
            context=build_context(),
            source=build_source(),
            csv_text="   ",
        )


def test_non_csv_source_is_rejected():
    with pytest.raises(
        AssessmentEvidenceIntakeError,
        match="CSV evidence source",
    ):
        SERVICE.ingest_csv(
            context=build_context(),
            source=build_source(EvidenceSourceKind.API),
            csv_text=valid_csv(),
        )


def test_assessment_context_is_required():
    context = CommercialHierarchyContext(
        tenant_id="tenant-alpha",
        client_id="client-acme",
        engagement_id="engagement-001",
    )

    with pytest.raises(
        AssessmentEvidenceIntakeError,
        match="assessment_id",
    ):
        SERVICE.ingest_csv(
            context=context,
            source=build_source(),
            csv_text=valid_csv(),
        )


def test_result_serializes_counts_and_records():
    result = SERVICE.ingest_csv(
        context=build_context(),
        source=build_source(),
        csv_text=valid_csv(),
    )

    serialized = result.to_dict()

    assert serialized["accepted_count"] == 2
    assert serialized["rejected_count"] == 0
    assert serialized["valid"] is True
    assert (
        serialized["accepted_records"][0]
        ["event_type"]
        == "APPROVAL_DELAYED"
    )


def test_evidence_record_is_immutable():
    result = SERVICE.ingest_csv(
        context=build_context(),
        source=build_source(),
        csv_text=valid_csv(),
    )

    with pytest.raises(FrozenInstanceError):
        result.accepted_records[0].event_id = "changed"
