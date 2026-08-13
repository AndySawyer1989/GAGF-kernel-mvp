from __future__ import annotations

from dataclasses import FrozenInstanceError, replace

import pytest

from backend.app.gagf.governance_intervention_verification_set import (
    GovernanceInterventionVerificationSet,
    GovernanceInterventionVerificationSetEntry,
)
from backend.app.gagf.governance_intervention_verification_summary import (
    GOVERNANCE_INTERVENTION_VERIFICATION_SUMMARY_ID,
    GOVERNANCE_INTERVENTION_VERIFICATION_SUMMARY_SCHEMA_VERSION,
    GOVERNANCE_INTERVENTION_VERIFICATION_SUMMARY_VERSION,
    GovernanceInterventionVerificationSummaryDisposition,
    GovernanceInterventionVerificationSummaryDispositionError,
    GovernanceInterventionVerificationSummaryIntegrityError,
    GovernanceInterventionVerificationSummaryBuilder,
)
from backend.app.gagf.scientific_authority_guard import (
    canonical_json,
    sha256_hex,
)


def make_entry(
    *,
    ordinal: int,
    requirement_id: str,
    disposition: str,
):
    return GovernanceInterventionVerificationSetEntry(
        ordinal=ordinal,
        legacy_requirement=f"Requirement {ordinal}",
        requirement_id=requirement_id,
        requirement_hash=f"requirement-hash-{requirement_id}",
        verification_hash=f"verification-hash-{requirement_id}",
        verification_disposition=disposition,
    )


def make_set(
    dispositions=("VERIFIED", "VERIFIED", "VERIFIED"),
):
    entries = tuple(
        make_entry(
            ordinal=index,
            requirement_id=f"req-{index}",
            disposition=disposition,
        )
        for index, disposition in enumerate(dispositions)
    )

    payload = {
        "verification_set_id": (
            "governance-intervention-verification-set"
        ),
        "version": "0.1.0",
        "schema_version": "1.0.0",
        "tenant_id": "tenant-a",
        "contract_hash": "contract-hash-1",
        "intervention_id": "intervention-1",
        "intervention_type": "POLICY_CHANGE",
        "required_count": len(entries),
        "result_count": len(entries),
        "entries": [
            entry.to_dict()
            for entry in entries
        ],
    }

    return GovernanceInterventionVerificationSet(
        verification_set_id=payload["verification_set_id"],
        version=payload["version"],
        schema_version=payload["schema_version"],
        tenant_id=payload["tenant_id"],
        contract_hash=payload["contract_hash"],
        intervention_id=payload["intervention_id"],
        intervention_type=payload["intervention_type"],
        required_count=payload["required_count"],
        result_count=payload["result_count"],
        entries=entries,
        verification_set_hash=sha256_hex(
            canonical_json(payload)
        ),
    )


def build_summary(
    dispositions=("VERIFIED", "VERIFIED", "VERIFIED"),
):
    verification_set = make_set(dispositions)

    summary = GovernanceInterventionVerificationSummaryBuilder.build(
        verification_set=verification_set
    )

    return verification_set, summary


def test_constants_are_stable():
    assert (
        GOVERNANCE_INTERVENTION_VERIFICATION_SUMMARY_ID
        == "governance-intervention-verification-summary"
    )

    assert (
        GOVERNANCE_INTERVENTION_VERIFICATION_SUMMARY_VERSION
        == "0.1.0"
    )

    assert (
        GOVERNANCE_INTERVENTION_VERIFICATION_SUMMARY_SCHEMA_VERSION
        == "1.0.0"
    )


def test_all_verified_maps_to_verified():
    _, summary = build_summary(
        ("VERIFIED", "VERIFIED", "VERIFIED")
    )

    assert summary.verified_count == 3
    assert summary.not_verified_count == 0
    assert summary.inconclusive_count == 0

    assert (
        summary.verification_disposition
        is GovernanceInterventionVerificationSummaryDisposition.VERIFIED
    )


def test_any_not_verified_dominates():
    _, summary = build_summary(
        ("VERIFIED", "NOT_VERIFIED", "VERIFIED")
    )

    assert (
        summary.verification_disposition
        is GovernanceInterventionVerificationSummaryDisposition
        .NOT_VERIFIED
    )


