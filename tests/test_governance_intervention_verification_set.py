from __future__ import annotations

from dataclasses import FrozenInstanceError, replace

import pytest

from backend.app.gagf.governance_intervention_actuation_contract import (
    GovernanceInterventionActuationContract,
)
from backend.app.gagf.governance_intervention_outcome_verification_result import (
    GovernanceInterventionOutcomeVerificationDisposition,
    GovernanceInterventionOutcomeVerificationResult,
)
from backend.app.gagf.governance_intervention_verification_requirement import (
    GovernanceInterventionVerificationOperator,
    GovernanceInterventionVerificationRequirement,
)
from backend.app.gagf.governance_intervention_verification_set import (
    GOVERNANCE_INTERVENTION_VERIFICATION_SET_ID,
    GOVERNANCE_INTERVENTION_VERIFICATION_SET_SCHEMA_VERSION,
    GOVERNANCE_INTERVENTION_VERIFICATION_SET_VERSION,
    GovernanceInterventionVerificationSetCompletenessError,
    GovernanceInterventionVerificationSetIntegrityError,
    GovernanceInterventionVerificationSetLineageError,
    GovernanceInterventionVerificationSetBuilder,
)
from backend.app.gagf.scientific_authority_guard import (
    canonical_json,
    sha256_hex,
)


LEGACY_A = "Verify approval latency."
LEGACY_B = "Verify audit evidence continuity."
LEGACY_C = "Verify escalation rate."


def make_contract(
    *,
    verification_requirements=(
        LEGACY_A,
        LEGACY_B,
        LEGACY_C,
    ),
):
    contract = GovernanceInterventionActuationContract(
        contract_id="governance-intervention-actuation-contract",
        contract_version="0.1.0",
        schema_version="1",
        tenant_id="tenant-a",
        binding_hash="binding-hash",
        authorization_receipt_hash="authorization-hash",
        execution_context_hash="context-hash",
        intervention_id="intervention-1",
        intervention_type="POLICY_CHANGE",
        requested_effect="reduce governance friction",
        effect_boundary="approval workflow only",
        preconditions=("system reachable",),
        abort_criteria=("error budget exceeded",),
        rollback_strategy="restore prior policy",
        max_attempts=3,
        timeout_seconds=30,
        verification_requirements=verification_requirements,
        contract_hash="",
    )

    payload = contract.to_dict()
    payload.pop("contract_hash")

    return replace(
        contract,
        contract_hash=sha256_hex(
            canonical_json(payload)
        ),
    )


def make_requirement(
    contract,
    *,
    legacy_requirement,
    requirement_id,
    metric_id,
):
    payload = {
        "requirement_contract_id": (
            "governance-intervention-verification-requirement"
        ),
        "version": "0.1.0",
        "schema_version": "1.0.0",
        "tenant_id": contract.tenant_id,
        "actuation_contract_hash": contract.contract_hash,
        "intervention_id": contract.intervention_id,
        "intervention_type": contract.intervention_type,
        "legacy_requirement": legacy_requirement,
        "requirement_id": requirement_id,
        "description": f"Structured rule for {legacy_requirement}",
        "metric_id": metric_id,
        "operator": "LTE",
        "target_value": 120.0,
        "unit": "seconds",
        "measurement_window_seconds": 86400,
        "minimum_record_count": 10,
    }

    return GovernanceInterventionVerificationRequirement(
        requirement_contract_id=payload["requirement_contract_id"],
        version=payload["version"],
        schema_version=payload["schema_version"],
        tenant_id=payload["tenant_id"],
        actuation_contract_hash=payload[
            "actuation_contract_hash"
        ],
        intervention_id=payload["intervention_id"],
        intervention_type=payload["intervention_type"],
        legacy_requirement=payload["legacy_requirement"],
        requirement_id=payload["requirement_id"],
        description=payload["description"],
        metric_id=payload["metric_id"],
        operator=GovernanceInterventionVerificationOperator.LTE,
        target_value=payload["target_value"],
        unit=payload["unit"],
        measurement_window_seconds=payload[
            "measurement_window_seconds"
        ],
        minimum_record_count=payload["minimum_record_count"],
        requirement_hash=sha256_hex(
            canonical_json(payload)
        ),
    )


