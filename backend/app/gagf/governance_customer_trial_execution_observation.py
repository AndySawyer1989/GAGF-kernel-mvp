from __future__ import annotations

from dataclasses import dataclass

from backend.app.gagf.governance_customer_trial_execution_handoff_receipt_store import (
    CustomerTrialExecutionHandoffReceipt,
)
from backend.app.gagf.governance_real_paid_assessment_execution import (
    REAL_EXECUTION_STATUS_COMPLETE,
    RealPaidAssessmentExecutionResult,
)


CUSTOMER_TRIAL_EXECUTION_OBSERVATION_ID = (
    "governance-customer-trial-execution-observation"
)

CUSTOMER_TRIAL_EXECUTION_OBSERVATION_VERSION = "0.1.0"
CUSTOMER_TRIAL_EXECUTION_OBSERVATION_SCHEMA_VERSION = "1.0.0"

EXECUTION_OBSERVED = "execution_observed"


class CustomerTrialExecutionObservationError(RuntimeError):
    """Base error for invalid customer-trial execution observation."""


class CustomerTrialExecutionObservationIdentityError(
    CustomerTrialExecutionObservationError
):
    """Raised when controlled-trial and execution identity differ."""


class CustomerTrialExecutionObservationLineageError(
    CustomerTrialExecutionObservationError
):
    """Raised when execution lineage does not match the trial handoff."""


class CustomerTrialExecutionObservationStateError(
    CustomerTrialExecutionObservationError
):
    """Raised when authoritative execution is not complete."""


@dataclass(frozen=True, slots=True)
class CustomerTrialExecutionObservation:
    tenant_id: str
    client_id: str
    engagement_id: str
    assessment_id: str
    hierarchy_key: str

    observation_status: str

    handoff_receipt_hash: str
    handoff_lineage_hash: str

    handoff_hash: str
    assessment_execution_request_hash: str

    execution_result_hash: str
    application_hash: str
    persistence_hash: str

    report_id: str
    report_package_hash: str

    application_completed: bool
    repository_chain_valid: bool

    observation_type: str = (
        CUSTOMER_TRIAL_EXECUTION_OBSERVATION_ID
    )

    version: str = (
        CUSTOMER_TRIAL_EXECUTION_OBSERVATION_VERSION
    )

    schema_version: str = (
        CUSTOMER_TRIAL_EXECUTION_OBSERVATION_SCHEMA_VERSION
    )

    @property
    def boundaries(
        self,
    ) -> dict[str, bool]:
        return {
            "observation_is_read_only": True,
            "observation_is_not_execution_authority": True,
            "observation_is_not_recovery_authority": True,
            "observation_is_not_delivery_authority": True,
            "observation_is_not_closeout_authority": True,
            "observation_is_not_intervention_authority": True,
            "execution_complete_is_not_customer_outcome_verified": True,
            "execution_complete_is_not_causal_proof": True,
            "execution_complete_is_not_roi_verified": True,
        }

    def to_dict(
        self,
    ) -> dict[str, object]:
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
            "handoff_receipt_hash":
                self.handoff_receipt_hash,
            "handoff_lineage_hash":
                self.handoff_lineage_hash,
            "execution_lineage": {
                "handoff_hash":
                    self.handoff_hash,
                "assessment_execution_request_hash":
                    self.assessment_execution_request_hash,
                "execution_result_hash":
                    self.execution_result_hash,
                "application_hash":
                    self.application_hash,
                "persistence_hash":
                    self.persistence_hash,
            },
            "report": {
                "report_id":
                    self.report_id,
                "report_package_hash":
                    self.report_package_hash,
            },
            "application_completed":
                self.application_completed,
            "repository_chain_valid":
                self.repository_chain_valid,
            "boundaries":
                self.boundaries,
        }


