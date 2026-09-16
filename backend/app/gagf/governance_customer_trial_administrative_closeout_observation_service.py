from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from backend.app.gagf.governance_customer_trial_administrative_closeout_observation_receipt_store import (
    CustomerTrialAdministrativeCloseoutObservationReceipt,
    GovernanceCustomerTrialAdministrativeCloseoutObservationReceiptStore,
)


CUSTOMER_TRIAL_ADMINISTRATIVE_CLOSEOUT_OBSERVATION_SERVICE_ID = (
    "governance-customer-trial-administrative-closeout-observation-service"
)

CUSTOMER_TRIAL_ADMINISTRATIVE_CLOSEOUT_OBSERVATION_SERVICE_VERSION = "0.1.0"


@dataclass(
    frozen=True,
    slots=True,
)
class CustomerTrialAdministrativeCloseoutObservationStatusResult:
    receipt_found: bool
    controlled_trial_complete: bool

    receipt: (
        CustomerTrialAdministrativeCloseoutObservationReceipt
        | None
    )

    @property
    def hierarchy_key(
        self,
    ) -> str | None:
        if self.receipt is None:
            return None

        return self.receipt.hierarchy_key

    @property
    def controlled_trial_status(
        self,
    ) -> str | None:
        if self.receipt is None:
            return None

        return self.receipt.controlled_trial_status

    def to_dict(
        self,
    ) -> dict[str, Any]:
        return {
            "service":
                CUSTOMER_TRIAL_ADMINISTRATIVE_CLOSEOUT_OBSERVATION_SERVICE_ID,

            "version":
                CUSTOMER_TRIAL_ADMINISTRATIVE_CLOSEOUT_OBSERVATION_SERVICE_VERSION,

            "operation":
                "controlled_trial_completion_status",

            "receipt_found":
                self.receipt_found,

            "controlled_trial_complete":
                self.controlled_trial_complete,

            "controlled_trial_status":
                self.controlled_trial_status,

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

                "status_does_not_create_closeout":
                    True,

                "status_does_not_recompute_pa010_closeout":
                    True,

                "status_does_not_infer_closeout_from_client_response":
                    True,

                "controlled_trial_complete_is_administrative_only":
                    True,

                "status_is_not_findings_validation":
                    True,

                "status_is_not_recommendation_implementation":
                    True,

                "status_is_not_intervention_request":
                    True,

                "status_is_not_intervention_authority":
                    True,

                "status_is_not_execution_authority":
                    True,

                "status_is_not_causal_success":
                    True,

                "status_is_not_roi_verification":
                    True,

                "status_is_not_remediation_success":
                    True,

                "status_is_not_customer_outcome_verification":
                    True,

                "pa010_remains_administrative_closeout_authority":
                    True,

                "pa012_remains_lifecycle_persistence_authority":
                    True,

                "pa013_remains_operator_coordination_authority":
                    True,
            },
        }


class GovernanceCustomerTrialAdministrativeCloseoutObservationStatusService:
    """
    Read persisted controlled-trial administrative-closeout evidence.

    Only a durable 10B receipt can establish controlled_trial_complete=True.

    This service never executes or reconstructs PA-010.
    """

    def __init__(
        self,
        *,
        receipt_store:
            GovernanceCustomerTrialAdministrativeCloseoutObservationReceiptStore,
    ) -> None:
        self._receipt_store = receipt_store

    def status(
        self,
        *,
        tenant_id: str,
        client_id: str,
        engagement_id: str,
        assessment_id: str,
    ) -> CustomerTrialAdministrativeCloseoutObservationStatusResult:
        receipt = self._receipt_store.get(
            tenant_id=tenant_id,
            client_id=client_id,
            engagement_id=engagement_id,
            assessment_id=assessment_id,
        )

        if receipt is None:
            return (
                CustomerTrialAdministrativeCloseoutObservationStatusResult(
                    receipt_found=False,
                    controlled_trial_complete=False,
                    receipt=None,
                )
            )

        controlled_trial_complete = (
            receipt.controlled_trial_complete is True
            and receipt.observation_status
            == "administrative_closeout_observed"
            and receipt.controlled_trial_status
            == "controlled_trial_complete"
            and receipt.closeout_status
            == "assessment_closed"
            and receipt.repository_chain_valid
            is True
        )

        return (
            CustomerTrialAdministrativeCloseoutObservationStatusResult(
                receipt_found=True,
                controlled_trial_complete=(
                    controlled_trial_complete
                ),
                receipt=receipt,
            )
        )