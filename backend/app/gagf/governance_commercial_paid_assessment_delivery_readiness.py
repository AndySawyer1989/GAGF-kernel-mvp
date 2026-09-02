from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from backend.app.gagf.governance_commercial_paid_assessment_execution import (
    GovernanceCommercialPaidAssessmentExecutionService,
)
from backend.app.gagf.governance_commercial_paid_assessment_operator_result_store import (
    CommercialPaidAssessmentOperatorResultStoreError,
    GovernanceCommercialPaidAssessmentOperatorResultStore,
)
from backend.app.gagf.governance_real_paid_assessment_delivery_readiness import (
    GovernanceRealPaidAssessmentDeliveryReadinessService,
    RealPaidAssessmentDeliveryReadinessError,
    RealPaidAssessmentDeliveryReadinessResult,
)


COMMERCIAL_PAID_ASSESSMENT_DELIVERY_READINESS_ID = (
    "governance-commercial-paid-assessment-delivery-readiness"
)
COMMERCIAL_PAID_ASSESSMENT_DELIVERY_READINESS_VERSION = "0.1.0"
COMMERCIAL_PAID_ASSESSMENT_DELIVERY_READINESS_SCHEMA_VERSION = "1.0.0"

COMMERCIAL_PAID_ASSESSMENT_OPERATOR_RESULT_DATABASE = (
    "commercial-paid-assessment-operator-results.sqlite3"
)


class CommercialPaidAssessmentDeliveryReadinessError(RuntimeError):
    """Raised when commercial paid delivery readiness cannot be verified."""


@dataclass(frozen=True, slots=True)
class CommercialPaidAssessmentDeliveryReadiness:
    tenant_id: str
    client_id: str
    engagement_id: str
    assessment_id: str

    execution_status_hash: str
    operator_result_hash: str
    operator_snapshot_hash: str

    readiness: RealPaidAssessmentDeliveryReadinessResult

    result_type: str = COMMERCIAL_PAID_ASSESSMENT_DELIVERY_READINESS_ID
    version: str = COMMERCIAL_PAID_ASSESSMENT_DELIVERY_READINESS_VERSION
    schema_version: str = (
        COMMERCIAL_PAID_ASSESSMENT_DELIVERY_READINESS_SCHEMA_VERSION
    )

    @property
    def hierarchy_key(self) -> str:
        return "/".join(
            (
                self.tenant_id,
                self.client_id,
                self.engagement_id,
                self.assessment_id,
            )
        )

    def to_dict(self) -> dict[str, Any]:
        """
        Safe commercial projection.

        The internally rehydrated readiness object remains available to
        server-side approval handoff code, but browser-safe serialization
        exposes only the minimum metadata required to render readiness.
        """
        return {
            "result_type": self.result_type,
            "version": self.version,
            "schema_version": self.schema_version,
            "tenant_id": self.tenant_id,
            "client_id": self.client_id,
            "engagement_id": self.engagement_id,
            "assessment_id": self.assessment_id,
            "hierarchy_key": self.hierarchy_key,
            "delivery_readiness_status": (
                self.readiness.delivery_readiness_status
            ),
            "recovery_disposition": self.readiness.recovery_disposition,
            "artifact_count": self.readiness.artifact_count,
            "repository_chain_valid": (
                self.readiness.repository_chain_valid
            ),
            "report_id": self.readiness.execution_result.report_id,
            "attempt_hash": self.readiness.attempt_hash,
            "recovery_record_hash": (
                self.readiness.recovery_record_hash
            ),
            "execution_status_hash": self.execution_status_hash,
            "operator_result_hash": self.operator_result_hash,
            "operator_snapshot_hash": self.operator_snapshot_hash,
            "boundaries": {
                "readiness_is_read_only": True,
                "readiness_is_not_execution_authority": True,
                "readiness_is_not_recovery_authority": True,
                "readiness_is_not_delivery_approval": True,
                "readiness_is_not_approved_for_human_delivery": True,
                "readiness_is_not_delivery": True,
                "browser_cannot_select_execution_repository": True,
                "operator_result_payload_not_exposed": True,
                "raw_evidence_not_exposed": True,
                "report_package_payload_not_exposed": True,
                "existing_delivery_readiness_service_is_authoritative": True,
            },
        }


