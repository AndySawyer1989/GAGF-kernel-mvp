from __future__ import annotations

from dataclasses import replace

import pytest

from backend.app.gagf.governance_intervention_reverification_attempt import (
    GovernanceInterventionReverificationAttemptJournal,
)
from backend.app.gagf.governance_intervention_reverification_evidence import (
    GOVERNANCE_INTERVENTION_REVERIFICATION_EVIDENCE_ID,
    GOVERNANCE_INTERVENTION_REVERIFICATION_EVIDENCE_SCHEMA_VERSION,
    GOVERNANCE_INTERVENTION_REVERIFICATION_EVIDENCE_VERSION,
    GovernanceInterventionReverificationEvidenceBuilder,
    GovernanceInterventionReverificationEvidenceIntegrityError,
    GovernanceInterventionReverificationEvidenceStateError,
    GovernanceInterventionReverificationEvidenceValueError,
)
from backend.app.gagf.governance_intervention_reverification_work_order import (
    GovernanceInterventionReverificationWorkOrder,
)
from backend.app.gagf.governance_intervention_verification_requirement import (
    GovernanceInterventionVerificationOperator,
    GovernanceInterventionVerificationRequirement,
)
from backend.app.gagf.scientific_authority_guard import (
    canonical_json,
    sha256_hex,
)


def make_work_order(
    *,
    tenant_id: str = "tenant-a",
    intervention_id: str = "intervention-1",
    verification_record_hash: str = "record-1",
    request_hash: str = "request-1",
    request_ledger_chain_hash: str = "request-chain-1",
    attempt_id: str = "attempt-1",
    reverification_scope: str = "POLICY",
    trigger_codes: tuple[str, ...] = (
        "POLICY_CHANGED",
    ),
) -> GovernanceInterventionReverificationWorkOrder:
    payload = {
        "work_order_id": (
            "governance-intervention-reverification-work-order"
        ),
        "version": "0.1.0",
        "schema_version": "1.0.0",
        "tenant_id": tenant_id,
        "intervention_id": intervention_id,
        "verification_record_hash": (
            verification_record_hash
        ),
        "request_hash": request_hash,
        "request_ledger_chain_hash": (
            request_ledger_chain_hash
        ),
        "attempt_id": attempt_id,
        "reverification_scope": reverification_scope,
        "trigger_codes": list(trigger_codes),
    }

    return GovernanceInterventionReverificationWorkOrder(
        work_order_id=payload["work_order_id"],
        version=payload["version"],
        schema_version=payload["schema_version"],
        tenant_id=payload["tenant_id"],
        intervention_id=payload["intervention_id"],
        verification_record_hash=payload[
            "verification_record_hash"
        ],
        request_hash=payload["request_hash"],
        request_ledger_chain_hash=payload[
            "request_ledger_chain_hash"
        ],
        attempt_id=payload["attempt_id"],
        reverification_scope=payload[
            "reverification_scope"
        ],
        trigger_codes=tuple(payload["trigger_codes"]),
        work_order_hash=sha256_hex(
            canonical_json(payload)
        ),
    )


