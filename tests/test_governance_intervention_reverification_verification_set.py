from __future__ import annotations

from dataclasses import replace

import pytest

from backend.app.gagf.governance_intervention_actuation_contract import (
    GovernanceInterventionActuationContract,
)
from backend.app.gagf.governance_intervention_reverification_verification_result import (
    GovernanceInterventionReverificationVerificationDisposition,
    GovernanceInterventionReverificationVerificationResult,
)
from backend.app.gagf.governance_intervention_reverification_verification_set import (
    GOVERNANCE_INTERVENTION_REVERIFICATION_VERIFICATION_SET_ID,
    GOVERNANCE_INTERVENTION_REVERIFICATION_VERIFICATION_SET_SCHEMA_VERSION,
    GOVERNANCE_INTERVENTION_REVERIFICATION_VERIFICATION_SET_VERSION,
    GovernanceInterventionReverificationVerificationSetBuilder,
    GovernanceInterventionReverificationVerificationSetCompletenessError,
    GovernanceInterventionReverificationVerificationSetIntegrityError,
    GovernanceInterventionReverificationVerificationSetLineageError,
)
from backend.app.gagf.governance_intervention_verification_requirement import (
    GovernanceInterventionVerificationOperator,
    GovernanceInterventionVerificationRequirement,
)
from backend.app.gagf.scientific_authority_guard import (
    canonical_json,
    sha256_hex,
)


def make_contract(
    *,
    verification_requirements=(
        "latency must remain bounded",
        "error rate must remain bounded",
    ),
) -> GovernanceInterventionActuationContract:
    contract = GovernanceInterventionActuationContract(
        contract_id=(
            "governance-intervention-actuation-contract"
        ),
        contract_version="0.1.0",
        schema_version="1",
        tenant_id="tenant-a",
        binding_hash="binding-hash",
        authorization_receipt_hash="authorization-hash",
        execution_context_hash="context-hash",
        intervention_id="intervention-1",
        intervention_type="policy-update",
        requested_effect="reduce governance friction",
        effect_boundary="service-a",
        preconditions=(
            "system reachable",
        ),
        abort_criteria=(
            "error budget exceeded",
        ),
        rollback_strategy="restore prior policy",
        max_attempts=3,
        timeout_seconds=300,
        verification_requirements=tuple(
            verification_requirements
        ),
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
    *,
    contract,
    legacy_requirement,
    requirement_id,
    metric_id,
) -> GovernanceInterventionVerificationRequirement:
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
        "description": legacy_requirement,
        "metric_id": metric_id,
        "operator": (
            GovernanceInterventionVerificationOperator.LTE.value
        ),
        "target_value": 100.0,
        "unit": "ms",
        "measurement_window_seconds": 300,
        "minimum_record_count": 10,
    }

    return GovernanceInterventionVerificationRequirement(
        requirement_contract_id=payload[
            "requirement_contract_id"
        ],
        version=payload["version"],
        schema_version=payload["schema_version"],
        tenant_id=payload["tenant_id"],
        actuation_contract_hash=payload[
            "actuation_contract_hash"
        ],
        intervention_id=payload["intervention_id"],
        intervention_type=payload[
            "intervention_type"
        ],
        legacy_requirement=payload[
            "legacy_requirement"
        ],
        requirement_id=payload["requirement_id"],
        description=payload["description"],
        metric_id=payload["metric_id"],
        operator=GovernanceInterventionVerificationOperator(
            payload["operator"]
        ),
        target_value=payload["target_value"],
        unit=payload["unit"],
        measurement_window_seconds=payload[
            "measurement_window_seconds"
        ],
        minimum_record_count=payload[
            "minimum_record_count"
        ],
        requirement_hash=sha256_hex(
            canonical_json(payload)
        ),
    )


