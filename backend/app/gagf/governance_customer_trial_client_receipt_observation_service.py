from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from backend.app.gagf.governance_customer_trial_client_receipt_observation_receipt_store import (
    CustomerTrialClientReceiptObservationReceipt,
    GovernanceCustomerTrialClientReceiptObservationReceiptStore,
)


CUSTOMER_TRIAL_CLIENT_RECEIPT_OBSERVATION_SERVICE_ID = (
    "governance-customer-trial-client-receipt-observation-service"
)

CUSTOMER_TRIAL_CLIENT_RECEIPT_OBSERVATION_SERVICE_VERSION = "0.1.0"


@dataclass(
    frozen=True,
    slots=True,
)
class CustomerTrialClientReceiptObservationStatusResult:
    receipt_found: bool
    receipt: (
        CustomerTrialClientReceiptObservationReceipt
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
                CUSTOMER_TRIAL_CLIENT_RECEIPT_OBSERVATION_SERVICE_ID,
            "version":
                CUSTOMER_TRIAL_CLIENT_RECEIPT_OBSERVATION_SERVICE_VERSION,
            "operation":
                "client_receipt_observation_status",
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
                "status_does_not_create_client_receipt_observation":
                    True,
                "status_does_not_recompute_pa006_receipt":
                    True,
                "status_does_not_infer_receipt_from_delivery":
                    True,
                "status_is_not_client_response":
                    True,
                "status_is_not_findings_acceptance":
                    True,
                "status_is_not_recommendation_acceptance":
                    True,
                "status_is_not_client_satisfaction":
                    True,
                "status_is_not_closeout_authority":
                    True,
                "status_is_not_intervention_authority":
                    True,
                "status_is_not_roi_verification":
                    True,
                "status_is_not_customer_outcome_verification":
                    True,
                "pa006_remains_client_receipt_authority":
                    True,
                "pa012_remains_lifecycle_persistence_authority":
                    True,
            },
        }


class GovernanceCustomerTrialClientReceiptObservationStatusService:
    """
    Read persisted controlled-trial client-receipt observation evidence.

    This service does not create or recompute client receipt.

    A delivered assessment or PA-006 repository artifact alone does not
    make receipt_found=True here. Only a persisted 08B observation
    receipt does so.
    """

    def __init__(
        self,
        *,
        receipt_store:
            GovernanceCustomerTrialClientReceiptObservationReceiptStore,
    ) -> None:
        self._receipt_store = receipt_store

    def status(
        self,
        *,
        tenant_id: str,
        client_id: str,
        engagement_id: str,
        assessment_id: str,
    ) -> CustomerTrialClientReceiptObservationStatusResult:
        receipt = self._receipt_store.get(
            tenant_id=tenant_id,
            client_id=client_id,
            engagement_id=engagement_id,
            assessment_id=assessment_id,
        )

        return CustomerTrialClientReceiptObservationStatusResult(
            receipt_found=(
                receipt is not None
            ),
            receipt=receipt,
        )