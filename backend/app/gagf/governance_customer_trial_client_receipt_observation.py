from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from backend.app.gagf.governance_commercial_paid_assessment_client_acknowledgment import (
    CommercialPaidAssessmentClientAcknowledgmentResult,
)
from backend.app.gagf.governance_customer_trial_delivery_observation_receipt_store import (
    CustomerTrialDeliveryObservationReceipt,
)
from backend.app.gagf.governance_paid_assessment_lifecycle_persistence import (
    ACKNOWLEDGMENT_ARTIFACT_TYPE,
)
from backend.app.gagf.governance_paid_assessment_resumable_operator_runner import (
    PaidAssessmentOperatorActionResult,
)


CUSTOMER_TRIAL_CLIENT_RECEIPT_OBSERVATION_ID = (
    "governance-customer-trial-client-receipt-observation"
)

CUSTOMER_TRIAL_CLIENT_RECEIPT_OBSERVATION_VERSION = "0.1.0"

CUSTOMER_TRIAL_CLIENT_RECEIPT_OBSERVATION_SCHEMA_VERSION = "1.0.0"

CLIENT_RECEIPT_OBSERVED = "client_receipt_observed"

EXPECTED_ACKNOWLEDGMENT_STATUS = (
    "client_receipt_acknowledged"
)


class CustomerTrialClientReceiptObservationError(
    RuntimeError
):
    """Base controlled-trial client-receipt observation error."""


class CustomerTrialClientReceiptObservationIdentityError(
    CustomerTrialClientReceiptObservationError
):
    """Raised when client-receipt hierarchy does not match."""


class CustomerTrialClientReceiptObservationLineageError(
    CustomerTrialClientReceiptObservationError
):
    """Raised when client-receipt lineage does not match delivery."""


class CustomerTrialClientReceiptObservationStateError(
    CustomerTrialClientReceiptObservationError
):
    """Raised when authoritative receipt state is not satisfied."""


@dataclass(
    frozen=True,
    slots=True,
)
class CustomerTrialClientReceiptObservation:
    tenant_id: str
    client_id: str
    engagement_id: str
    assessment_id: str
    hierarchy_key: str

    observation_status: str

    delivery_observation_receipt_hash: str
    delivery_observation_hash: str

    report_id: str

    acknowledgment_id: str
    acknowledged_by: str
    acknowledged_at: str
    acknowledgment_method: str
    acknowledgment_reference: str
    acknowledgment_status: str

    acknowledgment_artifact_id: str
    acknowledgment_artifact_hash: str
    acknowledgment_sequence_number: int
    acknowledgment_chain_hash: str

    observation_type: str = (
        CUSTOMER_TRIAL_CLIENT_RECEIPT_OBSERVATION_ID
    )

    version: str = (
        CUSTOMER_TRIAL_CLIENT_RECEIPT_OBSERVATION_VERSION
    )

    schema_version: str = (
        CUSTOMER_TRIAL_CLIENT_RECEIPT_OBSERVATION_SCHEMA_VERSION
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
                "delivery_observation_receipt_hash": (
                    self.delivery_observation_receipt_hash
                ),
                "delivery_observation_hash": (
                    self.delivery_observation_hash
                ),
            },

            "report": {
                "report_id":
                    self.report_id,
            },

            "client_receipt": {
                "acknowledgment_id":
                    self.acknowledgment_id,
                "acknowledged_by":
                    self.acknowledged_by,
                "acknowledged_at":
                    self.acknowledged_at,
                "acknowledgment_method":
                    self.acknowledgment_method,
                "acknowledgment_reference":
                    self.acknowledgment_reference,
                "acknowledgment_status":
                    self.acknowledgment_status,
            },

            "persistence_lineage": {
                "artifact_type":
                    ACKNOWLEDGMENT_ARTIFACT_TYPE,
                "artifact_id":
                    self.acknowledgment_artifact_id,
                "artifact_hash":
                    self.acknowledgment_artifact_hash,
                "sequence_number":
                    self.acknowledgment_sequence_number,
                "chain_hash":
                    self.acknowledgment_chain_hash,
                "repository_chain_valid":
                    True,
            },

            "boundaries": {
                "observation_is_audit_evidence_only":
                    True,
                "observation_does_not_create_client_receipt":
                    True,
                "observation_is_not_client_response":
                    True,
                "observation_is_not_findings_acceptance":
                    True,
                "observation_is_not_recommendation_acceptance":
                    True,
                "observation_is_not_client_satisfaction":
                    True,
                "observation_is_not_closeout_authority":
                    True,
                "observation_is_not_intervention_authority":
                    True,
                "observation_is_not_execution_authority":
                    True,
                "observation_is_not_roi_verification":
                    True,
                "observation_is_not_customer_outcome_verification":
                    True,
                "pa006_remains_client_receipt_authority":
                    True,
                "pa012_remains_lifecycle_persistence_authority":
                    True,
            },
        }