def test_not_verified_dominates_inconclusive():
    _, summary = build_summary(
        ("INCONCLUSIVE", "NOT_VERIFIED", "VERIFIED")
    )

    assert (
        summary.verification_disposition
        is GovernanceInterventionVerificationSummaryDisposition
        .NOT_VERIFIED
    )


def test_inconclusive_dominates_verified():
    _, summary = build_summary(
        ("VERIFIED", "INCONCLUSIVE", "VERIFIED")
    )

    assert (
        summary.verification_disposition
        is GovernanceInterventionVerificationSummaryDisposition
        .INCONCLUSIVE
    )


@pytest.mark.parametrize(
    ("dispositions", "expected"),
    (
        (
            ("VERIFIED",),
            GovernanceInterventionVerificationSummaryDisposition.VERIFIED,
        ),
        (
            ("NOT_VERIFIED",),
            GovernanceInterventionVerificationSummaryDisposition
            .NOT_VERIFIED,
        ),
        (
            ("INCONCLUSIVE",),
            GovernanceInterventionVerificationSummaryDisposition
            .INCONCLUSIVE,
        ),
        (
            ("VERIFIED", "VERIFIED"),
            GovernanceInterventionVerificationSummaryDisposition.VERIFIED,
        ),
        (
            ("VERIFIED", "INCONCLUSIVE"),
            GovernanceInterventionVerificationSummaryDisposition
            .INCONCLUSIVE,
        ),
        (
            ("VERIFIED", "NOT_VERIFIED"),
            GovernanceInterventionVerificationSummaryDisposition
            .NOT_VERIFIED,
        ),
        (
            ("INCONCLUSIVE", "NOT_VERIFIED"),
            GovernanceInterventionVerificationSummaryDisposition
            .NOT_VERIFIED,
        ),
    ),
)
def test_aggregation_precedence_is_exact(
    dispositions,
    expected,
):
    _, summary = build_summary(dispositions)

    assert summary.verification_disposition is expected


def test_counts_are_preserved():
    _, summary = build_summary(
        (
            "VERIFIED",
            "VERIFIED",
            "NOT_VERIFIED",
            "INCONCLUSIVE",
        )
    )

    assert summary.required_count == 4
    assert summary.verified_count == 2
    assert summary.not_verified_count == 1
    assert summary.inconclusive_count == 1


def test_summary_binds_verification_set_lineage():
    verification_set, summary = build_summary()

    assert summary.tenant_id == verification_set.tenant_id
    assert summary.contract_hash == verification_set.contract_hash

    assert (
        summary.intervention_id
        == verification_set.intervention_id
    )

    assert (
        summary.intervention_type
        == verification_set.intervention_type
    )

    assert (
        summary.verification_set_hash
        == verification_set.verification_set_hash
    )


def test_summary_is_deterministic():
    first = build_summary()[-1]
    second = build_summary()[-1]

    assert first == second
    assert (
        first.verification_summary_hash
        == second.verification_summary_hash
    )


def test_summary_is_frozen():
    summary = build_summary()[-1]

    with pytest.raises(FrozenInstanceError):
        summary.verified_count = 999


def test_tampered_summary_fails_verification():
    summary = build_summary()[-1]

    tampered = replace(
        summary,
        verified_count=999,
    )

    assert tampered.verify() is False


def test_rejects_tampered_verification_set():
    verification_set = make_set()

    tampered = replace(
        verification_set,
        required_count=999,
    )

    assert tampered.verify() is False

    with pytest.raises(
        GovernanceInterventionVerificationSummaryIntegrityError
    ):
        GovernanceInterventionVerificationSummaryBuilder.build(
            verification_set=tampered
        )


