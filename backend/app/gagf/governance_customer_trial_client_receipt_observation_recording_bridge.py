from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from backend.app.gagf.governance_commercial_paid_assessment_client_acknowledgment import (
    CommercialPaidAssessmentClientAcknowledgmentResult,
)
from backend.app.gagf.governance_customer_trial_client_receipt_observation import (
    GovernanceCustomerTrialClientReceiptObservationService,
)
from backend.app.gagf.governance_customer_trial_client_receipt_observation_receipt_store import (
    CustomerTrialClientReceiptObservationReceipt,
    GovernanceCustomerTrialClientReceiptObservationReceiptStore,
)
from backend.app.gagf.governance_customer_trial_delivery_observation_receipt_store import (
    GovernanceCustomerTrialDeliveryObservationReceiptStore,
)


CUSTOMER_TRIAL_CLIENT_RECEIPT_OBSERVATION_RECORDING_BRIDGE_ID = (
    "governance-customer-trial-client-receipt-observation-recording-bridge"
)

CUSTOMER_TRIAL_CLIENT_RECEIPT_OBSERVATION_RECORDING_BRIDGE_VERSION = "0.1.0"


class CustomerTrialClientReceiptObservationRecordingBridgeError(
    RuntimeError
):
    """Base controlled-trial client-receipt observer error."""


@dataclass(
    frozen=True,
    slots=True,
)
class CustomerTrialClientReceiptObservationRecordingResult:
    applicable: bool
    receipt: (
        CustomerTrialClientReceiptObservationReceipt
        | None
    )

    bridge_type: str = (
        CUSTOMER_TRIAL_CLIENT_RECEIPT_OBSERVATION_RECORDING_BRIDGE_ID
    )

    version: str = (
        CUSTOMER_TRIAL_CLIENT_RECEIPT_OBSERVATION_RECORDING_BRIDGE_VERSION
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
                "bridge_observes_existing_pa006_receipt":
                    True,
                "bridge_does_not_create_client_receipt":
                    True,
                "bridge_does_not_record_client_response":
                    True,
                "bridge_does_not_accept_findings":
                    True,
                "bridge_does_not_accept_recommendations":
                    True,
                "bridge_does_not_authorize_closeout":
                    True,
                "bridge_does_not_authorize_intervention":
                    True,
                "bridge_does_not_verify_roi":
                    True,
                "bridge_does_not_verify_customer_outcome":
                    True,
                "pa006_remains_client_receipt_authority":
                    True,
                "pa012_remains_lifecycle_persistence_authority":
                    True,
            },
        }


class GovernanceCustomerTrialClientReceiptObservationRecordingBridge:
    """
    Observe an already-authoritative commercial PA-006 receipt result.

    Ordinary paid assessments without 04J-07 controlled-trial delivery
    observation remain valid and are treated as not applicable.

    If 04J-07 evidence exists, exact 08A correlation is mandatory.
    """

    def __init__(
        self,
        *,
        delivery_observation_receipt_store: (
            GovernanceCustomerTrialDeliveryObservationReceiptStore
        ),
        observation_service: (
            GovernanceCustomerTrialClientReceiptObservationService
        ),
        observation_receipt_store: (
            GovernanceCustomerTrialClientReceiptObservationReceiptStore
        ),
    ) -> None:
        if not isinstance(
            delivery_observation_receipt_store,
            GovernanceCustomerTrialDeliveryObservationReceiptStore,
        ):
            raise CustomerTrialClientReceiptObservationRecordingBridgeError(
                "delivery_observation_receipt_store must be a "
                "GovernanceCustomerTrialDeliveryObservationReceiptStore"
            )

        if not isinstance(
            observation_service,
            GovernanceCustomerTrialClientReceiptObservationService,
        ):
            raise CustomerTrialClientReceiptObservationRecordingBridgeError(
                "observation_service must be a "
                "GovernanceCustomerTrialClientReceiptObservationService"
            )

        if not isinstance(
            observation_receipt_store,
            GovernanceCustomerTrialClientReceiptObservationReceiptStore,
        ):
            raise CustomerTrialClientReceiptObservationRecordingBridgeError(
                "observation_receipt_store must be a "
                "GovernanceCustomerTrialClientReceiptObservationReceiptStore"
            )

        self._delivery_observation_receipt_store = (
            delivery_observation_receipt_store
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
        commercial_client_acknowledgment: (
            CommercialPaidAssessmentClientAcknowledgmentResult
        ),
    ) -> CustomerTrialClientReceiptObservationRecordingResult:
        if not isinstance(
            commercial_client_acknowledgment,
            CommercialPaidAssessmentClientAcknowledgmentResult,
        ):
            raise CustomerTrialClientReceiptObservationRecordingBridgeError(
                "commercial_client_acknowledgment must be a "
                "CommercialPaidAssessmentClientAcknowledgmentResult"
            )

        delivery_receipt = (
            self._delivery_observation_receipt_store.get(
                tenant_id=(
                    commercial_client_acknowledgment.tenant_id
                ),
                client_id=(
                    commercial_client_acknowledgment.client_id
                ),
                engagement_id=(
                    commercial_client_acknowledgment.engagement_id
                ),
                assessment_id=(
                    commercial_client_acknowledgment.assessment_id
                ),
            )
        )

        if delivery_receipt is None:
            return (
                CustomerTrialClientReceiptObservationRecordingResult(
                    applicable=False,
                    receipt=None,
                )
            )

        observation = (
            self._observation_service.observe(
                delivery_observation_receipt=(
                    delivery_receipt
                ),
                commercial_client_acknowledgment=(
                    commercial_client_acknowledgment
                ),
            )
        )

        receipt = (
            self._observation_receipt_store.put(
                observation=observation
            )
        )

        return (
            CustomerTrialClientReceiptObservationRecordingResult(
                applicable=True,
                receipt=receipt,
            )
        )