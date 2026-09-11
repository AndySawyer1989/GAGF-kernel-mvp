from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from backend.app.gagf.governance_customer_trial_execution_handoff_bridge import (
    CustomerTrialExecutionHandoffBridgeResult,
    GovernanceCustomerTrialExecutionHandoffBridge,
)
from backend.app.gagf.governance_customer_trial_execution_handoff_receipt_store import (
    CustomerTrialExecutionHandoffReceipt,
    GovernanceCustomerTrialExecutionHandoffReceiptStore,
)
from backend.app.gagf.governance_paid_assessment_execution_handoff import (
    PaidAssessmentWorkAuthorization,
)


CUSTOMER_TRIAL_EXECUTION_HANDOFF_SERVICE_ID = (
    "governance-customer-trial-execution-handoff-service"
)

CUSTOMER_TRIAL_EXECUTION_HANDOFF_SERVICE_VERSION = "0.1.0"


@dataclass(
    frozen=True,
    slots=True,
)
class CustomerTrialExecutionHandoffPreparationResult:
    bridge_result: CustomerTrialExecutionHandoffBridgeResult
    receipt: CustomerTrialExecutionHandoffReceipt

    @property
    def hierarchy_key(
        self,
    ) -> str:
        return self.receipt.hierarchy_key

    def to_dict(
        self,
    ) -> dict[str, Any]:
        return {
            "service": (
                CUSTOMER_TRIAL_EXECUTION_HANDOFF_SERVICE_ID
            ),
            "version": (
                CUSTOMER_TRIAL_EXECUTION_HANDOFF_SERVICE_VERSION
            ),
            "operation":
                "prepare_execution_handoff",
            "hierarchy_key":
                self.hierarchy_key,
            "bridge_result":
                self.bridge_result.to_dict(),
            "receipt":
                self.receipt.to_dict(),
            "boundaries": {
                "service_is_not_execution_authority":
                    True,
                "service_is_not_paid_work_authority":
                    True,
                "service_is_not_contract_authority":
                    True,
                "service_does_not_execute_assessment":
                    True,
                "service_does_not_authorize_intervention":
                    True,
                (
                    "existing_paid_execution_handoff_"
                    "remains_authoritative"
                ):
                    True,
            },
        }


@dataclass(
    frozen=True,
    slots=True,
)
class CustomerTrialExecutionHandoffStatusResult:
    receipt_found: bool
    receipt: (
        CustomerTrialExecutionHandoffReceipt
        | None
    )

    @property
    def hierarchy_key(
        self,
    ) -> str | None:
        if self.receipt is None:
            return None

        return self.receipt.hierarchy_key

    def to_dict(
        self,
    ) -> dict[str, Any]:
        return {
            "service": (
                CUSTOMER_TRIAL_EXECUTION_HANDOFF_SERVICE_ID
            ),
            "version": (
                CUSTOMER_TRIAL_EXECUTION_HANDOFF_SERVICE_VERSION
            ),
            "operation":
                "execution_handoff_status",
            "receipt_found":
                self.receipt_found,
            "hierarchy_key":
                self.hierarchy_key,
            "receipt": (
                None
                if self.receipt is None
                else self.receipt.to_dict()
            ),
            "boundaries": {
                "status_is_read_only":
                    True,
                "status_is_not_execution_authority":
                    True,
                "status_is_not_recovery_authority":
                    True,
                "status_is_not_closeout_authority":
                    True,
                "status_is_not_intervention_authority":
                    True,
            },
        }


class GovernanceCustomerTrialExecutionHandoffService:
    """
    Prepare and persist the controlled
    customer-trial execution handoff.

    This service does not execute an assessment.

    It delegates governed handoff construction
    to the existing paid-assessment execution
    handoff authority and persists only the
    resulting audit receipt.
    """

    def __init__(
        self,
        *,
        bridge:
            GovernanceCustomerTrialExecutionHandoffBridge,
        receipt_store:
            GovernanceCustomerTrialExecutionHandoffReceiptStore,
    ) -> None:
        self._bridge = bridge
        self._receipt_store = receipt_store

    def prepare(
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
    ) -> CustomerTrialExecutionHandoffPreparationResult:
        bridge_result = (
            self._bridge.prepare_handoff(
                tenant_id=tenant_id,
                client_id=client_id,
                engagement_id=engagement_id,
                assessment_id=assessment_id,
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

        receipt = self._receipt_store.put(
            bridge_result=bridge_result
        )

        return (
            CustomerTrialExecutionHandoffPreparationResult(
                bridge_result=bridge_result,
                receipt=receipt,
            )
        )

    def status(
        self,
        *,
        tenant_id: str,
        client_id: str,
        engagement_id: str,
        assessment_id: str,
    ) -> CustomerTrialExecutionHandoffStatusResult:
        receipt = self._receipt_store.get(
            tenant_id=tenant_id,
            client_id=client_id,
            engagement_id=engagement_id,
            assessment_id=assessment_id,
        )

        return (
            CustomerTrialExecutionHandoffStatusResult(
                receipt_found=(
                    receipt is not None
                ),
                receipt=receipt,
            )
        )