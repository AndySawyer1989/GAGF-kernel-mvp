from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from backend.app.gagf.governance_commercial_paid_assessment_closeout import (
    CommercialPaidAssessmentCloseoutResult,
)
from backend.app.gagf.governance_customer_trial_client_response_observation_receipt_store import (
    CustomerTrialClientResponseObservationReceipt,
)


CUSTOMER_TRIAL_ADMINISTRATIVE_CLOSEOUT_OBSERVATION_ID = (
    "governance-customer-trial-administrative-closeout-observation"
)

CUSTOMER_TRIAL_ADMINISTRATIVE_CLOSEOUT_OBSERVATION_VERSION = "0.1.0"

CUSTOMER_TRIAL_ADMINISTRATIVE_CLOSEOUT_OBSERVATION_SCHEMA_VERSION = "1.0.0"

ADMINISTRATIVE_CLOSEOUT_OBSERVED = (
    "administrative_closeout_observed"
)

CONTROLLED_TRIAL_COMPLETE = (
    "controlled_trial_complete"
)

EXPECTED_CLOSEOUT_STATUS = (
    "assessment_closed"
)


class CustomerTrialAdministrativeCloseoutObservationError(
    RuntimeError
):
    """Base controlled-trial administrative-closeout observation error."""


class CustomerTrialAdministrativeCloseoutObservationIdentityError(
    CustomerTrialAdministrativeCloseoutObservationError
):
    """Raised when closeout hierarchy does not match trial lineage."""


class CustomerTrialAdministrativeCloseoutObservationLineageError(
    CustomerTrialAdministrativeCloseoutObservationError
):
    """Raised when closeout lineage is incomplete or inconsistent."""


class CustomerTrialAdministrativeCloseoutObservationStateError(
    CustomerTrialAdministrativeCloseoutObservationError
):
    """Raised when authoritative closeout state is not satisfied."""


@dataclass(
    frozen=True,
    slots=True,
)
class CustomerTrialAdministrativeCloseoutObservation:
    tenant_id: str
    client_id: str
    engagement_id: str
    assessment_id: str
    hierarchy_key: str

    observation_status: str
    controlled_trial_status: str
    controlled_trial_complete: bool

    client_response_observation_receipt_hash: str
    client_response_observation_hash: str

    report_id: str

    closeout_status: str
    closed_by: str
    closeout_reason: str

    closeout_artifact_id: str
    closeout_artifact_hash: str
    repository_chain_valid: bool

    observation_type: str = (
        CUSTOMER_TRIAL_ADMINISTRATIVE_CLOSEOUT_OBSERVATION_ID
    )

    version: str = (
        CUSTOMER_TRIAL_ADMINISTRATIVE_CLOSEOUT_OBSERVATION_VERSION
    )

    schema_version: str = (
        CUSTOMER_TRIAL_ADMINISTRATIVE_CLOSEOUT_OBSERVATION_SCHEMA_VERSION
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

            "trial_completion": {
                "status":
                    self.controlled_trial_status,
                "controlled_trial_complete":
                    self.controlled_trial_complete,
            },

            "controlled_trial_lineage": {
                "client_response_observation_receipt_hash": (
                    self.client_response_observation_receipt_hash
                ),
                "client_response_observation_hash": (
                    self.client_response_observation_hash
                ),
            },

            "report": {
                "report_id":
                    self.report_id,
            },

            "administrative_closeout": {
                "closeout_status":
                    self.closeout_status,
                "closed_by":
                    self.closed_by,
                "closeout_reason":
                    self.closeout_reason,
                "closeout_artifact_id":
                    self.closeout_artifact_id,
                "closeout_artifact_hash":
                    self.closeout_artifact_hash,
                "repository_chain_valid":
                    self.repository_chain_valid,
            },

            "boundaries": {
                "observation_is_audit_evidence_only":
                    True,

                "observation_does_not_create_closeout":
                    True,

                "response_observed_is_not_closeout":
                    True,

                "trial_complete_is_administrative_only":
                    True,

                "trial_complete_is_not_findings_validation":
                    True,

                "trial_complete_is_not_recommendation_implementation":
                    True,

                "trial_complete_is_not_intervention_request":
                    True,

                "trial_complete_is_not_intervention_authority":
                    True,

                "trial_complete_is_not_execution_authority":
                    True,

                "trial_complete_is_not_causal_success":
                    True,

                "trial_complete_is_not_roi_verification":
                    True,

                "trial_complete_is_not_remediation_success":
                    True,

                "trial_complete_is_not_customer_outcome_verification":
                    True,

                "pa010_remains_administrative_closeout_authority":
                    True,

                "pa012_remains_lifecycle_persistence_authority":
                    True,

                "pa013_remains_operator_coordination_authority":
                    True,
            },
        }


