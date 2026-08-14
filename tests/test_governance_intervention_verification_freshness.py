from __future__ import annotations

from dataclasses import replace

import pytest

from backend.app.gagf.governance_intervention_verification_freshness import (
    GOVERNANCE_INTERVENTION_VERIFICATION_FRESHNESS_ID,
    GOVERNANCE_INTERVENTION_VERIFICATION_FRESHNESS_SCHEMA_VERSION,
    GOVERNANCE_INTERVENTION_VERIFICATION_FRESHNESS_VERSION,
    GovernanceInterventionVerificationFreshnessDisposition,
    GovernanceInterventionVerificationFreshnessError,
    GovernanceInterventionVerificationFreshnessEvaluator,
    GovernanceInterventionVerificationFreshnessEvidence,
    GovernanceInterventionVerificationFreshnessIntegrityError,
    GovernanceInterventionVerificationFreshnessTrigger,
)
from backend.app.gagf.governance_intervention_verification_ledger import (
    GovernanceInterventionVerificationRecordBuilder,
)
from backend.app.gagf.governance_intervention_verification_summary import (
    GovernanceInterventionVerificationSummary,
    GovernanceInterventionVerificationSummaryDisposition,
)
from backend.app.gagf.scientific_authority_guard import (
    canonical_json,
    sha256_hex,
)


def make_summary(
    *,
    tenant_id: str = "tenant-a",
    intervention_id: str = "intervention-1",
    verification_set_hash: str = "verification-set-1",
) -> GovernanceInterventionVerificationSummary:
    payload = {
        "verification_summary_id": (
            "governance-intervention-verification-summary"
        ),
        "version": "0.1.0",
        "schema_version": "1.0.0",
        "tenant_id": tenant_id,
        "contract_hash": f"contract-{intervention_id}",
        "intervention_id": intervention_id,
        "intervention_type": "POLICY_CHANGE",
        "verification_set_hash": verification_set_hash,
        "required_count": 3,
        "verified_count": 3,
        "not_verified_count": 0,
        "inconclusive_count": 0,
        "verification_disposition": "VERIFIED",
    }

    return GovernanceInterventionVerificationSummary(
        verification_summary_id=payload[
            "verification_summary_id"
        ],
        version=payload["version"],
        schema_version=payload["schema_version"],
        tenant_id=payload["tenant_id"],
        contract_hash=payload["contract_hash"],
        intervention_id=payload["intervention_id"],
        intervention_type=payload["intervention_type"],
        verification_set_hash=payload[
            "verification_set_hash"
        ],
        required_count=payload["required_count"],
        verified_count=payload["verified_count"],
        not_verified_count=payload[
            "not_verified_count"
        ],
        inconclusive_count=payload[
            "inconclusive_count"
        ],
        verification_disposition=(
            GovernanceInterventionVerificationSummaryDisposition
            .VERIFIED
        ),
        verification_summary_hash=sha256_hex(
            canonical_json(payload)
        ),
    )


def make_record(
    *,
    tenant_id: str = "tenant-a",
    intervention_id: str = "intervention-1",
):
    return GovernanceInterventionVerificationRecordBuilder.build(
        summary=make_summary(
            tenant_id=tenant_id,
            intervention_id=intervention_id,
        )
    )


def make_evidence(
    record,
    **overrides,
):
    values = {
        "tenant_id": record.tenant_id,
        "intervention_id": record.intervention_id,
        "verification_record_hash": record.record_hash,
        "baseline_policy_hash": "policy-a",
        "current_policy_hash": "policy-a",
        "baseline_source_evidence_hash": "source-a",
        "current_source_evidence_hash": "source-a",
        "baseline_requirements_hash": "requirements-a",
        "current_requirements_hash": "requirements-a",
        "baseline_contract_hash": "contract-a",
        "current_contract_hash": "contract-a",
        "verification_window_end": (
            "2026-08-14T18:00:00+00:00"
        ),
        "observed_at": (
            "2026-08-14T17:00:00+00:00"
        ),
        "required_observations_valid": True,
        "measurement_threshold_drifted": False,
    }

    values.update(overrides)

    return GovernanceInterventionVerificationFreshnessEvidence(
        **values
    )