def make_requirement(
    *,
    tenant_id: str = "tenant-a",
    intervention_id: str = "intervention-1",
    actuation_contract_hash: str = "contract-1",
    requirement_id: str = "requirement-1",
    metric_id: str = "metric-1",
) -> GovernanceInterventionVerificationRequirement:
    payload = {
        "requirement_contract_id": (
            "governance-intervention-verification-requirement"
        ),
        "version": "0.1.0",
        "schema_version": "1.0.0",
        "tenant_id": tenant_id,
        "actuation_contract_hash": (
            actuation_contract_hash
        ),
        "intervention_id": intervention_id,
        "intervention_type": "policy-update",
        "legacy_requirement": "latency <= 100",
        "requirement_id": requirement_id,
        "description": "Latency remains bounded.",
        "metric_id": metric_id,
        "operator": (
            GovernanceInterventionVerificationOperator.LTE.value
        ),
        "target_value": 100.0,
        "unit": "ms",
        "measurement_window_seconds": 300,
        "minimum_record_count": 1,
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
        requirement_id=payload[
            "requirement_id"
        ],
        description=payload["description"],
        metric_id=payload["metric_id"],
        operator=(
            GovernanceInterventionVerificationOperator(
                payload["operator"]
            )
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


def make_started_attempt(
    tmp_path,
    *,
    work_order=None,
):
    if work_order is None:
        work_order = make_work_order()

    journal = (
        GovernanceInterventionReverificationAttemptJournal(
            tmp_path / "verification.db"
        )
    )

    attempt = journal.begin(
        work_order=work_order
    )

    return journal, work_order, attempt


def build_evidence(
    *,
    work_order,
    attempt,
    requirement,
    source_id="source-1",
    source_kind="telemetry",
    acquired_at="2026-08-17T16:00:00Z",
    evidence_summary="Observed fresh telemetry.",
    evidence_references=("ref-1",),
    record_count=1,
):
    return (
        GovernanceInterventionReverificationEvidenceBuilder.build(
            work_order=work_order,
            attempt=attempt,
            requirement=requirement,
            source_id=source_id,
            source_kind=source_kind,
            acquired_at=acquired_at,
            evidence_summary=evidence_summary,
            evidence_references=evidence_references,
            record_count=record_count,
        )
    )


def test_evidence_identity_constants_are_exact():
    assert (
        GOVERNANCE_INTERVENTION_REVERIFICATION_EVIDENCE_ID
        == "governance-intervention-reverification-evidence"
    )
    assert (
        GOVERNANCE_INTERVENTION_REVERIFICATION_EVIDENCE_VERSION
        == "0.1.0"
    )
    assert (
        GOVERNANCE_INTERVENTION_REVERIFICATION_EVIDENCE_SCHEMA_VERSION
        == "1.0.0"
    )


def test_started_attempt_allows_evidence(tmp_path):
    _, work_order, attempt = make_started_attempt(
        tmp_path
    )

    requirement = make_requirement()

    evidence = build_evidence(
        work_order=work_order,
        attempt=attempt,
        requirement=requirement,
    )

    assert evidence.verify()
    assert evidence.tenant_id == work_order.tenant_id
    assert (
        evidence.intervention_id
        == work_order.intervention_id
    )
    assert (
        evidence.work_order_hash
        == work_order.work_order_hash
    )
    assert (
        evidence.attempt_execution_id
        == attempt.attempt_execution_id
    )
    assert (
        evidence.requirement_hash
        == requirement.requirement_hash
    )


def test_same_inputs_produce_same_evidence_hash(
    tmp_path,
):
    _, work_order, attempt = make_started_attempt(
        tmp_path
    )
    requirement = make_requirement()

    first = build_evidence(
        work_order=work_order,
        attempt=attempt,
        requirement=requirement,
    )

    second = build_evidence(
        work_order=work_order,
        attempt=attempt,
        requirement=requirement,
    )

    assert first.evidence_hash == second.evidence_hash


def test_different_attempt_changes_evidence_hash(
    tmp_path,
):
    journal = (
        GovernanceInterventionReverificationAttemptJournal(
            tmp_path / "verification.db"
        )
    )

    first_order = make_work_order(
        attempt_id="attempt-1"
    )
    second_order = make_work_order(
        attempt_id="attempt-2"
    )

    first_attempt = journal.begin(
        work_order=first_order
    )
    second_attempt = journal.begin(
        work_order=second_order
    )

    requirement = make_requirement()

    first = build_evidence(
        work_order=first_order,
        attempt=first_attempt,
        requirement=requirement,
    )

    second = build_evidence(
        work_order=second_order,
        attempt=second_attempt,
        requirement=requirement,
    )

    assert first.evidence_hash != second.evidence_hash


def test_completed_attempt_rejects_evidence(
    tmp_path,
):
    journal, work_order, _ = make_started_attempt(
        tmp_path
    )

    completed = journal.complete(
        work_order=work_order
    )

    with pytest.raises(
        GovernanceInterventionReverificationEvidenceStateError,
        match="active STARTED attempt",
    ):
        build_evidence(
            work_order=work_order,
            attempt=completed,
            requirement=make_requirement(),
        )


def test_failed_attempt_rejects_evidence(
    tmp_path,
):
    journal, work_order, _ = make_started_attempt(
        tmp_path
    )

    failed = journal.fail(
        work_order=work_order,
        error=RuntimeError("source failure"),
    )

    with pytest.raises(
        GovernanceInterventionReverificationEvidenceStateError,
        match="active STARTED attempt",
    ):
        build_evidence(
            work_order=work_order,
            attempt=failed,
            requirement=make_requirement(),
        )


def test_tampered_work_order_is_rejected(
    tmp_path,
):
    _, work_order, attempt = make_started_attempt(
        tmp_path
    )

    tampered = replace(
        work_order,
        intervention_id="tampered",
    )

    with pytest.raises(
        GovernanceInterventionReverificationEvidenceIntegrityError,
        match="work order failed deterministic verification",
    ):
        build_evidence(
            work_order=tampered,
            attempt=attempt,
            requirement=make_requirement(),
        )


def test_tampered_requirement_is_rejected(
    tmp_path,
):
    _, work_order, attempt = make_started_attempt(
        tmp_path
    )

    requirement = make_requirement()

    tampered = replace(
        requirement,
        metric_id="tampered-metric",
    )

    with pytest.raises(
        GovernanceInterventionReverificationEvidenceIntegrityError,
        match="verification requirement failed deterministic verification",
    ):
        build_evidence(
            work_order=work_order,
            attempt=attempt,
            requirement=tampered,
        )


def test_attempt_work_order_mismatch_is_rejected(
    tmp_path,
):
    journal = (
        GovernanceInterventionReverificationAttemptJournal(
            tmp_path / "verification.db"
        )
    )

    first_order = make_work_order(
        attempt_id="attempt-1"
    )
    second_order = make_work_order(
        attempt_id="attempt-2"
    )

    first_attempt = journal.begin(
        work_order=first_order
    )

    with pytest.raises(
        GovernanceInterventionReverificationEvidenceIntegrityError,
        match="attempt does not match I-L work-order lineage",
    ):
        build_evidence(
            work_order=second_order,
            attempt=first_attempt,
            requirement=make_requirement(),
        )


def test_requirement_tenant_mismatch_is_rejected(
    tmp_path,
):
    _, work_order, attempt = make_started_attempt(
        tmp_path
    )

    requirement = make_requirement(
        tenant_id="tenant-b"
    )

    with pytest.raises(
        GovernanceInterventionReverificationEvidenceIntegrityError,
        match="requirement tenant does not match work order",
    ):
        build_evidence(
            work_order=work_order,
            attempt=attempt,
            requirement=requirement,
        )


def test_requirement_intervention_mismatch_is_rejected(
    tmp_path,
):
    _, work_order, attempt = make_started_attempt(
        tmp_path
    )

    requirement = make_requirement(
        intervention_id="intervention-2"
    )

    with pytest.raises(
        GovernanceInterventionReverificationEvidenceIntegrityError,
        match="requirement intervention_id does not match work order",
    ):
        build_evidence(
            work_order=work_order,
            attempt=attempt,
            requirement=requirement,
        )


@pytest.mark.parametrize(
    "field_name,field_value",
    [
        ("source_id", ""),
        ("source_kind", ""),
        ("acquired_at", ""),
        ("evidence_summary", ""),
    ],
)
def test_required_evidence_metadata_is_enforced(
    tmp_path,
    field_name,
    field_value,
):
    _, work_order, attempt = make_started_attempt(
        tmp_path
    )

    kwargs = {
        "work_order": work_order,
        "attempt": attempt,
        "requirement": make_requirement(),
        field_name: field_value,
    }

    with pytest.raises(
        GovernanceInterventionReverificationEvidenceValueError,
        match="is required",
    ):
        build_evidence(**kwargs)


def test_duplicate_evidence_references_are_rejected(
    tmp_path,
):
    _, work_order, attempt = make_started_attempt(
        tmp_path
    )

    with pytest.raises(
        GovernanceInterventionReverificationEvidenceValueError,
        match="must not contain duplicates",
    ):
        build_evidence(
            work_order=work_order,
            attempt=attempt,
            requirement=make_requirement(),
            evidence_references=(
                "ref-1",
                "ref-1",
            ),
        )


def test_empty_evidence_references_are_rejected(
    tmp_path,
):
    _, work_order, attempt = make_started_attempt(
        tmp_path
    )

    with pytest.raises(
        GovernanceInterventionReverificationEvidenceValueError,
        match="at least one evidence reference is required",
    ):
        build_evidence(
            work_order=work_order,
            attempt=attempt,
            requirement=make_requirement(),
            evidence_references=(),
        )


def test_zero_record_count_is_rejected(
    tmp_path,
):
    _, work_order, attempt = make_started_attempt(
        tmp_path
    )

    with pytest.raises(
        GovernanceInterventionReverificationEvidenceValueError,
        match="record_count must be at least 1",
    ):
        build_evidence(
            work_order=work_order,
            attempt=attempt,
            requirement=make_requirement(),
            record_count=0,
        )


def test_noncanonical_metadata_is_rejected(
    tmp_path,
):
    _, work_order, attempt = make_started_attempt(
        tmp_path
    )

    with pytest.raises(
        GovernanceInterventionReverificationEvidenceValueError,
        match="source_id must already be canonical",
    ):
        build_evidence(
            work_order=work_order,
            attempt=attempt,
            requirement=make_requirement(),
            source_id=" source-1 ",
        )


def test_evidence_contains_no_original_execution_fields(
    tmp_path,
):
    _, work_order, attempt = make_started_attempt(
        tmp_path
    )

    evidence = build_evidence(
        work_order=work_order,
        attempt=attempt,
        requirement=make_requirement(),
    )

    payload = evidence.to_dict()

    forbidden = {
        "execution_receipt_hash",
        "execution_result_hash",
        "actuation_id",
        "execution_adapter_id",
        "execution_adapter_version",
    }

    assert forbidden.isdisjoint(payload)


def test_evidence_contains_no_judgment_or_action_authority(
    tmp_path,
):
    _, work_order, attempt = make_started_attempt(
        tmp_path
    )

    evidence = build_evidence(
        work_order=work_order,
        attempt=attempt,
        requirement=make_requirement(),
    )

    payload = evidence.to_dict()

    forbidden = {
        "observed_value",
        "measurement_hash",
        "verification_disposition",
        "verified",
        "not_verified",
        "inconclusive",
        "success",
        "failure",
        "causation",
        "causal_effect",
        "authorized",
        "recommended_action",
        "next_action",
        "superseded",
        "superseded_record_hash",
    }

    assert forbidden.isdisjoint(payload)