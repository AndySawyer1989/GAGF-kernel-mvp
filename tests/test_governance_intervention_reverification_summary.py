from __future__ import annotations

from dataclasses import replace

import pytest

from backend.app.gagf.governance_intervention_reverification_summary import (
    GOVERNANCE_INTERVENTION_REVERIFICATION_SUMMARY_ID,
    GOVERNANCE_INTERVENTION_REVERIFICATION_SUMMARY_SCHEMA_VERSION,
    GOVERNANCE_INTERVENTION_REVERIFICATION_SUMMARY_VERSION,
    GovernanceInterventionReverificationSummaryBuilder,
    GovernanceInterventionReverificationSummaryDisposition,
    GovernanceInterventionReverificationSummaryDispositionError,
    GovernanceInterventionReverificationSummaryIntegrityError,
)
from backend.app.gagf.governance_intervention_reverification_verification_set import (
    GovernanceInterventionReverificationVerificationSet,
    GovernanceInterventionReverificationVerificationSetEntry,
)
from backend.app.gagf.scientific_authority_guard import (
    canonical_json,
    sha256_hex,
)


def make_entry(
    *,
    ordinal: int,
    disposition: str,
) -> GovernanceInterventionReverificationVerificationSetEntry:
    return GovernanceInterventionReverificationVerificationSetEntry(
        ordinal=ordinal,
        legacy_requirement=f"requirement-{ordinal}",
        requirement_id=f"req-{ordinal}",
        requirement_hash=f"req-hash-{ordinal}",
        verification_hash=f"verification-hash-{ordinal}",
        verification_disposition=disposition,
    )


def make_set(
    *,
    dispositions=(
        "VERIFIED",
        "VERIFIED",
    ),
) -> GovernanceInterventionReverificationVerificationSet:
    entries = tuple(
        make_entry(
            ordinal=index,
            disposition=disposition,
        )
        for index, disposition in enumerate(dispositions)
    )

    payload = {
        "verification_set_id": (
            "governance-intervention-"
            "reverification-verification-set"
        ),
        "version": "0.1.0",
        "schema_version": "1.0.0",
        "tenant_id": "tenant-a",
        "actuation_contract_hash": "contract-hash",
        "intervention_id": "intervention-1",
        "intervention_type": "POLICY_CHANGE",
        "verification_record_hash": "record-hash",
        "request_hash": "request-hash",
        "work_order_hash": "work-order-hash",
        "attempt_id": "attempt-1",
        "attempt_execution_id": "attempt-execution-1",
        "reverification_scope": "FULL",
        "required_count": len(entries),
        "result_count": len(entries),
        "entries": [
            entry.to_dict()
            for entry in entries
        ],
    }

    return GovernanceInterventionReverificationVerificationSet(
        verification_set_id=payload[
            "verification_set_id"
        ],
        version=payload["version"],
        schema_version=payload[
            "schema_version"
        ],
        tenant_id=payload["tenant_id"],
        actuation_contract_hash=payload[
            "actuation_contract_hash"
        ],
        intervention_id=payload[
            "intervention_id"
        ],
        intervention_type=payload[
            "intervention_type"
        ],
        verification_record_hash=payload[
            "verification_record_hash"
        ],
        request_hash=payload[
            "request_hash"
        ],
        work_order_hash=payload[
            "work_order_hash"
        ],
        attempt_id=payload[
            "attempt_id"
        ],
        attempt_execution_id=payload[
            "attempt_execution_id"
        ],
        reverification_scope=payload[
            "reverification_scope"
        ],
        required_count=payload[
            "required_count"
        ],
        result_count=payload[
            "result_count"
        ],
        entries=entries,
        verification_set_hash=sha256_hex(
            canonical_json(payload)
        ),
    )


def rehash_set(
    verification_set,
):
    return replace(
        verification_set,
        verification_set_hash=sha256_hex(
            canonical_json(
                verification_set.payload()
            )
        ),
    )


def test_identity_constants_are_exact():
    assert (
        GOVERNANCE_INTERVENTION_REVERIFICATION_SUMMARY_ID
        == "governance-intervention-reverification-summary"
    )

    assert (
        GOVERNANCE_INTERVENTION_REVERIFICATION_SUMMARY_VERSION
        == "0.1.0"
    )

    assert (
        GOVERNANCE_INTERVENTION_REVERIFICATION_SUMMARY_SCHEMA_VERSION
        == "1.0.0"
    )