def evaluate(record, **overrides):
    return (
        GovernanceInterventionVerificationFreshnessEvaluator
        .evaluate(
            record=record,
            evidence=make_evidence(
                record,
                **overrides,
            ),
        )
    )


def test_freshness_constants_are_stable():
    assert (
        GOVERNANCE_INTERVENTION_VERIFICATION_FRESHNESS_ID
        == "governance-intervention-verification-freshness"
    )
    assert (
        GOVERNANCE_INTERVENTION_VERIFICATION_FRESHNESS_VERSION
        == "0.1.0"
    )
    assert (
        GOVERNANCE_INTERVENTION_VERIFICATION_FRESHNESS_SCHEMA_VERSION
        == "1.0.0"
    )


def test_trigger_enum_is_exact():
    assert {
        trigger.value
        for trigger in (
            GovernanceInterventionVerificationFreshnessTrigger
        )
    } == {
        "POLICY_CHANGED",
        "SOURCE_EVIDENCE_CHANGED",
        "VERIFICATION_WINDOW_EXPIRED",
        "MEASUREMENT_THRESHOLD_DRIFT",
        "REQUIRED_OBSERVATION_INVALIDATED",
        "REQUIREMENTS_CHANGED",
        "CONTRACT_CHANGED",
    }


def test_disposition_enum_is_exact():
    assert {
        disposition.value
        for disposition in (
            GovernanceInterventionVerificationFreshnessDisposition
        )
    } == {
        "FRESH",
        "STALE",
        "REVERIFICATION_REQUIRED",
    }


def test_no_trigger_is_fresh():
    record = make_record()

    result = evaluate(record)

    assert result.freshness_disposition == "FRESH"
    assert result.proposed_lifecycle_status is None
    assert result.trigger_codes == ()


@pytest.mark.parametrize(
    ("field_name", "value", "expected_trigger"),
    (
        (
            "current_source_evidence_hash",
            "source-b",
            "SOURCE_EVIDENCE_CHANGED",
        ),
        (
            "observed_at",
            "2026-08-14T19:00:00+00:00",
            "VERIFICATION_WINDOW_EXPIRED",
        ),
        (
            "measurement_threshold_drifted",
            True,
            "MEASUREMENT_THRESHOLD_DRIFT",
        ),
    ),
)
def test_stale_class_triggers_propose_stale(
    field_name,
    value,
    expected_trigger,
):
    record = make_record()

    result = evaluate(
        record,
        **{
            field_name: value,
        },
    )

    assert result.freshness_disposition == "STALE"
    assert result.proposed_lifecycle_status == "STALE"
    assert result.trigger_codes == (
        expected_trigger,
    )


@pytest.mark.parametrize(
    ("field_name", "value", "expected_trigger"),
    (
        (
            "current_policy_hash",
            "policy-b",
            "POLICY_CHANGED",
        ),
        (
            "required_observations_valid",
            False,
            "REQUIRED_OBSERVATION_INVALIDATED",
        ),
        (
            "current_requirements_hash",
            "requirements-b",
            "REQUIREMENTS_CHANGED",
        ),
        (
            "current_contract_hash",
            "contract-b",
            "CONTRACT_CHANGED",
        ),
    ),
)
def test_reverification_class_triggers_require_reverification(
    field_name,
    value,
    expected_trigger,
):
    record = make_record()

    result = evaluate(
        record,
        **{
            field_name: value,
        },
    )

    assert (
        result.freshness_disposition
        == "REVERIFICATION_REQUIRED"
    )
    assert (
        result.proposed_lifecycle_status
        == "REVERIFICATION_REQUIRED"
    )
    assert result.trigger_codes == (
        expected_trigger,
    )


def test_reverification_trigger_has_precedence_over_stale_trigger():
    record = make_record()

    result = evaluate(
        record,
        current_policy_hash="policy-b",
        current_source_evidence_hash="source-b",
    )

    assert (
        result.freshness_disposition
        == "REVERIFICATION_REQUIRED"
    )
    assert (
        result.proposed_lifecycle_status
        == "REVERIFICATION_REQUIRED"
    )
    assert result.trigger_codes == (
        "POLICY_CHANGED",
        "SOURCE_EVIDENCE_CHANGED",
    )


