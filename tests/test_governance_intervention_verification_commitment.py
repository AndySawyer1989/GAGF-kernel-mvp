from __future__ import annotations

from dataclasses import FrozenInstanceError, replace

import pytest

from backend.app.gagf.governance_intervention_actuation_contract import (
    GovernanceInterventionActuationContract,
)
from backend.app.gagf.governance_intervention_verification_commitment import (
    GOVERNANCE_INTERVENTION_VERIFICATION_COMMITMENT_ID,
    GOVERNANCE_INTERVENTION_VERIFICATION_COMMITMENT_SCHEMA_VERSION,
    GOVERNANCE_INTERVENTION_VERIFICATION_COMMITMENT_VERSION,
    GovernanceInterventionVerificationCommitmentBuilder,
    GovernanceInterventionVerificationCommitmentLineageError,
)
from backend.app.gagf.governance_intervention_verification_requirement import (
    GovernanceInterventionVerificationOperator,
    GovernanceInterventionVerificationRequirement,
    GovernanceInterventionVerificationRequirementBuilder,
)
from backend.app.gagf.scientific_authority_guard import (
    canonical_json,
    sha256_hex,
)


LEGACY_REQUIREMENT = "Verify approval latency."


def make_contract() -> GovernanceInterventionActuationContract:
    return GovernanceInterventionActuationContract(
        contract_id="governance-intervention-actuation-contract",
        contract_version="0.1.0",
        schema_version="1",
        tenant_id="tenant-a",
        binding_hash="binding-hash",
        authorization_receipt_hash="authorization-hash",
        execution_context_hash="context-hash",
        intervention_id="intervention-1",
        intervention_type="POLICY_CHANGE",
        requested_effect="reduce approval delay",
        effect_boundary="approval workflow only",
        preconditions=("approval system reachable",),
        abort_criteria=("error budget exceeded",),
        rollback_strategy="restore prior approval policy",
        max_attempts=3,
        timeout_seconds=30,
        verification_requirements=(
            LEGACY_REQUIREMENT,
            "Verify audit evidence continuity.",
        ),
        contract_hash="",
    )


def verified_contract() -> GovernanceInterventionActuationContract:
    contract = make_contract()

    payload = contract.to_dict()
    payload.pop("contract_hash")

    return replace(
        contract,
        contract_hash=sha256_hex(
            canonical_json(payload)
        ),
    )


def build_requirement(
    contract: GovernanceInterventionActuationContract | None = None,
) -> GovernanceInterventionVerificationRequirement:
    if contract is None:
        contract = verified_contract()

    return GovernanceInterventionVerificationRequirementBuilder.build(
        actuation_contract=contract,
        legacy_requirement=LEGACY_REQUIREMENT,
        requirement_id="approval-latency-lte-120",
        description=(
            "Approval latency must be no greater "
            "than 120 seconds after intervention."
        ),
        metric_id="approval_latency_seconds",
        operator=GovernanceInterventionVerificationOperator.LTE,
        target_value=120,
        unit="seconds",
        measurement_window_seconds=86400,
        minimum_record_count=10,
    )


def build_commitment():
    contract = verified_contract()
    requirement = build_requirement(contract)

    commitment = (
        GovernanceInterventionVerificationCommitmentBuilder.build(
            actuation_contract=contract,
            requirement=requirement,
        )
    )

    return contract, requirement, commitment


def test_constants_are_stable():
    assert (
        GOVERNANCE_INTERVENTION_VERIFICATION_COMMITMENT_ID
        == "governance-intervention-verification-commitment"
    )
    assert (
        GOVERNANCE_INTERVENTION_VERIFICATION_COMMITMENT_VERSION
        == "0.1.0"
    )
    assert (
        GOVERNANCE_INTERVENTION_VERIFICATION_COMMITMENT_SCHEMA_VERSION
        == "1.0.0"
    )


