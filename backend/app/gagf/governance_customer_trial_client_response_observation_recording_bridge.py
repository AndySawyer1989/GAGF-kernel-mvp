from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from backend.app.gagf.governance_commercial_paid_assessment_client_response import (
    CommercialPaidAssessmentClientResponseResult,
)
from backend.app.gagf.governance_customer_trial_client_receipt_observation_receipt_store import (
    GovernanceCustomerTrialClientReceiptObservationReceiptStore,
)
from backend.app.gagf.governance_customer_trial_client_response_observation import (
    GovernanceCustomerTrialClientResponseObservationService,
)
from backend.app.gagf.governance_customer_trial_client_response_observation_receipt_store import (
    CustomerTrialClientResponseObservationReceipt,
    GovernanceCustomerTrialClientResponseObservationReceiptStore,
)


CUSTOMER_TRIAL_CLIENT_RESPONSE_OBSERVATION_RECORDING_BRIDGE_ID = (
    "governance-customer-trial-client-response-observation-recording-bridge"
)

CUSTOMER_TRIAL_CLIENT_RESPONSE_OBSERVATION_RECORDING_BRIDGE_VERSION = "0.1.0"


class CustomerTrialClientResponseObservationRecordingBridgeError(
    RuntimeError
):
    """Base controlled-trial client-response observer error."""


@dataclass(
    frozen=True,
    slots=True,
)
class CustomerTrialClientResponseObservationRecordingResult:
    applicable: bool

    receipt: (
        CustomerTrialClientResponseObservationReceipt
        | None
    )

    bridge_type: str = (
        CUSTOMER_TRIAL_CLIENT_RESPONSE_OBSERVATION_RECORDING_BRIDGE_ID
    )

    version: str = (
        CUSTOMER_TRIAL_CLIENT_RESPONSE_OBSERVATION_RECORDING_BRIDGE_VERSION
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
                "bridge_observes_existing_pa007_response":
                    True,

                "bridge_does_not_create_client_response":
                    True,

                "bridge_does_not_validate_findings":
                    True,

                "bridge_does_not_implement_recommendations":
                    True,

                "bridge_does_not_authorize_closeout":
                    True,

                "bridge_does_not_authorize_intervention":
                    True,

                "bridge_does_not_verify_roi":
                    True,

                "bridge_does_not_verify_customer_outcome":
                    True,

                "pa007_remains_client_response_authority":
                    True,

                "pa012_remains_lifecycle_persistence_authority":
                    True,
            },
        }


class GovernanceCustomerTrialClientResponseObservationRecordingBridge:
    """
    Observe an already-authoritative commercial PA-007 response.

    Ordinary paid assessments without a controlled-trial 08B receipt
    remain valid and are treated as not applicable.

    If an 08B receipt exists, exact 09A correlation is mandatory.
    """

    def __init__(
        self,
        *,
        client_receipt_observation_receipt_store: (
            GovernanceCustomerTrialClientReceiptObservationReceiptStore
        ),
        observation_service: (
            GovernanceCustomerTrialClientResponseObservationService
        ),
        observation_receipt_store: (
            GovernanceCustomerTrialClientResponseObservationReceiptStore
        ),
    ) -> None:
        if not isinstance(
            client_receipt_observation_receipt_store,
            GovernanceCustomerTrialClientReceiptObservationReceiptStore,
        ):
            raise CustomerTrialClientResponseObservationRecordingBridgeError(
                "client_receipt_observation_receipt_store must be a "
                "GovernanceCustomerTrialClientReceiptObservationReceiptStore"
            )

        if not isinstance(
            observation_service,
            GovernanceCustomerTrialClientResponseObservationService,
        ):
            raise CustomerTrialClientResponseObservationRecordingBridgeError(
                "observation_service must be a "
                "GovernanceCustomerTrialClientResponseObservationService"
            )

        if not isinstance(
            observation_receipt_store,
            GovernanceCustomerTrialClientResponseObservationReceiptStore,
        ):
            raise CustomerTrialClientResponseObservationRecordingBridgeError(
                "observation_receipt_store must be a "
                "GovernanceCustomerTrialClientResponseObservationReceiptStore"
            )

        self._client_receipt_observation_receipt_store = (
            client_receipt_observation_receipt_store
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
        commercial_client_response: (
            CommercialPaidAssessmentClientResponseResult
        ),
    ) -> CustomerTrialClientResponseObservationRecordingResult:
        if not isinstance(
            commercial_client_response,
            CommercialPaidAssessmentClientResponseResult,
        ):
            raise CustomerTrialClientResponseObservationRecordingBridgeError(
                "commercial_client_response must be a "
                "CommercialPaidAssessmentClientResponseResult"
            )

        client_receipt = (
            self._client_receipt_observation_receipt_store.get(
                tenant_id=(
                    commercial_client_response.tenant_id
                ),
                client_id=(
                    commercial_client_response.client_id
                ),
                engagement_id=(
                    commercial_client_response.engagement_id
                ),
                assessment_id=(
                    commercial_client_response.assessment_id
                ),
            )
        )

        if client_receipt is None:
            return (
                CustomerTrialClientResponseObservationRecordingResult(
                    applicable=False,
                    receipt=None,
                )
            )

        observation = (
            self._observation_service.observe(
                client_receipt_observation_receipt=(
                    client_receipt
                ),
                commercial_client_response=(
                    commercial_client_response
                ),
            )
        )

        receipt = (
            self._observation_receipt_store.put(
                observation=observation
            )
        )

        return (
            CustomerTrialClientResponseObservationRecordingResult(
                applicable=True,
                receipt=receipt,
            )
        )