def test_all_verified_aggregates_to_verified():
    verification_set = make_set(
        dispositions=(
            "VERIFIED",
            "VERIFIED",
            "VERIFIED",
        )
    )

    summary = (
        GovernanceInterventionReverificationSummaryBuilder
        .build(
            verification_set=verification_set
        )
    )

    assert summary.verify()
    assert (
        summary.verification_disposition
        is GovernanceInterventionReverificationSummaryDisposition
        .VERIFIED
    )
    assert summary.verified_count == 3
    assert summary.not_verified_count == 0
    assert summary.inconclusive_count == 0


def test_any_not_verified_dominates_verified():
    verification_set = make_set(
        dispositions=(
            "VERIFIED",
            "NOT_VERIFIED",
            "VERIFIED",
        )
    )

    summary = (
        GovernanceInterventionReverificationSummaryBuilder
        .build(
            verification_set=verification_set
        )
    )

    assert (
        summary.verification_disposition
        is GovernanceInterventionReverificationSummaryDisposition
        .NOT_VERIFIED
    )
    assert summary.verified_count == 2
    assert summary.not_verified_count == 1
    assert summary.inconclusive_count == 0


def test_not_verified_dominates_inconclusive():
    verification_set = make_set(
        dispositions=(
            "INCONCLUSIVE",
            "NOT_VERIFIED",
            "VERIFIED",
        )
    )

    summary = (
        GovernanceInterventionReverificationSummaryBuilder
        .build(
            verification_set=verification_set
        )
    )

    assert (
        summary.verification_disposition
        is GovernanceInterventionReverificationSummaryDisposition
        .NOT_VERIFIED
    )
    assert summary.verified_count == 1
    assert summary.not_verified_count == 1
    assert summary.inconclusive_count == 1


def test_inconclusive_dominates_verified():
    verification_set = make_set(
        dispositions=(
            "VERIFIED",
            "INCONCLUSIVE",
            "VERIFIED",
        )
    )

    summary = (
        GovernanceInterventionReverificationSummaryBuilder
        .build(
            verification_set=verification_set
        )
    )

    assert (
        summary.verification_disposition
        is GovernanceInterventionReverificationSummaryDisposition
        .INCONCLUSIVE
    )
    assert summary.verified_count == 2
    assert summary.not_verified_count == 0
    assert summary.inconclusive_count == 1


def test_all_inconclusive_aggregates_to_inconclusive():
    verification_set = make_set(
        dispositions=(
            "INCONCLUSIVE",
            "INCONCLUSIVE",
        )
    )

    summary = (
        GovernanceInterventionReverificationSummaryBuilder
        .build(
            verification_set=verification_set
        )
    )

    assert (
        summary.verification_disposition
        is GovernanceInterventionReverificationSummaryDisposition
        .INCONCLUSIVE
    )
    assert summary.verified_count == 0
    assert summary.not_verified_count == 0
    assert summary.inconclusive_count == 2


def test_tampered_verification_set_is_rejected():
    verification_set = make_set()

    tampered = replace(
        verification_set,
        tenant_id="tenant-b",
    )

    with pytest.raises(
        GovernanceInterventionReverificationSummaryIntegrityError,
        match="failed deterministic verification",
    ):
        GovernanceInterventionReverificationSummaryBuilder.build(
            verification_set=tampered
        )


def test_zero_required_count_is_rejected():
    verification_set = make_set(
        dispositions=(
            "VERIFIED",
        )
    )

    invalid = replace(
        verification_set,
        required_count=0,
    )
    invalid = rehash_set(
        invalid
    )

    with pytest.raises(
        GovernanceInterventionReverificationSummaryIntegrityError,
        match="at least one requirement",
    ):
        GovernanceInterventionReverificationSummaryBuilder.build(
            verification_set=invalid
        )


