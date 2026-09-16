from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from backend.app.gagf.governance_customer_trial_delivery_observation_receipt_store import (
    CustomerTrialDeliveryObservationReceipt,
    GovernanceCustomerTrialDeliveryObservationReceiptStore,
)


CUSTOMER_TRIAL_DELIVERY_OBSERVATION_SERVICE_ID = (
    "governance-customer-trial-delivery-observation-service"
)

CUSTOMER_TRIAL_DELIVERY_OBSERVATION_SERVICE_VERSION = "0.1.0"


@dataclass(
    frozen=True,
    slots=True,
)
class CustomerTrialDeliveryObservationStatusResult:
    receipt_found: bool
    receipt: (
        CustomerTrialDeliveryObservationReceipt
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
            "service":
                CUSTOMER_TRIAL_DELIVERY_OBSERVATION_SERVICE_ID,
            "version":
                CUSTOMER_TRIAL_DELIVERY_OBSERVATION_SERVICE_VERSION,
            "operation":
                "delivery_observation_status",
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
                "status_does_not_create_delivery_observation":
                    True,
                "status_does_not_recompute_pa005_delivery":
                    True,
                "status_does_not_infer_observation_from_delivery_status":
                    True,
                "status_is_not_delivery_approval":
                    True,
                "status_is_not_approved_for_human_delivery":
                    True,
                "status_is_not_delivery_authority":
                    True,
                "status_is_not_client_receipt":
                    True,
                "status_is_not_client_acknowledgment":
                    True,
                "status_is_not_client_response":
                    True,
                "status_is_not_closeout_authority":
                    True,
                "status_is_not_intervention_authority":
                    True,
                "pa005_remains_delivery_event_authority":
                    True,
                "pa012_remains_lifecycle_persistence_authority":
                    True,
            },
        }


class GovernanceCustomerTrialDeliveryObservationStatusService:
    """
    Read durable controlled-trial delivery-observation evidence.

    This service does not create or recompute delivery observation.

    A persisted PA-005 delivery event alone is insufficient to make
    receipt_found=True. Only a persisted governed 07B receipt does so.
    """

    def __init__(
        self,
        *,
        receipt_store:
            GovernanceCustomerTrialDeliveryObservationReceiptStore,
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
    ) -> CustomerTrialDeliveryObservationStatusResult:
        receipt = self._receipt_store.get(
            tenant_id=tenant_id,
            client_id=client_id,
            engagement_id=engagement_id,
            assessment_id=assessment_id,
        )

        return (
            CustomerTrialDeliveryObservationStatusResult(
                receipt_found=(
                    receipt is not None
                ),
                receipt=receipt,
            )
        )