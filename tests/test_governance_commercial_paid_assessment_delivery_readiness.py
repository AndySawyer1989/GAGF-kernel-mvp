from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from backend.app.gagf.governance_commercial_paid_assessment_delivery_readiness import (
    CommercialPaidAssessmentDeliveryReadinessError,
    GovernanceCommercialPaidAssessmentDeliveryReadinessService,
)
from backend.app.gagf.governance_commercial_paid_assessment_execution import (
    GovernanceCommercialPaidAssessmentExecutionService,
)
from tests.test_governance_commercial_paid_assessment_execution import (
    BINDING_HASH,
    build_execution_input,
)


HIERARCHY = {
    "tenant_id": "tenant-001",
    "client_id": "client-001",
    "engagement_id": "engagement-001",
    "assessment_id": "assessment-001",
}


def build_completed_assessment(
    tmp_path: Path,
) -> tuple[
    GovernanceCommercialPaidAssessmentExecutionService,
    object,
]:
    execution_directory = tmp_path / "paid-assessments"

    execution_service = (
        GovernanceCommercialPaidAssessmentExecutionService(
            execution_directory=execution_directory
        )
    )

    database_path = (
        execution_service.database_path_for_hierarchy(
            **HIERARCHY
        )
    )

    execution_input = build_execution_input(
        database_path
    )

    result = execution_service.execute(
        execution_input=execution_input,
        execution_input_binding_hash=BINDING_HASH,
    )

    return execution_service, result


def test_restart_safe_readiness_rehydrates_from_durable_snapshot(
    tmp_path: Path,
) -> None:
    execution_service, result = build_completed_assessment(
        tmp_path
    )

    restarted_execution_service = (
        GovernanceCommercialPaidAssessmentExecutionService(
            execution_directory=(
                execution_service.execution_directory
            )
        )
    )

    readiness_service = (
        GovernanceCommercialPaidAssessmentDeliveryReadinessService(
            execution_service=restarted_execution_service
        )
    )

    readiness = readiness_service.verify(
        **HIERARCHY
    )

    assert (
        readiness.readiness.delivery_readiness_status
        == "ready_for_delivery_approval_review"
    )
    assert readiness.readiness.repository_chain_valid is True
    assert readiness.readiness.artifact_count == 10

    assert (
        readiness.readiness.execution_result.hierarchy_key
        == result.attempt.hierarchy_key
    )
    assert (
        readiness.readiness.recovery_disposition
        == "executed"
    )

    safe = readiness.to_dict()

    assert (
        safe["delivery_readiness_status"]
        == "ready_for_delivery_approval_review"
    )
    assert safe["artifact_count"] == 10
    assert safe["repository_chain_valid"] is True
    assert safe["report_id"] == result.execution_result.report_id

    assert "execution_result" not in safe
    assert "report_package" not in safe
    assert "operator_result" not in safe
    assert "database_path" not in safe

    assert (
        safe["boundaries"][
            "existing_delivery_readiness_service_is_authoritative"
        ]
        is True
    )


def test_reconciled_repeat_is_restart_safe_for_readiness(
    tmp_path: Path,
) -> None:
    execution_service, first = build_completed_assessment(
        tmp_path
    )

    database_path = (
        execution_service.database_path_for_hierarchy(
            **HIERARCHY
        )
    )

    execution_input = build_execution_input(
        database_path
    )

    second = execution_service.execute(
        execution_input=execution_input,
        execution_input_binding_hash=BINDING_HASH,
    )

    assert first.disposition == "executed"
    assert second.disposition == "reconciled"

    restarted_execution_service = (
        GovernanceCommercialPaidAssessmentExecutionService(
            execution_directory=(
                execution_service.execution_directory
            )
        )
    )

    readiness = (
        GovernanceCommercialPaidAssessmentDeliveryReadinessService(
            execution_service=restarted_execution_service
        )
        .verify(
            **HIERARCHY
        )
    )

    assert (
        readiness.readiness.recovery_disposition
        == "reconciled"
    )
    assert (
        readiness.readiness.attempt_hash
        == second.attempt.attempt_hash
    )
    assert (
        readiness.readiness.recovery_record_hash
        == second.attempt.record_hash
    )

    assert (
        readiness.to_dict()["recovery_disposition"]
        == "reconciled"
    )


def test_readiness_requires_operator_snapshot(
    tmp_path: Path,
) -> None:
    execution_directory = tmp_path / "paid-assessments"

    execution_service = (
        GovernanceCommercialPaidAssessmentExecutionService(
            execution_directory=execution_directory
        )
    )

    service = (
        GovernanceCommercialPaidAssessmentDeliveryReadinessService(
            execution_service=execution_service
        )
    )

    with pytest.raises(
        CommercialPaidAssessmentDeliveryReadinessError,
        match="snapshot was not found",
    ):
        service.verify(
            **HIERARCHY
        )


def test_readiness_fails_closed_when_snapshot_status_binding_is_stale(
    tmp_path: Path,
) -> None:
    execution_service, _ = build_completed_assessment(
        tmp_path
    )

    snapshot_database = (
        execution_service.execution_directory
        / "commercial-paid-assessment-operator-results.sqlite3"
    )

    with sqlite3.connect(snapshot_database) as connection:
        connection.execute(
            """
            UPDATE governance_commercial_paid_assessment_operator_results
            SET execution_status_hash = ?
            """,
            ("f" * 64,),
        )
        connection.commit()

    service = (
        GovernanceCommercialPaidAssessmentDeliveryReadinessService(
            execution_service=execution_service
        )
    )

    with pytest.raises(
        CommercialPaidAssessmentDeliveryReadinessError,
        match="snapshot is invalid",
    ):
        service.verify(
            **HIERARCHY
        )


def test_readiness_verification_does_not_mutate_paid_database(
    tmp_path: Path,
) -> None:
    execution_service, _ = build_completed_assessment(
        tmp_path
    )

    database_path = (
        execution_service.database_path_for_hierarchy(
            **HIERARCHY
        )
    )

    before = database_path.read_bytes()

    service = (
        GovernanceCommercialPaidAssessmentDeliveryReadinessService(
            execution_service=execution_service
        )
    )

    service.verify(
        **HIERARCHY
    )

    after = database_path.read_bytes()

    assert after == before