def test_multiple_reverification_triggers_remain_deterministic():
    record = make_record()

    result = evaluate(
        record,
        current_policy_hash="policy-b",
        current_requirements_hash="requirements-b",
        current_contract_hash="contract-b",
        required_observations_valid=False,
    )

    assert result.trigger_codes == (
        "POLICY_CHANGED",
        "REQUIRED_OBSERVATION_INVALIDATED",
        "REQUIREMENTS_CHANGED",
        "CONTRACT_CHANGED",
    )


def test_trigger_order_is_enum_order_not_input_order():
    record = make_record()

    result = evaluate(
        record,
        current_contract_hash="contract-b",
        current_source_evidence_hash="source-b",
        current_policy_hash="policy-b",
    )

    assert result.trigger_codes == (
        "POLICY_CHANGED",
        "SOURCE_EVIDENCE_CHANGED",
        "CONTRACT_CHANGED",
    )


def test_window_equal_to_observation_time_is_not_expired():
    record = make_record()

    result = evaluate(
        record,
        verification_window_end=(
            "2026-08-14T18:00:00+00:00"
        ),
        observed_at=(
            "2026-08-14T18:00:00+00:00"
        ),
    )

    assert result.freshness_disposition == "FRESH"


def test_timezone_offsets_are_normalized_for_comparison():
    record = make_record()

    result = evaluate(
        record,
        verification_window_end=(
            "2026-08-14T18:00:00+00:00"
        ),
        observed_at=(
            "2026-08-14T14:00:00-04:00"
        ),
    )

    assert result.freshness_disposition == "FRESH"


def test_z_timestamp_is_supported():
    record = make_record()

    result = evaluate(
        record,
        verification_window_end=(
            "2026-08-14T18:00:00Z"
        ),
        observed_at=(
            "2026-08-14T17:00:00Z"
        ),
    )

    assert result.freshness_disposition == "FRESH"


def test_naive_window_timestamp_is_rejected():
    record = make_record()

    with pytest.raises(
        GovernanceInterventionVerificationFreshnessError,
        match="must include a timezone",
    ):
        evaluate(
            record,
            verification_window_end=(
                "2026-08-14T18:00:00"
            ),
        )


def test_naive_observed_timestamp_is_rejected():
    record = make_record()

    with pytest.raises(
        GovernanceInterventionVerificationFreshnessError,
        match="must include a timezone",
    ):
        evaluate(
            record,
            observed_at=(
                "2026-08-14T17:00:00"
            ),
        )


def test_invalid_timestamp_is_rejected():
    record = make_record()

    with pytest.raises(
        GovernanceInterventionVerificationFreshnessError,
        match="must be ISO-8601",
    ):
        evaluate(
            record,
            observed_at="not-a-timestamp",
        )


def test_blank_tenant_is_rejected():
    record = make_record()

    evidence = make_evidence(
        record,
        tenant_id="",
    )

    with pytest.raises(
        GovernanceInterventionVerificationFreshnessError,
        match="tenant_id is required",
    ):
        GovernanceInterventionVerificationFreshnessEvaluator.evaluate(
            record=record,
            evidence=evidence,
        )


def test_noncanonical_tenant_is_rejected():
    record = make_record()

    evidence = make_evidence(
        record,
        tenant_id=" tenant-a ",
    )

    with pytest.raises(
        GovernanceInterventionVerificationFreshnessError,
        match="must already be canonical",
    ):
        GovernanceInterventionVerificationFreshnessEvaluator.evaluate(
            record=record,
            evidence=evidence,
        )


def test_cross_tenant_evidence_is_rejected():
    record = make_record(
        tenant_id="tenant-a"
    )

    evidence = make_evidence(
        record,
        tenant_id="tenant-b",
    )

    with pytest.raises(
        GovernanceInterventionVerificationFreshnessIntegrityError,
        match="tenant does not match",
    ):
        GovernanceInterventionVerificationFreshnessEvaluator.evaluate(
            record=record,
            evidence=evidence,
        )


def test_cross_intervention_evidence_is_rejected():
    record = make_record(
        intervention_id="intervention-a"
    )

    evidence = make_evidence(
        record,
        intervention_id="intervention-b",
    )

    with pytest.raises(
        GovernanceInterventionVerificationFreshnessIntegrityError,
        match="intervention does not match",
    ):
        GovernanceInterventionVerificationFreshnessEvaluator.evaluate(
            record=record,
            evidence=evidence,
        )


