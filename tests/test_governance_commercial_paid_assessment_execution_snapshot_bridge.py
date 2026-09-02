from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from backend.app.gagf.governance_commercial_paid_assessment_execution import (
    GovernanceCommercialPaidAssessmentExecutionService,
)
from backend.app.gagf.governance_commercial_paid_assessment_execution_snapshot_bridge import (
    CommercialPaidAssessmentExecutionSnapshotBridgeError,
    GovernanceCommercialPaidAssessmentExecutionSnapshotBridgeService,
)
from tests.test_governance_commercial_paid_assessment_execution import (
    build_execution_input,
)


BINDING_HASH = "b" * 64


def build_executed(tmp_path: Path):
    execution_directory = tmp_path / "paid-assessments"

    service = GovernanceCommercialPaidAssessmentExecutionService(
        execution_directory=execution_directory
    )

    database_path = service.database_path_for_hierarchy(
        tenant_id="tenant-001",
        client_id="client-001",
        engagement_id="engagement-001",
        assessment_id="assessment-001",
    )

    execution_input = build_execution_input(database_path)

    result = service.execute(
        execution_input=execution_input,
        execution_input_binding_hash=BINDING_HASH,
    )

    return service, result


def test_bridge_captures_exact_successful_pa015_result(tmp_path):
    service, result = build_executed(tmp_path)

    bridge = (
        GovernanceCommercialPaidAssessmentExecutionSnapshotBridgeService(
            execution_service=service
        )
    )

    captured = bridge.capture(result=result)

    stored = bridge.snapshot_store.get(
        tenant_id="tenant-001",
        client_id="client-001",
        engagement_id="engagement-001",
        assessment_id="assessment-001",
    )

    assert stored is not None
    assert stored.snapshot_hash == captured.snapshot.snapshot_hash
    assert stored.operator_result["operator_run_passed"] is True
    assert stored.operator_result["result"] == result.to_dict()


def test_bridge_binds_snapshot_to_durable_status_hash(tmp_path):
    service, result = build_executed(tmp_path)

    status = service.status_store.get_status(
        tenant_id="tenant-001",
        client_id="client-001",
        engagement_id="engagement-001",
        assessment_id="assessment-001",
    )
    assert status is not None

    bridge = (
        GovernanceCommercialPaidAssessmentExecutionSnapshotBridgeService(
            execution_service=service
        )
    )

    captured = bridge.capture(result=result)

    assert (
        captured.snapshot.execution_status_hash
        == status.status_hash
    )
    assert (
        captured.snapshot.execution_input_binding_hash
        == status.execution_input_binding_hash
    )
    assert (
        captured.snapshot.assessment_execution_request_hash
        == status.assessment_execution_request_hash
    )


def test_bridge_requires_durable_execution_status(tmp_path):
    service, result = build_executed(tmp_path)

    with sqlite3.connect(
        service.status_store.database_path
    ) as connection:
        connection.execute(
            """
            DELETE FROM governance_commercial_paid_assessment_execution_status
            """
        )
        connection.commit()

    bridge = (
        GovernanceCommercialPaidAssessmentExecutionSnapshotBridgeService(
            execution_service=service
        )
    )

    with pytest.raises(
        CommercialPaidAssessmentExecutionSnapshotBridgeError,
        match="status was not found",
    ):
        bridge.capture(result=result)


def test_bridge_rejects_status_disposition_mismatch(tmp_path):
    service, result = build_executed(tmp_path)

    with sqlite3.connect(
        service.status_store.database_path
    ) as connection:
        connection.execute(
            """
            UPDATE governance_commercial_paid_assessment_execution_status
            SET disposition = 'resumed'
            """
        )
        connection.commit()

    bridge = (
        GovernanceCommercialPaidAssessmentExecutionSnapshotBridgeService(
            execution_service=service
        )
    )

    with pytest.raises(Exception):
        bridge.capture(result=result)


def test_bridge_is_idempotent_for_same_pa015_result(tmp_path):
    service, result = build_executed(tmp_path)

    bridge = (
        GovernanceCommercialPaidAssessmentExecutionSnapshotBridgeService(
            execution_service=service
        )
    )

    first = bridge.capture(result=result)
    second = bridge.capture(result=result)

    assert first.snapshot.snapshot_hash == second.snapshot.snapshot_hash


def test_bridge_does_not_mutate_paid_assessment_database(tmp_path):
    service, result = build_executed(tmp_path)

    database_path = service.database_path_for_hierarchy(
        tenant_id="tenant-001",
        client_id="client-001",
        engagement_id="engagement-001",
        assessment_id="assessment-001",
    )

    before = database_path.read_bytes()

    bridge = (
        GovernanceCommercialPaidAssessmentExecutionSnapshotBridgeService(
            execution_service=service
        )
    )

    bridge.capture(result=result)

    after = database_path.read_bytes()

    assert after == before