class GovernanceCustomerTrialAdministrativeCloseoutObservationService:
    """
    Observe an already-authoritative PA-010 administrative closeout.

    A controlled trial is administratively complete only when:

    1. 04J-09 has durably observed the authoritative PA-007 response.
    2. PA-010 has durably closed the same governed assessment.
    3. The PA-010 repository chain remains valid.

    This observation does not create intervention, remediation,
    causation, ROI, implementation, or customer-outcome authority.
    """

    def observe(
        self,
        *,
        client_response_observation_receipt: (
            CustomerTrialClientResponseObservationReceipt
        ),
        commercial_closeout: (
            CommercialPaidAssessmentCloseoutResult
        ),
    ) -> CustomerTrialAdministrativeCloseoutObservation:
        if not isinstance(
            client_response_observation_receipt,
            CustomerTrialClientResponseObservationReceipt,
        ):
            raise CustomerTrialAdministrativeCloseoutObservationError(
                "client_response_observation_receipt must be a "
                "CustomerTrialClientResponseObservationReceipt"
            )

        if (
            client_response_observation_receipt.observation_status
            != "client_response_observed"
        ):
            raise CustomerTrialAdministrativeCloseoutObservationStateError(
                "controlled-trial client response must be observed "
                "before administrative closeout can be observed"
            )

        if not isinstance(
            commercial_closeout,
            CommercialPaidAssessmentCloseoutResult,
        ):
            raise CustomerTrialAdministrativeCloseoutObservationError(
                "commercial_closeout must be a "
                "CommercialPaidAssessmentCloseoutResult"
            )

        self._validate_identity(
            client_response_observation_receipt=(
                client_response_observation_receipt
            ),
            commercial_closeout=(
                commercial_closeout
            ),
        )

        self._validate_state(
            commercial_closeout=(
                commercial_closeout
            ),
        )

        self._validate_lineage(
            client_response_observation_receipt=(
                client_response_observation_receipt
            ),
            commercial_closeout=(
                commercial_closeout
            ),
        )

        return (
            CustomerTrialAdministrativeCloseoutObservation(
                tenant_id=(
                    client_response_observation_receipt.tenant_id
                ),
                client_id=(
                    client_response_observation_receipt.client_id
                ),
                engagement_id=(
                    client_response_observation_receipt.engagement_id
                ),
                assessment_id=(
                    client_response_observation_receipt.assessment_id
                ),
                hierarchy_key=(
                    client_response_observation_receipt.hierarchy_key
                ),

                observation_status=(
                    ADMINISTRATIVE_CLOSEOUT_OBSERVED
                ),

                controlled_trial_status=(
                    CONTROLLED_TRIAL_COMPLETE
                ),

                controlled_trial_complete=True,

                client_response_observation_receipt_hash=(
                    client_response_observation_receipt.receipt_hash
                ),

                client_response_observation_hash=(
                    client_response_observation_receipt.observation_hash
                ),

                report_id=(
                    commercial_closeout.report_id
                ),

                closeout_status=(
                    commercial_closeout.closeout_status
                ),

                closed_by=(
                    commercial_closeout.closed_by
                ),

                closeout_reason=(
                    commercial_closeout.closeout_reason
                ),

                closeout_artifact_id=(
                    commercial_closeout.closeout_artifact_id
                ),

                closeout_artifact_hash=(
                    commercial_closeout.closeout_artifact_hash
                ),

                repository_chain_valid=(
                    commercial_closeout.repository_chain_valid
                ),
            )
        )

    @staticmethod
    def _validate_identity(
        *,
        client_response_observation_receipt:
            CustomerTrialClientResponseObservationReceipt,
        commercial_closeout:
            CommercialPaidAssessmentCloseoutResult,
    ) -> None:
        expected = (
            client_response_observation_receipt.tenant_id,
            client_response_observation_receipt.client_id,
            client_response_observation_receipt.engagement_id,
            client_response_observation_receipt.assessment_id,
        )

        actual = (
            commercial_closeout.tenant_id,
            commercial_closeout.client_id,
            commercial_closeout.engagement_id,
            commercial_closeout.assessment_id,
        )

        if actual != expected:
            raise CustomerTrialAdministrativeCloseoutObservationIdentityError(
                "commercial closeout hierarchy does not match "
                "controlled-trial client-response observation"
            )

        if (
            commercial_closeout.hierarchy_key
            != client_response_observation_receipt.hierarchy_key
        ):
            raise CustomerTrialAdministrativeCloseoutObservationIdentityError(
                "commercial closeout hierarchy_key does not match "
                "controlled trial"
            )

    @staticmethod
    def _validate_state(
        *,
        commercial_closeout:
            CommercialPaidAssessmentCloseoutResult,
    ) -> None:
        if (
            commercial_closeout.closeout_status
            != EXPECTED_CLOSEOUT_STATUS
        ):
            raise CustomerTrialAdministrativeCloseoutObservationStateError(
                "commercial closeout must have "
                "closeout_status=assessment_closed"
            )

        if (
            commercial_closeout.repository_chain_valid
            is not True
        ):
            raise CustomerTrialAdministrativeCloseoutObservationStateError(
                "commercial closeout repository chain must be valid"
            )

        if not commercial_closeout.closed_by:
            raise CustomerTrialAdministrativeCloseoutObservationLineageError(
                "commercial closeout closed_by must be present"
            )

        if not commercial_closeout.closeout_reason:
            raise CustomerTrialAdministrativeCloseoutObservationLineageError(
                "commercial closeout closeout_reason must be present"
            )

        if not commercial_closeout.closeout_artifact_id:
            raise CustomerTrialAdministrativeCloseoutObservationLineageError(
                "commercial closeout artifact id must be present"
            )

        if not commercial_closeout.closeout_artifact_hash:
            raise CustomerTrialAdministrativeCloseoutObservationLineageError(
                "commercial closeout artifact hash must be present"
            )

    @staticmethod
    def _validate_lineage(
        *,
        client_response_observation_receipt:
            CustomerTrialClientResponseObservationReceipt,
        commercial_closeout:
            CommercialPaidAssessmentCloseoutResult,
    ) -> None:
        if (
            commercial_closeout.report_id
            != client_response_observation_receipt.report_id
        ):
            raise CustomerTrialAdministrativeCloseoutObservationLineageError(
                "commercial closeout report_id does not match "
                "controlled-trial client-response observation"
            )