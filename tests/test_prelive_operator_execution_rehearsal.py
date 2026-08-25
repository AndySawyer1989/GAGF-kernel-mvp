from __future__ import annotations

from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from backend.app.gagf.governance_assessment_repository import (
    GovernanceAssessmentRepository,
)
from backend.app.gagf.governance_paid_assessment_execution_handoff import (
    PaidAssessmentExecutionHandoff,
)
from backend.app.gagf.prelive_blind_assessment import (
    PreliveScenarioError,
)
from backend.app.gagf.prelive_operator_execution_rehearsal import (
    PRELIVE_OPERATOR_EXECUTION_AUTHORITY,
    PRELIVE_OPERATOR_EXECUTION_REHEARSAL_STATUS,
    PreliveOperatorExecutionConfirmation,
    PreliveOperatorExecutionRehearsal,
)
from tests.test_prelive_blind_assessment import (
    build_scenario,
)
from tests.test_prelive_execution_handoff_bridge import (
    build_authorization,
    build_contract_event,
    build_metadata,
)


def prepare_rehearsal():
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

    return rehearsal, prepared


def build_confirmation(
    prepared,
    **overrides,
) -> PreliveOperatorExecutionConfirmation:
    values = {
        "operator_id":
            "PRELIVE Human Operator",
        "confirmed_at":
            "2026-08-24T21:30:00-04:00",
        "handoff_hash":
            prepared.handoff.handoff_hash,
        "assessment_execution_request_hash":
            (
                prepared.handoff
                .assessment_execution_request_hash
            ),
        "execution_confirmed":
            True,
    }

    values.update(overrides)

    return PreliveOperatorExecutionConfirmation(
        **values
    )


def execute_rehearsal(
    tmp_path: Path,
):
    rehearsal, prepared = prepare_rehearsal()

    result = rehearsal.execute_prepared(
        database_path=(
            tmp_path
            / "prelive-execution-rehearsal.sqlite3"
        ),
        prepared=prepared,
        operator_confirmation=(
            build_confirmation(prepared)
        ),
    )

    return prepared, result


def test_executes_real_governance_assessment_application(
    tmp_path,
):
    prepared, result = execute_rehearsal(
        tmp_path
    )

    assert (
        result.execution_result
        .application_completed
        is True
    )

    assert (
        result.execution_result
        .handoff_hash
        == prepared.handoff.handoff_hash
    )


def test_execution_preserves_full_hierarchy(
    tmp_path,
):
    _, result = execute_rehearsal(
        tmp_path
    )

    assert (
        result.execution_result.hierarchy_key
        == (
            "synthetic-tenant/"
            "prelive-client/"
            "prelive-engagement/"
            "prelive-assessment"
        )
    )


def test_execution_preserves_request_hash(
    tmp_path,
):
    prepared, result = execute_rehearsal(
        tmp_path
    )

    expected_hash = (
        prepared.handoff
        .assessment_execution_request_hash
    )

    assert (
        result.execution_result
        .assessment_execution_request_hash
        == expected_hash
    )

    assert (
        result.execution_result
        .application_request_hash
        == expected_hash
    )


def test_execution_preserves_application_lineage(
    tmp_path,
):
    _, result = execute_rehearsal(
        tmp_path
    )

    execution = result.execution_result

    assert len(
        execution.application_hash
    ) == 64

    assert len(
        execution.demonstration_hash
    ) == 64

    assert len(
        execution.persistence_hash
    ) == 64

    assert len(
        execution.execution_result_hash
    ) == 64

    assert execution.report_id

    assert execution.artifact_count == 10