class GovernanceCustomerTrialClientReceiptObservationService:
    """
    Correlate existing controlled-trial delivery observation with an
    already-authoritative commercial PA-006 client acknowledgment.

    The commercial PA-006 adapter rehydrates authoritative delivery
    lineage server-side before producing its result.

    PA-006 remains client-receipt authority.
    PA-012 remains lifecycle-persistence authority.
    """

    def observe(
        self,
        *,
        delivery_observation_receipt: (
            CustomerTrialDeliveryObservationReceipt
        ),
        commercial_client_acknowledgment: (
            CommercialPaidAssessmentClientAcknowledgmentResult
        ),
    ) -> CustomerTrialClientReceiptObservation:
        if not isinstance(
            delivery_observation_receipt,
            CustomerTrialDeliveryObservationReceipt,
        ):
            raise CustomerTrialClientReceiptObservationError(
                "delivery_observation_receipt must be a "
                "CustomerTrialDeliveryObservationReceipt"
            )

        if (
            delivery_observation_receipt.observation_status
            != "delivery_observed"
        ):
            raise CustomerTrialClientReceiptObservationStateError(
                "controlled-trial delivery must be observed before "
                "client receipt can be observed"
            )

        if not isinstance(
            commercial_client_acknowledgment,
            CommercialPaidAssessmentClientAcknowledgmentResult,
        ):
            raise CustomerTrialClientReceiptObservationError(
                "commercial_client_acknowledgment must be a "
                "CommercialPaidAssessmentClientAcknowledgmentResult"
            )

        persistence = (
            commercial_client_acknowledgment.persistence_result
        )

        if not isinstance(
            persistence,
            PaidAssessmentOperatorActionResult,
        ):
            raise CustomerTrialClientReceiptObservationStateError(
                "commercial client acknowledgment must contain "
                "authoritative PA-012 persistence evidence"
            )

        self._validate_identity(
            delivery_observation_receipt=(
                delivery_observation_receipt
            ),
            commercial_client_acknowledgment=(
                commercial_client_acknowledgment
            ),
        )

        self._validate_state(
            commercial_client_acknowledgment=(
                commercial_client_acknowledgment
            ),
            persistence=persistence,
        )

        self._validate_lineage(
            delivery_observation_receipt=(
                delivery_observation_receipt
            ),
            commercial_client_acknowledgment=(
                commercial_client_acknowledgment
            ),
        )

        return CustomerTrialClientReceiptObservation(
            tenant_id=(
                delivery_observation_receipt.tenant_id
            ),
            client_id=(
                delivery_observation_receipt.client_id
            ),
            engagement_id=(
                delivery_observation_receipt.engagement_id
            ),
            assessment_id=(
                delivery_observation_receipt.assessment_id
            ),
            hierarchy_key=(
                delivery_observation_receipt.hierarchy_key
            ),

            observation_status=(
                CLIENT_RECEIPT_OBSERVED
            ),

            delivery_observation_receipt_hash=(
                delivery_observation_receipt.receipt_hash
            ),
            delivery_observation_hash=(
                delivery_observation_receipt.observation_hash
            ),

            report_id=(
                commercial_client_acknowledgment.report_id
            ),

            acknowledgment_id=(
                commercial_client_acknowledgment.acknowledgment_id
            ),
            acknowledged_by=(
                commercial_client_acknowledgment.acknowledged_by
            ),
            acknowledged_at=(
                commercial_client_acknowledgment.acknowledged_at
            ),
            acknowledgment_method=(
                commercial_client_acknowledgment
                .acknowledgment_method
            ),
            acknowledgment_reference=(
                commercial_client_acknowledgment
                .acknowledgment_reference
            ),
            acknowledgment_status=(
                commercial_client_acknowledgment
                .acknowledgment_status
            ),

            acknowledgment_artifact_id=(
                persistence.artifact_id
            ),
            acknowledgment_artifact_hash=(
                persistence.artifact_hash
            ),
            acknowledgment_sequence_number=(
                persistence.sequence_number
            ),
            acknowledgment_chain_hash=(
                persistence.chain_hash
            ),
        )

    @staticmethod
    def _validate_identity(
        *,
        delivery_observation_receipt:
            CustomerTrialDeliveryObservationReceipt,
        commercial_client_acknowledgment:
            CommercialPaidAssessmentClientAcknowledgmentResult,
    ) -> None:
        expected = (
            delivery_observation_receipt.tenant_id,
            delivery_observation_receipt.client_id,
            delivery_observation_receipt.engagement_id,
            delivery_observation_receipt.assessment_id,
        )

        actual = (
            commercial_client_acknowledgment.tenant_id,
            commercial_client_acknowledgment.client_id,
            commercial_client_acknowledgment.engagement_id,
            commercial_client_acknowledgment.assessment_id,
        )

        if actual != expected:
            raise CustomerTrialClientReceiptObservationIdentityError(
                "commercial client acknowledgment hierarchy does "
                "not match controlled-trial delivery observation"
            )

        if (
            commercial_client_acknowledgment.hierarchy_key
            != delivery_observation_receipt.hierarchy_key
        ):
            raise CustomerTrialClientReceiptObservationIdentityError(
                "commercial client acknowledgment hierarchy_key "
                "does not match controlled trial"
            )

    @staticmethod
    def _validate_state(
        *,
        commercial_client_acknowledgment:
            CommercialPaidAssessmentClientAcknowledgmentResult,
        persistence:
            PaidAssessmentOperatorActionResult,
    ) -> None:
        if (
            commercial_client_acknowledgment.acknowledgment_status
            != EXPECTED_ACKNOWLEDGMENT_STATUS
        ):
            raise CustomerTrialClientReceiptObservationStateError(
                "commercial client acknowledgment must have "
                "acknowledgment_status="
                "client_receipt_acknowledged"
            )

        if (
            persistence.artifact_type
            != ACKNOWLEDGMENT_ARTIFACT_TYPE
        ):
            raise CustomerTrialClientReceiptObservationStateError(
                "PA-012 persistence artifact must be an "
                "acknowledgment artifact"
            )

        if persistence.repository_chain_valid is not True:
            raise CustomerTrialClientReceiptObservationStateError(
                "PA-012 acknowledgment repository chain "
                "must be valid"
            )

        if not persistence.artifact_id:
            raise CustomerTrialClientReceiptObservationLineageError(
                "PA-012 acknowledgment artifact_id must be present"
            )

        if not persistence.artifact_hash:
            raise CustomerTrialClientReceiptObservationLineageError(
                "PA-012 acknowledgment artifact_hash must be present"
            )

        if not persistence.chain_hash:
            raise CustomerTrialClientReceiptObservationLineageError(
                "PA-012 acknowledgment chain_hash must be present"
            )

    @staticmethod
    def _validate_lineage(
        *,
        delivery_observation_receipt:
            CustomerTrialDeliveryObservationReceipt,
        commercial_client_acknowledgment:
            CommercialPaidAssessmentClientAcknowledgmentResult,
    ) -> None:
        if (
            commercial_client_acknowledgment.report_id
            != delivery_observation_receipt.report_id
        ):
            raise CustomerTrialClientReceiptObservationLineageError(
                "commercial client acknowledgment report_id "
                "does not match controlled-trial delivered report"
            )