def test_result_count_must_equal_required_count():
    verification_set = make_set(
        dispositions=(
            "VERIFIED",
            "VERIFIED",
        )
    )

    invalid = replace(
        verification_set,
        result_count=1,
    )
    invalid = rehash_set(
        invalid
    )

    with pytest.raises(
        GovernanceInterventionReverificationSummaryIntegrityError,
        match="result_count",
    ):
        GovernanceInterventionReverificationSummaryBuilder.build(
            verification_set=invalid
        )


def test_entry_count_must_equal_required_count():
    verification_set = make_set(
        dispositions=(
            "VERIFIED",
            "VERIFIED",
        )
    )

    invalid = replace(
        verification_set,
        entries=(
            verification_set.entries[0],
        ),
    )
    invalid = rehash_set(
        invalid
    )

    with pytest.raises(
        GovernanceInterventionReverificationSummaryIntegrityError,
        match="entry count",
    ):
        GovernanceInterventionReverificationSummaryBuilder.build(
            verification_set=invalid
        )


def test_unsupported_requirement_disposition_is_rejected():
    verification_set = make_set(
        dispositions=(
            "VERIFIED",
            "UNKNOWN",
        )
    )

    with pytest.raises(
        GovernanceInterventionReverificationSummaryDispositionError,
        match="unsupported requirement-level",
    ):
        GovernanceInterventionReverificationSummaryBuilder.build(
            verification_set=verification_set
        )


def test_reverification_lineage_is_preserved():
    verification_set = make_set(
        dispositions=(
            "VERIFIED",
            "INCONCLUSIVE",
        )
    )

    summary = (
        GovernanceInterventionReverificationSummaryBuilder
        .build(
            verification_set=verification_set
        )
    )

    assert summary.tenant_id == "tenant-a"
    assert (
        summary.actuation_contract_hash
        == "contract-hash"
    )
    assert summary.intervention_id == "intervention-1"
    assert summary.intervention_type == "POLICY_CHANGE"
    assert (
        summary.verification_record_hash
        == "record-hash"
    )
    assert summary.request_hash == "request-hash"
    assert (
        summary.work_order_hash
        == "work-order-hash"
    )
    assert summary.attempt_id == "attempt-1"
    assert (
        summary.attempt_execution_id
        == "attempt-execution-1"
    )
    assert summary.reverification_scope == "FULL"
    assert (
        summary.verification_set_hash
        == verification_set.verification_set_hash
    )


def test_same_input_produces_same_summary_hash():
    verification_set = make_set(
        dispositions=(
            "VERIFIED",
            "INCONCLUSIVE",
            "VERIFIED",
        )
    )

    first = (
        GovernanceInterventionReverificationSummaryBuilder
        .build(
            verification_set=verification_set
        )
    )

    second = (
        GovernanceInterventionReverificationSummaryBuilder
        .build(
            verification_set=verification_set
        )
    )

    assert (
        first.verification_summary_hash
        == second.verification_summary_hash
    )


def test_summary_hash_changes_when_set_hash_changes():
    verification_set = make_set(
        dispositions=(
            "VERIFIED",
            "VERIFIED",
        )
    )

    first = (
        GovernanceInterventionReverificationSummaryBuilder
        .build(
            verification_set=verification_set
        )
    )

    changed = replace(
        verification_set,
        request_hash="request-hash-2",
    )
    changed = rehash_set(
        changed
    )

    second = (
        GovernanceInterventionReverificationSummaryBuilder
        .build(
            verification_set=changed
        )
    )

    assert (
        first.verification_summary_hash
        != second.verification_summary_hash
    )


def test_summary_contains_no_lifecycle_or_action_authority():
    verification_set = make_set(
        dispositions=(
            "NOT_VERIFIED",
            "INCONCLUSIVE",
        )
    )

    summary = (
        GovernanceInterventionReverificationSummaryBuilder
        .build(
            verification_set=verification_set
        )
    )

    payload = summary.to_dict()

    forbidden = {
        "success",
        "failure",
        "intervention_success",
        "intervention_failure",
        "causation",
        "causal_effect",
        "attempt_completed",
        "completed_attempt",
        "lifecycle_state",
        "lifecycle_status",
        "superseded",
        "superseded_record_hash",
        "authorized",
        "future_authorization",
        "recommended_action",
        "next_action",
        "rollback",
        "continuation",
        "remediation",
        "policy_recommendation",
    }

    assert forbidden.isdisjoint(
        payload
    )