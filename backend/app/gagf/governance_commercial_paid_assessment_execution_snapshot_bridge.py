from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from backend.app.gagf.governance_commercial_paid_assessment_execution_status import (
    GovernanceCommercialPaidAssessmentExecutionStatusStore,
)
from backend.app.gagf.governance_commercial_paid_assessment_operator_result_store import (
    CommercialPaidAssessmentOperatorResultSnapshot,
    CommercialPaidAssessmentOperatorResultStoreError,
    GovernanceCommercialPaidAssessmentOperatorResultStore,
)
from backend.app.gagf.governance_real_paid_assessment_execution_recovery import (
    RealPaidAssessmentExecutionRecoveryResult,
)


COMMERCIAL_PAID_ASSESSMENT_EXECUTION_SNAPSHOT_BRIDGE_ID = (
    "governance-commercial-paid-assessment-execution-snapshot-bridge"
)
COMMERCIAL_PAID_ASSESSMENT_EXECUTION_SNAPSHOT_BRIDGE_VERSION = "0.1.0"
COMMERCIAL_PAID_ASSESSMENT_EXECUTION_SNAPSHOT_BRIDGE_SCHEMA_VERSION = "1.0.0"


class CommercialPaidAssessmentExecutionSnapshotBridgeError(RuntimeError):
    """Raised when a successful PA015 result cannot be bound durably."""


class CommercialPaidAssessmentExecutionSnapshotSource(Protocol):
    """
    Minimal commercial-execution interface required by the snapshot bridge.

    This protocol prevents a circular import when the concrete execution
    service imports this bridge for automatic post-execution capture.
    """

    execution_directory: Path

    @property
    def status_store(
        self,
    ) -> GovernanceCommercialPaidAssessmentExecutionStatusStore:
        ...


@dataclass(frozen=True, slots=True)
class CommercialPaidAssessmentExecutionSnapshotBridgeResult:
    snapshot: CommercialPaidAssessmentOperatorResultSnapshot

    result_type: str = (
        COMMERCIAL_PAID_ASSESSMENT_EXECUTION_SNAPSHOT_BRIDGE_ID
    )
    version: str = (
        COMMERCIAL_PAID_ASSESSMENT_EXECUTION_SNAPSHOT_BRIDGE_VERSION
    )
    schema_version: str = (
        COMMERCIAL_PAID_ASSESSMENT_EXECUTION_SNAPSHOT_BRIDGE_SCHEMA_VERSION
    )

    @property
    def hierarchy_key(self) -> str:
        return self.snapshot.hierarchy_key

    def to_dict(self) -> dict[str, Any]:
        return {
            "result_type": self.result_type,
            "version": self.version,
            "schema_version": self.schema_version,
            "hierarchy_key": self.hierarchy_key,
            "snapshot_hash": self.snapshot.snapshot_hash,
            "operator_result_hash": self.snapshot.operator_result_hash,
            "execution_status_hash": self.snapshot.execution_status_hash,
            "boundaries": {
                "bridge_is_not_execution_authority": True,
                "bridge_is_not_recovery_authority": True,
                "bridge_is_not_delivery_readiness": True,
                "bridge_is_not_delivery_approval": True,
                "bridge_is_not_delivery": True,
                "pa015_result_is_reused_without_reexecution": True,
                "durable_status_must_preexist_snapshot": True,
            },
        }


