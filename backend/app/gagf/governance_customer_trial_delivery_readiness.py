from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from backend.app.gagf.governance_commercial_paid_assessment_delivery_readiness import (
    CommercialPaidAssessmentDeliveryReadiness,
    CommercialPaidAssessmentDeliveryReadinessError,
    GovernanceCommercialPaidAssessmentDeliveryReadinessService,
)
from backend.app.gagf.governance_customer_trial_execution_observation_receipt_store import (
    CustomerTrialExecutionObservationReceipt,
)


CUSTOMER_TRIAL_DELIVERY_READINESS_ID = (
    "governance-customer-trial-delivery-readiness"
)

CUSTOMER_TRIAL_DELIVERY_READINESS_VERSION = "0.1.0"

CUSTOMER_TRIAL_DELIVERY_READINESS_SCHEMA_VERSION = "1.0.0"

CONTROLLED_TRIAL_DELIVERY_READY = (
    "controlled_trial_delivery_ready"
)


class CustomerTrialDeliveryReadinessError(
    RuntimeError
):
    """Base controlled-trial delivery-readiness error."""


class CustomerTrialDeliveryReadinessIdentityError(
    CustomerTrialDeliveryReadinessError
):
    """Raised when observation/readiness identity does not match."""


class CustomerTrialDeliveryReadinessLineageError(
    CustomerTrialDeliveryReadinessError
):
    """Raised when controlled-trial delivery lineage is inconsistent."""


class CustomerTrialDeliveryReadinessStateError(
    CustomerTrialDeliveryReadinessError
):
    """Raised when authoritative delivery readiness is not satisfied."""


