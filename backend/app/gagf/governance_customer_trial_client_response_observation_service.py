from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from backend.app.gagf.governance_customer_trial_client_response_observation_receipt_store import (
    CustomerTrialClientResponseObservationReceipt,
    GovernanceCustomerTrialClientResponseObservationReceiptStore,
)


CUSTOMER_TRIAL_CLIENT_RESPONSE_OBSERVATION_SERVICE_ID = (
    "governance-customer-trial-client-response-observation-service"
)

CUSTOMER_TRIAL_CLIENT_RESPONSE_OBSERVATION_SERVICE_VERSION = "0.1.0"


@dataclass(
    frozen=True,
    slots=True,
)
class CustomerTrialClientResponseObservationStatusResult:
    receipt_found: bool
    receipt: (
        CustomerTrialClientResponseObservationReceipt
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
                CUSTOMER_TRIAL_CLIENT_RESPONSE_OBSERVATION_SERVICE_ID,
            "version":
                CUSTOMER_TRIAL_CLIENT_RESPONSE_OBSERVATION_SERVICE_VERSION,
            "operation":
                "client_response_observation_status",
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
                "status_does_not_create_client_response_observation":
                    True,
                "status_does_not_recompute_pa007_response":
                    True,
                "status_does_not_infer_response_from_receipt":
                    True,
                "status_does_not_validate_findings":
                    True,
                "status_does_not_implement_recommendations":
                    True,
                "status_is_not_closeout_authority":
                    True,
                "status_is_not_intervention_authority":
                    True,
                "status_is_not_roi_verification":
                    True,
                "status_is_not_customer_outcome_verification":
                    True,
                "pa007_remains_client_response_authority":
                    True,
                "pa012_remains_lifecycle_persistence_authority":
                    True,
            },
        }


class GovernanceCustomerTrialClientResponseObservationStatusService:
    """
    Read persisted controlled-trial client-response observation evidence.

    Only a persisted 09B receipt makes receipt_found=True.
    This service does not rerun PA-007 or infer response from PA-006.
    """

    def __init__(
        self,
        *,
        receipt_store:
            GovernanceCustomerTrialClientResponseObservationReceiptStore,
    ) -> None:
        self._receipt_store = receipt_store

    def status(
        self,
        *,
        tenant_id: str,
        client_id: str,
        engagement_id: str,
        assessment_id: str,
    ) -> CustomerTrialClientResponseObservationStatusResult:
        receipt = self._receipt_store.get(
            tenant_id=tenant_id,
            client_id=client_id,
            engagement_id=engagement_id,
            assessment_id=assessment_id,
        )

        return CustomerTrialClientResponseObservationStatusResult(
            receipt_found=(
                receipt is not None
            ),
            receipt=receipt,
        )