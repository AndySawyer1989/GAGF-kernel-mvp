from __future__ import annotations

from dataclasses import replace

import pytest

from backend.app.gagf.governance_intervention_actuation_port import (
    GovernanceInterventionActuationRequestBuilder,
    InvalidGovernanceInterventionVerificationCommitmentError,
)
from backend.app.gagf.governance_intervention_verification_commitment import (
    GovernanceInterventionVerificationCommitmentBuilder,
)
from backend.app.gagf.governance_intervention_verification_requirement import (
    GovernanceInterventionVerificationOperator,
    GovernanceInterventionVerificationRequirementBuilder,
)

from tests.test_governance_intervention_actuation_port import _contract


LEGACY_REQUIREMENT = "Verify approval latency."


def _requirement(contract):
    return GovernanceInterventionVerificationRequirementBuilder.build(
        actuation_contract=contract,
        legacy_requirement=LEGACY_REQUIREMENT,
        requirement_id="approval-latency-lte-120",
        description="Approval latency must remain at or below 120 seconds.",
        metric_id="approval_latency_seconds",
        operator=GovernanceInterventionVerificationOperator.LTE,
        target_value=120,
        unit="seconds",
        measurement_window_seconds=86400,
        minimum_record_count=10,
    )


def _commitment(contract):
    requirement = _requirement(contract)

    return GovernanceInterventionVerificationCommitmentBuilder.build(
        actuation_contract=contract,
        requirement=requirement,
    )


def test_request_requires_valid_commitment_lineage():
    contract = _contract()
    commitment = _commitment(contract)

    request = GovernanceInterventionActuationRequestBuilder().build(
        contract=contract,
        verification_commitment=commitment,
        idempotency_key="actuation-001",
    )

    assert request.contract_hash == contract.contract_hash
    assert (
        request.verification_commitment_hash
        == commitment.commitment_hash
    )


def test_request_serialization_binds_commitment_hash():
    contract = _contract()
    commitment = _commitment(contract)

    request = GovernanceInterventionActuationRequestBuilder().build(
        contract=contract,
        verification_commitment=commitment,
        idempotency_key="actuation-001",
    )

    serialized = request.to_dict()

    assert (
        serialized["verification_commitment_hash"]
        == commitment.commitment_hash
    )


def test_rejects_tampered_commitment():
    contract = _contract()
    commitment = _commitment(contract)

    tampered = replace(
        commitment,
        requirement_hash="tampered-requirement-hash",
    )

    assert tampered.verify() is False

    with pytest.raises(
        InvalidGovernanceInterventionVerificationCommitmentError
    ):
        GovernanceInterventionActuationRequestBuilder().build(
            contract=contract,
            verification_commitment=tampered,
            idempotency_key="actuation-001",
        )


def test_rejects_cross_tenant_commitment_even_if_rehashed():
    contract = _contract()
    commitment = _commitment(contract)

    from backend.app.gagf.scientific_authority_guard import (
        canonical_json,
        sha256_hex,
    )

    payload = commitment.payload()
    payload["tenant_id"] = "tenant-b"

    mismatched = replace(
        commitment,
        tenant_id="tenant-b",
        commitment_hash=sha256_hex(
            canonical_json(payload)
        ),
    )

    assert mismatched.verify() is True

    with pytest.raises(
        InvalidGovernanceInterventionVerificationCommitmentError
    ):
        GovernanceInterventionActuationRequestBuilder().build(
            contract=contract,
            verification_commitment=mismatched,
            idempotency_key="actuation-001",
        )


def test_rejects_different_contract_commitment_even_if_rehashed():
    contract = _contract()
    commitment = _commitment(contract)

    from backend.app.gagf.scientific_authority_guard import (
        canonical_json,
        sha256_hex,
    )

    payload = commitment.payload()
    payload["actuation_contract_hash"] = "different-contract"

    mismatched = replace(
        commitment,
        actuation_contract_hash="different-contract",
        commitment_hash=sha256_hex(
            canonical_json(payload)
        ),
    )

    assert mismatched.verify() is True

    with pytest.raises(
        InvalidGovernanceInterventionVerificationCommitmentError
    ):
        GovernanceInterventionActuationRequestBuilder().build(
            contract=contract,
            verification_commitment=mismatched,
            idempotency_key="actuation-001",
        )


def test_rejects_different_intervention_id_even_if_rehashed():
    contract = _contract()
    commitment = _commitment(contract)

    from backend.app.gagf.scientific_authority_guard import (
        canonical_json,
        sha256_hex,
    )

    payload = commitment.payload()
    payload["intervention_id"] = "other-intervention"

    mismatched = replace(
        commitment,
        intervention_id="other-intervention",
        commitment_hash=sha256_hex(
            canonical_json(payload)
        ),
    )

    assert mismatched.verify() is True

    with pytest.raises(
        InvalidGovernanceInterventionVerificationCommitmentError
    ):
        GovernanceInterventionActuationRequestBuilder().build(
            contract=contract,
            verification_commitment=mismatched,
            idempotency_key="actuation-001",
        )


def test_rejects_different_intervention_type_even_if_rehashed():
    contract = _contract()
    commitment = _commitment(contract)

    from backend.app.gagf.scientific_authority_guard import (
        canonical_json,
        sha256_hex,
    )

    payload = commitment.payload()
    payload["intervention_type"] = "DIFFERENT_TYPE"

    mismatched = replace(
        commitment,
        intervention_type="DIFFERENT_TYPE",
        commitment_hash=sha256_hex(
            canonical_json(payload)
        ),
    )

    assert mismatched.verify() is True

    with pytest.raises(
        InvalidGovernanceInterventionVerificationCommitmentError
    ):
        GovernanceInterventionActuationRequestBuilder().build(
            contract=contract,
            verification_commitment=mismatched,
            idempotency_key="actuation-001",
        )


def test_commitment_does_not_claim_execution_success():
    contract = _contract()
    commitment = _commitment(contract)

    request = GovernanceInterventionActuationRequestBuilder().build(
        contract=contract,
        verification_commitment=commitment,
        idempotency_key="actuation-001",
    )

    serialized = request.to_dict()

    assert "executed" not in serialized
    assert "success" not in serialized
    assert "verified" not in serialized
    assert "verification_result" not in serialized