@dataclass(
    frozen=True,
    slots=True,
)
class CustomerTrialDeliveryReadiness:
    tenant_id: str
    client_id: str
    engagement_id: str
    assessment_id: str
    hierarchy_key: str

    readiness_status: str

    observation_receipt_hash: str
    observation_hash: str

    handoff_receipt_hash: str
    handoff_lineage_hash: str
    handoff_hash: str
    assessment_execution_request_hash: str

    execution_result_hash: str
    application_hash: str
    persistence_hash: str

    report_id: str
    report_package_hash: str

    execution_status_hash: str
    operator_result_hash: str
    operator_snapshot_hash: str

    delivery_readiness_status: str
    recovery_disposition: str
    artifact_count: int
    repository_chain_valid: bool

    result_type: str = (
        CUSTOMER_TRIAL_DELIVERY_READINESS_ID
    )

    version: str = (
        CUSTOMER_TRIAL_DELIVERY_READINESS_VERSION
    )

    schema_version: str = (
        CUSTOMER_TRIAL_DELIVERY_READINESS_SCHEMA_VERSION
    )

    def to_dict(
        self,
    ) -> dict[str, Any]:
        return {
            "result_type":
                self.result_type,
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
            "readiness_status":
                self.readiness_status,
            "observation_receipt_hash":
                self.observation_receipt_hash,
            "observation_hash":
                self.observation_hash,
            "controlled_trial_lineage": {
                "handoff_receipt_hash":
                    self.handoff_receipt_hash,
                "handoff_lineage_hash":
                    self.handoff_lineage_hash,
                "handoff_hash":
                    self.handoff_hash,
                "assessment_execution_request_hash":
                    self.assessment_execution_request_hash,
            },
            "execution_lineage": {
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
            "commercial_readiness": {
                "execution_status_hash":
                    self.execution_status_hash,
                "operator_result_hash":
                    self.operator_result_hash,
                "operator_snapshot_hash":
                    self.operator_snapshot_hash,
                "delivery_readiness_status":
                    self.delivery_readiness_status,
                "recovery_disposition":
                    self.recovery_disposition,
                "artifact_count":
                    self.artifact_count,
                "repository_chain_valid":
                    self.repository_chain_valid,
            },
            "boundaries": {
                "readiness_is_read_only":
                    True,
                "readiness_is_not_execution_authority":
                    True,
                "readiness_is_not_recovery_authority":
                    True,
                "readiness_is_not_delivery_approval":
                    True,
                "readiness_is_not_approved_for_human_delivery":
                    True,
                "readiness_is_not_delivery":
                    True,
                "readiness_is_not_client_receipt":
                    True,
                "readiness_is_not_client_response":
                    True,
                "readiness_is_not_closeout_authority":
                    True,
                "readiness_is_not_intervention_authority":
                    True,
                "existing_commercial_delivery_readiness_is_authoritative":
                    True,
                "pa003_remains_delivery_readiness_authority":
                    True,
            },
        }


class GovernanceCustomerTrialDeliveryReadinessService:
    """
    Read-only controlled-trial projection over the already-authoritative
    commercial paid-assessment delivery-readiness service.

    The controlled-trial layer does not create another readiness engine,
    does not approve delivery, and does not record delivery.

    It proves that:
      1. authoritative paid execution was durably observed for this trial,
      2. the existing commercial PA-003 readiness service independently
         verifies the same assessment,
      3. both projections refer to the same hierarchy and report.
    """

    def __init__(
        self,
        *,
        commercial_readiness_service: (
            GovernanceCommercialPaidAssessmentDeliveryReadinessService
        ),
    ) -> None:
        if not isinstance(
            commercial_readiness_service,
            GovernanceCommercialPaidAssessmentDeliveryReadinessService,
        ):
            raise CustomerTrialDeliveryReadinessError(
                "commercial_readiness_service must be a "
                "GovernanceCommercialPaidAssessmentDeliveryReadinessService"
            )

        self._commercial_readiness_service = (
            commercial_readiness_service
        )

    def verify(
        self,
        *,
        observation_receipt: (
            CustomerTrialExecutionObservationReceipt
        ),
    ) -> CustomerTrialDeliveryReadiness:
        if not isinstance(
            observation_receipt,
            CustomerTrialExecutionObservationReceipt,
        ):
            raise CustomerTrialDeliveryReadinessError(
                "observation_receipt must be a "
                "CustomerTrialExecutionObservationReceipt"
            )

        if (
            observation_receipt.observation_status
            != "execution_observed"
        ):
            raise CustomerTrialDeliveryReadinessStateError(
                "controlled-trial execution must be observed "
                "before delivery readiness can be projected"
            )

        try:
            commercial_readiness = (
                self._commercial_readiness_service.verify(
                    tenant_id=(
                        observation_receipt.tenant_id
                    ),
                    client_id=(
                        observation_receipt.client_id
                    ),
                    engagement_id=(
                        observation_receipt.engagement_id
                    ),
                    assessment_id=(
                        observation_receipt.assessment_id
                    ),
                )
            )
        except (
            CommercialPaidAssessmentDeliveryReadinessError
        ) as exc:
            raise CustomerTrialDeliveryReadinessStateError(
                "authoritative commercial delivery readiness failed: "
                f"{exc}"
            ) from exc

        return self.correlate(
            observation_receipt=observation_receipt,
            commercial_readiness=commercial_readiness,
        )

    def correlate(
        self,
        *,
        observation_receipt: (
            CustomerTrialExecutionObservationReceipt
        ),
        commercial_readiness: (
            CommercialPaidAssessmentDeliveryReadiness
        ),
    ) -> CustomerTrialDeliveryReadiness:
        """
        Correlate an already-authoritative commercial PA-003
        readiness result with durable controlled-trial execution
        observation evidence.

        This method does not execute PA-003 readiness again.
        """

        if not isinstance(
            observation_receipt,
            CustomerTrialExecutionObservationReceipt,
        ):
            raise CustomerTrialDeliveryReadinessError(
                "observation_receipt must be a "
                "CustomerTrialExecutionObservationReceipt"
            )

        if (
            observation_receipt.observation_status
            != "execution_observed"
        ):
            raise CustomerTrialDeliveryReadinessStateError(
                "controlled-trial execution must be observed "
                "before delivery readiness can be projected"
            )

        if not isinstance(
            commercial_readiness,
            CommercialPaidAssessmentDeliveryReadiness,
        ):
            raise CustomerTrialDeliveryReadinessError(
                "commercial_readiness must be a "
                "CommercialPaidAssessmentDeliveryReadiness"
            )

        self._validate_identity(
            observation_receipt=observation_receipt,
            commercial_readiness=commercial_readiness,
        )

        self._validate_lineage(
            observation_receipt=observation_receipt,
            commercial_readiness=commercial_readiness,
        )

        readiness = commercial_readiness.readiness

        return CustomerTrialDeliveryReadiness(
            tenant_id=(
                observation_receipt.tenant_id
            ),
            client_id=(
                observation_receipt.client_id
            ),
            engagement_id=(
                observation_receipt.engagement_id
            ),
            assessment_id=(
                observation_receipt.assessment_id
            ),
            hierarchy_key=(
                observation_receipt.hierarchy_key
            ),
            readiness_status=(
                CONTROLLED_TRIAL_DELIVERY_READY
            ),
            observation_receipt_hash=(
                observation_receipt.receipt_hash
            ),
            observation_hash=(
                observation_receipt.observation_hash
            ),
            handoff_receipt_hash=(
                observation_receipt.handoff_receipt_hash
            ),
            handoff_lineage_hash=(
                observation_receipt.handoff_lineage_hash
            ),
            handoff_hash=(
                observation_receipt.handoff_hash
            ),
            assessment_execution_request_hash=(
                observation_receipt
                .assessment_execution_request_hash
            ),
            execution_result_hash=(
                observation_receipt.execution_result_hash
            ),
            application_hash=(
                observation_receipt.application_hash
            ),
            persistence_hash=(
                observation_receipt.persistence_hash
            ),
            report_id=(
                observation_receipt.report_id
            ),
            report_package_hash=(
                observation_receipt.report_package_hash
            ),
            execution_status_hash=(
                commercial_readiness.execution_status_hash
            ),
            operator_result_hash=(
                commercial_readiness.operator_result_hash
            ),
            operator_snapshot_hash=(
                commercial_readiness.operator_snapshot_hash
            ),
            delivery_readiness_status=(
                readiness.delivery_readiness_status
            ),
            recovery_disposition=(
                readiness.recovery_disposition
            ),
            artifact_count=(
                readiness.artifact_count
            ),
            repository_chain_valid=(
                readiness.repository_chain_valid
            ),
        )

    @staticmethod
    def _validate_identity(
        *,
        observation_receipt: (
            CustomerTrialExecutionObservationReceipt
        ),
        commercial_readiness: (
            CommercialPaidAssessmentDeliveryReadiness
        ),
    ) -> None:
        observation_identity = (
            observation_receipt.tenant_id,
            observation_receipt.client_id,
            observation_receipt.engagement_id,
            observation_receipt.assessment_id,
        )

        readiness_identity = (
            commercial_readiness.tenant_id,
            commercial_readiness.client_id,
            commercial_readiness.engagement_id,
            commercial_readiness.assessment_id,
        )

        if (
            observation_identity
            != readiness_identity
        ):
            raise CustomerTrialDeliveryReadinessIdentityError(
                "controlled-trial observation hierarchy does not "
                "match commercial delivery readiness"
            )

        if (
            observation_receipt.hierarchy_key
            != commercial_readiness.hierarchy_key
        ):
            raise CustomerTrialDeliveryReadinessIdentityError(
                "controlled-trial observation hierarchy_key does not "
                "match commercial delivery readiness"
            )

    @staticmethod
    def _validate_lineage(
        *,
        observation_receipt: (
            CustomerTrialExecutionObservationReceipt
        ),
        commercial_readiness: (
            CommercialPaidAssessmentDeliveryReadiness
        ),
    ) -> None:
        readiness = (
            commercial_readiness.readiness
        )

        if (
            readiness.execution_result.report_id
            != observation_receipt.report_id
        ):
            raise CustomerTrialDeliveryReadinessLineageError(
                "commercial delivery readiness report_id does not "
                "match controlled-trial execution observation"
            )

        if (
            readiness.repository_chain_valid
            is not True
        ):
            raise CustomerTrialDeliveryReadinessStateError(
                "authoritative delivery readiness repository chain "
                "must be valid"
            )
