from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from backend.app.gagf.governance_commercial_paid_assessment_delivery_recording import (
    CommercialPaidAssessmentDeliveryRecording,
)
from backend.app.gagf.governance_customer_trial_delivery_observation import (
    GovernanceCustomerTrialDeliveryObservationService,
)
from backend.app.gagf.governance_customer_trial_delivery_observation_receipt_store import (
    CustomerTrialDeliveryObservationReceipt,
    GovernanceCustomerTrialDeliveryObservationReceiptStore,
)
from backend.app.gagf.governance_customer_trial_delivery_readiness_receipt_store import (
    GovernanceCustomerTrialDeliveryReadinessReceiptStore,
)


CUSTOMER_TRIAL_DELIVERY_OBSERVATION_RECORDING_BRIDGE_ID = (
    "governance-customer-trial-delivery-observation-recording-bridge"
)

CUSTOMER_TRIAL_DELIVERY_OBSERVATION_RECORDING_BRIDGE_VERSION = "0.1.0"


class CustomerTrialDeliveryObservationRecordingBridgeError(
    RuntimeError
):
    """Base controlled-trial delivery observation recording error."""


@dataclass(
    frozen=True,
    slots=True,
)
class CustomerTrialDeliveryObservationRecordingResult:
    applicable: bool
    receipt: (
        CustomerTrialDeliveryObservationReceipt
        | None
    )

    bridge_type: str = (
        CUSTOMER_TRIAL_DELIVERY_OBSERVATION_RECORDING_BRIDGE_ID
    )

    version: str = (
        CUSTOMER_TRIAL_DELIVERY_OBSERVATION_RECORDING_BRIDGE_VERSION
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
                "bridge_observes_existing_pa005_delivery":
                    True,
                "bridge_does_not_approve_delivery":
                    True,
                "bridge_does_not_create_approved_for_human_delivery":
                    True,
                "bridge_does_not_deliver":
                    True,
                "bridge_does_not_create_client_receipt":
                    True,
                "bridge_does_not_create_client_acknowledgment":
                    True,
                "bridge_does_not_create_client_response":
                    True,
                "bridge_does_not_authorize_closeout":
                    True,
                "bridge_does_not_authorize_intervention":
                    True,
                "pa005_remains_delivery_event_authority":
                    True,
                "pa012_remains_lifecycle_persistence_authority":
                    True,
            },
        }


class GovernanceCustomerTrialDeliveryObservationRecordingBridge:
    """
    Observe an already-authoritative commercial PA-005 delivery result.

    If no controlled-trial delivery-readiness receipt exists for the
    hierarchy, ordinary paid delivery remains valid and this bridge is
    not applicable.

    If controlled-trial readiness evidence exists, exact correlation
    is mandatory and failures propagate closed.
    """

    def __init__(
        self,
        *,
        readiness_receipt_store: (
            GovernanceCustomerTrialDeliveryReadinessReceiptStore
        ),
        observation_service: (
            GovernanceCustomerTrialDeliveryObservationService
        ),
        observation_receipt_store: (
            GovernanceCustomerTrialDeliveryObservationReceiptStore
        ),
    ) -> None:
        if not isinstance(
            readiness_receipt_store,
            GovernanceCustomerTrialDeliveryReadinessReceiptStore,
        ):
            raise CustomerTrialDeliveryObservationRecordingBridgeError(
                "readiness_receipt_store must be a "
                "GovernanceCustomerTrialDeliveryReadinessReceiptStore"
            )

        if not isinstance(
            observation_service,
            GovernanceCustomerTrialDeliveryObservationService,
        ):
            raise CustomerTrialDeliveryObservationRecordingBridgeError(
                "observation_service must be a "
                "GovernanceCustomerTrialDeliveryObservationService"
            )

        if not isinstance(
            observation_receipt_store,
            GovernanceCustomerTrialDeliveryObservationReceiptStore,
        ):
            raise CustomerTrialDeliveryObservationRecordingBridgeError(
                "observation_receipt_store must be a "
                "GovernanceCustomerTrialDeliveryObservationReceiptStore"
            )

        self._readiness_receipt_store = (
            readiness_receipt_store
        )
        self._observation_service = (
            observation_service
        )
        self._observation_receipt_store = (
            observation_receipt_store
        )

    def capture(
        self,
        *,
        commercial_delivery_recording: (
            CommercialPaidAssessmentDeliveryRecording
        ),
    ) -> CustomerTrialDeliveryObservationRecordingResult:
        if not isinstance(
            commercial_delivery_recording,
            CommercialPaidAssessmentDeliveryRecording,
        ):
            raise CustomerTrialDeliveryObservationRecordingBridgeError(
                "commercial_delivery_recording must be a "
                "CommercialPaidAssessmentDeliveryRecording"
            )

        readiness_receipt = (
            self._readiness_receipt_store.get(
                tenant_id=(
                    commercial_delivery_recording.tenant_id
                ),
                client_id=(
                    commercial_delivery_recording.client_id
                ),
                engagement_id=(
                    commercial_delivery_recording.engagement_id
                ),
                assessment_id=(
                    commercial_delivery_recording.assessment_id
                ),
            )
        )

        if readiness_receipt is None:
            return (
                CustomerTrialDeliveryObservationRecordingResult(
                    applicable=False,
                    receipt=None,
                )
            )

        observation = (
            self._observation_service.observe(
                readiness_receipt=(
                    readiness_receipt
                ),
                commercial_delivery_recording=(
                    commercial_delivery_recording
                ),
            )
        )

        receipt = (
            self._observation_receipt_store.put(
                observation=observation
            )
        )

        return (
            CustomerTrialDeliveryObservationRecordingResult(
                applicable=True,
                receipt=receipt,
            )
        )