def test_builds_commitment_from_verified_lineage():
    contract, requirement, commitment = build_commitment()

    assert commitment.verify() is True

    assert commitment.tenant_id == contract.tenant_id
    assert (
        commitment.actuation_contract_hash
        == contract.contract_hash
    )

    assert commitment.intervention_id == contract.intervention_id
    assert commitment.intervention_type == contract.intervention_type

    assert commitment.requirement_id == requirement.requirement_id
    assert (
        commitment.legacy_requirement
        == requirement.legacy_requirement
    )
    assert (
        commitment.requirement_hash
        == requirement.requirement_hash
    )


def test_commitment_hash_is_deterministic():
    first_contract = verified_contract()
    second_contract = verified_contract()

    first_requirement = build_requirement(first_contract)
    second_requirement = build_requirement(second_contract)

    first = GovernanceInterventionVerificationCommitmentBuilder.build(
        actuation_contract=first_contract,
        requirement=first_requirement,
    )

    second = GovernanceInterventionVerificationCommitmentBuilder.build(
        actuation_contract=second_contract,
        requirement=second_requirement,
    )

    assert first == second
    assert first.commitment_hash == second.commitment_hash


def test_serialization_preserves_committed_lineage():
    contract, requirement, commitment = build_commitment()

    serialized = commitment.to_dict()

    assert (
        serialized["commitment_id"]
        == GOVERNANCE_INTERVENTION_VERIFICATION_COMMITMENT_ID
    )
    assert serialized["tenant_id"] == contract.tenant_id
    assert (
        serialized["actuation_contract_hash"]
        == contract.contract_hash
    )
    assert (
        serialized["requirement_hash"]
        == requirement.requirement_hash
    )
    assert (
        serialized["commitment_hash"]
        == commitment.commitment_hash
    )


def test_commitment_is_frozen():
    _, _, commitment = build_commitment()

    with pytest.raises(FrozenInstanceError):
        commitment.requirement_hash = "tampered"


@pytest.mark.parametrize(
    ("field_name", "replacement"),
    (
        ("tenant_id", "tenant-b"),
        ("actuation_contract_hash", "different-contract"),
        ("intervention_id", "different-intervention"),
        ("intervention_type", "DIFFERENT_TYPE"),
        ("requirement_id", "different-requirement"),
        ("legacy_requirement", "different legacy requirement"),
        ("requirement_hash", "different-requirement-hash"),
    ),
)
def test_tampered_commitment_fails_verification(
    field_name,
    replacement,
):
    _, _, commitment = build_commitment()

    tampered = replace(
        commitment,
        **{field_name: replacement},
    )

    assert tampered.verify() is False


def test_rejects_tampered_actuation_contract():
    contract = verified_contract()
    requirement = build_requirement(contract)

    tampered_contract = replace(
        contract,
        requested_effect="tampered requested effect",
    )

    assert tampered_contract.verify() is False

    with pytest.raises(
        GovernanceInterventionVerificationCommitmentLineageError
    ):
        GovernanceInterventionVerificationCommitmentBuilder.build(
            actuation_contract=tampered_contract,
            requirement=requirement,
        )


def test_rejects_tampered_structured_requirement():
    contract = verified_contract()
    requirement = build_requirement(contract)

    tampered_requirement = replace(
        requirement,
        target_value=999.0,
    )

    assert tampered_requirement.verify() is False

    with pytest.raises(
        GovernanceInterventionVerificationCommitmentLineageError
    ):
        GovernanceInterventionVerificationCommitmentBuilder.build(
            actuation_contract=contract,
            requirement=tampered_requirement,
        )


def test_rejects_cross_tenant_requirement():
    contract = verified_contract()
    requirement = build_requirement(contract)

    payload = requirement.payload()
    payload["tenant_id"] = "tenant-b"

    mismatched = replace(
        requirement,
        tenant_id="tenant-b",
        requirement_hash=sha256_hex(
            canonical_json(payload)
        ),
    )

    assert mismatched.verify() is True

    with pytest.raises(
        GovernanceInterventionVerificationCommitmentLineageError
    ):
        GovernanceInterventionVerificationCommitmentBuilder.build(
            actuation_contract=contract,
            requirement=mismatched,
        )