def test_wrong_record_hash_is_rejected():
    record = make_record()

    evidence = make_evidence(
        record,
        verification_record_hash="wrong-record-hash",
    )

    with pytest.raises(
        GovernanceInterventionVerificationFreshnessIntegrityError,
        match="not bound",
    ):
        GovernanceInterventionVerificationFreshnessEvaluator.evaluate(
            record=record,
            evidence=evidence,
        )


@pytest.mark.parametrize(
    "field_name",
    (
        "baseline_policy_hash",
        "current_policy_hash",
        "baseline_source_evidence_hash",
        "current_source_evidence_hash",
        "baseline_requirements_hash",
        "current_requirements_hash",
        "baseline_contract_hash",
        "current_contract_hash",
    ),
)
def test_required_comparison_hashes_cannot_be_blank(
    field_name,
):
    record = make_record()

    evidence = make_evidence(
        record,
        **{
            field_name: "   ",
        },
    )

    with pytest.raises(
        GovernanceInterventionVerificationFreshnessError,
        match=f"{field_name} is required",
    ):
        GovernanceInterventionVerificationFreshnessEvaluator.evaluate(
            record=record,
            evidence=evidence,
        )


def test_tampered_verification_record_is_rejected():
    record = make_record()

    tampered = replace(
        record,
        intervention_id="tampered",
    )

    evidence = make_evidence(
        record
    )

    with pytest.raises(
        GovernanceInterventionVerificationFreshnessIntegrityError,
        match="failed deterministic verification",
    ):
        GovernanceInterventionVerificationFreshnessEvaluator.evaluate(
            record=tampered,
            evidence=evidence,
        )


def test_same_inputs_produce_same_evaluation():
    record = make_record()

    evidence = make_evidence(
        record,
        current_source_evidence_hash="source-b",
    )

    first = (
        GovernanceInterventionVerificationFreshnessEvaluator
        .evaluate(
            record=record,
            evidence=evidence,
        )
    )

    second = (
        GovernanceInterventionVerificationFreshnessEvaluator
        .evaluate(
            record=record,
            evidence=evidence,
        )
    )

    assert first == second
    assert (
        first.freshness_evaluation_hash
        == second.freshness_evaluation_hash
    )


def test_evidence_change_changes_evidence_hash():
    record = make_record()

    first = evaluate(record)

    second = evaluate(
        record,
        current_source_evidence_hash="source-b",
    )

    assert first.evidence_hash != second.evidence_hash


def test_evaluation_hash_verifies():
    record = make_record()

    result = evaluate(
        record,
        current_policy_hash="policy-b",
    )

    assert result.verify() is True


def test_evaluation_hash_detects_tampering():
    record = make_record()

    result = evaluate(record)

    tampered = replace(
        result,
        freshness_disposition="STALE",
    )

    assert result.verify() is True
    assert tampered.verify() is False


def test_freshness_evaluation_contains_no_verification_rewrite():
    record = make_record()

    result = evaluate(
        record,
        current_contract_hash="contract-b",
    )

    payload = result.to_dict()

    forbidden = {
        "verification_disposition",
        "verified_count",
        "not_verified_count",
        "inconclusive_count",
        "success",
        "failure",
        "causation",
        "causal_effect",
        "authorized",
        "rollback",
        "continue_intervention",
        "next_action",
    }

    assert forbidden.isdisjoint(payload)


def test_evaluator_has_no_lifecycle_mutation_methods():
    actual_methods = {
        name
        for name in dir(
            GovernanceInterventionVerificationFreshnessEvaluator
        )
        if not name.startswith("_")
    }

    forbidden_methods = {
        "activate",
        "mark_stale",
        "require_reverification",
        "supersede",
        "execute",
        "actuate",
        "authorize",
        "rollback",
        "reverify",
        "verify_outcome",
    }

    assert forbidden_methods.isdisjoint(
        actual_methods
    )


def test_evidence_payload_is_explicit_and_replayable():
    record = make_record()

    evidence = make_evidence(
        record
    )

    payload = evidence.payload()

    assert "observed_at" in payload
    assert "verification_window_end" in payload
    assert "current_policy_hash" in payload
    assert "current_source_evidence_hash" in payload

    assert "current_time" not in payload
    assert "now" not in payload