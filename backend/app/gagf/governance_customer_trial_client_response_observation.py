from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from backend.app.gagf.governance_commercial_paid_assessment_client_response import (
    CommercialPaidAssessmentClientResponseResult,
)
from backend.app.gagf.governance_customer_trial_client_receipt_observation_receipt_store import (
    CustomerTrialClientReceiptObservationReceipt,
)


CUSTOMER_TRIAL_CLIENT_RESPONSE_OBSERVATION_ID = (
    "governance-customer-trial-client-response-observation"
)

CUSTOMER_TRIAL_CLIENT_RESPONSE_OBSERVATION_VERSION = "0.1.0"

CUSTOMER_TRIAL_CLIENT_RESPONSE_OBSERVATION_SCHEMA_VERSION = "1.0.0"

CLIENT_RESPONSE_OBSERVED = "client_response_observed"

EXPECTED_CLIENT_RESPONSE_STATUS = (
    "client_response_recorded"
)


class CustomerTrialClientResponseObservationError(
    RuntimeError
):
    """Base controlled-trial client-response observation error."""


class CustomerTrialClientResponseObservationIdentityError(
    CustomerTrialClientResponseObservationError
):
    """Raised when response hierarchy does not match receipt lineage."""


class CustomerTrialClientResponseObservationLineageError(
    CustomerTrialClientResponseObservationError
):
    """Raised when response/report lineage does not match."""


class CustomerTrialClientResponseObservationStateError(
    CustomerTrialClientResponseObservationError
):
    """Raised when authoritative response state is not satisfied."""


@dataclass(
    frozen=True,
    slots=True,
)
class CustomerTrialClientResponseObservation:
    tenant_id: str
    client_id: str
    engagement_id: str
    assessment_id: str
    hierarchy_key: str

    observation_status: str

    client_receipt_observation_receipt_hash: str
    client_receipt_observation_hash: str

    report_id: str

    response_id: str
    responded_by: str
    responded_at: str
    response_method: str
    response_reference: str

    findings_disposition: str
    recommendations_disposition: str
    response_note: str

    response_status: str

    observation_type: str = (
        CUSTOMER_TRIAL_CLIENT_RESPONSE_OBSERVATION_ID
    )

    version: str = (
        CUSTOMER_TRIAL_CLIENT_RESPONSE_OBSERVATION_VERSION
    )

    schema_version: str = (
        CUSTOMER_TRIAL_CLIENT_RESPONSE_OBSERVATION_SCHEMA_VERSION
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
                "client_receipt_observation_receipt_hash": (
                    self.client_receipt_observation_receipt_hash
                ),
                "client_receipt_observation_hash": (
                    self.client_receipt_observation_hash
                ),
            },

            "report": {
                "report_id":
                    self.report_id,
            },

            "client_response": {
                "response_id":
                    self.response_id,
                "responded_by":
                    self.responded_by,
                "responded_at":
                    self.responded_at,
                "response_method":
                    self.response_method,
                "response_reference":
                    self.response_reference,
                "findings_disposition":
                    self.findings_disposition,
                "recommendations_disposition":
                    self.recommendations_disposition,
                "response_note":
                    self.response_note,
                "response_status":
                    self.response_status,
            },

            "boundaries": {
                "observation_is_audit_evidence_only":
                    True,
                "observation_does_not_create_client_response":
                    True,
                "observation_does_not_validate_findings":
                    True,
                "observation_does_not_implement_recommendations":
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
                "pa007_remains_client_response_authority":
                    True,
                "pa012_remains_lifecycle_persistence_authority":
                    True,
            },
        }


