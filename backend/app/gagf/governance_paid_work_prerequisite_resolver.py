from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from backend.app.gagf.governance_assessment_auth import (
    AssessmentActorContext,
)
from backend.app.gagf.governance_paid_work_authorization_issuance_service import (
    GovernancePaidWorkAuthorizationIssuanceResult,
    GovernancePaidWorkAuthorizationIssuanceService,
)
from backend.app.gagf.governance_paid_work_prerequisite_record import (
    AUTHORIZATION_PACKAGE_KIND,
    CONTRACT_EXECUTION_EVENT_KIND,
    PAYMENT_CONFIRMATION_EVENT_KIND,
    GovernancePaidWorkPrerequisiteRecord,
)
from backend.app.gagf.governance_paid_work_prerequisite_record_store import (
    GovernancePaidWorkPrerequisiteRecordStore,
)


GOVERNANCE_PAID_WORK_PREREQUISITE_RESOLVER_VERSION = "0.1.0"


class GovernancePaidWorkPrerequisiteResolverError(ValueError):
    """Raised when prerequisite IDs cannot be resolved for PA-001 issuance."""


def _require_text(
    value: Any,
    field_name: str,
) -> str:
    if not isinstance(value, str):
        raise GovernancePaidWorkPrerequisiteResolverError(
            f"{field_name} must be a string"
        )

    normalized = value.strip()

    if not normalized:
        raise GovernancePaidWorkPrerequisiteResolverError(
            f"{field_name} must not be empty"
        )

    return normalized


@dataclass(frozen=True, slots=True)
class GovernancePaidWorkPrerequisiteResolution:
    authorization_package: GovernancePaidWorkPrerequisiteRecord
    contract_execution_event: GovernancePaidWorkPrerequisiteRecord
    payment_confirmation_event: GovernancePaidWorkPrerequisiteRecord
    resolver_version: str = (
        GOVERNANCE_PAID_WORK_PREREQUISITE_RESOLVER_VERSION
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "resolver_version": self.resolver_version,
            "authorization_package": (
                self.authorization_package.to_dict()
            ),
            "contract_execution_event": (
                self.contract_execution_event.to_dict()
            ),
            "payment_confirmation_event": (
                self.payment_confirmation_event.to_dict()
            ),
            "boundaries": {
                "ids_are_not_authority": True,
                "resolution_is_not_paid_work_authority": True,
                "resolution_is_not_actor_authentication": True,
                "resolution_is_not_execution": True,
                "resolution_is_not_delivery": True,
                "resolution_is_not_intervention_authority": True,
            },
        }


@dataclass(frozen=True, slots=True)
class GovernancePaidWorkPrerequisiteResolvedIssuanceResult:
    resolution: GovernancePaidWorkPrerequisiteResolution
    issuance: GovernancePaidWorkAuthorizationIssuanceResult

    def to_dict(self) -> dict[str, Any]:
        return {
            "resolution": self.resolution.to_dict(),
            "issuance": self.issuance.to_dict(),
            "boundaries": {
                "prerequisites_resolved_server_side": True,
                "browser_artifact_payloads_not_used": True,
                "issuance_service_remains_authority_boundary": True,
                "resolver_does_not_create_prerequisite_records": True,
                "resolver_does_not_bypass_admin_issuance": True,
            },
        }