class GovernanceCommercialPaidAssessmentDeliveryReadinessService:
    """
    Restart-safe commercial bridge to the existing PA-003 delivery-readiness
    verifier.

    This service does not execute or recover an assessment. It does not
    approve delivery and does not record delivery. It loads the durable
    PA015 operator-result snapshot created by 04F-03, derives the
    server-controlled hierarchy database, and delegates verification to the
    existing GovernanceRealPaidAssessmentDeliveryReadinessService.
    """

    def __init__(
        self,
        *,
        execution_service: GovernanceCommercialPaidAssessmentExecutionService,
        snapshot_store: (
            GovernanceCommercialPaidAssessmentOperatorResultStore | None
        ) = None,
        readiness_service: (
            GovernanceRealPaidAssessmentDeliveryReadinessService | None
        ) = None,
    ) -> None:
        if not isinstance(
            execution_service,
            GovernanceCommercialPaidAssessmentExecutionService,
        ):
            raise CommercialPaidAssessmentDeliveryReadinessError(
                "execution_service must be a "
                "GovernanceCommercialPaidAssessmentExecutionService"
            )

        self._execution_service = execution_service

        self._snapshot_store = (
            snapshot_store
            if snapshot_store is not None
            else GovernanceCommercialPaidAssessmentOperatorResultStore(
                database_path=(
                    Path(execution_service.execution_directory)
                    / COMMERCIAL_PAID_ASSESSMENT_OPERATOR_RESULT_DATABASE
                )
            )
        )

        self._readiness_service = (
            readiness_service
            if readiness_service is not None
            else GovernanceRealPaidAssessmentDeliveryReadinessService()
        )

    @property
    def execution_service(
        self,
    ) -> GovernanceCommercialPaidAssessmentExecutionService:
        return self._execution_service

    def verify(
        self,
        *,
        tenant_id: str,
        client_id: str,
        engagement_id: str,
        assessment_id: str,
    ) -> CommercialPaidAssessmentDeliveryReadiness:
        hierarchy = self._validate_hierarchy(
            tenant_id=tenant_id,
            client_id=client_id,
            engagement_id=engagement_id,
            assessment_id=assessment_id,
        )

        try:
            snapshot = self._snapshot_store.get(
                tenant_id=hierarchy[0],
                client_id=hierarchy[1],
                engagement_id=hierarchy[2],
                assessment_id=hierarchy[3],
            )
        except CommercialPaidAssessmentOperatorResultStoreError as exc:
            raise CommercialPaidAssessmentDeliveryReadinessError(
                "durable PA015 operator-result snapshot is invalid: "
                f"{exc}"
            ) from exc

        if snapshot is None:
            raise CommercialPaidAssessmentDeliveryReadinessError(
                "durable PA015 operator-result snapshot was not found"
            )

        expected_hierarchy_key = "/".join(hierarchy)

        if snapshot.hierarchy_key != expected_hierarchy_key:
            raise CommercialPaidAssessmentDeliveryReadinessError(
                "operator-result snapshot hierarchy mismatch"
            )

        status = self._execution_service.status_store.get_status(
            tenant_id=hierarchy[0],
            client_id=hierarchy[1],
            engagement_id=hierarchy[2],
            assessment_id=hierarchy[3],
        )

        if status is None:
            raise CommercialPaidAssessmentDeliveryReadinessError(
                "durable commercial paid execution status was not found"
            )

        if status.hierarchy_key != expected_hierarchy_key:
            raise CommercialPaidAssessmentDeliveryReadinessError(
                "durable execution status hierarchy mismatch"
            )

        if snapshot.execution_status_hash != status.status_hash:
            raise CommercialPaidAssessmentDeliveryReadinessError(
                "operator-result snapshot is not bound to current "
                "durable execution status"
            )

        if (
            snapshot.execution_input_binding_hash
            != status.execution_input_binding_hash
        ):
            raise CommercialPaidAssessmentDeliveryReadinessError(
                "operator-result snapshot binding hash mismatch"
            )

        if (
            snapshot.assessment_execution_request_hash
            != status.assessment_execution_request_hash
        ):
            raise CommercialPaidAssessmentDeliveryReadinessError(
                "operator-result snapshot request hash mismatch"
            )

        database_path = (
            self._execution_service.database_path_for_hierarchy(
                tenant_id=hierarchy[0],
                client_id=hierarchy[1],
                engagement_id=hierarchy[2],
                assessment_id=hierarchy[3],
            )
        )

        try:
            readiness = self._readiness_service.verify(
                database_path=database_path,
                operator_payload=snapshot.operator_result,
            )
        except RealPaidAssessmentDeliveryReadinessError as exc:
            raise CommercialPaidAssessmentDeliveryReadinessError(
                "governed paid-assessment delivery readiness failed: "
                f"{exc}"
            ) from exc

        if readiness.hierarchy_key != expected_hierarchy_key:
            raise CommercialPaidAssessmentDeliveryReadinessError(
                "delivery readiness hierarchy mismatch"
            )

        if readiness.recovery_disposition != status.disposition:
            raise CommercialPaidAssessmentDeliveryReadinessError(
                "delivery readiness recovery disposition does not match "
                "durable execution status"
            )

        if readiness.attempt_hash != status.attempt_hash:
            raise CommercialPaidAssessmentDeliveryReadinessError(
                "delivery readiness attempt hash does not match "
                "durable execution status"
            )

        if readiness.recovery_record_hash != status.attempt_record_hash:
            raise CommercialPaidAssessmentDeliveryReadinessError(
                "delivery readiness recovery record hash does not match "
                "durable execution status"
            )

        if readiness.artifact_count != status.artifact_count_after:
            raise CommercialPaidAssessmentDeliveryReadinessError(
                "delivery readiness artifact count does not match "
                "durable execution status"
            )

        return CommercialPaidAssessmentDeliveryReadiness(
            tenant_id=hierarchy[0],
            client_id=hierarchy[1],
            engagement_id=hierarchy[2],
            assessment_id=hierarchy[3],
            execution_status_hash=status.status_hash,
            operator_result_hash=snapshot.operator_result_hash,
            operator_snapshot_hash=snapshot.snapshot_hash,
            readiness=readiness,
        )

    @staticmethod
    def _validate_hierarchy(
        *,
        tenant_id: str,
        client_id: str,
        engagement_id: str,
        assessment_id: str,
    ) -> tuple[str, str, str, str]:
        values = (
            tenant_id,
            client_id,
            engagement_id,
            assessment_id,
        )

        normalized: list[str] = []

        for name, value in zip(
            (
                "tenant_id",
                "client_id",
                "engagement_id",
                "assessment_id",
            ),
            values,
            strict=True,
        ):
            if not isinstance(value, str) or not value.strip():
                raise CommercialPaidAssessmentDeliveryReadinessError(
                    f"{name} must be non-empty"
                )
            normalized.append(value.strip())

        return (
            normalized[0],
            normalized[1],
            normalized[2],
            normalized[3],
        )