class GovernanceCustomerTrialClientResponseObservationService:
    """
    Observe an already-authoritative commercial PA-007 client response.

    This service does not create response, acceptance, closeout,
    implementation, intervention, ROI, or customer-outcome authority.

    PA-007 remains client-response authority.
    PA-012 remains lifecycle-persistence authority.
    """

    def observe(
        self,
        *,
        client_receipt_observation_receipt: (
            CustomerTrialClientReceiptObservationReceipt
        ),
        commercial_client_response: (
            CommercialPaidAssessmentClientResponseResult
        ),
    ) -> CustomerTrialClientResponseObservation:
        if not isinstance(
            client_receipt_observation_receipt,
            CustomerTrialClientReceiptObservationReceipt,
        ):
            raise CustomerTrialClientResponseObservationError(
                "client_receipt_observation_receipt must be a "
                "CustomerTrialClientReceiptObservationReceipt"
            )

        if (
            client_receipt_observation_receipt.observation_status
            != "client_receipt_observed"
        ):
            raise CustomerTrialClientResponseObservationStateError(
                "controlled-trial client receipt must be observed "
                "before client response can be observed"
            )

        if not isinstance(
            commercial_client_response,
            CommercialPaidAssessmentClientResponseResult,
        ):
            raise CustomerTrialClientResponseObservationError(
                "commercial_client_response must be a "
                "CommercialPaidAssessmentClientResponseResult"
            )

        self._validate_identity(
            client_receipt_observation_receipt=(
                client_receipt_observation_receipt
            ),
            commercial_client_response=(
                commercial_client_response
            ),
        )

        self._validate_state(
            commercial_client_response=(
                commercial_client_response
            ),
        )

        self._validate_lineage(
            client_receipt_observation_receipt=(
                client_receipt_observation_receipt
            ),
            commercial_client_response=(
                commercial_client_response
            ),
        )

        return CustomerTrialClientResponseObservation(
            tenant_id=(
                client_receipt_observation_receipt.tenant_id
            ),
            client_id=(
                client_receipt_observation_receipt.client_id
            ),
            engagement_id=(
                client_receipt_observation_receipt.engagement_id
            ),
            assessment_id=(
                client_receipt_observation_receipt.assessment_id
            ),
            hierarchy_key=(
                client_receipt_observation_receipt.hierarchy_key
            ),

            observation_status=(
                CLIENT_RESPONSE_OBSERVED
            ),

            client_receipt_observation_receipt_hash=(
                client_receipt_observation_receipt.receipt_hash
            ),
            client_receipt_observation_hash=(
                client_receipt_observation_receipt.observation_hash
            ),

            report_id=(
                commercial_client_response.report_id
            ),

            response_id=(
                commercial_client_response.response_id
            ),
            responded_by=(
                commercial_client_response.responded_by
            ),
            responded_at=(
                commercial_client_response.responded_at
            ),
            response_method=(
                commercial_client_response.response_method
            ),
            response_reference=(
                commercial_client_response.response_reference
            ),

            findings_disposition=(
                commercial_client_response.findings_disposition
            ),
            recommendations_disposition=(
                commercial_client_response
                .recommendations_disposition
            ),
            response_note=(
                commercial_client_response.response_note
            ),

            response_status=(
                commercial_client_response.response_status
            ),
        )

    @staticmethod
    def _validate_identity(
        *,
        client_receipt_observation_receipt:
            CustomerTrialClientReceiptObservationReceipt,
        commercial_client_response:
            CommercialPaidAssessmentClientResponseResult,
    ) -> None:
        expected = (
            client_receipt_observation_receipt.tenant_id,
            client_receipt_observation_receipt.client_id,
            client_receipt_observation_receipt.engagement_id,
            client_receipt_observation_receipt.assessment_id,
        )

        actual = (
            commercial_client_response.tenant_id,
            commercial_client_response.client_id,
            commercial_client_response.engagement_id,
            commercial_client_response.assessment_id,
        )

        if actual != expected:
            raise CustomerTrialClientResponseObservationIdentityError(
                "commercial client response hierarchy does not "
                "match controlled-trial client receipt observation"
            )

        if (
            commercial_client_response.hierarchy_key
            != client_receipt_observation_receipt.hierarchy_key
        ):
            raise CustomerTrialClientResponseObservationIdentityError(
                "commercial client response hierarchy_key does "
                "not match controlled trial"
            )

    @staticmethod
    def _validate_state(
        *,
        commercial_client_response:
            CommercialPaidAssessmentClientResponseResult,
    ) -> None:
        if (
            commercial_client_response.response_status
            != EXPECTED_CLIENT_RESPONSE_STATUS
        ):
            raise CustomerTrialClientResponseObservationStateError(
                "commercial client response must have "
                "response_status=client_response_recorded"
            )

        if not commercial_client_response.response_id:
            raise CustomerTrialClientResponseObservationLineageError(
                "commercial client response_id must be present"
            )

        if not commercial_client_response.responded_by:
            raise CustomerTrialClientResponseObservationLineageError(
                "commercial responded_by must be present"
            )

        if not commercial_client_response.responded_at:
            raise CustomerTrialClientResponseObservationLineageError(
                "commercial responded_at must be present"
            )

        if not commercial_client_response.response_method:
            raise CustomerTrialClientResponseObservationLineageError(
                "commercial response_method must be present"
            )

        if not commercial_client_response.response_reference:
            raise CustomerTrialClientResponseObservationLineageError(
                "commercial response_reference must be present"
            )

        if not commercial_client_response.findings_disposition:
            raise CustomerTrialClientResponseObservationLineageError(
                "commercial findings_disposition must be present"
            )

        if not commercial_client_response.recommendations_disposition:
            raise CustomerTrialClientResponseObservationLineageError(
                "commercial recommendations_disposition must be present"
            )

    @staticmethod
    def _validate_lineage(
        *,
        client_receipt_observation_receipt:
            CustomerTrialClientReceiptObservationReceipt,
        commercial_client_response:
            CommercialPaidAssessmentClientResponseResult,
    ) -> None:
        if (
            commercial_client_response.report_id
            != client_receipt_observation_receipt.report_id
        ):
            raise CustomerTrialClientResponseObservationLineageError(
                "commercial client response report_id does not "
                "match controlled-trial received report"
            )