class GovernanceCustomerTrialExecutionObservationService:
    """
    Join controlled-customer-trial handoff evidence to the
    authoritative real paid-assessment execution result.

    This service observes an already-completed governed execution.

    It does not execute, recover, deliver, close out, recommend,
    authorize intervention, or create any substitute execution
    authority.
    """

    def observe(
        self,
        *,
        handoff_receipt:
            CustomerTrialExecutionHandoffReceipt,
        execution_result:
            RealPaidAssessmentExecutionResult,
    ) -> CustomerTrialExecutionObservation:
        self._validate_types(
            handoff_receipt=handoff_receipt,
            execution_result=execution_result,
        )

        self._validate_identity(
            handoff_receipt=handoff_receipt,
            execution_result=execution_result,
        )

        self._validate_lineage(
            handoff_receipt=handoff_receipt,
            execution_result=execution_result,
        )

        self._validate_execution_state(
            execution_result=execution_result,
        )

        return CustomerTrialExecutionObservation(
            tenant_id=
                execution_result.tenant_id,
            client_id=
                execution_result.client_id,
            engagement_id=
                execution_result.engagement_id,
            assessment_id=
                execution_result.assessment_id,
            hierarchy_key=
                execution_result.hierarchy_key,
            observation_status=
                EXECUTION_OBSERVED,
            handoff_receipt_hash=
                handoff_receipt.receipt_hash,
            handoff_lineage_hash=
                handoff_receipt.lineage_hash,
            handoff_hash=
                execution_result.handoff_hash,
            assessment_execution_request_hash=(
                execution_result
                .assessment_execution_request_hash
            ),
            execution_result_hash=
                execution_result.execution_result_hash,
            application_hash=
                execution_result.application_hash,
            persistence_hash=
                execution_result.persistence_hash,
            report_id=
                execution_result.report_id,
            report_package_hash=
                execution_result.report_package_hash,
            application_completed=
                execution_result.application_completed,
            repository_chain_valid=
                execution_result.repository_chain_valid,
        )

    @staticmethod
    def _validate_types(
        *,
        handoff_receipt:
            CustomerTrialExecutionHandoffReceipt,
        execution_result:
            RealPaidAssessmentExecutionResult,
    ) -> None:
        if not isinstance(
            handoff_receipt,
            CustomerTrialExecutionHandoffReceipt,
        ):
            raise CustomerTrialExecutionObservationError(
                "handoff_receipt must be a "
                "CustomerTrialExecutionHandoffReceipt"
            )

        if not isinstance(
            execution_result,
            RealPaidAssessmentExecutionResult,
        ):
            raise CustomerTrialExecutionObservationError(
                "execution_result must be a "
                "RealPaidAssessmentExecutionResult"
            )

    @staticmethod
    def _validate_identity(
        *,
        handoff_receipt:
            CustomerTrialExecutionHandoffReceipt,
        execution_result:
            RealPaidAssessmentExecutionResult,
    ) -> None:
        expected = (
            handoff_receipt.tenant_id,
            handoff_receipt.client_id,
            handoff_receipt.engagement_id,
            handoff_receipt.assessment_id,
            handoff_receipt.hierarchy_key,
        )

        actual = (
            execution_result.tenant_id,
            execution_result.client_id,
            execution_result.engagement_id,
            execution_result.assessment_id,
            execution_result.hierarchy_key,
        )

        if actual != expected:
            raise CustomerTrialExecutionObservationIdentityError(
                "real paid-assessment execution identity does "
                "not match customer-trial handoff receipt"
            )

    @staticmethod
    def _validate_lineage(
        *,
        handoff_receipt:
            CustomerTrialExecutionHandoffReceipt,
        execution_result:
            RealPaidAssessmentExecutionResult,
    ) -> None:
        if (
            execution_result.handoff_hash
            != handoff_receipt.handoff_hash
        ):
            raise CustomerTrialExecutionObservationLineageError(
                "real paid-assessment execution handoff_hash "
                "does not match customer-trial handoff receipt"
            )

        if (
            execution_result
            .assessment_execution_request_hash
            != handoff_receipt
            .assessment_execution_request_hash
        ):
            raise CustomerTrialExecutionObservationLineageError(
                "real paid-assessment execution request hash "
                "does not match customer-trial handoff receipt"
            )

    @staticmethod
    def _validate_execution_state(
        *,
        execution_result:
            RealPaidAssessmentExecutionResult,
    ) -> None:
        if (
            execution_result.execution_status
            != REAL_EXECUTION_STATUS_COMPLETE
        ):
            raise CustomerTrialExecutionObservationStateError(
                "real paid-assessment execution is not complete"
            )

        if execution_result.application_completed is not True:
            raise CustomerTrialExecutionObservationStateError(
                "paid-assessment application did not complete"
            )

        if execution_result.repository_chain_valid is not True:
            raise CustomerTrialExecutionObservationStateError(
                "paid-assessment repository chain is not valid"
            )