def make_result(
    *,
    requirement,
    verification_disposition=(
        GovernanceInterventionReverificationVerificationDisposition
        .VERIFIED
    ),
    verification_record_hash="record-1",
    request_hash="request-1",
    work_order_hash="work-order-1",
    attempt_id="attempt-1",
    attempt_execution_id="attempt-exec-1",
    reverification_scope="FULL",
) -> GovernanceInterventionReverificationVerificationResult:
    evaluation_disposition = "SATISFIED"
    comparison_satisfied = True
    evidence_sufficient = True

    if (
        verification_disposition
        is GovernanceInterventionReverificationVerificationDisposition
        .NOT_VERIFIED
    ):
        evaluation_disposition = "NOT_SATISFIED"
        comparison_satisfied = False

    if (
        verification_disposition
        is GovernanceInterventionReverificationVerificationDisposition
        .INCONCLUSIVE
    ):
        evaluation_disposition = "INSUFFICIENT_EVIDENCE"
        comparison_satisfied = None
        evidence_sufficient = False

    payload = {
        "verification_result_id": (
            "governance-intervention-"
            "reverification-verification-result"
        ),
        "version": "0.1.0",
        "schema_version": "1.0.0",
        "tenant_id": requirement.tenant_id,
        "intervention_id": requirement.intervention_id,
        "verification_record_hash": (
            verification_record_hash
        ),
        "request_hash": request_hash,
        "work_order_hash": work_order_hash,
        "attempt_id": attempt_id,
        "attempt_execution_id": (
            attempt_execution_id
        ),
        "reverification_scope": reverification_scope,
        "evidence_hash": (
            f"evidence-{requirement.requirement_id}"
        ),
        "measurement_hash": (
            f"measurement-{requirement.requirement_id}"
        ),
        "evaluation_hash": (
            f"evaluation-{requirement.requirement_id}"
        ),
        "actuation_contract_hash": (
            requirement.actuation_contract_hash
        ),
        "intervention_type": (
            requirement.intervention_type
        ),
        "requirement_id": requirement.requirement_id,
        "requirement_hash": requirement.requirement_hash,
        "metric_id": requirement.metric_id,
        "operator": requirement.operator.value,
        "target_value": requirement.target_value,
        "observed_value": 90.0,
        "unit": requirement.unit,
        "evidence_sufficient": evidence_sufficient,
        "comparison_satisfied": comparison_satisfied,
        "evaluation_disposition": (
            evaluation_disposition
        ),
        "verification_disposition": (
            verification_disposition.value
        ),
    }

    return GovernanceInterventionReverificationVerificationResult(
        verification_result_id=payload[
            "verification_result_id"
        ],
        version=payload["version"],
        schema_version=payload["schema_version"],
        tenant_id=payload["tenant_id"],
        intervention_id=payload["intervention_id"],
        verification_record_hash=payload[
            "verification_record_hash"
        ],
        request_hash=payload["request_hash"],
        work_order_hash=payload["work_order_hash"],
        attempt_id=payload["attempt_id"],
        attempt_execution_id=payload[
            "attempt_execution_id"
        ],
        reverification_scope=payload[
            "reverification_scope"
        ],
        evidence_hash=payload["evidence_hash"],
        measurement_hash=payload[
            "measurement_hash"
        ],
        evaluation_hash=payload["evaluation_hash"],
        actuation_contract_hash=payload[
            "actuation_contract_hash"
        ],
        intervention_type=payload[
            "intervention_type"
        ],
        requirement_id=payload["requirement_id"],
        requirement_hash=payload[
            "requirement_hash"
        ],
        metric_id=payload["metric_id"],
        operator=payload["operator"],
        target_value=payload["target_value"],
        observed_value=payload["observed_value"],
        unit=payload["unit"],
        evidence_sufficient=payload[
            "evidence_sufficient"
        ],
        comparison_satisfied=payload[
            "comparison_satisfied"
        ],
        evaluation_disposition=payload[
            "evaluation_disposition"
        ],
        verification_disposition=(
            verification_disposition
        ),
        verification_hash=sha256_hex(
            canonical_json(payload)
        ),
    )


