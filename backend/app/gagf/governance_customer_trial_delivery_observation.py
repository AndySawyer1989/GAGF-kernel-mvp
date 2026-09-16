from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from backend.app.gagf.governance_commercial_paid_assessment_delivery_recording import (
    CommercialPaidAssessmentDeliveryRecording,
)
from backend.app.gagf.governance_customer_trial_delivery_readiness import (
    CONTROLLED_TRIAL_DELIVERY_READY,
)
from backend.app.gagf.governance_customer_trial_delivery_readiness_receipt_store import (
    CustomerTrialDeliveryReadinessReceipt,
)


CUSTOMER_TRIAL_DELIVERY_OBSERVATION_ID = (
    "governance-customer-trial-delivery-observation"
)

CUSTOMER_TRIAL_DELIVERY_OBSERVATION_VERSION = "0.1.0"
CUSTOMER_TRIAL_DELIVERY_OBSERVATION_SCHEMA_VERSION = "1.0.0"

DELIVERY_OBSERVED = "delivery_observed"


class CustomerTrialDeliveryObservationError(RuntimeError):
    """Base controlled-trial delivery-observation error."""


class CustomerTrialDeliveryObservationIdentityError(
    CustomerTrialDeliveryObservationError
):
    """Raised when delivery identity does not match the trial."""


class CustomerTrialDeliveryObservationLineageError(
    CustomerTrialDeliveryObservationError
):
    """Raised when governed delivery lineage does not match."""


class CustomerTrialDeliveryObservationStateError(
    CustomerTrialDeliveryObservationError
):
    """Raised when prerequisite governed state is not satisfied."""


@dataclass(
    frozen=True,
    slots=True,
)
class CustomerTrialDeliveryObservation:
    tenant_id: str
    client_id: str
    engagement_id: str
    assessment_id: str
    hierarchy_key: str

    observation_status: str

    delivery_readiness_receipt_hash: str
    delivery_readiness_hash: str

    delivery_event_id: str
    delivery_event_hash: str

    report_id: str

    delivered_by: str
    delivered_at: str
    delivery_method: str
    delivery_reference: str

    human_delivery_confirmation_hash: str
    approved_delivery_snapshot_hash: str

    observation_type: str = (
        CUSTOMER_TRIAL_DELIVERY_OBSERVATION_ID
    )

    version: str = (
        CUSTOMER_TRIAL_DELIVERY_OBSERVATION_VERSION
    )

    schema_version: str = (
        CUSTOMER_TRIAL_DELIVERY_OBSERVATION_SCHEMA_VERSION
    )

    def to_dict(
        self,
    ) -> dict[str, Any]:
        return {
            "observation_type":
                self.observation_type,
            "version":
                self.version,
            "schema_version":
                self.schema_version,

            "tenant_id":
                self.tenant_id,
            "client_id":
                self.client_id,
            "engagement_id":
                self.engagement_id,
            "assessment_id":
                self.assessment_id,
            "hierarchy_key":
                self.hierarchy_key,

            "observation_status":
                self.observation_status,

            "controlled_trial_lineage": {
                "delivery_readiness_receipt_hash": (
                    self.delivery_readiness_receipt_hash
                ),
                "delivery_readiness_hash": (
                    self.delivery_readiness_hash
                ),
            },

            "delivery_lineage": {
                "delivery_event_id":
                    self.delivery_event_id,
                "delivery_event_hash":
                    self.delivery_event_hash,
                "human_delivery_confirmation_hash": (
                    self.human_delivery_confirmation_hash
                ),
                "approved_delivery_snapshot_hash": (
                    self.approved_delivery_snapshot_hash
                ),
            },

            "report": {
                "report_id":
                    self.report_id,
            },

            "delivery": {
                "delivered_by":
                    self.delivered_by,
                "delivered_at":
                    self.delivered_at,
                "delivery_method":
                    self.delivery_method,
                "delivery_reference":
                    self.delivery_reference,
            },

            "boundaries": {
                "observation_is_audit_evidence_only":
                    True,
                "observation_does_not_approve_delivery":
                    True,
                "observation_does_not_create_approved_for_human_delivery":
                    True,
                "observation_does_not_deliver":
                    True,
                "observation_is_not_delivery_event_authority":
                    True,
                "observation_is_not_client_receipt":
                    True,
                "observation_is_not_client_acknowledgment":
                    True,
                "observation_is_not_client_response":
                    True,
                "observation_is_not_client_acceptance":
                    True,
                "observation_is_not_closeout_authority":
                    True,
                "observation_is_not_intervention_authority":
                    True,
                "pa005_remains_delivery_event_authority":
                    True,
                "pa012_remains_lifecycle_persistence_authority":
                    True,
            },
        }


