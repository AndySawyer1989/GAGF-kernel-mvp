from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from backend.app.gagf.governance_commercial_paid_assessment_closeout import (
    CommercialPaidAssessmentCloseoutResult,
)
from backend.app.gagf.governance_customer_trial_administrative_closeout_observation import (
    GovernanceCustomerTrialAdministrativeCloseoutObservationService,
)
from backend.app.gagf.governance_customer_trial_administrative_closeout_observation_receipt_store import (
    CustomerTrialAdministrativeCloseoutObservationReceipt,
    GovernanceCustomerTrialAdministrativeCloseoutObservationReceiptStore,
)
from backend.app.gagf.governance_customer_trial_client_response_observation_receipt_store import (
    GovernanceCustomerTrialClientResponseObservationReceiptStore,
)


CUSTOMER_TRIAL_ADMINISTRATIVE_CLOSEOUT_OBSERVATION_RECORDING_BRIDGE_ID = (
    "governance-customer-trial-administrative-closeout-observation-recording-bridge"
)

CUSTOMER_TRIAL_ADMINISTRATIVE_CLOSEOUT_OBSERVATION_RECORDING_BRIDGE_VERSION = (
    "0.1.0"
)


class CustomerTrialAdministrativeCloseoutObservationRecordingBridgeError(
    RuntimeError
):
    """Base controlled-trial administrative-closeout observer error."""


@dataclass(
    frozen=True,
    slots=True,
)
class CustomerTrialAdministrativeCloseoutObservationRecordingResult:
    applicable: bool

    receipt: (
        CustomerTrialAdministrativeCloseoutObservationReceipt
        | None
    )

    bridge_type: str = (
        CUSTOMER_TRIAL_ADMINISTRATIVE_CLOSEOUT_OBSERVATION_RECORDING_BRIDGE_ID
    )

    version: str = (
        CUSTOMER_TRIAL_ADMINISTRATIVE_CLOSEOUT_OBSERVATION_RECORDING_BRIDGE_VERSION
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
                "bridge_observes_existing_pa010_closeout":
                    True,

                "bridge_does_not_create_closeout":
                    True,

                "controlled_trial_complete_is_administrative_only":
                    True,

                "bridge_does_not_validate_findings":
                    True,

                "bridge_does_not_implement_recommendations":
                    True,

                "bridge_does_not_request_intervention":
                    True,

                "bridge_does_not_authorize_intervention":
                    True,

                "bridge_does_not_authorize_execution":
                    True,

                "bridge_does_not_verify_causation":
                    True,

                "bridge_does_not_verify_roi":
                    True,

                "bridge_does_not_verify_remediation_success":
                    True,

                "bridge_does_not_verify_customer_outcome":
                    True,

                "pa010_remains_administrative_closeout_authority":
                    True,

                "pa012_remains_lifecycle_persistence_authority":
                    True,

                "pa013_remains_operator_coordination_authority":
                    True,
            },
        }


class GovernanceCustomerTrialAdministrativeCloseoutObservationRecordingBridge:
    """
    Observe an already-authoritative commercial PA-010 closeout.

    Ordinary paid assessments without a durable controlled-trial
    09B client-response observation remain valid and not applicable.

    If a 09B receipt exists, exact 10A correlation is mandatory.
    """

    def __init__(
        self,
        *,
        client_response_observation_receipt_store: (
            GovernanceCustomerTrialClientResponseObservationReceiptStore
        ),
        observation_service: (
            GovernanceCustomerTrialAdministrativeCloseoutObservationService
        ),
        observation_receipt_store: (
            GovernanceCustomerTrialAdministrativeCloseoutObservationReceiptStore
        ),
    ) -> None:
        if not isinstance(
            client_response_observation_receipt_store,
            GovernanceCustomerTrialClientResponseObservationReceiptStore,
        ):
            raise (
                CustomerTrialAdministrativeCloseoutObservationRecordingBridgeError(
                    "client_response_observation_receipt_store must be a "
                    "GovernanceCustomerTrialClientResponseObservationReceiptStore"
                )
            )

        if not isinstance(
            observation_service,
            GovernanceCustomerTrialAdministrativeCloseoutObservationService,
        ):
            raise (
                CustomerTrialAdministrativeCloseoutObservationRecordingBridgeError(
                    "observation_service must be a "
                    "GovernanceCustomerTrialAdministrativeCloseoutObservationService"
                )
            )

        if not isinstance(
            observation_receipt_store,
            GovernanceCustomerTrialAdministrativeCloseoutObservationReceiptStore,
        ):
            raise (
                CustomerTrialAdministrativeCloseoutObservationRecordingBridgeError(
                    "observation_receipt_store must be a "
                    "GovernanceCustomerTrialAdministrativeCloseoutObservationReceiptStore"
                )
            )

        self._client_response_observation_receipt_store = (
            client_response_observation_receipt_store
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
        commercial_closeout:
            CommercialPaidAssessmentCloseoutResult,
    ) -> CustomerTrialAdministrativeCloseoutObservationRecordingResult:
        if not isinstance(
            commercial_closeout,
            CommercialPaidAssessmentCloseoutResult,
        ):
            raise (
                CustomerTrialAdministrativeCloseoutObservationRecordingBridgeError(
                    "commercial_closeout must be a "
                    "CommercialPaidAssessmentCloseoutResult"
                )
            )

        client_response_receipt = (
            self._client_response_observation_receipt_store.get(
                tenant_id=(
                    commercial_closeout.tenant_id
                ),
                client_id=(
                    commercial_closeout.client_id
                ),
                engagement_id=(
                    commercial_closeout.engagement_id
                ),
                assessment_id=(
                    commercial_closeout.assessment_id
                ),
            )
        )

        if client_response_receipt is None:
            return (
                CustomerTrialAdministrativeCloseoutObservationRecordingResult(
                    applicable=False,
                    receipt=None,
                )
            )

        observation = (
            self._observation_service.observe(
                client_response_observation_receipt=(
                    client_response_receipt
                ),
                commercial_closeout=(
                    commercial_closeout
                ),
            )
        )

        receipt = (
            self._observation_receipt_store.put(
                observation=observation
            )
        )

        return (
            CustomerTrialAdministrativeCloseoutObservationRecordingResult(
                applicable=True,
                receipt=receipt,
            )
        )