def test_rejects_different_actuation_contract_hash():
    contract = verified_contract()
    requirement = build_requirement(contract)

    payload = requirement.payload()
    payload["actuation_contract_hash"] = "different-contract-hash"

    mismatched = replace(
        requirement,
        actuation_contract_hash="different-contract-hash",
        requirement_hash=sha256_hex(
            canonical_json(payload)
        ),
    )

    assert mismatched.verify() is True

    with pytest.raises(
        GovernanceInterventionVerificationCommitmentLineageError
    ):
        GovernanceInterventionVerificationCommitmentBuilder.build(
            actuation_contract=contract,
            requirement=mismatched,
        )


def test_rejects_different_intervention_id():
    contract = verified_contract()
    requirement = build_requirement(contract)

    payload = requirement.payload()
    payload["intervention_id"] = "different-intervention"

    mismatched = replace(
        requirement,
        intervention_id="different-intervention",
        requirement_hash=sha256_hex(
            canonical_json(payload)
        ),
    )

    assert mismatched.verify() is True

    with pytest.raises(
        GovernanceInterventionVerificationCommitmentLineageError
    ):
        GovernanceInterventionVerificationCommitmentBuilder.build(
            actuation_contract=contract,
            requirement=mismatched,
        )


def test_rejects_different_intervention_type():
    contract = verified_contract()
    requirement = build_requirement(contract)

    payload = requirement.payload()
    payload["intervention_type"] = "DIFFERENT_TYPE"

    mismatched = replace(
        requirement,
        intervention_type="DIFFERENT_TYPE",
        requirement_hash=sha256_hex(
            canonical_json(payload)
        ),
    )

    assert mismatched.verify() is True

    with pytest.raises(
        GovernanceInterventionVerificationCommitmentLineageError
    ):
        GovernanceInterventionVerificationCommitmentBuilder.build(
            actuation_contract=contract,
            requirement=mismatched,
        )


def test_rejects_requirement_not_present_in_contract():
    contract = verified_contract()
    requirement = build_requirement(contract)

    payload = requirement.payload()
    payload["legacy_requirement"] = "Invented requirement."

    mismatched = replace(
        requirement,
        legacy_requirement="Invented requirement.",
        requirement_hash=sha256_hex(
            canonical_json(payload)
        ),
    )

    assert mismatched.verify() is True

    with pytest.raises(
        GovernanceInterventionVerificationCommitmentLineageError
    ):
        GovernanceInterventionVerificationCommitmentBuilder.build(
            actuation_contract=contract,
            requirement=mismatched,
        )


def test_commitment_contains_no_execution_or_outcome_judgment():
    _, _, commitment = build_commitment()

    serialized = commitment.to_dict()

    forbidden_fields = {
        "accepted",
        "execution_result",
        "observed_value",
        "observation_hash",
        "verified",
        "success",
        "outcome_achieved",
        "verification_result",
        "verification_disposition",
        "evaluation_result",
    }

    assert forbidden_fields.isdisjoint(serialized)


def test_commitment_does_not_claim_temporal_proof():
    _, _, commitment = build_commitment()

    serialized = commitment.to_dict()

    forbidden_temporal_fields = {
        "committed_at",
        "created_at",
        "execution_started_at",
        "accepted_at",
        "pre_execution_proven",
    }

    assert forbidden_temporal_fields.isdisjoint(serialized)


def test_builder_has_no_execution_evaluation_or_authorization_methods():
    forbidden_methods = (
        "execute",
        "dispatch",
        "actuate",
        "accept",
        "observe",
        "evaluate",
        "verify_outcome",
        "determine_success",
        "authorize",
        "rollback",
    )

    for method_name in forbidden_methods:
        assert not hasattr(
            GovernanceInterventionVerificationCommitmentBuilder,
            method_name,
        )