def test_execution_persists_real_repository_artifacts(
    tmp_path,
):
    database_path = (
        tmp_path
        / "prelive-execution-rehearsal.sqlite3"
    )

    rehearsal, prepared = prepare_rehearsal()

    result = rehearsal.execute_prepared(
        database_path=database_path,
        prepared=prepared,
        operator_confirmation=(
            build_confirmation(prepared)
        ),
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

    assert repository.verify_chain(
        context=(
            prepared.request_bridge
            .request.context
        )
    ) is True

    assert (
        result.execution_result.artifact_count
        == len(artifacts)
    )


def test_rejects_wrong_handoff_hash_before_execution(
    tmp_path,
):
    rehearsal, prepared = prepare_rehearsal()

    confirmation = build_confirmation(
        prepared,
        handoff_hash="0" * 64,
    )

    database_path = (
        tmp_path
        / "should-not-execute.sqlite3"
    )

    with pytest.raises(
        PreliveScenarioError,
        match="handoff hash does not match",
    ):
        rehearsal.execute_prepared(
            database_path=database_path,
            prepared=prepared,
            operator_confirmation=(
                confirmation
            ),
        )

    assert not database_path.exists()


def test_rejects_wrong_request_hash_before_execution(
    tmp_path,
):
    rehearsal, prepared = prepare_rehearsal()

    confirmation = build_confirmation(
        prepared,
        assessment_execution_request_hash=(
            "0" * 64
        ),
    )

    database_path = (
        tmp_path
        / "should-not-execute.sqlite3"
    )

    with pytest.raises(
        PreliveScenarioError,
        match="request hash does not match",
    ):
        rehearsal.execute_prepared(
            database_path=database_path,
            prepared=prepared,
            operator_confirmation=(
                confirmation
            ),
        )

    assert not database_path.exists()


def test_rejects_non_explicit_operator_confirmation():
    rehearsal, prepared = prepare_rehearsal()

    with pytest.raises(
        PreliveScenarioError,
        match=(
            "operator execution confirmation "
            "must be explicit"
        ),
    ):
        build_confirmation(
            prepared,
            execution_confirmed=False,
        )


def test_rejects_non_confirmation_object(
    tmp_path,
):
    rehearsal, prepared = prepare_rehearsal()

    database_path = (
        tmp_path
        / "should-not-execute.sqlite3"
    )

    with pytest.raises(
        PreliveScenarioError,
        match=(
            "requires explicit operator "
            "execution confirmation"
        ),
    ):
        rehearsal.execute_prepared(
            database_path=database_path,
            prepared=prepared,
            operator_confirmation=object(),
        )

    assert not database_path.exists()


def test_rejects_non_prepared_handoff(
    tmp_path,
):
    rehearsal = (
        PreliveOperatorExecutionRehearsal()
    )

    confirmation = (
        PreliveOperatorExecutionConfirmation(
            operator_id="operator",
            confirmed_at=(
                "2026-08-24T21:30:00-04:00"
            ),
            handoff_hash="a" * 64,
            assessment_execution_request_hash=(
                "b" * 64
            ),
            execution_confirmed=True,
        )
    )

    with pytest.raises(
        PreliveScenarioError,
        match=(
            "requires a prepared execution "
            "handoff result"
        ),
    ):
        rehearsal.execute_prepared(
            database_path=(
                tmp_path / "unused.sqlite3"
            ),
            prepared=object(),
            operator_confirmation=(
                confirmation
            ),
        )


def test_result_does_not_claim_customer_outcome(
    tmp_path,
):
    _, result = execute_rehearsal(
        tmp_path
    )

    payload = result.to_dict()

    assert (
        payload["rehearsal_status"]
        == PRELIVE_OPERATOR_EXECUTION_REHEARSAL_STATUS
    )

    assert (
        payload["authority"]
        == PRELIVE_OPERATOR_EXECUTION_AUTHORITY
    )

    assert (
        payload["application_completed"]
        is True
    )

    forbidden_keys = {
        "customer_outcome_verified",
        "intervention_success",
        "intervention_failure",
        "causation_established",
        "roi_verified",
        "remediation_authorized",
        "rollback_authorized",
        "future_action_authorized",
        "production_onboarding_authorized",
    }

    assert forbidden_keys.isdisjoint(
        payload
    )

    assert forbidden_keys.isdisjoint(
        payload["execution_result"]
    )


def test_operator_confirmation_is_immutable():
    _, prepared = prepare_rehearsal()

    confirmation = build_confirmation(
        prepared
    )

    with pytest.raises(
        FrozenInstanceError
    ):
        confirmation.operator_id = (
            "changed"
        )


def test_result_is_immutable(
    tmp_path,
):
    _, result = execute_rehearsal(
        tmp_path
    )

    with pytest.raises(
        FrozenInstanceError
    ):
        result.authority = "changed"


def test_prepared_handoff_is_real_paid_assessment_handoff():
    _, prepared = prepare_rehearsal()

    assert isinstance(
        prepared.handoff,
        PaidAssessmentExecutionHandoff,
    )


def test_rehearsal_service_exposes_no_http_router():
    assert not hasattr(
        PreliveOperatorExecutionRehearsal,
        "router",
    )

    assert not hasattr(
        PreliveOperatorExecutionRehearsal,
        "create_router",
    )