def build_fixture():
    contract = make_contract()

    first_requirement = make_requirement(
        contract=contract,
        legacy_requirement=(
            "latency must remain bounded"
        ),
        requirement_id="requirement-1",
        metric_id="latency",
    )

    second_requirement = make_requirement(
        contract=contract,
        legacy_requirement=(
            "error rate must remain bounded"
        ),
        requirement_id="requirement-2",
        metric_id="error-rate",
    )

    first_result = make_result(
        requirement=first_requirement,
    )

    second_result = make_result(
        requirement=second_requirement,
        verification_disposition=(
            GovernanceInterventionReverificationVerificationDisposition
            .NOT_VERIFIED
        ),
    )

    return (
        contract,
        first_requirement,
        second_requirement,
        first_result,
        second_result,
    )


def build_set(
    *,
    contract,
    requirements,
    results,
):
    return (
        GovernanceInterventionReverificationVerificationSetBuilder
        .build(
            actuation_contract=contract,
            requirements=tuple(requirements),
            verification_results=tuple(results),
        )
    )


def rehash_contract(contract):
    return replace(
        contract,
        contract_hash=sha256_hex(
            canonical_json(contract.payload())
        ),
    )


def rehash_requirement(requirement):
    return replace(
        requirement,
        requirement_hash=sha256_hex(
            canonical_json(requirement.payload())
        ),
    )


def rehash_result(result):
    return replace(
        result,
        verification_hash=sha256_hex(
            canonical_json(result.payload())
        ),
    )


def test_set_identity_constants_are_exact():
    assert (
        GOVERNANCE_INTERVENTION_REVERIFICATION_VERIFICATION_SET_ID
        == (
            "governance-intervention-"
            "reverification-verification-set"
        )
    )

    assert (
        GOVERNANCE_INTERVENTION_REVERIFICATION_VERIFICATION_SET_VERSION
        == "0.1.0"
    )

    assert (
        GOVERNANCE_INTERVENTION_REVERIFICATION_VERIFICATION_SET_SCHEMA_VERSION
        == "1.0.0"
    )


def test_complete_set_builds_and_verifies():
    (
        contract,
        first_requirement,
        second_requirement,
        first_result,
        second_result,
    ) = build_fixture()

    result_set = build_set(
        contract=contract,
        requirements=(
            first_requirement,
            second_requirement,
        ),
        results=(
            first_result,
            second_result,
        ),
    )

    assert result_set.verify()
    assert result_set.required_count == 2
    assert result_set.result_count == 2


def test_input_order_does_not_control_entry_order():
    (
        contract,
        first_requirement,
        second_requirement,
        first_result,
        second_result,
    ) = build_fixture()

    result_set = build_set(
        contract=contract,
        requirements=(
            second_requirement,
            first_requirement,
        ),
        results=(
            second_result,
            first_result,
        ),
    )

    assert [
        entry.legacy_requirement
        for entry in result_set.entries
    ] == [
        "latency must remain bounded",
        "error rate must remain bounded",
    ]

    assert [
        entry.ordinal
        for entry in result_set.entries
    ] == [0, 1]


def test_mixed_dispositions_are_allowed():
    (
        contract,
        first_requirement,
        second_requirement,
        first_result,
        second_result,
    ) = build_fixture()

    result_set = build_set(
        contract=contract,
        requirements=(
            first_requirement,
            second_requirement,
        ),
        results=(
            first_result,
            second_result,
        ),
    )

    assert {
        entry.verification_disposition
        for entry in result_set.entries
    } == {
        "VERIFIED",
        "NOT_VERIFIED",
    }


