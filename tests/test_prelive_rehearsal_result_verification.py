from __future__ import annotations

import sqlite3
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from backend.app.gagf.governance_assessment_demonstration_persistence import (
    ARTIFACT_TYPE_ORDER,
)
from backend.app.gagf.governance_assessment_repository import (
    GovernanceAssessmentRepository,
)
from backend.app.gagf.prelive_blind_assessment import (
    PreliveScenarioError,
)
from backend.app.gagf.prelive_operator_execution_rehearsal import (
    PreliveOperatorExecutionConfirmation,
    PreliveOperatorExecutionRehearsal,
)
from backend.app.gagf.prelive_rehearsal_result_verification import (
    PRELIVE_REHEARSAL_VERIFICATION_AUTHORITY,
    PRELIVE_REHEARSAL_VERIFICATION_STATUS,
    PreliveRehearsalResultVerifier,
    find_forbidden_keys,
)
from tests.test_prelive_blind_assessment import (
    build_scenario,
)
from tests.test_prelive_execution_handoff_bridge import (
    build_authorization,
    build_contract_event,
    build_metadata,
)


def execute_blind_rehearsal(
    tmp_path: Path,
):
    database_path = (
        tmp_path
        / "prelive-verification.sqlite3"
    )

    rehearsal = (
        PreliveOperatorExecutionRehearsal()
    )

    prepared = rehearsal.prepare(
        scenario=build_scenario(),
        metadata=build_metadata(),
        contract_execution_event=(
            build_contract_event()
        ),
        paid_work_authorization=(
            build_authorization()
        ),
    )

    confirmation = (
        PreliveOperatorExecutionConfirmation(
            operator_id=(
                "PRELIVE Human Operator"
            ),
            confirmed_at=(
                "2026-08-24T21:45:00-04:00"
            ),
            handoff_hash=(
                prepared.handoff.handoff_hash
            ),
            assessment_execution_request_hash=(
                prepared.handoff
                .assessment_execution_request_hash
            ),
            execution_confirmed=True,
        )
    )

    result = rehearsal.execute_prepared(
        database_path=database_path,
        prepared=prepared,
        operator_confirmation=confirmation,
    )

    return (
        database_path,
        prepared,
        result,
    )


def verify_blind_rehearsal(
    tmp_path: Path,
):
    (
        database_path,
        prepared,
        execution,
    ) = execute_blind_rehearsal(
        tmp_path
    )

    verification = (
        PreliveRehearsalResultVerifier()
        .verify(
            database_path=database_path,
            rehearsal_result=execution,
        )
    )

    return (
        database_path,
        prepared,
        execution,
        verification,
    )


def test_verifies_completed_blind_rehearsal(
    tmp_path,
):
    (
        _,
        _,
        execution,
        verification,
    ) = verify_blind_rehearsal(
        tmp_path
    )

    assert (
        verification.verification_status
        == PRELIVE_REHEARSAL_VERIFICATION_STATUS
    )

    assert (
        verification.authority
        == PRELIVE_REHEARSAL_VERIFICATION_AUTHORITY
    )

    assert (
        verification.repository_chain_valid
        is True
    )

    assert (
        verification.artifact_count
        == execution.execution_result.artifact_count
    )

    assert (
        verification.oracle_leakage_detected
        is False
    )


def test_reloads_exact_persisted_artifact_contract(
    tmp_path,
):
    (
        database_path,
        prepared,
        _,
        verification,
    ) = verify_blind_rehearsal(
        tmp_path
    )

    repository = GovernanceAssessmentRepository(
        database_path
    )

    artifacts = repository.list_artifacts(
        context=(
            prepared.request_bridge
            .request.context
        )
    )

    assert len(artifacts) == 10

    assert (
        tuple(
            artifact.artifact_type
            for artifact in artifacts
        )
        == ARTIFACT_TYPE_ORDER
    )

    assert (
        verification.artifact_types
        == ARTIFACT_TYPE_ORDER
    )


def test_verifies_repository_chain_from_disk(
    tmp_path,
):
    (
        database_path,
        prepared,
        _,
        verification,
    ) = verify_blind_rehearsal(
        tmp_path
    )

    repository = GovernanceAssessmentRepository(
        database_path
    )

    assert repository.verify_chain(
        context=(
            prepared.request_bridge
            .request.context
        )
    ) is True

    assert (
        verification.repository_chain_valid
        is True
    )


def test_verifies_request_hash_lineage(
    tmp_path,
):
    (
        _,
        prepared,
        execution,
        verification,
    ) = verify_blind_rehearsal(
        tmp_path
    )

    assert (
        verification.request_hash
        == prepared.handoff
        .assessment_execution_request_hash
    )

    assert (
        verification.request_hash
        == execution.operator_confirmation
        .assessment_execution_request_hash
    )

    assert (
        verification.request_hash
        == execution.execution_result
        .assessment_execution_request_hash
    )

    assert (
        verification.request_hash
        == execution.execution_result
        .application_request_hash
    )


def test_verifies_handoff_hash_lineage(
    tmp_path,
):
    (
        _,
        prepared,
        execution,
        verification,
    ) = verify_blind_rehearsal(
        tmp_path
    )

    assert (
        verification.handoff_hash
        == prepared.handoff.handoff_hash
    )

    assert (
        verification.handoff_hash
        == execution.operator_confirmation
        .handoff_hash
    )

    assert (
        verification.handoff_hash
        == execution.execution_result
        .handoff_hash
    )


