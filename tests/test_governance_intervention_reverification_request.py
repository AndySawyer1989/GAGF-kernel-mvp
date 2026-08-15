from __future__ import annotations

from dataclasses import replace

import pytest

from backend.app.gagf.governance_intervention_reverification_request import (
    GOVERNANCE_INTERVENTION_REVERIFICATION_REQUEST_ID,
    GOVERNANCE_INTERVENTION_REVERIFICATION_REQUEST_SCHEMA_VERSION,
    GOVERNANCE_INTERVENTION_REVERIFICATION_REQUEST_VERSION,
    GovernanceInterventionReverificationRequestBuilder,
    GovernanceInterventionReverificationRequestError,
    GovernanceInterventionReverificationRequestIntegrityError,
    GovernanceInterventionReverificationScope,
)
from backend.app.gagf.governance_intervention_verification_freshness import (
    GovernanceInterventionVerificationFreshnessEvaluator,
    GovernanceInterventionVerificationFreshnessEvidence,
)
from backend.app.gagf.governance_intervention_verification_freshness_transition import (
    GovernanceInterventionVerificationFreshnessTransitionService,
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


def activate_and_apply(
    database_path,
    record,
    evaluation,
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

    transition = (
        GovernanceInterventionVerificationFreshnessTransitionService(
            database_path=database_path
        )
    )

    transition.apply(
        evaluation=evaluation
    )

    state = lifecycle.get_current_state(
        tenant_id=record.tenant_id,
        verification_record_hash=record.record_hash,
    )

    assert state is not None

    return lifecycle, state


def build_request(
    *,
    record,
    evaluation,
    lifecycle_state,
):
    return GovernanceInterventionReverificationRequestBuilder.build(
        record=record,
        freshness_evaluation=evaluation,
        lifecycle_state=lifecycle_state,
    )


def test_request_constants_are_stable():
    assert (
        GOVERNANCE_INTERVENTION_REVERIFICATION_REQUEST_ID
        == "governance-intervention-reverification-request"
    )

    assert (
        GOVERNANCE_INTERVENTION_REVERIFICATION_REQUEST_VERSION
        == "0.1.0"
    )

    assert (
        GOVERNANCE_INTERVENTION_REVERIFICATION_REQUEST_SCHEMA_VERSION
        == "1.0.0"
    )


def test_reverification_scope_enum_is_exact():
    assert {
        scope.value
        for scope in GovernanceInterventionReverificationScope
    } == {
        "FULL",
        "REQUIREMENTS",
        "OBSERVATIONS",
        "POLICY",
        "CONTRACT",
    }


def test_policy_change_builds_policy_scope(
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

    _, state = activate_and_apply(
        database_path,
        record,
        evaluation,
    )

    request = build_request(
        record=record,
        evaluation=evaluation,
        lifecycle_state=state,
    )

    assert request.reverification_scope == "POLICY"
    assert request.trigger_codes == (
        "POLICY_CHANGED",
    )
    assert request.verify() is True


def test_invalidated_observation_builds_observation_scope(
    tmp_path,
):
    database_path = tmp_path / "verification.db"

    _, record = persist_record(
        database_path
    )

    evaluation = evaluate(
        record,
        required_observations_valid=False,
    )

    _, state = activate_and_apply(
        database_path,
        record,
        evaluation,
    )

    request = build_request(
        record=record,
        evaluation=evaluation,
        lifecycle_state=state,
    )

    assert request.reverification_scope == "OBSERVATIONS"


def test_requirements_change_builds_requirements_scope(
    tmp_path,
):
    database_path = tmp_path / "verification.db"

    _, record = persist_record(
        database_path
    )

    evaluation = evaluate(
        record,
        current_requirements_hash="requirements-b",
    )

    _, state = activate_and_apply(
        database_path,
        record,
        evaluation,
    )

    request = build_request(
        record=record,
        evaluation=evaluation,
        lifecycle_state=state,
    )

    assert request.reverification_scope == "REQUIREMENTS"


def test_contract_change_builds_full_scope(
    tmp_path,
):
    database_path = tmp_path / "verification.db"

    _, record = persist_record(
        database_path
    )

    evaluation = evaluate(
        record,
        current_contract_hash="contract-b",
    )

    _, state = activate_and_apply(
        database_path,
        record,
        evaluation,
    )

    request = build_request(
        record=record,
        evaluation=evaluation,
        lifecycle_state=state,
    )

    assert request.reverification_scope == "FULL"


def test_contract_change_has_scope_precedence(
    tmp_path,
):
    database_path = tmp_path / "verification.db"

    _, record = persist_record(
        database_path
    )

    evaluation = evaluate(
        record,
        current_policy_hash="policy-b",
        required_observations_valid=False,
        current_requirements_hash="requirements-b",
        current_contract_hash="contract-b",
    )

    _, state = activate_and_apply(
        database_path,
        record,
        evaluation,
    )

    request = build_request(
        record=record,
        evaluation=evaluation,
        lifecycle_state=state,
    )

    assert request.reverification_scope == "FULL"


def test_requirements_change_precedes_observation_and_policy(
    tmp_path,
):
    database_path = tmp_path / "verification.db"

    _, record = persist_record(
        database_path
    )

    evaluation = evaluate(
        record,
        current_policy_hash="policy-b",
        required_observations_valid=False,
        current_requirements_hash="requirements-b",
    )

    _, state = activate_and_apply(
        database_path,
        record,
        evaluation,
    )

    request = build_request(
        record=record,
        evaluation=evaluation,
        lifecycle_state=state,
    )

    assert request.reverification_scope == "REQUIREMENTS"


def test_observation_invalidation_precedes_policy(
    tmp_path,
):
    database_path = tmp_path / "verification.db"

    _, record = persist_record(
        database_path
    )

    evaluation = evaluate(
        record,
        current_policy_hash="policy-b",
        required_observations_valid=False,
    )

    _, state = activate_and_apply(
        database_path,
        record,
        evaluation,
    )

    request = build_request(
        record=record,
        evaluation=evaluation,
        lifecycle_state=state,
    )

    assert request.reverification_scope == "OBSERVATIONS"


def test_stale_only_evaluation_cannot_build_request(
    tmp_path,
):
    database_path = tmp_path / "verification.db"

    _, record = persist_record(
        database_path
    )

    evaluation = evaluate(
        record,
        current_source_evidence_hash="source-b",
    )

    lifecycle, _ = activate_and_apply(
        database_path,
        record,
        evaluation,
    )

    state = lifecycle.get_current_state(
        tenant_id=record.tenant_id,
        verification_record_hash=record.record_hash,
    )

    with pytest.raises(
        GovernanceInterventionReverificationRequestError,
        match="does not require reverification",
    ):
        build_request(
            record=record,
            evaluation=evaluation,
            lifecycle_state=state,
        )


def test_fresh_evaluation_cannot_build_request(
    tmp_path,
):
    database_path = tmp_path / "verification.db"

    _, record = persist_record(
        database_path
    )

    lifecycle = (
        GovernanceInterventionVerificationLifecycleLedger(
            database_path=database_path
        )
    )

    lifecycle.activate(
        tenant_id=record.tenant_id,
        verification_record_hash=record.record_hash,
    )

    state = lifecycle.get_current_state(
        tenant_id=record.tenant_id,
        verification_record_hash=record.record_hash,
    )

    evaluation = evaluate(
        record
    )

    with pytest.raises(
        GovernanceInterventionReverificationRequestError,
        match="does not require reverification",
    ):
        build_request(
            record=record,
            evaluation=evaluation,
            lifecycle_state=state,
        )


def test_active_lifecycle_state_cannot_build_request(
    tmp_path,
):
    database_path = tmp_path / "verification.db"

    _, record = persist_record(
        database_path
    )

    lifecycle = (
        GovernanceInterventionVerificationLifecycleLedger(
            database_path=database_path
        )
    )

    lifecycle.activate(
        tenant_id=record.tenant_id,
        verification_record_hash=record.record_hash,
    )

    state = lifecycle.get_current_state(
        tenant_id=record.tenant_id,
        verification_record_hash=record.record_hash,
    )

    evaluation = evaluate(
        record,
        current_policy_hash="policy-b",
    )

    with pytest.raises(
        GovernanceInterventionReverificationRequestError,
        match="lifecycle state is not REVERIFICATION_REQUIRED",
    ):
        build_request(
            record=record,
            evaluation=evaluation,
            lifecycle_state=state,
        )


def test_tampered_record_is_rejected(
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

    _, state = activate_and_apply(
        database_path,
        record,
        evaluation,
    )

    tampered = replace(
        record,
        intervention_id="tampered",
    )

    with pytest.raises(
        GovernanceInterventionReverificationRequestIntegrityError,
        match="record failed deterministic verification",
    ):
        build_request(
            record=tampered,
            evaluation=evaluation,
            lifecycle_state=state,
        )


def test_tampered_freshness_evaluation_is_rejected(
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

    _, state = activate_and_apply(
        database_path,
        record,
        evaluation,
    )

    tampered = replace(
        evaluation,
        freshness_disposition="FRESH",
    )

    with pytest.raises(
        GovernanceInterventionReverificationRequestIntegrityError,
        match="freshness evaluation failed deterministic verification",
    ):
        build_request(
            record=record,
            evaluation=tampered,
            lifecycle_state=state,
        )


def test_cross_tenant_freshness_binding_is_rejected(
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

    _, state = activate_and_apply(
        database_path,
        record,
        evaluation,
    )

    payload = evaluation.payload()
    payload["tenant_id"] = "tenant-b"

    tampered = replace(
        evaluation,
        tenant_id="tenant-b",
        freshness_evaluation_hash=sha256_hex(
            canonical_json(payload)
        ),
    )

    assert tampered.verify() is True

    with pytest.raises(
        GovernanceInterventionReverificationRequestIntegrityError,
        match="freshness tenant binding",
    ):
        build_request(
            record=record,
            evaluation=tampered,
            lifecycle_state=state,
        )


def test_cross_intervention_lifecycle_binding_is_rejected(
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

    _, state = activate_and_apply(
        database_path,
        record,
        evaluation,
    )

    tampered_state = replace(
        state,
        intervention_id="other-intervention",
    )

    with pytest.raises(
        GovernanceInterventionReverificationRequestIntegrityError,
        match="lifecycle intervention binding",
    ):
        build_request(
            record=record,
            evaluation=evaluation,
            lifecycle_state=tampered_state,
        )


def test_wrong_record_lifecycle_binding_is_rejected(
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

    _, state = activate_and_apply(
        database_path,
        record,
        evaluation,
    )

    tampered_state = replace(
        state,
        verification_record_hash="wrong-record",
    )

    with pytest.raises(
        GovernanceInterventionReverificationRequestIntegrityError,
        match="lifecycle verification record binding",
    ):
        build_request(
            record=record,
            evaluation=evaluation,
            lifecycle_state=tampered_state,
        )


def test_blank_lifecycle_event_hash_is_rejected(
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

    _, state = activate_and_apply(
        database_path,
        record,
        evaluation,
    )

    tampered_state = replace(
        state,
        lifecycle_event_hash="   ",
    )

    with pytest.raises(
        GovernanceInterventionReverificationRequestIntegrityError,
        match="lifecycle event hash is required",
    ):
        build_request(
            record=record,
            evaluation=evaluation,
            lifecycle_state=tampered_state,
        )


def test_request_is_deterministic(
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

    _, state = activate_and_apply(
        database_path,
        record,
        evaluation,
    )

    first = build_request(
        record=record,
        evaluation=evaluation,
        lifecycle_state=state,
    )

    second = build_request(
        record=record,
        evaluation=evaluation,
        lifecycle_state=state,
    )

    assert first == second
    assert first.request_hash == second.request_hash


def test_request_hash_detects_tampering(
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

    _, state = activate_and_apply(
        database_path,
        record,
        evaluation,
    )

    request = build_request(
        record=record,
        evaluation=evaluation,
        lifecycle_state=state,
    )

    tampered = replace(
        request,
        reverification_scope="FULL",
    )

    assert request.verify() is True
    assert tampered.verify() is False


def test_request_binds_exact_lineage(
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

    _, state = activate_and_apply(
        database_path,
        record,
        evaluation,
    )

    request = build_request(
        record=record,
        evaluation=evaluation,
        lifecycle_state=state,
    )

    assert (
        request.verification_record_hash
        == record.record_hash
    )

    assert (
        request.freshness_evaluation_hash
        == evaluation.freshness_evaluation_hash
    )

    assert (
        request.lifecycle_event_hash
        == state.lifecycle_event_hash
    )


def test_request_does_not_mutate_verification_record(
    tmp_path,
):
    database_path = tmp_path / "verification.db"

    summary, record = persist_record(
        database_path
    )

    evaluation = evaluate(
        record,
        current_policy_hash="policy-b",
    )

    _, state = activate_and_apply(
        database_path,
        record,
        evaluation,
    )

    build_request(
        record=record,
        evaluation=evaluation,
        lifecycle_state=state,
    )

    ledger = GovernanceInterventionVerificationLedger(
        database_path
    )

    stored = ledger.get_by_summary_hash(
        tenant_id=record.tenant_id,
        verification_summary_hash=(
            summary.verification_summary_hash
        ),
    )

    assert stored == record


def test_request_builder_does_not_change_lifecycle_history(
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

    lifecycle, state = activate_and_apply(
        database_path,
        record,
        evaluation,
    )

    before = lifecycle.list_history(
        tenant_id=record.tenant_id,
        verification_record_hash=record.record_hash,
    )

    build_request(
        record=record,
        evaluation=evaluation,
        lifecycle_state=state,
    )

    after = lifecycle.list_history(
        tenant_id=record.tenant_id,
        verification_record_hash=record.record_hash,
    )

    assert after == before


def test_request_contains_no_execution_or_outcome_claims(
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

    _, state = activate_and_apply(
        database_path,
        record,
        evaluation,
    )

    request = build_request(
        record=record,
        evaluation=evaluation,
        lifecycle_state=state,
    )

    payload = request.to_dict()

    forbidden = {
        "executed",
        "execution_status",
        "reverified",
        "reverification_completed",
        "verification_disposition",
        "success",
        "failure",
        "causation",
        "causal_effect",
        "authorized",
        "rollback",
        "continue_intervention",
        "recommended_action",
        "next_action",
    }

    assert forbidden.isdisjoint(payload)


def test_request_builder_has_no_execution_or_mutation_methods():
    actual_methods = {
        name
        for name in dir(
            GovernanceInterventionReverificationRequestBuilder
        )
        if not name.startswith("_")
    }

    forbidden_methods = {
        "execute",
        "actuate",
        "authorize",
        "reverify",
        "verify_outcome",
        "mark_stale",
        "require_reverification",
        "supersede",
        "rollback",
        "continue_intervention",
    }

    assert forbidden_methods.isdisjoint(
        actual_methods
    )