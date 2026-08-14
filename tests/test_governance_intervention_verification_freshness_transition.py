from __future__ import annotations

from dataclasses import replace

import pytest

from backend.app.gagf.governance_intervention_verification_freshness import (
    GovernanceInterventionVerificationFreshnessEvaluator,
    GovernanceInterventionVerificationFreshnessEvidence,
)
from backend.app.gagf.governance_intervention_verification_freshness_transition import (
    GOVERNANCE_INTERVENTION_VERIFICATION_FRESHNESS_TRANSITION_ID,
    GOVERNANCE_INTERVENTION_VERIFICATION_FRESHNESS_TRANSITION_SCHEMA_VERSION,
    GOVERNANCE_INTERVENTION_VERIFICATION_FRESHNESS_TRANSITION_VERSION,
    GovernanceInterventionVerificationFreshnessTransitionIntegrityError,
    GovernanceInterventionVerificationFreshnessTransitionService,
    GovernanceInterventionVerificationFreshnessTransitionStateError,
)
from backend.app.gagf.governance_intervention_verification_ledger import (
    GovernanceInterventionVerificationLedger,
    GovernanceInterventionVerificationRecordBuilder,
)
from backend.app.gagf.governance_intervention_verification_lifecycle import (
    GovernanceInterventionVerificationLifecycleLedger,
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


def persist_record(
    database_path,
    *,
    tenant_id: str = "tenant-a",
    intervention_id: str = "intervention-1",
    verification_set_hash: str = "verification-set-1",
):
    summary = make_summary(
        tenant_id=tenant_id,
        intervention_id=intervention_id,
        verification_set_hash=verification_set_hash,
    )

    record = GovernanceInterventionVerificationRecordBuilder.build(
        summary=summary
    )

    ledger = GovernanceInterventionVerificationLedger(
        database_path
    )

    ledger.append(
        record=record
    )

    return summary, record


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


def evaluate(
    record,
    **overrides,
):
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


def activate(
    database_path,
    record,
):
    lifecycle = (
        GovernanceInterventionVerificationLifecycleLedger(
            database_path=database_path
        )
    )

    lifecycle.activate(
        tenant_id=record.tenant_id,
        verification_record_hash=record.record_hash,
    )

    return lifecycle


def current_state(
    lifecycle,
    record,
):
    return lifecycle.get_current_state(
        tenant_id=record.tenant_id,
        verification_record_hash=record.record_hash,
    )


def test_transition_constants_are_stable():
    assert (
        GOVERNANCE_INTERVENTION_VERIFICATION_FRESHNESS_TRANSITION_ID
        == "governance-intervention-verification-freshness-transition"
    )

    assert (
        GOVERNANCE_INTERVENTION_VERIFICATION_FRESHNESS_TRANSITION_VERSION
        == "0.1.0"
    )

    assert (
        GOVERNANCE_INTERVENTION_VERIFICATION_FRESHNESS_TRANSITION_SCHEMA_VERSION
        == "1.0.0"
    )


def test_fresh_evaluation_does_not_mutate_active_state(
    tmp_path,
):
    database_path = tmp_path / "verification.db"

    _, record = persist_record(
        database_path
    )

    lifecycle = activate(
        database_path,
        record,
    )

    before = lifecycle.list_history(
        tenant_id="tenant-a",
        verification_record_hash=record.record_hash,
    )

    evaluation = evaluate(
        record
    )

    service = (
        GovernanceInterventionVerificationFreshnessTransitionService(
            database_path=database_path
        )
    )

    result = service.apply(
        evaluation=evaluation
    )

    after = lifecycle.list_history(
        tenant_id="tenant-a",
        verification_record_hash=record.record_hash,
    )

    assert result.applied is False
    assert result.prior_lifecycle_status == "ACTIVE"
    assert result.proposed_lifecycle_status is None
    assert result.resulting_lifecycle_status == "ACTIVE"
    assert result.lifecycle_event_hash is None
    assert after == before


def test_active_stale_evaluation_appends_stale(
    tmp_path,
):
    database_path = tmp_path / "verification.db"

    _, record = persist_record(
        database_path
    )

    lifecycle = activate(
        database_path,
        record,
    )

    evaluation = evaluate(
        record,
        current_source_evidence_hash="source-b",
    )

    service = (
        GovernanceInterventionVerificationFreshnessTransitionService(
            database_path=database_path
        )
    )

    result = service.apply(
        evaluation=evaluation
    )

    state = current_state(
        lifecycle,
        record,
    )

    assert result.applied is True
    assert result.prior_lifecycle_status == "ACTIVE"
    assert result.proposed_lifecycle_status == "STALE"
    assert result.resulting_lifecycle_status == "STALE"
    assert result.lifecycle_event_hash is not None
    assert state.lifecycle_status == "STALE"


def test_stale_repeated_stale_is_noop(
    tmp_path,
):
    database_path = tmp_path / "verification.db"

    _, record = persist_record(
        database_path
    )

    lifecycle = activate(
        database_path,
        record,
    )

    evaluation = evaluate(
        record,
        current_source_evidence_hash="source-b",
    )

    service = (
        GovernanceInterventionVerificationFreshnessTransitionService(
            database_path=database_path
        )
    )

    first = service.apply(
        evaluation=evaluation
    )

    history_before = lifecycle.list_history(
        tenant_id="tenant-a",
        verification_record_hash=record.record_hash,
    )

    second = service.apply(
        evaluation=evaluation
    )

    history_after = lifecycle.list_history(
        tenant_id="tenant-a",
        verification_record_hash=record.record_hash,
    )

    assert first.applied is True
    assert second.applied is False
    assert second.resulting_lifecycle_status == "STALE"
    assert history_after == history_before


def test_active_reverification_evaluation_appends_reverification_required(
    tmp_path,
):
    database_path = tmp_path / "verification.db"

    _, record = persist_record(
        database_path
    )

    lifecycle = activate(
        database_path,
        record,
    )

    evaluation = evaluate(
        record,
        current_policy_hash="policy-b",
    )

    service = (
        GovernanceInterventionVerificationFreshnessTransitionService(
            database_path=database_path
        )
    )

    result = service.apply(
        evaluation=evaluation
    )

    state = current_state(
        lifecycle,
        record,
    )

    assert result.applied is True
    assert (
        result.resulting_lifecycle_status
        == "REVERIFICATION_REQUIRED"
    )
    assert (
        state.lifecycle_status
        == "REVERIFICATION_REQUIRED"
    )


def test_stale_escalates_to_reverification_required(
    tmp_path,
):
    database_path = tmp_path / "verification.db"

    _, record = persist_record(
        database_path
    )

    lifecycle = activate(
        database_path,
        record,
    )

    service = (
        GovernanceInterventionVerificationFreshnessTransitionService(
            database_path=database_path
        )
    )

    stale = evaluate(
        record,
        current_source_evidence_hash="source-b",
    )

    service.apply(
        evaluation=stale
    )

    reverify = evaluate(
        record,
        current_policy_hash="policy-b",
    )

    result = service.apply(
        evaluation=reverify
    )

    history = lifecycle.list_history(
        tenant_id="tenant-a",
        verification_record_hash=record.record_hash,
    )

    assert result.applied is True
    assert result.prior_lifecycle_status == "STALE"
    assert (
        result.resulting_lifecycle_status
        == "REVERIFICATION_REQUIRED"
    )

    assert [
        event.lifecycle_status
        for event in history
    ] == [
        "ACTIVE",
        "STALE",
        "REVERIFICATION_REQUIRED",
    ]


def test_reverification_required_does_not_downgrade_to_stale(
    tmp_path,
):
    database_path = tmp_path / "verification.db"

    _, record = persist_record(
        database_path
    )

    lifecycle = activate(
        database_path,
        record,
    )

    service = (
        GovernanceInterventionVerificationFreshnessTransitionService(
            database_path=database_path
        )
    )

    service.apply(
        evaluation=evaluate(
            record,
            current_policy_hash="policy-b",
        )
    )

    history_before = lifecycle.list_history(
        tenant_id="tenant-a",
        verification_record_hash=record.record_hash,
    )

    result = service.apply(
        evaluation=evaluate(
            record,
            current_source_evidence_hash="source-b",
        )
    )

    history_after = lifecycle.list_history(
        tenant_id="tenant-a",
        verification_record_hash=record.record_hash,
    )

    assert result.applied is False
    assert (
        result.resulting_lifecycle_status
        == "REVERIFICATION_REQUIRED"
    )
    assert history_after == history_before


def test_reverification_required_replay_is_noop(
    tmp_path,
):
    database_path = tmp_path / "verification.db"

    _, record = persist_record(
        database_path
    )

    lifecycle = activate(
        database_path,
        record,
    )

    evaluation = evaluate(
        record,
        current_policy_hash="policy-b",
    )

    service = (
        GovernanceInterventionVerificationFreshnessTransitionService(
            database_path=database_path
        )
    )

    first = service.apply(
        evaluation=evaluation
    )

    history_before = lifecycle.list_history(
        tenant_id="tenant-a",
        verification_record_hash=record.record_hash,
    )

    second = service.apply(
        evaluation=evaluation
    )

    history_after = lifecycle.list_history(
        tenant_id="tenant-a",
        verification_record_hash=record.record_hash,
    )

    assert first.applied is True
    assert second.applied is False
    assert history_after == history_before


def test_mutating_evaluation_requires_active_lifecycle_state(
    tmp_path,
):
    database_path = tmp_path / "verification.db"

    _, record = persist_record(
        database_path
    )

    evaluation = evaluate(
        record,
        current_policy_hash="policy-b",
    )

    service = (
        GovernanceInterventionVerificationFreshnessTransitionService(
            database_path=database_path
        )
    )

    with pytest.raises(
        GovernanceInterventionVerificationFreshnessTransitionStateError,
        match="existing ACTIVE lifecycle state",
    ):
        service.apply(
            evaluation=evaluation
        )


def test_fresh_without_lifecycle_state_remains_noop(
    tmp_path,
):
    database_path = tmp_path / "verification.db"

    _, record = persist_record(
        database_path
    )

    evaluation = evaluate(
        record
    )

    service = (
        GovernanceInterventionVerificationFreshnessTransitionService(
            database_path=database_path
        )
    )

    result = service.apply(
        evaluation=evaluation
    )

    assert result.applied is False
    assert result.prior_lifecycle_status is None
    assert result.resulting_lifecycle_status is None


def test_superseded_record_rejects_stale_transition(
    tmp_path,
):
    database_path = tmp_path / "verification.db"

    _, original = persist_record(
        database_path,
        verification_set_hash="set-original",
    )

    _, replacement = persist_record(
        database_path,
        verification_set_hash="set-replacement",
    )

    lifecycle = activate(
        database_path,
        original,
    )

    lifecycle.supersede(
        tenant_id="tenant-a",
        verification_record_hash=original.record_hash,
        superseded_by_record_hash=replacement.record_hash,
    )

    service = (
        GovernanceInterventionVerificationFreshnessTransitionService(
            database_path=database_path
        )
    )

    evaluation = evaluate(
        original,
        current_source_evidence_hash="source-b",
    )

    with pytest.raises(
        GovernanceInterventionVerificationFreshnessTransitionStateError,
        match="SUPERSEDED",
    ):
        service.apply(
            evaluation=evaluation
        )


def test_superseded_record_rejects_reverification_transition(
    tmp_path,
):
    database_path = tmp_path / "verification.db"

    _, original = persist_record(
        database_path,
        verification_set_hash="set-original",
    )

    _, replacement = persist_record(
        database_path,
        verification_set_hash="set-replacement",
    )

    lifecycle = activate(
        database_path,
        original,
    )

    lifecycle.supersede(
        tenant_id="tenant-a",
        verification_record_hash=original.record_hash,
        superseded_by_record_hash=replacement.record_hash,
    )

    service = (
        GovernanceInterventionVerificationFreshnessTransitionService(
            database_path=database_path
        )
    )

    evaluation = evaluate(
        original,
        current_policy_hash="policy-b",
    )

    with pytest.raises(
        GovernanceInterventionVerificationFreshnessTransitionStateError,
        match="SUPERSEDED",
    ):
        service.apply(
            evaluation=evaluation
        )


def test_tampered_freshness_evaluation_is_rejected(
    tmp_path,
):
    database_path = tmp_path / "verification.db"

    _, record = persist_record(
        database_path
    )

    activate(
        database_path,
        record,
    )

    evaluation = evaluate(
        record
    )

    tampered = replace(
        evaluation,
        freshness_disposition="STALE",
    )

    service = (
        GovernanceInterventionVerificationFreshnessTransitionService(
            database_path=database_path
        )
    )

    with pytest.raises(
        GovernanceInterventionVerificationFreshnessTransitionIntegrityError,
        match="failed deterministic verification",
    ):
        service.apply(
            evaluation=tampered
        )


def test_fresh_cannot_propose_lifecycle_mutation(
    tmp_path,
):
    database_path = tmp_path / "verification.db"

    _, record = persist_record(
        database_path
    )

    activate(
        database_path,
        record,
    )

    evaluation = evaluate(
        record
    )

    payload = evaluation.payload()
    payload["proposed_lifecycle_status"] = "STALE"

    tampered = replace(
        evaluation,
        proposed_lifecycle_status="STALE",
        freshness_evaluation_hash=sha256_hex(
            canonical_json(payload)
        ),
    )

    assert tampered.verify() is True

    service = (
        GovernanceInterventionVerificationFreshnessTransitionService(
            database_path=database_path
        )
    )

    with pytest.raises(
        GovernanceInterventionVerificationFreshnessTransitionIntegrityError,
        match="must not propose lifecycle mutation",
    ):
        service.apply(
            evaluation=tampered
        )


def test_stale_must_propose_stale(
    tmp_path,
):
    database_path = tmp_path / "verification.db"

    _, record = persist_record(
        database_path
    )

    activate(
        database_path,
        record,
    )

    evaluation = evaluate(
        record,
        current_source_evidence_hash="source-b",
    )

    payload = evaluation.payload()
    payload["proposed_lifecycle_status"] = (
        "REVERIFICATION_REQUIRED"
    )

    tampered = replace(
        evaluation,
        proposed_lifecycle_status=(
            "REVERIFICATION_REQUIRED"
        ),
        freshness_evaluation_hash=sha256_hex(
            canonical_json(payload)
        ),
    )

    assert tampered.verify() is True

    service = (
        GovernanceInterventionVerificationFreshnessTransitionService(
            database_path=database_path
        )
    )

    with pytest.raises(
        GovernanceInterventionVerificationFreshnessTransitionIntegrityError,
        match="must propose STALE",
    ):
        service.apply(
            evaluation=tampered
        )


def test_reverification_must_propose_reverification_required(
    tmp_path,
):
    database_path = tmp_path / "verification.db"

    _, record = persist_record(
        database_path
    )

    activate(
        database_path,
        record,
    )

    evaluation = evaluate(
        record,
        current_policy_hash="policy-b",
    )

    payload = evaluation.payload()
    payload["proposed_lifecycle_status"] = "STALE"

    tampered = replace(
        evaluation,
        proposed_lifecycle_status="STALE",
        freshness_evaluation_hash=sha256_hex(
            canonical_json(payload)
        ),
    )

    assert tampered.verify() is True

    service = (
        GovernanceInterventionVerificationFreshnessTransitionService(
            database_path=database_path
        )
    )

    with pytest.raises(
        GovernanceInterventionVerificationFreshnessTransitionIntegrityError,
        match="must propose REVERIFICATION_REQUIRED",
    ):
        service.apply(
            evaluation=tampered
        )


def test_transition_result_hash_verifies(
    tmp_path,
):
    database_path = tmp_path / "verification.db"

    _, record = persist_record(
        database_path
    )

    activate(
        database_path,
        record,
    )

    service = (
        GovernanceInterventionVerificationFreshnessTransitionService(
            database_path=database_path
        )
    )

    result = service.apply(
        evaluation=evaluate(
            record,
            current_source_evidence_hash="source-b",
        )
    )

    assert result.verify() is True


def test_transition_result_hash_detects_tampering(
    tmp_path,
):
    database_path = tmp_path / "verification.db"

    _, record = persist_record(
        database_path
    )

    activate(
        database_path,
        record,
    )

    service = (
        GovernanceInterventionVerificationFreshnessTransitionService(
            database_path=database_path
        )
    )

    result = service.apply(
        evaluation=evaluate(
            record
        )
    )

    tampered = replace(
        result,
        applied=True,
    )

    assert result.verify() is True
    assert tampered.verify() is False


def test_transition_does_not_change_verification_record(
    tmp_path,
):
    database_path = tmp_path / "verification.db"

    summary, original = persist_record(
        database_path
    )

    activate(
        database_path,
        original,
    )

    service = (
        GovernanceInterventionVerificationFreshnessTransitionService(
            database_path=database_path
        )
    )

    service.apply(
        evaluation=evaluate(
            original,
            current_policy_hash="policy-b",
        )
    )

    ledger = GovernanceInterventionVerificationLedger(
        database_path
    )

    stored = ledger.get_by_summary_hash(
        tenant_id="tenant-a",
        verification_summary_hash=(
            summary.verification_summary_hash
        ),
    )

    assert stored == original


def test_transition_result_contains_no_reverification_claim(
    tmp_path,
):
    database_path = tmp_path / "verification.db"

    _, record = persist_record(
        database_path
    )

    activate(
        database_path,
        record,
    )

    service = (
        GovernanceInterventionVerificationFreshnessTransitionService(
            database_path=database_path
        )
    )

    result = service.apply(
        evaluation=evaluate(
            record,
            current_policy_hash="policy-b",
        )
    )

    payload = result.to_dict()

    forbidden = {
        "reverified",
        "reverification_completed",
        "verification_disposition",
        "success",
        "failure",
        "causation",
        "causal_effect",
        "authorized",
        "execute",
        "rollback",
        "continue_intervention",
        "recommended_action",
        "next_action",
    }

    assert forbidden.isdisjoint(
        payload
    )


def test_transition_service_has_no_execution_or_causal_methods():
    actual_methods = {
        name
        for name in dir(
            GovernanceInterventionVerificationFreshnessTransitionService
        )
        if not name.startswith("_")
    }

    forbidden_methods = {
        "execute",
        "actuate",
        "authorize",
        "rollback",
        "continue_intervention",
        "infer_causation",
        "attribute_causation",
        "reverify",
        "verify_outcome",
        "supersede",
    }

    assert forbidden_methods.isdisjoint(
        actual_methods
    )