def test_reconstructs_all_execution_hashes(
    tmp_path,
):
    (
        _,
        _,
        execution,
        verification,
    ) = verify_blind_rehearsal(
        tmp_path
    )

    result = execution.execution_result

    assert (
        verification.demonstration_hash
        == result.demonstration_hash
    )

    assert (
        verification.persistence_hash
        == result.persistence_hash
    )

    assert (
        verification.application_hash
        == result.application_hash
    )

    assert (
        verification.execution_result_hash
        == result.execution_result_hash
    )


def test_verifies_persisted_report_identity(
    tmp_path,
):
    (
        database_path,
        prepared,
        execution,
        verification,
    ) = verify_blind_rehearsal(
        tmp_path
    )

    repository = GovernanceAssessmentRepository(
        database_path
    )

    reports = repository.list_artifacts(
        context=(
            prepared.request_bridge
            .request.context
        ),
        artifact_type=(
            "client-report-package"
        ),
    )

    assert len(reports) == 1

    assert (
        reports[0].payload["report_id"]
        == execution.execution_result.report_id
    )

    assert (
        verification.report_id
        == execution.execution_result.report_id
    )


def test_persisted_output_contains_no_oracle_keys(
    tmp_path,
):
    (
        database_path,
        prepared,
        _,
        verification,
    ) = verify_blind_rehearsal(
        tmp_path
    )

    repository = GovernanceAssessmentRepository(
        database_path
    )

    artifacts = repository.list_artifacts(
        context=(
            prepared.request_bridge
            .request.context
        )
    )

    findings: list[str] = []

    for artifact in artifacts:
        findings.extend(
            find_forbidden_keys(
                artifact.payload
            )
        )

    assert findings == []

    assert (
        verification.oracle_leakage_paths
        == ()
    )


def test_forbidden_key_scanner_detects_nested_oracle():
    payload = {
        "safe": {
            "nested": [
                {
                    "oracle":
                        "hidden answer"
                }
            ]
        }
    }

    findings = find_forbidden_keys(
        payload
    )

    assert findings == (
        "$.safe.nested[0].oracle",
    )


def test_second_verification_pass_is_deterministic(
    tmp_path,
):
    (
        database_path,
        _,
        execution,
        first,
    ) = verify_blind_rehearsal(
        tmp_path
    )

    second = (
        PreliveRehearsalResultVerifier()
        .verify(
            database_path=database_path,
            rehearsal_result=execution,
        )
    )

    assert second == first

    assert (
        second.verification_hash
        == first.verification_hash
    )


def test_verification_is_read_only(
    tmp_path,
):
    (
        database_path,
        prepared,
        execution,
    ) = execute_blind_rehearsal(
        tmp_path
    )

    repository = GovernanceAssessmentRepository(
        database_path
    )

    context = (
        prepared.request_bridge
        .request.context
    )

    before_assessment = (
        repository.get_assessment(
            context=context
        )
    )

    before_artifacts = (
        repository.list_artifacts(
            context=context
        )
    )

    verifier = (
        PreliveRehearsalResultVerifier()
    )

    verifier.verify(
        database_path=database_path,
        rehearsal_result=execution,
    )

    after_assessment = (
        repository.get_assessment(
            context=context
        )
    )

    after_artifacts = (
        repository.list_artifacts(
            context=context
        )
    )

    assert after_assessment == before_assessment

    assert after_artifacts == before_artifacts

    assert len(after_artifacts) == 10


def test_rejects_tampered_persisted_payload(
    tmp_path,
):
    (
        database_path,
        prepared,
        execution,
    ) = execute_blind_rehearsal(
        tmp_path
    )

    context = (
        prepared.request_bridge
        .request.context
    )

    with sqlite3.connect(
        database_path
    ) as connection:
        connection.execute(
            "UPDATE governance_assessment_artifacts "
            "SET payload_json = ? "
            "WHERE tenant_id = ? "
            "AND client_id = ? "
            "AND engagement_id = ? "
            "AND assessment_id = ? "
            "AND sequence_number = 1",
            (
                '{"tampered":true}',
                context.tenant_id,
                context.client_id,
                context.engagement_id,
                context.assessment_id,
            ),
        )

    with pytest.raises(
        PreliveScenarioError,
        match=(
            "persisted-result verification failed"
        ),
    ):
        (
            PreliveRehearsalResultVerifier()
            .verify(
                database_path=database_path,
                rehearsal_result=execution,
            )
        )


def test_rejects_non_rehearsal_result(
    tmp_path,
):
    with pytest.raises(
        PreliveScenarioError,
        match=(
            "requires a completed operator "
            "execution rehearsal result"
        ),
    ):
        (
            PreliveRehearsalResultVerifier()
            .verify(
                database_path=(
                    tmp_path / "unused.sqlite3"
                ),
                rehearsal_result=object(),
            )
        )


def test_verification_receipt_is_immutable(
    tmp_path,
):
    (
        _,
        _,
        _,
        verification,
    ) = verify_blind_rehearsal(
        tmp_path
    )

    with pytest.raises(
        FrozenInstanceError
    ):
        verification.authority = "changed"


def test_verification_does_not_claim_outcome_authority(
    tmp_path,
):
    (
        _,
        _,
        _,
        verification,
    ) = verify_blind_rehearsal(
        tmp_path
    )

    payload = verification.to_dict()

    forbidden_authority_claims = {
        "customer_outcome_verified",
        "intervention_success",
        "intervention_failure",
        "causation_established",
        "roi_verified",
        "remediation_success",
        "remediation_authorized",
        "rollback_authorized",
        "future_action_authorized",
        "production_onboarding_authorized",
    }

    assert forbidden_authority_claims.isdisjoint(
        payload
    )