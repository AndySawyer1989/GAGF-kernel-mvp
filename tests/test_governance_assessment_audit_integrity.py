from backend.app.gagf.governance_assessment_audit_integrity import (
    ASSESSMENT_AUDIT_GENESIS_HASH,
    ASSESSMENT_AUDIT_HASH_VERSION,
    canonical_audit_payload,
    compute_assessment_audit_hash,
    verify_assessment_audit_chain,
)


def event_payload(
    *,
    event_id: str = "event-001",
    previous_hash: str = ASSESSMENT_AUDIT_GENESIS_HASH,
):
    payload = {
        "event_id": event_id,
        "request_id": "request-001",
        "tenant_id": "tenant-alpha",
        "actor_id": "actor-001",
        "actor_roles": ["assessment:read"],
        "method": "GET",
        "route": "/api/v1/governance-assessments",
        "outcome": "allowed",
        "status_code": 200,
        "reason_code": None,
        "occurred_at": "2026-07-28T12:00:00+00:00",
        "previous_hash": previous_hash,
        "hash_version": ASSESSMENT_AUDIT_HASH_VERSION,
    }
    payload["event_hash"] = compute_assessment_audit_hash(
        **payload
    )
    return payload


def test_hash_is_deterministic():
    first = event_payload()
    second = event_payload()

    assert first["event_hash"] == second["event_hash"]


def test_hash_changes_when_event_content_changes():
    original = event_payload()
    changed = dict(original)
    changed["status_code"] = 403
    changed["event_hash"] = compute_assessment_audit_hash(
        **{
            key: value
            for key, value in changed.items()
            if key != "event_hash"
        }
    )

    assert changed["event_hash"] != original["event_hash"]


def test_actor_role_order_does_not_change_hash():
    common = {
        "event_id": "event-001",
        "request_id": "request-001",
        "tenant_id": "tenant-alpha",
        "actor_id": "actor-001",
        "method": "GET",
        "route": "/route",
        "outcome": "allowed",
        "status_code": 200,
        "reason_code": None,
        "occurred_at": "2026-07-28T12:00:00+00:00",
        "previous_hash": ASSESSMENT_AUDIT_GENESIS_HASH,
    }

    first = compute_assessment_audit_hash(
        actor_roles=("assessment:admin", "assessment:read"),
        **common,
    )
    second = compute_assessment_audit_hash(
        actor_roles=("assessment:read", "assessment:admin"),
        **common,
    )

    assert first == second


def test_canonical_payload_normalizes_method():
    payload = canonical_audit_payload(
        event_id="event-001",
        request_id="request-001",
        tenant_id="tenant-alpha",
        actor_id="actor-001",
        actor_roles=("assessment:read",),
        method="get",
        route="/route",
        outcome="allowed",
        status_code=200,
        reason_code=None,
        occurred_at="2026-07-28T12:00:00+00:00",
        previous_hash=ASSESSMENT_AUDIT_GENESIS_HASH,
    )

    assert payload["method"] == "GET"


def test_single_event_chain_is_valid():
    result = verify_assessment_audit_chain(
        [event_payload()]
    )

    assert result.valid is True
    assert result.checked_count == 1
    assert result.reason_code is None


def test_multi_event_chain_is_valid():
    first = event_payload(event_id="event-001")
    second = event_payload(
        event_id="event-002",
        previous_hash=first["event_hash"],
    )

    result = verify_assessment_audit_chain(
        [first, second]
    )

    assert result.valid is True
    assert result.checked_count == 2


def test_modified_event_fails_verification():
    event = event_payload()
    event["status_code"] = 403

    result = verify_assessment_audit_chain([event])

    assert result.valid is False
    assert result.failure_index == 0
    assert result.failure_event_id == "event-001"
    assert result.reason_code == (
        "AUDIT_EVENT_HASH_MISMATCH"
    )


def test_broken_previous_hash_fails_verification():
    first = event_payload(event_id="event-001")
    second = event_payload(
        event_id="event-002",
        previous_hash="f" * 64,
    )

    result = verify_assessment_audit_chain(
        [first, second]
    )

    assert result.valid is False
    assert result.checked_count == 1
    assert result.failure_index == 1
    assert result.reason_code == (
        "AUDIT_PREVIOUS_HASH_MISMATCH"
    )


def test_empty_chain_is_valid():
    result = verify_assessment_audit_chain([])

    assert result.valid is True
    assert result.checked_count == 0


def test_unsupported_hash_version_is_rejected():
    try:
        compute_assessment_audit_hash(
            event_id="event-001",
            request_id="request-001",
            tenant_id="tenant-alpha",
            actor_id="actor-001",
            actor_roles=("assessment:read",),
            method="GET",
            route="/route",
            outcome="allowed",
            status_code=200,
            reason_code=None,
            occurred_at="2026-07-28T12:00:00+00:00",
            previous_hash=ASSESSMENT_AUDIT_GENESIS_HASH,
            hash_version="unsupported",
        )
    except ValueError as error:
        assert "unsupported" in str(error)
    else:
        raise AssertionError(
            "unsupported hash version was accepted"
        )
