from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from backend.app.gagf.governance_customer_trial_preflight_service import (
    GovernanceCustomerTrialPreflightService,
)
from backend.app.gagf.governance_paid_assessment_execution_handoff import (
    GovernancePaidAssessmentExecutionHandoffService,
    PaidAssessmentExecutionHandoff,
    PaidAssessmentWorkAuthorization,
)


CUSTOMER_TRIAL_EXECUTION_HANDOFF_BRIDGE_ID = (
    "governance-customer-trial-execution-handoff-bridge"
)

CUSTOMER_TRIAL_EXECUTION_HANDOFF_BRIDGE_VERSION = "0.1.0"


class CustomerTrialExecutionHandoffBridgeError(
    ValueError
):
    """
    Raised when customer-trial readiness
    cannot be bound safely to the existing
    paid-assessment execution handoff.
    """


@dataclass(
    frozen=True,
    slots=True,
)
class CustomerTrialExecutionHandoffBridgeResult:
    preflight_receipt_hash: str
    preflight_decision_payload_hash: str
    preflight_package_hash: str
    hierarchy_key: str
    handoff: PaidAssessmentExecutionHandoff

    def to_dict(
        self,
    ) -> dict[str, Any]:
        return {
            "bridge": (
                CUSTOMER_TRIAL_EXECUTION_HANDOFF_BRIDGE_ID
            ),
            "version": (
                CUSTOMER_TRIAL_EXECUTION_HANDOFF_BRIDGE_VERSION
            ),
            "hierarchy_key": self.hierarchy_key,
            "preflight_lineage": {
                "receipt_hash": (
                    self.preflight_receipt_hash
                ),
                "decision_payload_hash": (
                    self.preflight_decision_payload_hash
                ),
                "package_hash": (
                    self.preflight_package_hash
                ),
            },
            "handoff": self.handoff.to_dict(),
            "boundaries": {
                "preflight_receipt_is_not_execution_authority": True,
                "bridge_is_not_paid_work_authority": True,
                "bridge_is_not_contract_execution_authority": True,
                "bridge_is_not_assessment_execution": True,
                "existing_paid_execution_handoff_remains_authoritative": True,
                "intervention_authority_not_granted": True,
            },
        }


class GovernanceCustomerTrialExecutionHandoffBridge:
    """
    Bind a verified customer-trial readiness
    receipt to the repository's existing
    paid-assessment execution-handoff boundary.

    This bridge does not create paid-work
    authorization and does not execute an
    assessment.
    """

    def __init__(
        self,
        *,
        preflight_service:
            GovernanceCustomerTrialPreflightService,
        handoff_service:
            GovernancePaidAssessmentExecutionHandoffService
            | None = None,
    ) -> None:
        self._preflight_service = (
            preflight_service
        )

        self._handoff_service = (
            handoff_service
            or GovernancePaidAssessmentExecutionHandoffService()
        )

    def prepare_handoff(
        self,
        *,
        tenant_id: str,
        client_id: str,
        engagement_id: str,
        assessment_id: str,
        contract_execution_event:
            dict[str, Any],
        paid_work_authorization:
            PaidAssessmentWorkAuthorization,
        assessment_execution_request: Any,
    ) -> CustomerTrialExecutionHandoffBridgeResult:
        status = self._preflight_service.status(
            tenant_id=tenant_id,
            client_id=client_id,
            engagement_id=engagement_id,
            assessment_id=assessment_id,
        )

        if not status.receipt_found:
            raise (
                CustomerTrialExecutionHandoffBridgeError(
                    "customer trial execution handoff "
                    "requires a persisted preflight receipt"
                )
            )

        if status.receipt is None:
            raise (
                CustomerTrialExecutionHandoffBridgeError(
                    "customer trial preflight receipt "
                    "is unavailable"
                )
            )

        if status.trial_ready is not True:
            raise (
                CustomerTrialExecutionHandoffBridgeError(
                    "customer trial preflight "
                    "must be trial_ready"
                )
            )

        receipt = status.receipt

        expected_hierarchy = "/".join(
            (
                tenant_id,
                client_id,
                engagement_id,
                assessment_id,
            )
        )

        if (
            receipt.hierarchy_key
            != expected_hierarchy
        ):
            raise (
                CustomerTrialExecutionHandoffBridgeError(
                    "preflight receipt hierarchy "
                    "does not match requested handoff"
                )
            )

        request_context = getattr(
            assessment_execution_request,
            "context",
            None,
        )

        if request_context is None:
            raise (
                CustomerTrialExecutionHandoffBridgeError(
                    "assessment execution request "
                    "requires context"
                )
            )

        request_hierarchy = "/".join(
            (
                str(
                    getattr(
                        request_context,
                        "tenant_id",
                        "",
                    )
                ),
                str(
                    getattr(
                        request_context,
                        "client_id",
                        "",
                    )
                ),
                str(
                    getattr(
                        request_context,
                        "engagement_id",
                        "",
                    )
                ),
                str(
                    getattr(
                        request_context,
                        "assessment_id",
                        "",
                    )
                ),
            )
        )

        if request_hierarchy != expected_hierarchy:
            raise (
                CustomerTrialExecutionHandoffBridgeError(
                    "assessment execution request "
                    "hierarchy does not match "
                    "customer trial preflight receipt"
                )
            )

        decision_payload = (
            receipt.decision_payload
        )

        package_hash = (
            decision_payload.get(
                "package_hash"
            )
        )

        if (
            not isinstance(
                package_hash,
                str,
            )
            or len(package_hash) != 64
        ):
            raise (
                CustomerTrialExecutionHandoffBridgeError(
                    "preflight decision requires "
                    "a valid package_hash"
                )
            )

        handoff = (
            self._handoff_service.build_handoff(
                contract_execution_event=(
                    contract_execution_event
                ),
                paid_work_authorization=(
                    paid_work_authorization
                ),
                assessment_execution_request=(
                    assessment_execution_request
                ),
            )
        )

        return (
            CustomerTrialExecutionHandoffBridgeResult(
                preflight_receipt_hash=(
                    receipt.receipt_hash
                ),
                preflight_decision_payload_hash=(
                    receipt.decision_payload_hash
                ),
                preflight_package_hash=(
                    package_hash
                ),
                hierarchy_key=(
                    expected_hierarchy
                ),
                handoff=handoff,
            )
        )