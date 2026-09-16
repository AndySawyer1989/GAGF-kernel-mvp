from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from backend.app.gagf.governance_commercial_paid_assessment_delivery_readiness import (
    CommercialPaidAssessmentDeliveryReadiness,
)
from backend.app.gagf.governance_customer_trial_delivery_readiness import (
    GovernanceCustomerTrialDeliveryReadinessService,
)
from backend.app.gagf.governance_customer_trial_delivery_readiness_receipt_store import (
    CustomerTrialDeliveryReadinessReceipt,
    GovernanceCustomerTrialDeliveryReadinessReceiptStore,
)
from backend.app.gagf.governance_customer_trial_execution_observation_receipt_store import (
    GovernanceCustomerTrialExecutionObservationReceiptStore,
)


CUSTOMER_TRIAL_DELIVERY_READINESS_RECORDING_BRIDGE_ID = (
    "governance-customer-trial-delivery-readiness-recording-bridge"
)

CUSTOMER_TRIAL_DELIVERY_READINESS_RECORDING_BRIDGE_VERSION = "0.1.0"


class CustomerTrialDeliveryReadinessRecordingBridgeError(
    RuntimeError
):
    """Base controlled-trial readiness recording error."""


@dataclass(
    frozen=True,
    slots=True,
)
class CustomerTrialDeliveryReadinessRecordingResult:
    applicable: bool

    receipt: (
        CustomerTrialDeliveryReadinessReceipt
        | None
    )

    bridge_type: str = (
        CUSTOMER_TRIAL_DELIVERY_READINESS_RECORDING_BRIDGE_ID
    )

    version: str = (
        CUSTOMER_TRIAL_DELIVERY_READINESS_RECORDING_BRIDGE_VERSION
    )

    def to_dict(
        self,
    ) -> dict[str, Any]:
        return {
            "bridge_type":
                self.bridge_type,
            "version":
                self.version,
            "applicable":
                self.applicable,
            "receipt": (
                None
                if self.receipt is None
                else self.receipt.to_dict()
            ),
            "boundaries": {
                "bridge_observes_existing_commercial_readiness":
                    True,
                "bridge_does_not_compute_pa003_readiness":
                    True,
                "bridge_does_not_execute_assessment":
                    True,
                "bridge_does_not_recover_assessment":
                    True,
                "bridge_does_not_approve_delivery":
                    True,
                "bridge_does_not_create_approved_for_human_delivery":
                    True,
                "bridge_does_not_record_delivery":
                    True,
                "bridge_does_not_record_client_receipt":
                    True,
                "bridge_does_not_record_client_response":
                    True,
                "bridge_does_not_authorize_closeout":
                    True,
                "bridge_does_not_authorize_intervention":
                    True,
                "pa003_remains_delivery_readiness_authority":
                    True,
            },
        }


class GovernanceCustomerTrialDeliveryReadinessRecordingBridge:
    """
    Persist controlled-trial delivery-readiness evidence after the
    existing commercial PA-003 readiness service has already produced
    an authoritative readiness result.

    Ordinary paid assessments without a controlled-trial execution
    observation remain valid and are treated as not applicable.

    If controlled-trial observation evidence exists, exact correlation
    is mandatory and failures propagate closed.
    """

    def __init__(
        self,
        *,
        observation_receipt_store: (
            GovernanceCustomerTrialExecutionObservationReceiptStore
        ),
        readiness_projection_service: (
            GovernanceCustomerTrialDeliveryReadinessService
        ),
        readiness_receipt_store: (
            GovernanceCustomerTrialDeliveryReadinessReceiptStore
        ),
    ) -> None:
        if not isinstance(
            observation_receipt_store,
            GovernanceCustomerTrialExecutionObservationReceiptStore,
        ):
            raise CustomerTrialDeliveryReadinessRecordingBridgeError(
                "observation_receipt_store must be a "
                "GovernanceCustomerTrialExecutionObservationReceiptStore"
            )

        if not isinstance(
            readiness_projection_service,
            GovernanceCustomerTrialDeliveryReadinessService,
        ):
            raise CustomerTrialDeliveryReadinessRecordingBridgeError(
                "readiness_projection_service must be a "
                "GovernanceCustomerTrialDeliveryReadinessService"
            )

        if not isinstance(
            readiness_receipt_store,
            GovernanceCustomerTrialDeliveryReadinessReceiptStore,
        ):
            raise CustomerTrialDeliveryReadinessRecordingBridgeError(
                "readiness_receipt_store must be a "
                "GovernanceCustomerTrialDeliveryReadinessReceiptStore"
            )

        self._observation_receipt_store = (
            observation_receipt_store
        )

        self._readiness_projection_service = (
            readiness_projection_service
        )

        self._readiness_receipt_store = (
            readiness_receipt_store
        )

    def capture(
        self,
        *,
        commercial_readiness: (
            CommercialPaidAssessmentDeliveryReadiness
        ),
    ) -> CustomerTrialDeliveryReadinessRecordingResult:
        if not isinstance(
            commercial_readiness,
            CommercialPaidAssessmentDeliveryReadiness,
        ):
            raise CustomerTrialDeliveryReadinessRecordingBridgeError(
                "commercial_readiness must be a "
                "CommercialPaidAssessmentDeliveryReadiness"
            )

        observation_receipt = (
            self._observation_receipt_store.get(
                tenant_id=(
                    commercial_readiness.tenant_id
                ),
                client_id=(
                    commercial_readiness.client_id
                ),
                engagement_id=(
                    commercial_readiness.engagement_id
                ),
                assessment_id=(
                    commercial_readiness.assessment_id
                ),
            )
        )

        if observation_receipt is None:
            return (
                CustomerTrialDeliveryReadinessRecordingResult(
                    applicable=False,
                    receipt=None,
                )
            )

        controlled_trial_readiness = (
            self._readiness_projection_service.correlate(
                observation_receipt=(
                    observation_receipt
                ),
                commercial_readiness=(
                    commercial_readiness
                ),
            )
        )

        receipt = (
            self._readiness_receipt_store.put(
                readiness=(
                    controlled_trial_readiness
                )
            )
        )

        return (
            CustomerTrialDeliveryReadinessRecordingResult(
                applicable=True,
                receipt=receipt,
            )
        )