def make_result(
    requirement,
    *,
    disposition=(
        GovernanceInterventionOutcomeVerificationDisposition.VERIFIED
    ),
    suffix="",
):
    if (
        disposition
        is GovernanceInterventionOutcomeVerificationDisposition.VERIFIED
    ):
        evaluation_disposition = "SATISFIED"
        evidence_sufficient = True
        comparison_satisfied = True
        observed_value = 95.0
    elif (
        disposition
        is GovernanceInterventionOutcomeVerificationDisposition
        .NOT_VERIFIED
    ):
        evaluation_disposition = "NOT_SATISFIED"
        evidence_sufficient = True
        comparison_satisfied = False
        observed_value = 150.0
    else:
        evaluation_disposition = "INSUFFICIENT_EVIDENCE"
        evidence_sufficient = False
        comparison_satisfied = None
        observed_value = 95.0

    payload = {
        "verification_result_id": (
            "governance-intervention-outcome-verification-result"
        ),
        "version": "0.1.0",
        "schema_version": "1.0.0",
        "tenant_id": requirement.tenant_id,
        "contract_hash": requirement.actuation_contract_hash,
        "intervention_id": requirement.intervention_id,
        "intervention_type": requirement.intervention_type,
        "requirement_id": requirement.requirement_id,
        "requirement_hash": requirement.requirement_hash,
        "measurement_hash": f"measurement-{requirement.requirement_id}{suffix}",
        "observation_hash": f"observation-{requirement.requirement_id}{suffix}",
        "execution_receipt_hash": "receipt-hash-1",
        "evaluation_hash": f"evaluation-{requirement.requirement_id}{suffix}",
        "metric_id": requirement.metric_id,
        "operator": requirement.operator.value,
        "target_value": requirement.target_value,
        "observed_value": observed_value,
        "unit": requirement.unit,
        "evidence_sufficient": evidence_sufficient,
        "comparison_satisfied": comparison_satisfied,
        "evaluation_disposition": evaluation_disposition,
        "verification_disposition": disposition.value,
    }

    return GovernanceInterventionOutcomeVerificationResult(
        verification_result_id=payload["verification_result_id"],
        version=payload["version"],
        schema_version=payload["schema_version"],
        tenant_id=payload["tenant_id"],
        contract_hash=payload["contract_hash"],
        intervention_id=payload["intervention_id"],
        intervention_type=payload["intervention_type"],
        requirement_id=payload["requirement_id"],
        requirement_hash=payload["requirement_hash"],
        measurement_hash=payload["measurement_hash"],
        observation_hash=payload["observation_hash"],
        execution_receipt_hash=payload["execution_receipt_hash"],
        evaluation_hash=payload["evaluation_hash"],
        metric_id=payload["metric_id"],
        operator=payload["operator"],
        target_value=payload["target_value"],
        observed_value=payload["observed_value"],
        unit=payload["unit"],
        evidence_sufficient=payload["evidence_sufficient"],
        comparison_satisfied=payload["comparison_satisfied"],
        evaluation_disposition=payload["evaluation_disposition"],
        verification_disposition=disposition,
        verification_hash=sha256_hex(
            canonical_json(payload)
        ),
    )


def governed_inputs():
    contract = make_contract()

    requirement_a = make_requirement(
        contract,
        legacy_requirement=LEGACY_A,
        requirement_id="req-a",
        metric_id="approval_latency_seconds",
    )

    requirement_b = make_requirement(
        contract,
        legacy_requirement=LEGACY_B,
        requirement_id="req-b",
        metric_id="audit_continuity_seconds",
    )

    requirement_c = make_requirement(
        contract,
        legacy_requirement=LEGACY_C,
        requirement_id="req-c",
        metric_id="escalation_rate_seconds",
    )

    result_a = make_result(
        requirement_a,
        disposition=(
            GovernanceInterventionOutcomeVerificationDisposition.VERIFIED
        ),
    )

    result_b = make_result(
        requirement_b,
        disposition=(
            GovernanceInterventionOutcomeVerificationDisposition
            .NOT_VERIFIED
        ),
    )

    result_c = make_result(
        requirement_c,
        disposition=(
            GovernanceInterventionOutcomeVerificationDisposition
            .INCONCLUSIVE
        ),
    )

    return (
        contract,
        (requirement_a, requirement_b, requirement_c),
        (result_a, result_b, result_c),
    )


