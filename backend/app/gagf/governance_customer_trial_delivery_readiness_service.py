from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from backend.app.gagf.governance_customer_trial_delivery_readiness_receipt_store import (
    CustomerTrialDeliveryReadinessReceipt,
    GovernanceCustomerTrialDeliveryReadinessReceiptStore,
)


CUSTOMER_TRIAL_DELIVERY_READINESS_SERVICE_ID = (
    "governance-customer-trial-delivery-readiness-service"
)

CUSTOMER_TRIAL_DELIVERY_READINESS_SERVICE_VERSION = "0.1.0"


@dataclass(
    frozen=True,
    slots=True,
)
class CustomerTrialDeliveryReadinessStatusResult:
    receipt_found: bool
    receipt: (
        CustomerTrialDeliveryReadinessReceipt
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
                CUSTOMER_TRIAL_DELIVERY_READINESS_SERVICE_ID
            ),
            "version": (
                CUSTOMER_TRIAL_DELIVERY_READINESS_SERVICE_VERSION
            ),
            "operation":
                "delivery_readiness_status",
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
                "status_does_not_create_readiness":
                    True,
                "status_does_not_recompute_pa003_readiness":
                    True,
                "status_does_not_infer_readiness_from_execution_observation":
                    True,
                "status_is_not_execution_authority":
                    True,
                "status_is_not_recovery_authority":
                    True,
                "status_is_not_delivery_approval":
                    True,
                "status_is_not_approved_for_human_delivery":
                    True,
                "status_is_not_delivery_authority":
                    True,
                "status_is_not_client_receipt":
                    True,
                "status_is_not_client_response":
                    True,
                "status_is_not_closeout_authority":
                    True,
                "status_is_not_intervention_authority":
                    True,
                "pa003_remains_delivery_readiness_authority":
                    True,
            },
        }


class GovernanceCustomerTrialDeliveryReadinessStatusService:
    """
    Read durable controlled-customer-trial delivery-readiness evidence.

    This service does not create readiness.

    It does not rerun PA-003 delivery readiness and does not infer
    readiness merely because an execution-observation receipt exists.

    It does not execute, recover, approve delivery, deliver,
    record client receipt/response, close out, or authorize
    intervention.
    """

    def __init__(
        self,
        *,
        receipt_store:
            GovernanceCustomerTrialDeliveryReadinessReceiptStore,
    ) -> None:
        self._receipt_store = (
            receipt_store
        )

    def status(
        self,
        *,
        tenant_id: str,
        client_id: str,
        engagement_id: str,
        assessment_id: str,
    ) -> CustomerTrialDeliveryReadinessStatusResult:
        receipt = self._receipt_store.get(
            tenant_id=tenant_id,
            client_id=client_id,
            engagement_id=engagement_id,
            assessment_id=assessment_id,
        )

        return (
            CustomerTrialDeliveryReadinessStatusResult(
                receipt_found=(
                    receipt is not None
                ),
                receipt=receipt,
            )
        )