def test_missing_requirement_is_rejected():
    (
        contract,
        first_requirement,
        _,
        first_result,
        second_result,
    ) = build_fixture()

    with pytest.raises(
        GovernanceInterventionReverificationVerificationSetCompletenessError,
        match="structured requirement count",
    ):
        build_set(
            contract=contract,
            requirements=(
                first_requirement,
            ),
            results=(
                first_result,
                second_result,
            ),
        )


def test_missing_result_is_rejected():
    (
        contract,
        first_requirement,
        second_requirement,
        first_result,
        _,
    ) = build_fixture()

    with pytest.raises(
        GovernanceInterventionReverificationVerificationSetCompletenessError,
        match="reverification-result count",
    ):
        build_set(
            contract=contract,
            requirements=(
                first_requirement,
                second_requirement,
            ),
            results=(
                first_result,
            ),
        )


def test_duplicate_contract_obligations_are_rejected():
    contract = make_contract(
        verification_requirements=(
            "same obligation",
            "same obligation",
        )
    )

    with pytest.raises(
        GovernanceInterventionReverificationVerificationSetCompletenessError,
        match="duplicate verification obligations",
    ):
        build_set(
            contract=contract,
            requirements=(),
            results=(),
        )


def test_duplicate_requirement_id_is_rejected():
    (
        contract,
        first_requirement,
        second_requirement,
        first_result,
        second_result,
    ) = build_fixture()

    second_requirement = replace(
        second_requirement,
        requirement_id=(
            first_requirement.requirement_id
        ),
    )
    second_requirement = rehash_requirement(
        second_requirement
    )

    second_result = replace(
        second_result,
        requirement_id=(
            second_requirement.requirement_id
        ),
        requirement_hash=(
            second_requirement.requirement_hash
        ),
    )
    second_result = rehash_result(
        second_result
    )

    with pytest.raises(
        GovernanceInterventionReverificationVerificationSetCompletenessError,
        match="duplicate structured requirement_id",
    ):
        build_set(
            contract=contract,
            requirements=(
                first_requirement,
                second_requirement,
            ),
            results=(
                first_result,
                second_result,
            ),
        )


def test_duplicate_requirement_hash_is_rejected():
    (
        contract,
        first_requirement,
        second_requirement,
        first_result,
        second_result,
    ) = build_fixture()

    second_requirement = replace(
        second_requirement,
        requirement_hash=(
            first_requirement.requirement_hash
        ),
    )

    with pytest.raises(
        GovernanceInterventionReverificationVerificationSetIntegrityError,
    ):
        build_set(
            contract=contract,
            requirements=(
                first_requirement,
                second_requirement,
            ),
            results=(
                first_result,
                second_result,
            ),
        )


def test_duplicate_result_requirement_id_is_rejected():
    (
        contract,
        first_requirement,
        second_requirement,
        first_result,
        second_result,
    ) = build_fixture()

    second_result = replace(
        second_result,
        requirement_id=(
            first_result.requirement_id
        ),
    )
    second_result = rehash_result(
        second_result
    )

    with pytest.raises(
        GovernanceInterventionReverificationVerificationSetCompletenessError,
        match="duplicate reverification result requirement_id",
    ):
        build_set(
            contract=contract,
            requirements=(
                first_requirement,
                second_requirement,
            ),
            results=(
                first_result,
                second_result,
            ),
        )


def test_duplicate_verification_hash_is_rejected():
    (
        contract,
        first_requirement,
        second_requirement,
        first_result,
        second_result,
    ) = build_fixture()

    second_result = replace(
        second_result,
        verification_hash=(
            first_result.verification_hash
        ),
    )

    with pytest.raises(
        GovernanceInterventionReverificationVerificationSetIntegrityError,
    ):
        build_set(
            contract=contract,
            requirements=(
                first_requirement,
                second_requirement,
            ),
            results=(
                first_result,
                second_result,
            ),
        )


