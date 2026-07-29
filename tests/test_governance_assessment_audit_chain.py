import sqlite3

from backend.app.gagf.governance_assessment_audit import (
    AssessmentAuditLedger,
    build_assessment_audit_event,
)
from backend.app.gagf.governance_assessment_audit_integrity import (
    ASSESSMENT_AUDIT_GENESIS_HASH,
)


def build_event(
    *,
    tenant_id: str = "tenant-alpha",
    request_id: str = "request-001",
):
    return build_assessment_audit_event(
        request_id=request_id,
        tenant_id=tenant_id,
        actor_id="actor-001",
        actor_roles=("assessment:read",),
        method="GET",
        route="/api/v1/governance-assessments",
        outcome="allowed",
        status_code=200,
    )


def test_first_tenant_event_uses_genesis_hash(tmp_path):
    ledger = AssessmentAuditLedger(
        tmp_path / "audit.sqlite3"
    )

    stored = ledger.append(build_event())

    assert stored.previous_hash == (
        ASSESSMENT_AUDIT_GENESIS_HASH
    )
    assert len(stored.event_hash) == 64


def test_second_event_links_to_first_event(tmp_path):
    ledger = AssessmentAuditLedger(
        tmp_path / "audit.sqlite3"
    )

    first = ledger.append(
        build_event(request_id="request-001")
    )
    second = ledger.append(
        build_event(request_id="request-002")
    )

    assert second.previous_hash == first.event_hash


def test_tenant_chains_have_separate_genesis_events(tmp_path):
    ledger = AssessmentAuditLedger(
        tmp_path / "audit.sqlite3"
    )

    alpha = ledger.append(
        build_event(tenant_id="tenant-alpha")
    )
    beta = ledger.append(
        build_event(tenant_id="tenant-beta")
    )

    assert alpha.previous_hash == (
        ASSESSMENT_AUDIT_GENESIS_HASH
    )
    assert beta.previous_hash == (
        ASSESSMENT_AUDIT_GENESIS_HASH
    )


def test_valid_persisted_chain_verifies(tmp_path):
    ledger = AssessmentAuditLedger(
        tmp_path / "audit.sqlite3"
    )

    ledger.append(build_event(request_id="request-001"))
    ledger.append(build_event(request_id="request-002"))
    ledger.append(build_event(request_id="request-003"))

    result = ledger.verify_tenant_chain(
        tenant_id="tenant-alpha"
    )

    assert result.valid is True
    assert result.checked_count == 3


def test_modified_database_record_fails_verification(tmp_path):
    database_path = tmp_path / "audit.sqlite3"
    ledger = AssessmentAuditLedger(database_path)

    event = ledger.append(build_event())

    with sqlite3.connect(database_path) as connection:
        connection.execute(
            """
            UPDATE assessment_audit_events
            SET status_code = 403
            WHERE event_id = ?
            """,
            (event.event_id,),
        )
        connection.commit()

    result = ledger.verify_tenant_chain(
        tenant_id="tenant-alpha"
    )

    assert result.valid is False
    assert result.reason_code == (
        "AUDIT_EVENT_HASH_MISMATCH"
    )


def test_deleted_middle_event_breaks_chain(tmp_path):
    database_path = tmp_path / "audit.sqlite3"
    ledger = AssessmentAuditLedger(database_path)

    ledger.append(build_event(request_id="request-001"))
    middle = ledger.append(
        build_event(request_id="request-002")
    )
    ledger.append(build_event(request_id="request-003"))

    with sqlite3.connect(database_path) as connection:
        connection.execute(
            """
            DELETE FROM assessment_audit_events
            WHERE event_id = ?
            """,
            (middle.event_id,),
        )
        connection.commit()

    result = ledger.verify_tenant_chain(
        tenant_id="tenant-alpha"
    )

    assert result.valid is False
    assert result.reason_code == (
        "AUDIT_PREVIOUS_HASH_MISMATCH"
    )


def test_existing_legacy_table_is_migrated(tmp_path):
    database_path = tmp_path / "audit.sqlite3"

    with sqlite3.connect(database_path) as connection:
        connection.execute(
            """
            CREATE TABLE assessment_audit_events (
                event_id TEXT PRIMARY KEY,
                request_id TEXT NOT NULL,
                tenant_id TEXT,
                actor_id TEXT,
                actor_roles_json TEXT NOT NULL,
                method TEXT NOT NULL,
                route TEXT NOT NULL,
                outcome TEXT NOT NULL,
                status_code INTEGER NOT NULL,
                reason_code TEXT,
                occurred_at TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            INSERT INTO assessment_audit_events
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "legacy-event",
                "legacy-request",
                "tenant-alpha",
                "legacy-actor",
                '["assessment:read"]',
                "GET",
                "/legacy",
                "allowed",
                200,
                None,
                "2026-07-28T12:00:00+00:00",
            ),
        )
        connection.commit()

    ledger = AssessmentAuditLedger(database_path)
    events = ledger.list_events_chronological(
        tenant_id="tenant-alpha"
    )

    assert len(events) == 1
    assert events[0].previous_hash == (
        ASSESSMENT_AUDIT_GENESIS_HASH
    )
    assert len(events[0].event_hash) == 64
    assert ledger.verify_tenant_chain(
        tenant_id="tenant-alpha"
    ).valid is True


def test_list_events_remains_newest_first(tmp_path):
    ledger = AssessmentAuditLedger(
        tmp_path / "audit.sqlite3"
    )

    ledger.append(build_event(request_id="request-001"))
    ledger.append(build_event(request_id="request-002"))

    events = ledger.list_events(
        tenant_id="tenant-alpha"
    )

    assert [event.request_id for event in events] == [
        "request-002",
        "request-001",
    ]