class GovernanceCustomerTrialDeliveryObservationService:
    """
    Correlate an existing controlled-trial delivery-readiness receipt
    with an already-authoritative commercial PA-005 delivery recording.

    This service does not approve or perform delivery.

    PA-005 remains delivery-event authority.
    PA-012 remains lifecycle-persistence authority.

    The result is observation evidence only.
    """

    def observe(
        self,
        *,
        readiness_receipt: (
            CustomerTrialDeliveryReadinessReceipt
        ),
        commercial_delivery_recording: (
            CommercialPaidAssessmentDeliveryRecording
        ),
    ) -> CustomerTrialDeliveryObservation:
        if not isinstance(
            readiness_receipt,
            CustomerTrialDeliveryReadinessReceipt,
        ):
            raise CustomerTrialDeliveryObservationError(
                "readiness_receipt must be a "
                "CustomerTrialDeliveryReadinessReceipt"
            )

        if (
            readiness_receipt.readiness_status
            != CONTROLLED_TRIAL_DELIVERY_READY
        ):
            raise CustomerTrialDeliveryObservationStateError(
                "controlled-trial delivery readiness must be "
                "established before delivery can be observed"
            )

        if not isinstance(
            commercial_delivery_recording,
            CommercialPaidAssessmentDeliveryRecording,
        ):
            raise CustomerTrialDeliveryObservationError(
                "commercial_delivery_recording must be a "
                "CommercialPaidAssessmentDeliveryRecording"
            )

        self._validate_identity(
            readiness_receipt=readiness_receipt,
            commercial_delivery_recording=(
                commercial_delivery_recording
            ),
        )

        self._validate_delivery(
            commercial_delivery_recording=(
                commercial_delivery_recording
            ),
        )

        self._validate_lineage(
            readiness_receipt=readiness_receipt,
            commercial_delivery_recording=(
                commercial_delivery_recording
            ),
        )

        event = (
            commercial_delivery_recording
            .recording
            .delivery_event
        )

        confirmation = (
            commercial_delivery_recording
            .recording
            .human_confirmation
        )

        return CustomerTrialDeliveryObservation(
            tenant_id=(
                readiness_receipt.tenant_id
            ),
            client_id=(
                readiness_receipt.client_id
            ),
            engagement_id=(
                readiness_receipt.engagement_id
            ),
            assessment_id=(
                readiness_receipt.assessment_id
            ),
            hierarchy_key=(
                readiness_receipt.hierarchy_key
            ),

            observation_status=(
                DELIVERY_OBSERVED
            ),

            delivery_readiness_receipt_hash=(
                readiness_receipt.receipt_hash
            ),
            delivery_readiness_hash=(
                readiness_receipt.readiness_hash
            ),

            delivery_event_id=(
                event.delivery_event_id
            ),
            delivery_event_hash=(
                event.delivery_event_hash
            ),

            report_id=(
                event.report_id
            ),

            delivered_by=(
                event.delivered_by
            ),
            delivered_at=(
                event.delivered_at
            ),
            delivery_method=(
                event.delivery_method
            ),
            delivery_reference=(
                event.delivery_reference
            ),

            human_delivery_confirmation_hash=(
                confirmation.confirmation_hash
            ),
            approved_delivery_snapshot_hash=(
                commercial_delivery_recording
                .approved_delivery_snapshot_hash
            ),
        )

    @staticmethod
    def _validate_identity(
        *,
        readiness_receipt: (
            CustomerTrialDeliveryReadinessReceipt
        ),
        commercial_delivery_recording: (
            CommercialPaidAssessmentDeliveryRecording
        ),
    ) -> None:
        readiness_identity = (
            readiness_receipt.tenant_id,
            readiness_receipt.client_id,
            readiness_receipt.engagement_id,
            readiness_receipt.assessment_id,
        )

        recording_identity = (
            commercial_delivery_recording.tenant_id,
            commercial_delivery_recording.client_id,
            commercial_delivery_recording.engagement_id,
            commercial_delivery_recording.assessment_id,
        )

        if (
            readiness_identity
            != recording_identity
        ):
            raise (
                CustomerTrialDeliveryObservationIdentityError(
                    "controlled-trial delivery readiness hierarchy "
                    "does not match commercial delivery recording"
                )
            )

        if (
            readiness_receipt.hierarchy_key
            != commercial_delivery_recording.hierarchy_key
        ):
            raise (
                CustomerTrialDeliveryObservationIdentityError(
                    "controlled-trial hierarchy_key does not match "
                    "commercial delivery recording"
                )
            )

    @staticmethod
    def _validate_delivery(
        *,
        commercial_delivery_recording: (
            CommercialPaidAssessmentDeliveryRecording
        ),
    ) -> None:
        recording = (
            commercial_delivery_recording.recording
        )

        if (
            recording.delivery_status
            != "delivered"
        ):
            raise CustomerTrialDeliveryObservationStateError(
                "commercial delivery recording must have "
                "delivery_status=delivered"
            )

        event = recording.delivery_event

        if (
            event.delivery_status
            != "delivered"
        ):
            raise CustomerTrialDeliveryObservationStateError(
                "commercial delivery event must have "
                "delivery_status=delivered"
            )

        if not event.delivery_event_id:
            raise CustomerTrialDeliveryObservationLineageError(
                "commercial delivery event_id must be present"
            )

        if not event.delivery_event_hash:
            raise CustomerTrialDeliveryObservationLineageError(
                "commercial delivery event hash must be present"
            )

        if not commercial_delivery_recording.approved_delivery_snapshot_hash:
            raise CustomerTrialDeliveryObservationLineageError(
                "approved delivery snapshot hash must be present"
            )

    @staticmethod
    def _validate_lineage(
        *,
        readiness_receipt: (
            CustomerTrialDeliveryReadinessReceipt
        ),
        commercial_delivery_recording: (
            CommercialPaidAssessmentDeliveryRecording
        ),
    ) -> None:
        event = (
            commercial_delivery_recording
            .recording
            .delivery_event
        )

        if (
            event.report_id
            != readiness_receipt.report_id
        ):
            raise CustomerTrialDeliveryObservationLineageError(
                "commercial delivery report_id does not match "
                "controlled-trial delivery readiness"
            )