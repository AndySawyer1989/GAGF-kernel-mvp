from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from backend.app.gagf.governance_customer_trial_execution_observation_receipt_store import (
    CustomerTrialExecutionObservationReceipt,
    GovernanceCustomerTrialExecutionObservationReceiptStore,
)


CUSTOMER_TRIAL_EXECUTION_OBSERVATION_SERVICE_ID = (
    "governance-customer-trial-execution-observation-service"
)

CUSTOMER_TRIAL_EXECUTION_OBSERVATION_SERVICE_VERSION = "0.1.0"


@dataclass(
    frozen=True,
    slots=True,
)
class CustomerTrialExecutionObservationStatusResult:
    receipt_found: bool
    receipt: (
        CustomerTrialExecutionObservationReceipt
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
                CUSTOMER_TRIAL_EXECUTION_OBSERVATION_SERVICE_ID
            ),
            "version": (
                CUSTOMER_TRIAL_EXECUTION_OBSERVATION_SERVICE_VERSION
            ),
            "operation":
                "execution_observation_status",
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
                "status_is_not_delivery_authority":
                    True,
                "status_is_not_closeout_authority":
                    True,
                "status_is_not_intervention_authority":
                    True,
                "status_does_not_infer_execution_from_handoff":
                    True,
            },
        }


class GovernanceCustomerTrialExecutionObservationStatusService:
    """
    Read durable controlled-customer-trial execution
    observation evidence.

    This service does not create an observation.

    It does not execute, recover, deliver, close out,
    recommend, or authorize intervention.

    A customer-trial execution handoff existing by itself
    is not sufficient to report execution observed.
    """

    def __init__(
        self,
        *,
        receipt_store:
            GovernanceCustomerTrialExecutionObservationReceiptStore,
    ) -> None:
        self._receipt_store = receipt_store

    def status(
        self,
        *,
        tenant_id: str,
        client_id: str,
        engagement_id: str,
        assessment_id: str,
    ) -> CustomerTrialExecutionObservationStatusResult:
        receipt = self._receipt_store.get(
            tenant_id=tenant_id,
            client_id=client_id,
            engagement_id=engagement_id,
            assessment_id=assessment_id,
        )

        return (
            CustomerTrialExecutionObservationStatusResult(
                receipt_found=(
                    receipt is not None
                ),
                receipt=receipt,
            )
        )