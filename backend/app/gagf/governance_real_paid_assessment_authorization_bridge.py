from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from backend.app.gagf.governance_paid_assessment_execution_handoff import (
    PaidAssessmentWorkAuthorization,
)
from backend.app.gagf.governance_real_paid_assessment_readiness import (
    READINESS_STATUS_READY,
    RealPaidAssessmentIntake,
    RealPaidAssessmentReadinessResult,
)


REAL_PAID_ASSESSMENT_AUTHORIZATION_BRIDGE_ID = (
    "governance-real-paid-assessment-authorization-bridge"
)
REAL_PAID_ASSESSMENT_AUTHORIZATION_BRIDGE_VERSION = "0.1.0"
REAL_PAID_ASSESSMENT_AUTHORIZATION_BRIDGE_SCHEMA_VERSION = "1.0.0"

BRIDGE_STATUS_READY = "ready_for_execution_handoff"


class RealPaidAssessmentAuthorizationBridgeError(ValueError):
    """Raised when readiness and paid-work authority cannot be bound."""


@dataclass(frozen=True, slots=True)
class RealPaidAssessmentAuthorizationBridge:
    tenant_id: str
    client_id: str
    engagement_id: str
    assessment_id: str

    readiness_status: str
    authorization_id: str
    authorized_by: str
    authorized_at: str

    paid_assessment_authorized: bool
    bridge_status: str

    bridge_type: str = (
        REAL_PAID_ASSESSMENT_AUTHORIZATION_BRIDGE_ID
    )
    version: str = (
        REAL_PAID_ASSESSMENT_AUTHORIZATION_BRIDGE_VERSION
    )
    schema_version: str = (
        REAL_PAID_ASSESSMENT_AUTHORIZATION_BRIDGE_SCHEMA_VERSION
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
        return {
            "bridge_type": self.bridge_type,
            "version": self.version,
            "schema_version": self.schema_version,
            "tenant_id": self.tenant_id,
            "client_id": self.client_id,
            "engagement_id": self.engagement_id,
            "assessment_id": self.assessment_id,
            "hierarchy_key": self.hierarchy_key,
            "readiness_status": self.readiness_status,
            "authorization_id": self.authorization_id,
            "authorized_by": self.authorized_by,
            "authorized_at": self.authorized_at,
            "paid_assessment_authorized": (
                self.paid_assessment_authorized
            ),
            "bridge_status": self.bridge_status,
            "boundaries": {
                "readiness_did_not_create_authorization": True,
                "bridge_did_not_create_authorization": True,
                "authorization_is_not_execution": True,
                "authorization_is_not_production_onboarding": True,
                "authorization_is_not_customer_outcome": True,
            },
        }


class GovernanceRealPaidAssessmentAuthorizationBridgeService:
    """
    Bind an already-ready real assessment intake to an independently
    supplied PA-001 PaidAssessmentWorkAuthorization.

    This service does not create paid-work authority.
    """

    def bind(
        self,
        *,
        intake: RealPaidAssessmentIntake,
        readiness: RealPaidAssessmentReadinessResult,
        paid_work_authorization: PaidAssessmentWorkAuthorization,
    ) -> RealPaidAssessmentAuthorizationBridge:
        if not isinstance(
            intake,
            RealPaidAssessmentIntake,
        ):
            raise RealPaidAssessmentAuthorizationBridgeError(
                "intake must be a RealPaidAssessmentIntake"
            )

        if not isinstance(
            readiness,
            RealPaidAssessmentReadinessResult,
        ):
            raise RealPaidAssessmentAuthorizationBridgeError(
                "readiness must be a RealPaidAssessmentReadinessResult"
            )

        if not isinstance(
            paid_work_authorization,
            PaidAssessmentWorkAuthorization,
        ):
            raise RealPaidAssessmentAuthorizationBridgeError(
                "paid_work_authorization must be a "
                "PaidAssessmentWorkAuthorization"
            )

        if readiness.readiness_status != READINESS_STATUS_READY:
            raise RealPaidAssessmentAuthorizationBridgeError(
                "real paid assessment readiness is not READY"
            )

        if readiness.ready_for_paid_work_authorization is not True:
            raise RealPaidAssessmentAuthorizationBridgeError(
                "readiness does not permit advancing to paid-work authorization"
            )

        expected_hierarchy = (
            intake.tenant_id,
            intake.client_id,
            intake.engagement_id,
            intake.assessment_id,
        )

        readiness_hierarchy = (
            readiness.tenant_id,
            readiness.client_id,
            readiness.engagement_id,
            readiness.assessment_id,
        )

        authorization_hierarchy = (
            paid_work_authorization.tenant_id,
            paid_work_authorization.client_id,
            paid_work_authorization.engagement_id,
            paid_work_authorization.assessment_id,
        )

        if readiness_hierarchy != expected_hierarchy:
            raise RealPaidAssessmentAuthorizationBridgeError(
                "readiness hierarchy does not match intake"
            )

        if authorization_hierarchy != expected_hierarchy:
            raise RealPaidAssessmentAuthorizationBridgeError(
                "paid-work authorization hierarchy does not match intake"
            )

        if paid_work_authorization.paid_assessment_authorized is not True:
            raise RealPaidAssessmentAuthorizationBridgeError(
                "paid-work authorization is not affirmative"
            )

        return RealPaidAssessmentAuthorizationBridge(
            tenant_id=intake.tenant_id,
            client_id=intake.client_id,
            engagement_id=intake.engagement_id,
            assessment_id=intake.assessment_id,
            readiness_status=readiness.readiness_status,
            authorization_id=(
                paid_work_authorization.authorization_id
            ),
            authorized_by=paid_work_authorization.authorized_by,
            authorized_at=paid_work_authorization.authorized_at,
            paid_assessment_authorized=True,
            bridge_status=BRIDGE_STATUS_READY,
        )


SERVICE_TYPE = (
    GovernanceRealPaidAssessmentAuthorizationBridgeService
)