def test_rejects_zero_requirement_set():
    entries = ()

    payload = {
        "verification_set_id": (
            "governance-intervention-verification-set"
        ),
        "version": "0.1.0",
        "schema_version": "1.0.0",
        "tenant_id": "tenant-a",
        "contract_hash": "contract-hash-1",
        "intervention_id": "intervention-1",
        "intervention_type": "POLICY_CHANGE",
        "required_count": 0,
        "result_count": 0,
        "entries": [],
    }

    verification_set = GovernanceInterventionVerificationSet(
        verification_set_id=payload["verification_set_id"],
        version=payload["version"],
        schema_version=payload["schema_version"],
        tenant_id=payload["tenant_id"],
        contract_hash=payload["contract_hash"],
        intervention_id=payload["intervention_id"],
        intervention_type=payload["intervention_type"],
        required_count=0,
        result_count=0,
        entries=entries,
        verification_set_hash=sha256_hex(
            canonical_json(payload)
        ),
    )

    assert verification_set.verify() is True

    with pytest.raises(
        GovernanceInterventionVerificationSummaryIntegrityError
    ):
        GovernanceInterventionVerificationSummaryBuilder.build(
            verification_set=verification_set
        )


def test_rejects_result_count_mismatch():
    verification_set = make_set()

    mismatched = replace(
        verification_set,
        result_count=2,
    )

    mismatched = replace(
        mismatched,
        verification_set_hash=sha256_hex(
            canonical_json(
                mismatched.payload()
            )
        ),
    )

    assert mismatched.verify() is True

    with pytest.raises(
        GovernanceInterventionVerificationSummaryIntegrityError
    ):
        GovernanceInterventionVerificationSummaryBuilder.build(
            verification_set=mismatched
        )


def test_rejects_entry_count_mismatch():
    verification_set = make_set()

    mismatched = replace(
        verification_set,
        entries=verification_set.entries[:2],
    )

    mismatched = replace(
        mismatched,
        verification_set_hash=sha256_hex(
            canonical_json(
                mismatched.payload()
            )
        ),
    )

    assert mismatched.verify() is True

    with pytest.raises(
        GovernanceInterventionVerificationSummaryIntegrityError
    ):
        GovernanceInterventionVerificationSummaryBuilder.build(
            verification_set=mismatched
        )


def test_rejects_unknown_requirement_disposition():
    verification_set = make_set()

    bad_entry = replace(
        verification_set.entries[0],
        verification_disposition="UNKNOWN",
    )

    mismatched = replace(
        verification_set,
        entries=(
            bad_entry,
            verification_set.entries[1],
            verification_set.entries[2],
        ),
    )

    mismatched = replace(
        mismatched,
        verification_set_hash=sha256_hex(
            canonical_json(
                mismatched.payload()
            )
        ),
    )

    assert mismatched.verify() is True

    with pytest.raises(
        GovernanceInterventionVerificationSummaryDispositionError
    ):
        GovernanceInterventionVerificationSummaryBuilder.build(
            verification_set=mismatched
        )


def test_serialization_contains_summary_hash():
    summary = build_summary()[-1]

    serialized = summary.to_dict()

    assert serialized["verification_disposition"] == "VERIFIED"

    assert (
        serialized["verification_summary_hash"]
        == summary.verification_summary_hash
    )


def test_summary_contains_no_causal_or_future_action_fields():
    summary = build_summary()[-1]

    serialized = summary.to_dict()

    forbidden_fields = {
        "success",
        "failed",
        "intervention_success",
        "intervention_failure",
        "caused_by_intervention",
        "causal_effect",
        "causal_attribution",
        "rollback",
        "rollback_required",
        "continue_intervention",
        "continue_policy",
        "authorize",
        "authorized",
        "authorization",
        "next_action",
        "recommended_action",
        "policy_action",
        "future_action",
    }

    assert forbidden_fields.isdisjoint(serialized)


def test_verified_summary_means_complete_obligation_verification_only():
    summary = build_summary()[-1]

    serialized = summary.to_dict()

    assert serialized["verification_disposition"] == "VERIFIED"
    assert serialized["verified_count"] == 3
    assert serialized["not_verified_count"] == 0
    assert serialized["inconclusive_count"] == 0

    assert "intervention_success" not in serialized
    assert "caused_by_intervention" not in serialized
    assert "next_action" not in serialized


def test_builder_exposes_no_causal_execution_or_policy_methods():
    forbidden_methods = (
        "execute",
        "dispatch",
        "actuate",
        "authorize",
        "approve",
        "rollback",
        "continue_intervention",
        "determine_success",
        "determine_failure",
        "attribute_causation",
        "estimate_causal_effect",
        "recommend_action",
    )

    for method_name in forbidden_methods:
        assert not hasattr(
            GovernanceInterventionVerificationSummaryBuilder,
            method_name,
        )