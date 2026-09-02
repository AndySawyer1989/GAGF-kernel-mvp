from __future__ import annotations

from pathlib import Path

from backend.app.gagf.governance_commercial_paid_assessment_execution import (
    GovernanceCommercialPaidAssessmentExecutionService,
)
from backend.app.gagf.governance_commercial_paid_assessment_operator_result_store import (
    GovernanceCommercialPaidAssessmentOperatorResultStore,
)
from tests.test_governance_commercial_paid_assessment_execution import (
    BINDING_HASH,
    build_execution_input,
)


def build_service_and_store(
    tmp_path: Path,
) -> tuple[
    GovernanceCommercialPaidAssessmentExecutionService,
    GovernanceCommercialPaidAssessmentOperatorResultStore,
]:
    execution_directory = tmp_path / "paid-assessments"

    service = GovernanceCommercialPaidAssessmentExecutionService(
        execution_directory=execution_directory
    )

    store = GovernanceCommercialPaidAssessmentOperatorResultStore(
        database_path=(
            execution_directory
            / "commercial-paid-assessment-operator-results.sqlite3"
        )
    )

    return service, store


def test_successful_commercial_execution_automatically_creates_operator_snapshot(
    tmp_path: Path,
) -> None:
    service, store = build_service_and_store(tmp_path)

    database_path = service.database_path_for_hierarchy(
        tenant_id="tenant-001",
        client_id="client-001",
        engagement_id="engagement-001",
        assessment_id="assessment-001",
    )

    execution_input = build_execution_input(
        database_path
    )

    result = service.execute(
        execution_input=execution_input,
        execution_input_binding_hash=BINDING_HASH,
    )

    snapshot = store.get(
        tenant_id="tenant-001",
        client_id="client-001",
        engagement_id="engagement-001",
        assessment_id="assessment-001",
    )

    assert snapshot is not None
    assert snapshot.hierarchy_key == result.attempt.hierarchy_key
    assert (
        snapshot.execution_input_binding_hash
        == BINDING_HASH
    )
    assert (
        snapshot.assessment_execution_request_hash
        == result.attempt.assessment_execution_request_hash
    )
    assert (
        snapshot.operator_result["operator_run_passed"]
        is True
    )
    assert (
        snapshot.operator_result["result"]
        == result.to_dict()
    )
    assert (
        snapshot.operator_result["result"]["disposition"]
        == "executed"
    )

    status = service.status_store.get_status(
        tenant_id="tenant-001",
        client_id="client-001",
        engagement_id="engagement-001",
        assessment_id="assessment-001",
    )

    assert status is not None
    assert (
        snapshot.execution_status_hash
        == status.status_hash
    )


def test_exact_repeat_advances_snapshot_to_reconciled_without_new_attempt(
    tmp_path: Path,
) -> None:
    service, store = build_service_and_store(tmp_path)

    database_path = service.database_path_for_hierarchy(
        tenant_id="tenant-001",
        client_id="client-001",
        engagement_id="engagement-001",
        assessment_id="assessment-001",
    )

    execution_input = build_execution_input(
        database_path
    )

    first = service.execute(
        execution_input=execution_input,
        execution_input_binding_hash=BINDING_HASH,
    )

    first_snapshot = store.get(
        tenant_id="tenant-001",
        client_id="client-001",
        engagement_id="engagement-001",
        assessment_id="assessment-001",
    )

    assert first_snapshot is not None

    second = service.execute(
        execution_input=execution_input,
        execution_input_binding_hash=BINDING_HASH,
    )

    second_snapshot = store.get(
        tenant_id="tenant-001",
        client_id="client-001",
        engagement_id="engagement-001",
        assessment_id="assessment-001",
    )

    assert second_snapshot is not None

    assert first.disposition == "executed"
    assert second.disposition == "reconciled"

    assert (
        first.attempt.attempt_hash
        == second.attempt.attempt_hash
    )
    assert (
        first.attempt.record_hash
        == second.attempt.record_hash
    )

    assert (
        second_snapshot.operator_result["result"]["disposition"]
        == "reconciled"
    )
    assert (
        second_snapshot.operator_result["result"]["attempt_hash"]
        == first.attempt.attempt_hash
    )
    assert (
        second_snapshot.operator_result["result"]["record_hash"]
        == first.attempt.record_hash
    )

    assert (
        second_snapshot.execution_input_binding_hash
        == first_snapshot.execution_input_binding_hash
    )
    assert (
        second_snapshot.assessment_execution_request_hash
        == first_snapshot.assessment_execution_request_hash
    )

    assert (
        second_snapshot.snapshot_hash
        != first_snapshot.snapshot_hash
    )

    status = service.status_store.get_status(
        tenant_id="tenant-001",
        client_id="client-001",
        engagement_id="engagement-001",
        assessment_id="assessment-001",
    )

    assert status is not None
    assert status.disposition == "reconciled"
    assert (
        second_snapshot.execution_status_hash
        == status.status_hash
    )
