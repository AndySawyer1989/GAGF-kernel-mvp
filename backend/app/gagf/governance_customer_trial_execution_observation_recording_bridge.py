from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from backend.app.gagf.governance_customer_trial_execution_handoff_receipt_store import (
    CustomerTrialExecutionHandoffReceipt,
)
from backend.app.gagf.governance_customer_trial_execution_observation import (
    GovernanceCustomerTrialExecutionObservationService,
)
from backend.app.gagf.governance_customer_trial_execution_observation_receipt_store import (
    CustomerTrialExecutionObservationReceipt,
    GovernanceCustomerTrialExecutionObservationReceiptStore,
)
from backend.app.gagf.governance_real_paid_assessment_execution import (
    RealPaidAssessmentExecutionResult,
)


CUSTOMER_TRIAL_EXECUTION_OBSERVATION_RECORDING_BRIDGE_ID = (
    "governance-customer-trial-execution-observation-recording-bridge"
)

CUSTOMER_TRIAL_EXECUTION_OBSERVATION_RECORDING_BRIDGE_VERSION = "0.1.0"

OBSERVATION_NOT_APPLICABLE = "observation_not_applicable"
OBSERVATION_RECORDED = "observation_recorded"


class CustomerTrialExecutionObservationRecordingBridgeError(
    RuntimeError
):
    """Raised when a controlled-trial observation cannot be recorded."""


class CustomerTrialExecutionHandoffReceiptReader(
    Protocol
):
    def get(
        self,
        *,
        tenant_id: str,
        client_id: str,
        engagement_id: str,
        assessment_id: str,
    ) -> CustomerTrialExecutionHandoffReceipt | None:
        ...


class CustomerTrialExecutionObservationRecordingSource(
    Protocol
):
    attempt: Any
    execution_result: RealPaidAssessmentExecutionResult


@dataclass(
    frozen=True,
    slots=True,
)
class CustomerTrialExecutionObservationRecordingResult:
    recording_status: str
    hierarchy_key: str

    handoff_receipt_found: bool

    observation_receipt: (
        CustomerTrialExecutionObservationReceipt
        | None
    )

    bridge_type: str = (
        CUSTOMER_TRIAL_EXECUTION_OBSERVATION_RECORDING_BRIDGE_ID
    )

    version: str = (
        CUSTOMER_TRIAL_EXECUTION_OBSERVATION_RECORDING_BRIDGE_VERSION
    )

    @property
    def boundaries(
        self,
    ) -> dict[str, bool]:
        return {
            "bridge_is_post_execution_only": True,
            "bridge_is_not_execution_authority": True,
            "bridge_is_not_recovery_authority": True,
            "bridge_is_not_paid_work_authority": True,
            "bridge_is_not_contract_authority": True,
            "bridge_is_not_delivery_authority": True,
            "bridge_is_not_closeout_authority": True,
            "bridge_is_not_intervention_authority": True,
            "missing_trial_handoff_does_not_create_observation": True,
            "pa015_result_is_reused_without_reexecution": True,
        }

    def to_dict(
        self,
    ) -> dict[str, object]:
        return {
            "bridge_type":
                self.bridge_type,
            "version":
                self.version,
            "recording_status":
                self.recording_status,
            "hierarchy_key":
                self.hierarchy_key,
            "handoff_receipt_found":
                self.handoff_receipt_found,
            "observation_receipt": (
                None
                if self.observation_receipt is None
                else self.observation_receipt.to_dict()
            ),
            "boundaries":
                self.boundaries,
        }


class GovernanceCustomerTrialExecutionObservationRecordingBridge:
    """
    Record controlled-customer-trial execution observation
    after authoritative PA015 execution has already completed.

    The bridge consumes the existing PA015 result. It never
    invokes execution or recovery itself.

    If the hierarchy has no controlled-trial handoff receipt,
    the bridge returns observation_not_applicable and creates
    no observation.

    If a controlled-trial handoff receipt exists, the bridge
    delegates lineage validation to 04J-05A and persistence to
    04J-05B.
    """

    def __init__(
        self,
        *,
        handoff_receipt_store:
            CustomerTrialExecutionHandoffReceiptReader,
        observation_receipt_store:
            GovernanceCustomerTrialExecutionObservationReceiptStore,
        observation_service:
            GovernanceCustomerTrialExecutionObservationService
            | None = None,
    ) -> None:
        self._handoff_receipt_store = (
            handoff_receipt_store
        )

        self._observation_receipt_store = (
            observation_receipt_store
        )

        self._observation_service = (
            observation_service
            if observation_service is not None
            else GovernanceCustomerTrialExecutionObservationService()
        )

    def capture(
        self,
        *,
        result:
            CustomerTrialExecutionObservationRecordingSource,
    ) -> CustomerTrialExecutionObservationRecordingResult:
        attempt = getattr(
            result,
            "attempt",
            None,
        )

        execution_result = getattr(
            result,
            "execution_result",
            None,
        )

        if attempt is None:
            raise (
                CustomerTrialExecutionObservationRecordingBridgeError(
                    "PA015 result attempt is required"
                )
            )

        if not isinstance(
            execution_result,
            RealPaidAssessmentExecutionResult,
        ):
            raise (
                CustomerTrialExecutionObservationRecordingBridgeError(
                    "PA015 result execution_result must be a "
                    "RealPaidAssessmentExecutionResult"
                )
            )

        tenant_id = self._required_text(
            attempt,
            "tenant_id",
        )

        client_id = self._required_text(
            attempt,
            "client_id",
        )

        engagement_id = self._required_text(
            attempt,
            "engagement_id",
        )

        assessment_id = self._required_text(
            attempt,
            "assessment_id",
        )

        hierarchy_key = "/".join(
            (
                tenant_id,
                client_id,
                engagement_id,
                assessment_id,
            )
        )

        handoff_receipt = (
            self._handoff_receipt_store.get(
                tenant_id=tenant_id,
                client_id=client_id,
                engagement_id=engagement_id,
                assessment_id=assessment_id,
            )
        )

        if handoff_receipt is None:
            return (
                CustomerTrialExecutionObservationRecordingResult(
                    recording_status=(
                        OBSERVATION_NOT_APPLICABLE
                    ),
                    hierarchy_key=hierarchy_key,
                    handoff_receipt_found=False,
                    observation_receipt=None,
                )
            )

        observation = (
            self._observation_service.observe(
                handoff_receipt=handoff_receipt,
                execution_result=execution_result,
            )
        )

        observation_receipt = (
            self._observation_receipt_store.put(
                observation=observation
            )
        )

        return (
            CustomerTrialExecutionObservationRecordingResult(
                recording_status=
                    OBSERVATION_RECORDED,
                hierarchy_key=
                    hierarchy_key,
                handoff_receipt_found=
                    True,
                observation_receipt=
                    observation_receipt,
            )
        )

    @staticmethod
    def _required_text(
        source: Any,
        field_name: str,
    ) -> str:
        value = getattr(
            source,
            field_name,
            None,
        )

        if (
            not isinstance(
                value,
                str,
            )
            or not value.strip()
        ):
            raise (
                CustomerTrialExecutionObservationRecordingBridgeError(
                    f"PA015 attempt {field_name} "
                    "must be non-empty"
                )
            )

        return value.strip()