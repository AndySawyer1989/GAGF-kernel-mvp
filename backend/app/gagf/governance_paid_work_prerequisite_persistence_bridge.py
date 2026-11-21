from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from backend.app.gagf.governance_paid_work_prerequisite_record import (
    AUTHORIZATION_PACKAGE_KIND,
    CONTRACT_EXECUTION_EVENT_KIND,
    PAYMENT_CONFIRMATION_EVENT_KIND,
    GovernancePaidWorkPrerequisiteRecord,
    build_paid_work_prerequisite_record,
)
from backend.app.gagf.governance_paid_work_prerequisite_record_store import (
    GovernancePaidWorkPrerequisiteRecordStore,
)


GOVERNANCE_PAID_WORK_PREREQUISITE_PERSISTENCE_BRIDGE_VERSION = "0.1.0"


@dataclass(frozen=True, slots=True)
class GovernancePaidWorkPrerequisitePersistenceResult:
    prerequisite_kind: str
    record: GovernancePaidWorkPrerequisiteRecord

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": "recorded",
            "bridge_version": (
                GOVERNANCE_PAID_WORK_PREREQUISITE_PERSISTENCE_BRIDGE_VERSION
            ),
            "prerequisite_kind": self.prerequisite_kind,
            "record": self.record.to_dict(),
            "boundaries": {
                "artifact_persisted_as_prerequisite_evidence": True,
                "persistence_does_not_create_paid_work_authority": True,
                "prerequisite_record_is_not_pa001": True,
                "authorization_package_readiness_is_not_pa001": True,
                "contract_execution_is_not_pa001": True,
                "payment_confirmation_is_not_pa001": True,
                "persistence_does_not_authenticate_actor": True,
                "persistence_does_not_authorize_execution": True,
                "persistence_does_not_approve_delivery": True,
                "persistence_does_not_grant_intervention_authority": True,
            },
        }


class GovernancePaidWorkPrerequisitePersistenceBridge:
    """
    Persist already-produced commercial prerequisite artifacts into the
    governed prerequisite evidence store.

    This bridge does not generate Factory Lite artifacts and does not create
    PA-001. The caller must supply the exact commercial hierarchy explicitly.
    """

    def __init__(
        self,
        *,
        prerequisite_store: GovernancePaidWorkPrerequisiteRecordStore,
    ) -> None:
        if not isinstance(
            prerequisite_store,
            GovernancePaidWorkPrerequisiteRecordStore,
        ):
            raise TypeError(
                "prerequisite_store must be a "
                "GovernancePaidWorkPrerequisiteRecordStore"
            )

        self.prerequisite_store = prerequisite_store

    def record_authorization_package(
        self,
        *,
        tenant_id: str,
        client_id: str,
        engagement_id: str,
        assessment_id: str,
        artifact: Mapping[str, Any],
    ) -> GovernancePaidWorkPrerequisitePersistenceResult:
        return self._record(
            prerequisite_kind=AUTHORIZATION_PACKAGE_KIND,
            tenant_id=tenant_id,
            client_id=client_id,
            engagement_id=engagement_id,
            assessment_id=assessment_id,
            artifact=artifact,
        )

    def record_contract_execution_event(
        self,
        *,
        tenant_id: str,
        client_id: str,
        engagement_id: str,
        assessment_id: str,
        artifact: Mapping[str, Any],
    ) -> GovernancePaidWorkPrerequisitePersistenceResult:
        return self._record(
            prerequisite_kind=CONTRACT_EXECUTION_EVENT_KIND,
            tenant_id=tenant_id,
            client_id=client_id,
            engagement_id=engagement_id,
            assessment_id=assessment_id,
            artifact=artifact,
        )

    def record_payment_confirmation_event(
        self,
        *,
        tenant_id: str,
        client_id: str,
        engagement_id: str,
        assessment_id: str,
        artifact: Mapping[str, Any],
    ) -> GovernancePaidWorkPrerequisitePersistenceResult:
        return self._record(
            prerequisite_kind=PAYMENT_CONFIRMATION_EVENT_KIND,
            tenant_id=tenant_id,
            client_id=client_id,
            engagement_id=engagement_id,
            assessment_id=assessment_id,
            artifact=artifact,
        )

    def _record(
        self,
        *,
        prerequisite_kind: str,
        tenant_id: str,
        client_id: str,
        engagement_id: str,
        assessment_id: str,
        artifact: Mapping[str, Any],
    ) -> GovernancePaidWorkPrerequisitePersistenceResult:
        record = build_paid_work_prerequisite_record(
            prerequisite_kind=prerequisite_kind,
            tenant_id=tenant_id,
            client_id=client_id,
            engagement_id=engagement_id,
            assessment_id=assessment_id,
            artifact=artifact,
        )

        stored = self.prerequisite_store.save(
            record=record
        )

        return GovernancePaidWorkPrerequisitePersistenceResult(
            prerequisite_kind=prerequisite_kind,
            record=stored,
        )
