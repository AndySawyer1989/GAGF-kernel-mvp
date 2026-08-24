from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from backend.app.gagf.governance_first_real_paid_assessment_execution_readiness import (
    FIRST_REAL_EXECUTION_STATUS_READY,
    FirstRealPaidAssessmentExecutionReadinessResult,
)
from backend.app.gagf.governance_paid_assessment_execution_handoff import (
    EXPECTED_CONTRACT_EVENT_STATUS,
    EXPECTED_CONTRACT_EVENT_TYPE,
    PaidAssessmentWorkAuthorization,
)
from backend.app.gagf.governance_real_paid_assessment_authorization_bridge import (
    BRIDGE_STATUS_READY,
    RealPaidAssessmentAuthorizationBridge,
)


FIRST_REAL_PAID_ASSESSMENT_LAUNCH_MANIFEST_ID = (
    "governance-first-real-paid-assessment-launch-manifest"
)
FIRST_REAL_PAID_ASSESSMENT_LAUNCH_MANIFEST_VERSION = "0.1.0"
FIRST_REAL_PAID_ASSESSMENT_LAUNCH_MANIFEST_SCHEMA_VERSION = "1.0.0"

EXPECTED_PAYMENT_CONFIRMATION_EVENT_TYPE = (
    "assessment_factory_lite_payment_confirmation_event"
)
EXPECTED_PAYMENT_CONFIRMATION_EVENT_STAGE = "payment_confirmation_event"
EXPECTED_PAYMENT_CONFIRMATION_EVENT_STATUS = "payment_confirmed"

LAUNCH_MANIFEST_STATUS_READY = "ready_for_human_launch_review"
LAUNCH_MANIFEST_STATUS_BLOCKED = "blocked"

ACTION_REVIEW_CONTROLLED_LAUNCH = (
    "perform_human_controlled_launch_review"
)
ACTION_RESOLVE_LAUNCH_BLOCKERS = "resolve_launch_manifest_blockers"


class FirstRealPaidAssessmentLaunchManifestError(ValueError):
    """Raised when PILOT-013 inputs are structurally invalid."""


@dataclass(frozen=True, slots=True)
class FirstRealPaidAssessmentLaunchManifest:
    tenant_id: str
    client_id: str
    engagement_id: str
    assessment_id: str

    contract_execution_event_id: str
    payment_confirmation_event_id: str
    paid_work_authorization_id: str
    authorization_id: str

    execution_readiness_status: str
    status: str
    ready_for_human_launch_review: bool
    required_operator_action: str
    blockers: tuple[str, ...]

    manifest_type: str = (
        FIRST_REAL_PAID_ASSESSMENT_LAUNCH_MANIFEST_ID
    )
    version: str = (
        FIRST_REAL_PAID_ASSESSMENT_LAUNCH_MANIFEST_VERSION
    )
    schema_version: str = (
        FIRST_REAL_PAID_ASSESSMENT_LAUNCH_MANIFEST_SCHEMA_VERSION
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
            "manifest_type": self.manifest_type,
            "version": self.version,
            "schema_version": self.schema_version,
            "tenant_id": self.tenant_id,
            "client_id": self.client_id,
            "engagement_id": self.engagement_id,
            "assessment_id": self.assessment_id,
            "hierarchy_key": self.hierarchy_key,
            "contract_execution_event_id": (
                self.contract_execution_event_id
            ),
            "payment_confirmation_event_id": (
                self.payment_confirmation_event_id
            ),
            "paid_work_authorization_id": (
                self.paid_work_authorization_id
            ),
            "authorization_id": self.authorization_id,
            "execution_readiness_status": (
                self.execution_readiness_status
            ),
            "status": self.status,
            "ready_for_human_launch_review": (
                self.ready_for_human_launch_review
            ),
            "required_operator_action": (
                self.required_operator_action
            ),
            "blockers": self.blockers,
            "boundaries": {
                "pilot013_is_read_only": True,
                "launch_manifest_does_not_create_commercial_events": True,
                "launch_manifest_does_not_create_paid_work_authorization": True,
                "launch_manifest_does_not_create_execution_authority": True,
                "launch_manifest_does_not_execute_assessment": True,
                "payment_confirmation_is_not_paid_work_authorization": True,
                "paid_work_authorization_is_independent_authority": True,
                "pilot012_remains_execution_readiness_authority": True,
                "human_launch_review_remains_required": True,
                "pa015_remains_execution_path": True,
                "launch_ready_does_not_mean_executed": True,
                "launch_ready_does_not_mean_delivered": True,
                "launch_ready_does_not_mean_customer_accepted": True,
                "launch_ready_does_not_verify_outcomes": True,
            },
        }


