from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from backend.app.gagf.governance_commercial_paid_assessment_approved_delivery_store import (
    CommercialPaidAssessmentApprovedDeliveryStoreError,
    GovernanceCommercialPaidAssessmentApprovedDeliveryStore,
)
from backend.app.gagf.governance_commercial_paid_assessment_delivery_approval_handoff import (
    GovernanceCommercialPaidAssessmentDeliveryApprovalHandoffService,
)
from backend.app.gagf.governance_commercial_paid_assessment_delivery_readiness import (
    GovernanceCommercialPaidAssessmentDeliveryReadinessService,
)
from backend.app.gagf.governance_commercial_paid_assessment_execution import (
    GovernanceCommercialPaidAssessmentExecutionService,
)
from tests.test_governance_commercial_paid_assessment_delivery_approval_handoff import (
    HIERARCHY,
    build_completed_assessment,
    valid_approval_payload,
)


def build_handoff(
    tmp_path: Path,
):
    execution_service = build_completed_assessment(tmp_path)

    readiness_service = (
        GovernanceCommercialPaidAssessmentDeliveryReadinessService(
            execution_service=execution_service
        )
    )

    service = (
        GovernanceCommercialPaidAssessmentDeliveryApprovalHandoffService(
            readiness_service=readiness_service
        )
    )

    result = service.handoff(
        **HIERARCHY,
        approval_payload=valid_approval_payload(
            execution_service
        ),
    )

    store = GovernanceCommercialPaidAssessmentApprovedDeliveryStore(
        execution_service.execution_directory
        / "commercial-paid-assessment-approved-deliveries.sqlite3"
    )

    return execution_service, result, store


def test_explicit_approval_is_persisted_as_exact_real_handoff(
    tmp_path: Path,
) -> None:
    _, result, store = build_handoff(tmp_path)

    snapshot = store.get(**HIERARCHY)

    assert snapshot is not None
    payload = snapshot.approved_delivery_payload

    assert payload["operator_handoff_passed"] is True
    assert payload["approved_for_human_delivery"] is True
    assert payload["result"] == result.handoff.to_dict()
    assert (
        payload["result"]["handoff_status"]
        == "approved_for_human_delivery"
    )
    assert (
        payload["result"]["delivery_envelope"][
            "delivery_status"
        ]
        == "approved_for_human_delivery"
    )


def test_approved_delivery_snapshot_survives_restart(
    tmp_path: Path,
) -> None:
    execution_service, result, _ = build_handoff(tmp_path)

    restarted_store = GovernanceCommercialPaidAssessmentApprovedDeliveryStore(
        execution_service.execution_directory
        / "commercial-paid-assessment-approved-deliveries.sqlite3"
    )

    snapshot = restarted_store.get(**HIERARCHY)

    assert snapshot is not None
    assert (
        snapshot.approved_delivery_payload["result"][
            "delivery_envelope"
        ]["envelope_hash"]
        == result.handoff.delivery_envelope.envelope_hash
    )


def test_identical_approval_persistence_is_idempotent(
    tmp_path: Path,
) -> None:
    execution_service, result, store = build_handoff(tmp_path)

    readiness = (
        GovernanceCommercialPaidAssessmentDeliveryReadinessService(
            execution_service=execution_service
        )
        .verify(**HIERARCHY)
    )

    first = store.get(**HIERARCHY)
    assert first is not None

    second = store.put(
        **HIERARCHY,
        execution_status_hash=readiness.execution_status_hash,
        operator_snapshot_hash=readiness.operator_snapshot_hash,
        approved_delivery_payload={
            "operator_handoff_passed": True,
            "approved_for_human_delivery": True,
            "result": result.handoff.to_dict(),
            "boundaries": {
                "commercial_wrapper_is_not_approval_authority": True,
                "real_approval_handoff_remains_authoritative": True,
                "pa003_remains_delivery_envelope_authority": True,
                "operator_handoff_passed_is_not_delivery": True,
                "approved_for_human_delivery_is_not_delivery": True,
            },
        },
    )

    assert second.snapshot_hash == first.snapshot_hash


def test_different_approval_material_cannot_replace_existing_snapshot(
    tmp_path: Path,
) -> None:
    execution_service, result, store = build_handoff(tmp_path)

    readiness = (
        GovernanceCommercialPaidAssessmentDeliveryReadinessService(
            execution_service=execution_service
        )
        .verify(**HIERARCHY)
    )

    changed = {
        "operator_handoff_passed": True,
        "approved_for_human_delivery": True,
        "result": result.handoff.to_dict(),
        "boundaries": {
            "commercial_wrapper_is_not_approval_authority": True,
            "real_approval_handoff_remains_authoritative": True,
            "pa003_remains_delivery_envelope_authority": True,
            "operator_handoff_passed_is_not_delivery": True,
            "approved_for_human_delivery_is_not_delivery": True,
        },
    }
    changed["result"]["delivery_approval"][
        "approved_by"
    ] = "Different Reviewer"

    with pytest.raises(
        CommercialPaidAssessmentApprovedDeliveryStoreError,
        match="different governed approval material",
    ):
        store.put(
            **HIERARCHY,
            execution_status_hash=readiness.execution_status_hash,
            operator_snapshot_hash=readiness.operator_snapshot_hash,
            approved_delivery_payload=changed,
        )


def test_approved_delivery_snapshot_tampering_is_detected(
    tmp_path: Path,
) -> None:
    execution_service, _, _ = build_handoff(tmp_path)

    database_path = (
        execution_service.execution_directory
        / "commercial-paid-assessment-approved-deliveries.sqlite3"
    )

    with sqlite3.connect(database_path) as connection:
        connection.execute(
            """
            UPDATE governance_commercial_paid_assessment_approved_deliveries
            SET approved_delivery_payload_hash = ?
            """,
            ("f" * 64,),
        )
        connection.commit()

    store = GovernanceCommercialPaidAssessmentApprovedDeliveryStore(
        database_path
    )

    with pytest.raises(
        CommercialPaidAssessmentApprovedDeliveryStoreError,
        match="payload hash verification failed",
    ):
        store.get(**HIERARCHY)