def build_set(
    *,
    requirements=None,
    results=None,
    contract=None,
):
    default_contract, default_requirements, default_results = (
        governed_inputs()
    )

    if contract is None:
        contract = default_contract

    if requirements is None:
        requirements = default_requirements

    if results is None:
        results = default_results

    return GovernanceInterventionVerificationSetBuilder.build(
        actuation_contract=contract,
        requirements=requirements,
        verification_results=results,
    )


def test_constants_are_stable():
    assert (
        GOVERNANCE_INTERVENTION_VERIFICATION_SET_ID
        == "governance-intervention-verification-set"
    )

    assert (
        GOVERNANCE_INTERVENTION_VERIFICATION_SET_VERSION
        == "0.1.0"
    )

    assert (
        GOVERNANCE_INTERVENTION_VERIFICATION_SET_SCHEMA_VERSION
        == "1.0.0"
    )


def test_builds_complete_governed_set():
    result = build_set()

    assert result.verify() is True
    assert result.required_count == 3
    assert result.result_count == 3
    assert len(result.entries) == 3


def test_entries_follow_contract_order():
    result = build_set()

    assert [
        entry.legacy_requirement
        for entry in result.entries
    ] == [
        LEGACY_A,
        LEGACY_B,
        LEGACY_C,
    ]

    assert [
        entry.ordinal
        for entry in result.entries
    ] == [0, 1, 2]


def test_input_order_does_not_change_canonical_set():
    contract, requirements, results = governed_inputs()

    first = GovernanceInterventionVerificationSetBuilder.build(
        actuation_contract=contract,
        requirements=requirements,
        verification_results=results,
    )

    second = GovernanceInterventionVerificationSetBuilder.build(
        actuation_contract=contract,
        requirements=(
            requirements[2],
            requirements[0],
            requirements[1],
        ),
        verification_results=(
            results[1],
            results[2],
            results[0],
        ),
    )

    assert first == second
    assert first.verification_set_hash == second.verification_set_hash


def test_preserves_individual_verification_dispositions_without_aggregation():
    result = build_set()

    assert [
        entry.verification_disposition
        for entry in result.entries
    ] == [
        "VERIFIED",
        "NOT_VERIFIED",
        "INCONCLUSIVE",
    ]

    serialized = result.to_dict()

    forbidden_fields = {
        "overall_verification",
        "overall_disposition",
        "intervention_verification",
        "intervention_success",
        "success",
        "failed",
        "rollback",
        "next_action",
        "authorized",
    }

    assert forbidden_fields.isdisjoint(serialized)


def test_set_is_deterministic():
    first = build_set()
    second = build_set()

    assert first == second
    assert first.verification_set_hash == second.verification_set_hash


def test_set_is_frozen():
    result = build_set()

    with pytest.raises(FrozenInstanceError):
        result.required_count = 99


def test_tampered_set_fails_verification():
    result = build_set()

    tampered = replace(
        result,
        result_count=99,
    )

    assert tampered.verify() is False


def test_rejects_missing_structured_requirement():
    contract, requirements, results = governed_inputs()

    with pytest.raises(
        GovernanceInterventionVerificationSetCompletenessError
    ):
        GovernanceInterventionVerificationSetBuilder.build(
            actuation_contract=contract,
            requirements=requirements[:2],
            verification_results=results,
        )


def test_rejects_missing_verification_result():
    contract, requirements, results = governed_inputs()

    with pytest.raises(
        GovernanceInterventionVerificationSetCompletenessError
    ):
        GovernanceInterventionVerificationSetBuilder.build(
            actuation_contract=contract,
            requirements=requirements,
            verification_results=results[:2],
        )


def test_rejects_duplicate_contract_obligation():
    contract = make_contract(
        verification_requirements=(
            LEGACY_A,
            LEGACY_A,
            LEGACY_C,
        ),
    )

    requirement_a = make_requirement(
        contract,
        legacy_requirement=LEGACY_A,
        requirement_id="req-a",
        metric_id="approval_latency_seconds",
    )

    requirement_c = make_requirement(
        contract,
        legacy_requirement=LEGACY_C,
        requirement_id="req-c",
        metric_id="escalation_rate_seconds",
    )

    with pytest.raises(
        GovernanceInterventionVerificationSetCompletenessError
    ):
        GovernanceInterventionVerificationSetBuilder.build(
            actuation_contract=contract,
            requirements=(
                requirement_a,
                requirement_c,
                requirement_c,
            ),
            verification_results=(
                make_result(requirement_a),
                make_result(requirement_c),
                make_result(
                    requirement_c,
                    suffix="-duplicate",
                ),
            ),
        )