class GovernanceCommercialPaidAssessmentExecutionSnapshotBridgeService:
    """
    Bind a successful PA015 recovery result to the durable commercial
    execution-status record and persist an internal CLI-compatible operator
    result snapshot.

    PA015 remains execution/recovery authority.
    The 04D status store remains durable commercial execution-state authority.
    This service does not execute, recover, approve delivery, or deliver.
    """

    def __init__(
        self,
        *,
        execution_service: CommercialPaidAssessmentExecutionSnapshotSource,
        snapshot_store: (
            GovernanceCommercialPaidAssessmentOperatorResultStore | None
        ) = None,
    ) -> None:
        execution_directory = getattr(
            execution_service,
            "execution_directory",
            None,
        )
        status_store = getattr(
            execution_service,
            "status_store",
            None,
        )

        if not isinstance(
            execution_directory,
            Path,
        ):
            raise CommercialPaidAssessmentExecutionSnapshotBridgeError(
                "execution_service must expose execution_directory as Path"
            )

        if not isinstance(
            status_store,
            GovernanceCommercialPaidAssessmentExecutionStatusStore,
        ):
            raise CommercialPaidAssessmentExecutionSnapshotBridgeError(
                "execution_service must expose a governed execution status store"
            )

        self._execution_service = execution_service
        self.snapshot_store = (
            snapshot_store
            if snapshot_store is not None
            else GovernanceCommercialPaidAssessmentOperatorResultStore(
                database_path=(
                    Path(execution_service.execution_directory)
                    / "commercial-paid-assessment-operator-results.sqlite3"
                )
            )
        )

    def capture(
        self,
        *,
        result: RealPaidAssessmentExecutionRecoveryResult,
    ) -> CommercialPaidAssessmentExecutionSnapshotBridgeResult:
        if not isinstance(
            result,
            RealPaidAssessmentExecutionRecoveryResult,
        ):
            raise CommercialPaidAssessmentExecutionSnapshotBridgeError(
                "result must be a RealPaidAssessmentExecutionRecoveryResult"
            )

        attempt = result.attempt

        status = self._execution_service.status_store.get_status(
            tenant_id=attempt.tenant_id,
            client_id=attempt.client_id,
            engagement_id=attempt.engagement_id,
            assessment_id=attempt.assessment_id,
        )

        if status is None:
            raise CommercialPaidAssessmentExecutionSnapshotBridgeError(
                "durable commercial paid execution status was not found"
            )

        if status.hierarchy_key != attempt.hierarchy_key:
            raise CommercialPaidAssessmentExecutionSnapshotBridgeError(
                "durable execution status hierarchy mismatch"
            )

        if status.disposition != result.disposition:
            raise CommercialPaidAssessmentExecutionSnapshotBridgeError(
                "durable execution status disposition mismatch"
            )

        if status.attempt_hash != attempt.attempt_hash:
            raise CommercialPaidAssessmentExecutionSnapshotBridgeError(
                "durable execution status attempt hash mismatch"
            )

        if status.attempt_record_hash != attempt.record_hash:
            raise CommercialPaidAssessmentExecutionSnapshotBridgeError(
                "durable execution status attempt record hash mismatch"
            )

        if (
            status.assessment_execution_request_hash
            != attempt.assessment_execution_request_hash
        ):
            raise CommercialPaidAssessmentExecutionSnapshotBridgeError(
                "durable execution status request hash mismatch"
            )

        if status.artifact_count_before != result.artifact_count_before:
            raise CommercialPaidAssessmentExecutionSnapshotBridgeError(
                "durable execution status artifact_count_before mismatch"
            )

        if status.artifact_count_after != result.artifact_count_after:
            raise CommercialPaidAssessmentExecutionSnapshotBridgeError(
                "durable execution status artifact_count_after mismatch"
            )

        operator_result = {
            "operator_run_passed": True,
            "result": result.to_dict(),
            "boundaries": {
                "commercial_bridge_reuses_pa015_result": True,
                "operator_snapshot_is_not_execution_authority": True,
                "operator_snapshot_is_not_recovery_authority": True,
                "operator_snapshot_is_not_delivery_readiness": True,
                "operator_snapshot_is_not_delivery_approval": True,
                "operator_snapshot_is_not_delivery": True,
            },
        }

        try:
            snapshot = self.snapshot_store.put(
                tenant_id=attempt.tenant_id,
                client_id=attempt.client_id,
                engagement_id=attempt.engagement_id,
                assessment_id=attempt.assessment_id,
                execution_status_hash=status.status_hash,
                execution_input_binding_hash=(
                    status.execution_input_binding_hash
                ),
                assessment_execution_request_hash=(
                    status.assessment_execution_request_hash
                ),
                operator_result=operator_result,
            )
        except CommercialPaidAssessmentOperatorResultStoreError as exc:
            raise CommercialPaidAssessmentExecutionSnapshotBridgeError(
                "durable PA015 operator-result snapshot failed: "
                f"{exc}"
            ) from exc

        return CommercialPaidAssessmentExecutionSnapshotBridgeResult(
            snapshot=snapshot
        )