class GovernanceFirstRealPaidAssessmentLaunchManifestService:
    """
    Bind terminal commercial evidence to existing execution authority.

    PILOT-013 does not manufacture contract execution, invoice creation,
    payment request, payment confirmation, paid-work authorization,
    authorization bridge, PILOT-012 readiness, human launch approval,
    execution authority, or assessment execution.

    The payment-confirmation event is commercial completion evidence only.
    PaidAssessmentWorkAuthorization remains an independent authority.
    """

    def build_manifest(
        self,
        *,
        contract_execution_event: dict[str, Any],
        payment_confirmation_event: dict[str, Any],
        paid_work_authorization: PaidAssessmentWorkAuthorization,
        authorization_bridge: RealPaidAssessmentAuthorizationBridge,
        execution_readiness: FirstRealPaidAssessmentExecutionReadinessResult,
    ) -> FirstRealPaidAssessmentLaunchManifest:
        self._require_types(
            contract_execution_event=contract_execution_event,
            payment_confirmation_event=payment_confirmation_event,
            paid_work_authorization=paid_work_authorization,
            authorization_bridge=authorization_bridge,
            execution_readiness=execution_readiness,
        )

        blockers: list[str] = []

        self._validate_contract_event(
            contract_execution_event,
            blockers,
        )

        self._validate_payment_confirmation_event(
            payment_confirmation_event,
            blockers,
        )

        self._validate_authorization(
            contract_execution_event=contract_execution_event,
            paid_work_authorization=paid_work_authorization,
            blockers=blockers,
        )

        self._validate_bridge(
            paid_work_authorization=paid_work_authorization,
            authorization_bridge=authorization_bridge,
            blockers=blockers,
        )

        self._validate_execution_readiness(
            paid_work_authorization=paid_work_authorization,
            execution_readiness=execution_readiness,
            blockers=blockers,
        )

        ready = len(blockers) == 0

        return FirstRealPaidAssessmentLaunchManifest(
            tenant_id=paid_work_authorization.tenant_id,
            client_id=paid_work_authorization.client_id,
            engagement_id=paid_work_authorization.engagement_id,
            assessment_id=paid_work_authorization.assessment_id,
            contract_execution_event_id=(
                paid_work_authorization.contract_execution_event_id
            ),
            payment_confirmation_event_id=self._require_text(
                payment_confirmation_event.get(
                    "payment_confirmation_event_id"
                ),
                "payment_confirmation_event_id",
            ),
            paid_work_authorization_id=(
                paid_work_authorization.authorization_id
            ),
            authorization_id=authorization_bridge.authorization_id,
            execution_readiness_status=execution_readiness.status,
            status=(
                LAUNCH_MANIFEST_STATUS_READY
                if ready
                else LAUNCH_MANIFEST_STATUS_BLOCKED
            ),
            ready_for_human_launch_review=ready,
            required_operator_action=(
                ACTION_REVIEW_CONTROLLED_LAUNCH
                if ready
                else ACTION_RESOLVE_LAUNCH_BLOCKERS
            ),
            blockers=tuple(blockers),
        )

    def _require_types(
        self,
        *,
        contract_execution_event: dict[str, Any],
        payment_confirmation_event: dict[str, Any],
        paid_work_authorization: PaidAssessmentWorkAuthorization,
        authorization_bridge: RealPaidAssessmentAuthorizationBridge,
        execution_readiness: FirstRealPaidAssessmentExecutionReadinessResult,
    ) -> None:
        if not isinstance(contract_execution_event, dict):
            raise FirstRealPaidAssessmentLaunchManifestError(
                "contract_execution_event must be a dict"
            )

        if not isinstance(payment_confirmation_event, dict):
            raise FirstRealPaidAssessmentLaunchManifestError(
                "payment_confirmation_event must be a dict"
            )

        if not isinstance(
            paid_work_authorization,
            PaidAssessmentWorkAuthorization,
        ):
            raise FirstRealPaidAssessmentLaunchManifestError(
                "paid_work_authorization must be a "
                "PaidAssessmentWorkAuthorization"
            )

        if not isinstance(
            authorization_bridge,
            RealPaidAssessmentAuthorizationBridge,
        ):
            raise FirstRealPaidAssessmentLaunchManifestError(
                "authorization_bridge must be a "
                "RealPaidAssessmentAuthorizationBridge"
            )

        if not isinstance(
            execution_readiness,
            FirstRealPaidAssessmentExecutionReadinessResult,
        ):
            raise FirstRealPaidAssessmentLaunchManifestError(
                "execution_readiness must be a "
                "FirstRealPaidAssessmentExecutionReadinessResult"
            )

    def _validate_contract_event(
        self,
        event: dict[str, Any],
        blockers: list[str],
    ) -> None:
        if event.get("status") != "ok":
            blockers.append("contract_event:status_not_ok")

        if event.get("event_type") != EXPECTED_CONTRACT_EVENT_TYPE:
            blockers.append("contract_event:unexpected_event_type")

        if (
            event.get("event_status")
            != EXPECTED_CONTRACT_EVENT_STATUS
        ):
            blockers.append("contract_event:not_contract_executed")

        event_blockers = event.get("event_blockers")

        if not isinstance(event_blockers, list):
            blockers.append("contract_event:blockers_not_list")
        elif event_blockers:
            blockers.append("contract_event:has_blockers")

    def _validate_payment_confirmation_event(
        self,
        event: dict[str, Any],
        blockers: list[str],
    ) -> None:
        if event.get("status") != "ok":
            blockers.append("payment_confirmation:status_not_ok")

        if (
            event.get("event_type")
            != EXPECTED_PAYMENT_CONFIRMATION_EVENT_TYPE
        ):
            blockers.append(
                "payment_confirmation:unexpected_event_type"
            )

        if (
            event.get("event_stage")
            != EXPECTED_PAYMENT_CONFIRMATION_EVENT_STAGE
        ):
            blockers.append(
                "payment_confirmation:unexpected_event_stage"
            )

        if (
            event.get("event_status")
            != EXPECTED_PAYMENT_CONFIRMATION_EVENT_STATUS
        ):
            blockers.append(
                "payment_confirmation:not_payment_confirmed"
            )

        event_blockers = event.get("event_blockers")

        if not isinstance(event_blockers, list):
            blockers.append(
                "payment_confirmation:blockers_not_list"
            )
        elif event_blockers:
            blockers.append(
                "payment_confirmation:has_blockers"
            )

        commercial_boundary = event.get(
            "commercial_boundary"
        )

        if not isinstance(commercial_boundary, dict):
            blockers.append(
                "payment_confirmation:"
                "commercial_boundary_missing"
            )
        else:
            if (
                commercial_boundary.get(
                    "payment_confirmation_recorded"
                )
                is not True
            ):
                blockers.append(
                    "payment_confirmation:"
                    "confirmation_not_recorded"
                )

            if (
                commercial_boundary.get("payment_confirmed")
                is not True
            ):
                blockers.append(
                    "payment_confirmation:"
                    "payment_not_confirmed"
                )

            if (
                commercial_boundary.get(
                    "requires_final_paid_work_authorization"
                )
                is not True
            ):
                blockers.append(
                    "payment_confirmation:"
                    "final_authorization_boundary_missing"
                )

            if (
                commercial_boundary.get(
                    "paid_assessment_authorized"
                )
                is not False
            ):
                blockers.append(
                    "payment_confirmation:"
                    "improper_paid_work_authorization_claim"
                )

        governance_boundary = event.get(
            "governance_boundary"
        )

        if not isinstance(governance_boundary, dict):
            blockers.append(
                "payment_confirmation:"
                "governance_boundary_missing"
            )
        else:
            if (
                governance_boundary.get(
                    "payment_confirmation_event_is_not_paid_work_authorization"
                )
                is not True
            ):
                blockers.append(
                    "payment_confirmation:"
                    "authorization_boundary_missing"
                )

    def _validate_authorization(
        self,
        *,
        contract_execution_event: dict[str, Any],
        paid_work_authorization: PaidAssessmentWorkAuthorization,
        blockers: list[str],
    ) -> None:
        if (
            paid_work_authorization.paid_assessment_authorized
            is not True
        ):
            blockers.append(
                "authorization:not_affirmative"
            )

        event_id = contract_execution_event.get(
            "contract_execution_event_id"
        )

        if (
            event_id
            != paid_work_authorization.contract_execution_event_id
        ):
            blockers.append(
                "authorization:contract_event_mismatch"
            )

    def _validate_bridge(
        self,
        *,
        paid_work_authorization: PaidAssessmentWorkAuthorization,
        authorization_bridge: RealPaidAssessmentAuthorizationBridge,
        blockers: list[str],
    ) -> None:
        authorization_hierarchy = (
            paid_work_authorization.tenant_id,
            paid_work_authorization.client_id,
            paid_work_authorization.engagement_id,
            paid_work_authorization.assessment_id,
        )

        bridge_hierarchy = (
            authorization_bridge.tenant_id,
            authorization_bridge.client_id,
            authorization_bridge.engagement_id,
            authorization_bridge.assessment_id,
        )

        if bridge_hierarchy != authorization_hierarchy:
            blockers.append(
                "authorization_bridge:commercial_hierarchy_mismatch"
            )

        if (
            authorization_bridge.authorization_id
            != paid_work_authorization.authorization_id
        ):
            blockers.append(
                "authorization_bridge:authorization_id_mismatch"
            )

        if (
            authorization_bridge.paid_assessment_authorized
            is not True
        ):
            blockers.append(
                "authorization_bridge:not_affirmative"
            )

        if (
            authorization_bridge.bridge_status
            != BRIDGE_STATUS_READY
        ):
            blockers.append(
                "authorization_bridge:not_ready"
            )

    def _validate_execution_readiness(
        self,
        *,
        paid_work_authorization: PaidAssessmentWorkAuthorization,
        execution_readiness: FirstRealPaidAssessmentExecutionReadinessResult,
        blockers: list[str],
    ) -> None:
        authorization_hierarchy = (
            paid_work_authorization.tenant_id,
            paid_work_authorization.client_id,
            paid_work_authorization.engagement_id,
            paid_work_authorization.assessment_id,
        )

        readiness_hierarchy = (
            execution_readiness.tenant_id,
            execution_readiness.client_id,
            execution_readiness.engagement_id,
            execution_readiness.assessment_id,
        )

        if readiness_hierarchy != authorization_hierarchy:
            blockers.append(
                "execution_readiness:commercial_hierarchy_mismatch"
            )

        if (
            execution_readiness.status
            != FIRST_REAL_EXECUTION_STATUS_READY
        ):
            blockers.append(
                "execution_readiness:not_ready"
            )

        if (
            execution_readiness.ready_for_controlled_execution
            is not True
        ):
            blockers.append(
                "execution_readiness:"
                "controlled_execution_not_ready"
            )

        if execution_readiness.blockers:
            blockers.append(
                "execution_readiness:has_blockers"
            )

    def _require_text(
        self,
        value: Any,
        field_name: str,
    ) -> str:
        if not isinstance(value, str):
            raise FirstRealPaidAssessmentLaunchManifestError(
                f"{field_name} must be text"
            )

        normalized = value.strip()

        if not normalized:
            raise FirstRealPaidAssessmentLaunchManifestError(
                f"{field_name} is required"
            )

        return normalized


SERVICE_TYPE = (
    GovernanceFirstRealPaidAssessmentLaunchManifestService
)