def test_rejects_two_structured_requirements_for_same_legacy_obligation():
    contract, requirements, results = governed_inputs()

    duplicate = make_requirement(
        contract,
        legacy_requirement=LEGACY_A,
        requirement_id="req-a-2",
        metric_id="approval_latency_seconds_2",
    )

    with pytest.raises(
        GovernanceInterventionVerificationSetCompletenessError
    ):
        GovernanceInterventionVerificationSetBuilder.build(
            actuation_contract=contract,
            requirements=(
                requirements[0],
                duplicate,
                requirements[2],
            ),
            verification_results=results,
        )


def test_rejects_duplicate_requirement_id():
    contract, requirements, results = governed_inputs()

    duplicate_id = replace(
        requirements[1],
        requirement_id=requirements[0].requirement_id,
    )

    duplicate_id = replace(
        duplicate_id,
        requirement_hash=sha256_hex(
            canonical_json(
                duplicate_id.payload()
            )
        ),
    )

    with pytest.raises(
        GovernanceInterventionVerificationSetCompletenessError
    ):
        GovernanceInterventionVerificationSetBuilder.build(
            actuation_contract=contract,
            requirements=(
                requirements[0],
                duplicate_id,
                requirements[2],
            ),
            verification_results=results,
        )


def test_rejects_duplicate_requirement_hash():
    contract, requirements, results = governed_inputs()

    duplicate_hash = replace(
        requirements[1],
        requirement_hash=requirements[0].requirement_hash,
    )

    assert duplicate_hash.verify() is False

    with pytest.raises(
        GovernanceInterventionVerificationSetIntegrityError
    ):
        GovernanceInterventionVerificationSetBuilder.build(
            actuation_contract=contract,
            requirements=(
                requirements[0],
                duplicate_hash,
                requirements[2],
            ),
            verification_results=results,
        )


def test_rejects_duplicate_result_requirement_id():
    contract, requirements, results = governed_inputs()

    duplicate = replace(
        results[1],
        requirement_id=results[0].requirement_id,
    )

    duplicate = replace(
        duplicate,
        verification_hash=sha256_hex(
            canonical_json(
                duplicate.payload()
            )
        ),
    )

    with pytest.raises(
        GovernanceInterventionVerificationSetCompletenessError
    ):
        GovernanceInterventionVerificationSetBuilder.build(
            actuation_contract=contract,
            requirements=requirements,
            verification_results=(
                results[0],
                duplicate,
                results[2],
            ),
        )


def test_rejects_duplicate_result_requirement_hash():
    contract, requirements, results = governed_inputs()

    duplicate = replace(
        results[1],
        requirement_hash=results[0].requirement_hash,
    )

    duplicate = replace(
        duplicate,
        verification_hash=sha256_hex(
            canonical_json(
                duplicate.payload()
            )
        ),
    )

    with pytest.raises(
        GovernanceInterventionVerificationSetCompletenessError
    ):
        GovernanceInterventionVerificationSetBuilder.build(
            actuation_contract=contract,
            requirements=requirements,
            verification_results=(
                results[0],
                duplicate,
                results[2],
            ),
        )


def test_rejects_duplicate_verification_hash():
    contract, requirements, results = governed_inputs()

    duplicate = replace(
        results[1],
        verification_hash=results[0].verification_hash,
    )

    assert duplicate.verify() is False

    with pytest.raises(
        GovernanceInterventionVerificationSetIntegrityError
    ):
        GovernanceInterventionVerificationSetBuilder.build(
            actuation_contract=contract,
            requirements=requirements,
            verification_results=(
                results[0],
                duplicate,
                results[2],
            ),
        )


def test_rejects_tampered_requirement():
    contract, requirements, results = governed_inputs()

    tampered = replace(
        requirements[0],
        metric_id="tampered_metric",
    )

    assert tampered.verify() is False

    with pytest.raises(
        GovernanceInterventionVerificationSetIntegrityError
    ):
        GovernanceInterventionVerificationSetBuilder.build(
            actuation_contract=contract,
            requirements=(
                tampered,
                requirements[1],
                requirements[2],
            ),
            verification_results=results,
        )