class GovernancePaidWorkPrerequisiteResolver:
    """
    Resolve authoritative PA-001 prerequisite records by immutable IDs.

    The resolver does not create prerequisite records and does not itself
    create paid-work authority. It resolves hierarchy-bound records from the
    server-side prerequisite store and delegates the explicit PA-001 issuance
    operation to GovernancePaidWorkAuthorizationIssuanceService.
    """

    def __init__(
        self,
        *,
        prerequisite_store: GovernancePaidWorkPrerequisiteRecordStore,
        issuance_service: GovernancePaidWorkAuthorizationIssuanceService,
    ) -> None:
        if not isinstance(
            prerequisite_store,
            GovernancePaidWorkPrerequisiteRecordStore,
        ):
            raise GovernancePaidWorkPrerequisiteResolverError(
                "prerequisite_store must be a "
                "GovernancePaidWorkPrerequisiteRecordStore"
            )

        if not isinstance(
            issuance_service,
            GovernancePaidWorkAuthorizationIssuanceService,
        ):
            raise GovernancePaidWorkPrerequisiteResolverError(
                "issuance_service must be a "
                "GovernancePaidWorkAuthorizationIssuanceService"
            )

        self.prerequisite_store = prerequisite_store
        self.issuance_service = issuance_service

    def resolve(
        self,
        *,
        tenant_id: str,
        client_id: str,
        engagement_id: str,
        assessment_id: str,
        authorization_package_id: str,
        contract_execution_event_id: str,
        payment_confirmation_event_id: str,
    ) -> GovernancePaidWorkPrerequisiteResolution:
        hierarchy = {
            "tenant_id": _require_text(
                tenant_id,
                "tenant_id",
            ),
            "client_id": _require_text(
                client_id,
                "client_id",
            ),
            "engagement_id": _require_text(
                engagement_id,
                "engagement_id",
            ),
            "assessment_id": _require_text(
                assessment_id,
                "assessment_id",
            ),
        }

        package_id = _require_text(
            authorization_package_id,
            "authorization_package_id",
        )
        contract_event_id = _require_text(
            contract_execution_event_id,
            "contract_execution_event_id",
        )
        payment_event_id = _require_text(
            payment_confirmation_event_id,
            "payment_confirmation_event_id",
        )

        authorization_package = (
            self.prerequisite_store.require_for_issuance(
                prerequisite_kind=AUTHORIZATION_PACKAGE_KIND,
                artifact_id=package_id,
                **hierarchy,
            )
        )

        contract_execution_event = (
            self.prerequisite_store.require_for_issuance(
                prerequisite_kind=CONTRACT_EXECUTION_EVENT_KIND,
                artifact_id=contract_event_id,
                **hierarchy,
            )
        )

        payment_confirmation_event = (
            self.prerequisite_store.require_for_issuance(
                prerequisite_kind=PAYMENT_CONFIRMATION_EVENT_KIND,
                artifact_id=payment_event_id,
                **hierarchy,
            )
        )

        return GovernancePaidWorkPrerequisiteResolution(
            authorization_package=authorization_package,
            contract_execution_event=contract_execution_event,
            payment_confirmation_event=payment_confirmation_event,
        )

    def issue_from_ids(
        self,
        *,
        tenant_id: str,
        client_id: str,
        engagement_id: str,
        assessment_id: str,
        authorization_package_id: str,
        contract_execution_event_id: str,
        payment_confirmation_event_id: str,
        actor: AssessmentActorContext,
    ) -> GovernancePaidWorkPrerequisiteResolvedIssuanceResult:
        resolution = self.resolve(
            tenant_id=tenant_id,
            client_id=client_id,
            engagement_id=engagement_id,
            assessment_id=assessment_id,
            authorization_package_id=authorization_package_id,
            contract_execution_event_id=contract_execution_event_id,
            payment_confirmation_event_id=payment_confirmation_event_id,
        )

        issuance = self.issuance_service.issue(
            tenant_id=tenant_id,
            client_id=client_id,
            engagement_id=engagement_id,
            assessment_id=assessment_id,
            authorization_package=(
                resolution.authorization_package.artifact
            ),
            contract_execution_event=(
                resolution.contract_execution_event.artifact
            ),
            payment_confirmation_event=(
                resolution.payment_confirmation_event.artifact
            ),
            actor=actor,
        )

        return GovernancePaidWorkPrerequisiteResolvedIssuanceResult(
            resolution=resolution,
            issuance=issuance,
        )