def test_requirement_coverage_must_exactly_match_contract():
    (
        contract,
        first_requirement,
        second_requirement,
        first_result,
        second_result,
    ) = build_fixture()

    second_requirement = replace(
        second_requirement,
        legacy_requirement="foreign obligation",
    )
    second_requirement = rehash_requirement(
        second_requirement
    )

    with pytest.raises(
        GovernanceInterventionReverificationVerificationSetLineageError,
        match="does not refine",
    ):
        build_set(
            contract=contract,
            requirements=(
                first_requirement,
                second_requirement,
            ),
            results=(
                first_result,
                second_result,
            ),
        )


def test_result_coverage_must_exactly_match_requirements():
    (
        contract,
        first_requirement,
        second_requirement,
        first_result,
        second_result,
    ) = build_fixture()

    second_result = replace(
        second_result,
        requirement_hash="foreign-requirement-hash",
    )
    second_result = rehash_result(
        second_result
    )

    with pytest.raises(
        GovernanceInterventionReverificationVerificationSetCompletenessError,
        match="do not exactly cover",
    ):
        build_set(
            contract=contract,
            requirements=(
                first_requirement,
                second_requirement,
            ),
            results=(
                first_result,
                second_result,
            ),
        )


def test_result_requirement_id_must_match_requirement():
    (
        contract,
        first_requirement,
        second_requirement,
        first_result,
        second_result,
    ) = build_fixture()

    second_result = replace(
        second_result,
        requirement_id="foreign-id",
    )
    second_result = rehash_result(
        second_result
    )

    with pytest.raises(
        GovernanceInterventionReverificationVerificationSetLineageError,
        match="requirement_id does not match",
    ):
        build_set(
            contract=contract,
            requirements=(
                first_requirement,
                second_requirement,
            ),
            results=(
                first_result,
                second_result,
            ),
        )


@pytest.mark.parametrize(
    (
        "field_name",
        "field_value",
        "message",
    ),
    [
        (
            "tenant_id",
            "tenant-b",
            "result tenant",
        ),
        (
            "actuation_contract_hash",
            "foreign-contract",
            "actuation contract hash",
        ),
        (
            "intervention_id",
            "intervention-b",
            "result intervention_id",
        ),
        (
            "intervention_type",
            "different-type",
            "result intervention_type",
        ),
    ],
)
def test_foreign_result_contract_lineage_is_rejected(
    field_name,
    field_value,
    message,
):
    (
        contract,
        first_requirement,
        second_requirement,
        first_result,
        second_result,
    ) = build_fixture()

    second_result = replace(
        second_result,
        **{
            field_name: field_value
        },
    )
    second_result = rehash_result(
        second_result
    )

    with pytest.raises(
        GovernanceInterventionReverificationVerificationSetLineageError,
        match=message,
    ):
        build_set(
            contract=contract,
            requirements=(
                first_requirement,
                second_requirement,
            ),
            results=(
                first_result,
                second_result,
            ),
        )


@pytest.mark.parametrize(
    (
        "field_name",
        "field_value",
    ),
    [
        (
            "verification_record_hash",
            "record-2",
        ),
        (
            "request_hash",
            "request-2",
        ),
        (
            "work_order_hash",
            "work-order-2",
        ),
        (
            "attempt_id",
            "attempt-2",
        ),
        (
            "attempt_execution_id",
            "attempt-exec-2",
        ),
        (
            "reverification_scope",
            "POLICY",
        ),
    ],
)
def test_mixed_attempt_lineage_is_rejected(
    field_name,
    field_value,
):
    (
        contract,
        first_requirement,
        second_requirement,
        first_result,
        second_result,
    ) = build_fixture()

    second_result = replace(
        second_result,
        **{
            field_name: field_value
        },
    )
    second_result = rehash_result(
        second_result
    )

    with pytest.raises(
        GovernanceInterventionReverificationVerificationSetLineageError,
        match="one exact attempt lineage",
    ):
        build_set(
            contract=contract,
            requirements=(
                first_requirement,
                second_requirement,
            ),
            results=(
                first_result,
                second_result,
            ),
        )


