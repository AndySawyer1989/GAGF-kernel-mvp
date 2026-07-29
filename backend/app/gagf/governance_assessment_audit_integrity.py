from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Mapping, Sequence


ASSESSMENT_AUDIT_HASH_VERSION = "sha256-v1"
ASSESSMENT_AUDIT_GENESIS_HASH = (
    "0" * 64
)


@dataclass(frozen=True)
class AssessmentAuditChainVerification:
    valid: bool
    checked_count: int
    failure_index: int | None = None
    failure_event_id: str | None = None
    reason_code: str | None = None


def canonical_audit_payload(
    *,
    event_id: str,
    request_id: str,
    tenant_id: str | None,
    actor_id: str | None,
    actor_roles: Sequence[str],
    method: str,
    route: str,
    outcome: str,
    status_code: int,
    reason_code: str | None,
    occurred_at: str,
    previous_hash: str,
    hash_version: str = ASSESSMENT_AUDIT_HASH_VERSION,
) -> dict[str, Any]:
    return {
        "actor_id": actor_id,
        "actor_roles": sorted(actor_roles),
        "event_id": event_id,
        "hash_version": hash_version,
        "method": method.upper(),
        "occurred_at": occurred_at,
        "outcome": outcome,
        "previous_hash": previous_hash,
        "reason_code": reason_code,
        "request_id": request_id,
        "route": route,
        "status_code": status_code,
        "tenant_id": tenant_id,
    }


def compute_assessment_audit_hash(
    *,
    event_id: str,
    request_id: str,
    tenant_id: str | None,
    actor_id: str | None,
    actor_roles: Sequence[str],
    method: str,
    route: str,
    outcome: str,
    status_code: int,
    reason_code: str | None,
    occurred_at: str,
    previous_hash: str,
    hash_version: str = ASSESSMENT_AUDIT_HASH_VERSION,
) -> str:
    if hash_version != ASSESSMENT_AUDIT_HASH_VERSION:
        raise ValueError(
            f"unsupported assessment audit hash version: {hash_version}"
        )

    payload = canonical_audit_payload(
        event_id=event_id,
        request_id=request_id,
        tenant_id=tenant_id,
        actor_id=actor_id,
        actor_roles=actor_roles,
        method=method,
        route=route,
        outcome=outcome,
        status_code=status_code,
        reason_code=reason_code,
        occurred_at=occurred_at,
        previous_hash=previous_hash,
        hash_version=hash_version,
    )

    canonical_json = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")

    return hashlib.sha256(canonical_json).hexdigest()


def verify_assessment_audit_chain(
    events: Sequence[Mapping[str, Any]],
) -> AssessmentAuditChainVerification:
    expected_previous_hash = (
        ASSESSMENT_AUDIT_GENESIS_HASH
    )

    for index, event in enumerate(events):
        event_id = str(event["event_id"])
        stored_previous_hash = str(
            event["previous_hash"]
        )

        if stored_previous_hash != expected_previous_hash:
            return AssessmentAuditChainVerification(
                valid=False,
                checked_count=index,
                failure_index=index,
                failure_event_id=event_id,
                reason_code="AUDIT_PREVIOUS_HASH_MISMATCH",
            )

        calculated_hash = compute_assessment_audit_hash(
            event_id=event_id,
            request_id=str(event["request_id"]),
            tenant_id=event.get("tenant_id"),
            actor_id=event.get("actor_id"),
            actor_roles=tuple(event["actor_roles"]),
            method=str(event["method"]),
            route=str(event["route"]),
            outcome=str(event["outcome"]),
            status_code=int(event["status_code"]),
            reason_code=event.get("reason_code"),
            occurred_at=str(event["occurred_at"]),
            previous_hash=stored_previous_hash,
            hash_version=str(event["hash_version"]),
        )

        if calculated_hash != event["event_hash"]:
            return AssessmentAuditChainVerification(
                valid=False,
                checked_count=index,
                failure_index=index,
                failure_event_id=event_id,
                reason_code="AUDIT_EVENT_HASH_MISMATCH",
            )

        expected_previous_hash = calculated_hash

    return AssessmentAuditChainVerification(
        valid=True,
        checked_count=len(events),
    )