def test_rejects_tampered_verification_result():
    contract, requirements, results = governed_inputs()

    tampered = replace(
        results[0],
        verification_disposition=(
            GovernanceInterventionOutcomeVerificationDisposition
            .NOT_VERIFIED
        ),
    )

    assert tampered.verify() is False

    with pytest.raises(
        GovernanceInterventionVerificationSetIntegrityError
    ):
        GovernanceInterventionVerificationSetBuilder.build(
            actuation_contract=contract,
            requirements=requirements,
            verification_results=(
                tampered,
                results[1],
                results[2],
            ),
        )


@pytest.mark.parametrize(
    ("field_name", "bad_value"),
    (
        ("tenant_id", "tenant-b"),
        ("actuation_contract_hash", "wrong-contract"),
        ("intervention_id", "wrong-intervention"),
        ("intervention_type", "WRONG_TYPE"),
    ),
)
def test_rejects_rehashed_requirement_lineage_mismatch(
    field_name,
    bad_value,
):
    contract, requirements, results = governed_inputs()

    mismatched = replace(
        requirements[0],
        **{
            field_name: bad_value,
        },
    )

    mismatched = replace(
        mismatched,
        requirement_hash=sha256_hex(
            canonical_json(
                mismatched.payload()
            )
        ),
    )

    assert mismatched.verify() is True

    with pytest.raises(
        GovernanceInterventionVerificationSetLineageError
    ):
        GovernanceInterventionVerificationSetBuilder.build(
            actuation_contract=contract,
            requirements=(
                mismatched,
                requirements[1],
                requirements[2],
            ),
            verification_results=results,
        )


@pytest.mark.parametrize(
    ("field_name", "bad_value"),
    (
        ("tenant_id", "tenant-b"),
        ("contract_hash", "wrong-contract"),
        ("intervention_id", "wrong-intervention"),
        ("intervention_type", "WRONG_TYPE"),
    ),
)
def test_rejects_rehashed_result_lineage_mismatch(
    field_name,
    bad_value,
):
    contract, requirements, results = governed_inputs()

    mismatched = replace(
        results[0],
        **{
            field_name: bad_value,
        },
    )

    mismatched = replace(
        mismatched,
        verification_hash=sha256_hex(
            canonical_json(
                mismatched.payload()
            )
        ),
    )

    assert mismatched.verify() is True

    with pytest.raises(
        GovernanceInterventionVerificationSetLineageError
    ):
        GovernanceInterventionVerificationSetBuilder.build(
            actuation_contract=contract,
            requirements=requirements,
            verification_results=(
                mismatched,
                results[1],
                results[2],
            ),
        )


def test_rejects_result_bound_to_wrong_structured_requirement():
    contract, requirements, results = governed_inputs()

    wrong = replace(
        results[0],
        requirement_id=requirements[1].requirement_id,
        requirement_hash=requirements[1].requirement_hash,
    )

    wrong = replace(
        wrong,
        verification_hash=sha256_hex(
            canonical_json(
                wrong.payload()
            )
        ),
    )

    assert wrong.verify() is True

    with pytest.raises(
        GovernanceInterventionVerificationSetCompletenessError
    ):
        GovernanceInterventionVerificationSetBuilder.build(
            actuation_contract=contract,
            requirements=requirements,
            verification_results=(
                wrong,
                results[1],
                results[2],
            ),
        )


def test_serialization_preserves_complete_ordered_entries():
    result = build_set()

    serialized = result.to_dict()

    assert serialized["required_count"] == 3
    assert serialized["result_count"] == 3

    assert [
        entry["legacy_requirement"]
        for entry in serialized["entries"]
    ] == [
        LEGACY_A,
        LEGACY_B,
        LEGACY_C,
    ]

    assert (
        serialized["verification_set_hash"]
        == result.verification_set_hash
    )


def test_builder_exposes_no_summary_or_action_methods():
    forbidden_methods = (
        "summarize",
        "aggregate",
        "determine_overall_verification",
        "determine_success",
        "determine_failure",
        "authorize",
        "approve",
        "rollback",
        "execute",
        "dispatch",
        "recommend_action",
    )

    for method_name in forbidden_methods:
        assert not hasattr(
            GovernanceInterventionVerificationSetBuilder,
            method_name,
        )