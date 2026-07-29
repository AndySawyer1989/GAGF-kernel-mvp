import sqlite3

from backend.app.gagf.governance_assessment_audit import (
    AssessmentAuditLedger,
    build_assessment_audit_event,
)


def build_event(
    *,
    tenant_id: str = "tenant-alpha",
    actor_id: str = "actor-001",
    outcome: str = "allowed",
    status_code: int = 200,
    reason_code: str | None = None,
):
    return build_assessment_audit_event(
        request_id="request-001",
        tenant_id=tenant_id,
        actor_id=actor_id,
        actor_roles=("assessment:read",),
        method="GET",
        route="/api/v1/governance-assessments",
        outcome=outcome,
        status_code=status_code,
        reason_code=reason_code,
    )


def test_append_and_list_event(tmp_path):
    ledger = AssessmentAuditLedger(
        tmp_path / "audit.sqlite3"
    )
    event = build_event()

    ledger.append(event)

    events = ledger.list_events(
        tenant_id="tenant-alpha"
    )

    assert events == [event]


def test_tenant_event_lists_are_isolated(tmp_path):
    ledger = AssessmentAuditLedger(
        tmp_path / "audit.sqlite3"
    )
    alpha = build_event(tenant_id="tenant-alpha")
    beta = build_event(tenant_id="tenant-beta")

    ledger.append(alpha)
    ledger.append(beta)

    assert ledger.list_events(
        tenant_id="tenant-alpha"
    ) == [alpha]
    assert ledger.list_events(
        tenant_id="tenant-beta"
    ) == [beta]


def test_denied_event_preserves_reason_code(tmp_path):
    ledger = AssessmentAuditLedger(
        tmp_path / "audit.sqlite3"
    )
    event = build_event(
        outcome="denied",
        status_code=403,
        reason_code="ASSESSMENT_TENANT_MISMATCH",
    )

    ledger.append(event)

    stored = ledger.list_events(
        tenant_id="tenant-alpha"
    )[0]

    assert stored.outcome == "denied"
    assert stored.status_code == 403
    assert stored.reason_code == (
        "ASSESSMENT_TENANT_MISMATCH"
    )


def test_event_ids_are_unique():
    first = build_event()
    second = build_event()

    assert first.event_id != second.event_id


def test_method_is_normalized_to_uppercase():
    event = build_assessment_audit_event(
        request_id="request-001",
        tenant_id="tenant-alpha",
        actor_id="actor-001",
        actor_roles=("assessment:read",),
        method="get",
        route="/route",
        outcome="allowed",
        status_code=200,
    )

    assert event.method == "GET"


def test_duplicate_event_id_is_rejected(tmp_path):
    ledger = AssessmentAuditLedger(
        tmp_path / "audit.sqlite3"
    )
    event = build_event()

    ledger.append(event)

    try:
        ledger.append(event)
    except sqlite3.IntegrityError:
        pass
    else:
        raise AssertionError(
            "duplicate audit event was accepted"
        )


def test_list_limit_is_enforced(tmp_path):
    ledger = AssessmentAuditLedger(
        tmp_path / "audit.sqlite3"
    )

    for index in range(5):
        event = build_assessment_audit_event(
            request_id=f"request-{index}",
            tenant_id="tenant-alpha",
            actor_id="actor-001",
            actor_roles=("assessment:read",),
            method="GET",
            route="/route",
            outcome="allowed",
            status_code=200,
        )
        ledger.append(event)

    events = ledger.list_events(
        tenant_id="tenant-alpha",
        limit=2,
    )

    assert len(events) == 2


def test_to_dict_serializes_roles_as_list():
    payload = build_event().to_dict()

    assert payload["actor_roles"] == [
        "assessment:read"
    ]