def test_tampered_contract_is_rejected():
    (
        contract,
        first_requirement,
        second_requirement,
        first_result,
        second_result,
    ) = build_fixture()

    tampered = replace(
        contract,
        intervention_type="tampered",
    )

    with pytest.raises(
        GovernanceInterventionReverificationVerificationSetIntegrityError,
        match="actuation contract failed",
    ):
        build_set(
            contract=tampered,
            requirements=(
                first_requirement,
                second_requirement,
            ),
            results=(
                first_result,
                second_result,
            ),
        )


def test_tampered_requirement_is_rejected():
    (
        contract,
        first_requirement,
        second_requirement,
        first_result,
        second_result,
    ) = build_fixture()

    tampered = replace(
        second_requirement,
        metric_id="tampered",
    )

    with pytest.raises(
        GovernanceInterventionReverificationVerificationSetIntegrityError,
        match="structured verification requirement failed",
    ):
        build_set(
            contract=contract,
            requirements=(
                first_requirement,
                tampered,
            ),
            results=(
                first_result,
                second_result,
            ),
        )


def test_tampered_result_is_rejected():
    (
        contract,
        first_requirement,
        second_requirement,
        first_result,
        second_result,
    ) = build_fixture()

    tampered = replace(
        second_result,
        observed_value=999.0,
    )

    with pytest.raises(
        GovernanceInterventionReverificationVerificationSetIntegrityError,
        match="reverification verification result",
    ):
        build_set(
            contract=contract,
            requirements=(
                first_requirement,
                second_requirement,
            ),
            results=(
                first_result,
                tampered,
            ),
        )


def test_attempt_lineage_is_preserved_on_set():
    (
        contract,
        first_requirement,
        second_requirement,
        first_result,
        second_result,
    ) = build_fixture()

    result_set = build_set(
        contract=contract,
        requirements=(
            first_requirement,
            second_requirement,
        ),
        results=(
            first_result,
            second_result,
        ),
    )

    assert (
        result_set.verification_record_hash
        == "record-1"
    )
    assert result_set.request_hash == "request-1"
    assert (
        result_set.work_order_hash
        == "work-order-1"
    )
    assert result_set.attempt_id == "attempt-1"
    assert (
        result_set.attempt_execution_id
        == "attempt-exec-1"
    )
    assert result_set.reverification_scope == "FULL"


def test_same_inputs_produce_same_set_hash():
    (
        contract,
        first_requirement,
        second_requirement,
        first_result,
        second_result,
    ) = build_fixture()

    first = build_set(
        contract=contract,
        requirements=(
            first_requirement,
            second_requirement,
        ),
        results=(
            first_result,
            second_result,
        ),
    )

    second = build_set(
        contract=contract,
        requirements=(
            second_requirement,
            first_requirement,
        ),
        results=(
            second_result,
            first_result,
        ),
    )

    assert (
        first.verification_set_hash
        == second.verification_set_hash
    )


def test_set_contains_no_aggregate_or_action_authority():
    (
        contract,
        first_requirement,
        second_requirement,
        first_result,
        second_result,
    ) = build_fixture()

    result_set = build_set(
        contract=contract,
        requirements=(
            first_requirement,
            second_requirement,
        ),
        results=(
            first_result,
            second_result,
        ),
    )

    payload = result_set.to_dict()

    forbidden = {
        "summary_disposition",
        "aggregate_disposition",
        "overall_verification",
        "success",
        "failure",
        "intervention_success",
        "intervention_failure",
        "causation",
        "causal_effect",
        "authorized",
        "recommended_action",
        "next_action",
        "lifecycle_state",
        "superseded",
        "superseded_record_hash",
        "rollback",
        "continuation",
        "remediation",
    }

    assert forbidden.isdisjoint(
        payload
    )