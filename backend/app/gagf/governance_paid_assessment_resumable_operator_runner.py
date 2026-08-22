from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable

from backend.app.gagf.governance_paid_assessment_execution_handoff import (
    canonical_json,
    sha256_text,
)

from backend.app.gagf.governance_assessment_isolation import (
    CommercialHierarchyContext,
)
from backend.app.gagf.governance_assessment_repository import (
    GovernanceAssessmentRepository,
    ImmutableAssessmentArtifact,
)
from backend.app.gagf.governance_paid_assessment_client_acknowledgment import (
    GovernedPaidAssessmentClientAcknowledgment,
)
from backend.app.gagf.governance_paid_assessment_client_response import (
    GovernedPaidAssessmentClientResponse,
)
from backend.app.gagf.governance_paid_assessment_closeout import (
    PAID_ASSESSMENT_CLOSEOUT_ARTIFACT_TYPE,
    GovernancePaidAssessmentCloseoutService,
    PaidAssessmentCloseoutRequest,
)
from backend.app.gagf.governance_paid_assessment_delivery_event import (
    GovernedPaidAssessmentDeliveryEvent,
)
from backend.app.gagf.governance_paid_assessment_lifecycle_persistence import (
    ACKNOWLEDGMENT_ARTIFACT_TYPE,
    CLIENT_RESPONSE_ARTIFACT_TYPE,
    DELIVERY_ARTIFACT_TYPE,
    GovernancePaidAssessmentLifecyclePersistenceService,
    PaidAssessmentLifecycleEventPersistenceReceipt,
)
from backend.app.gagf.governance_paid_assessment_operator_workflow import (
    ACTION_CONFIRM_ADMINISTRATIVE_CLOSEOUT,
    ACTION_RECORD_CLIENT_RECEIPT,
    ACTION_RECORD_CLIENT_RESPONSE,
    ACTION_RECORD_DELIVERY_EVENT,
    GovernancePaidAssessmentOperatorWorkflowService,
    PaidAssessmentOperatorWorkflowState,
)


PAID_ASSESSMENT_RESUMABLE_OPERATOR_RUNNER_ID = (
    "governance-paid-assessment-resumable-operator-runner"
)
PAID_ASSESSMENT_RESUMABLE_OPERATOR_RUNNER_VERSION = "0.1.0"
PAID_ASSESSMENT_RESUMABLE_OPERATOR_RUNNER_SCHEMA_VERSION = "1.0.0"

ACTION_RESULT_EXECUTED = "executed"
ACTION_RESULT_ALREADY_DURABLE = "already_durable"

SUPPORTED_ACTION_RESULTS = frozenset(
    {
        ACTION_RESULT_EXECUTED,
        ACTION_RESULT_ALREADY_DURABLE,
    }
)


class PaidAssessmentResumableOperatorRunnerError(RuntimeError):
    """Raised when an operator action cannot be applied safely."""


class PaidAssessmentOperatorActionConflictError(
    PaidAssessmentResumableOperatorRunnerError
):
    """Raised when an already-durable transition differs from the request."""


class PaidAssessmentOperatorActionNotAllowedError(
    PaidAssessmentResumableOperatorRunnerError
):
    """Raised when the requested action is not allowed by PA011 state."""


@dataclass(frozen=True, slots=True)
class PaidAssessmentOperatorActionResult:
    tenant_id: str
    client_id: str
    engagement_id: str
    assessment_id: str

    requested_action: str
    disposition: str

    artifact_type: str
    artifact_id: str
    artifact_hash: str
    sequence_number: int
    chain_hash: str

    workflow_stage_after: str
    required_operator_action_after: str
    repository_chain_valid: bool

    runner_type: str = PAID_ASSESSMENT_RESUMABLE_OPERATOR_RUNNER_ID
    version: str = PAID_ASSESSMENT_RESUMABLE_OPERATOR_RUNNER_VERSION
    schema_version: str = (
        PAID_ASSESSMENT_RESUMABLE_OPERATOR_RUNNER_SCHEMA_VERSION
    )

    def __post_init__(self) -> None:
        if self.disposition not in SUPPORTED_ACTION_RESULTS:
            raise PaidAssessmentResumableOperatorRunnerError(
                "unsupported operator-action disposition"
            )

        if self.repository_chain_valid is not True:
            raise PaidAssessmentResumableOperatorRunnerError(
                "operator-action result requires a valid repository chain"
            )

    @property
    def hierarchy_key(self) -> str:
        return "/".join(
            (
                self.tenant_id,
                self.client_id,
                self.engagement_id,
                self.assessment_id,
            )
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "runner_type": self.runner_type,
            "version": self.version,
            "schema_version": self.schema_version,
            "tenant_id": self.tenant_id,
            "client_id": self.client_id,
            "engagement_id": self.engagement_id,
            "assessment_id": self.assessment_id,
            "hierarchy_key": self.hierarchy_key,
            "requested_action": self.requested_action,
            "disposition": self.disposition,
            "artifact_type": self.artifact_type,
            "artifact_id": self.artifact_id,
            "artifact_hash": self.artifact_hash,
            "sequence_number": self.sequence_number,
            "chain_hash": self.chain_hash,
            "workflow_stage_after": self.workflow_stage_after,
            "required_operator_action_after": (
                self.required_operator_action_after
            ),
            "repository_chain_valid": self.repository_chain_valid,
            "boundaries": {
                "operator_command_is_not_event_authority": True,
                "runner_is_not_a_second_workflow_ledger": True,
                "retry_is_not_a_duplicate_business_event": True,
                "already_durable_is_not_a_new_append": True,
                "client_response_is_not_intervention_authorization": True,
                "closeout_is_not_customer_outcome_verification": True,
            },
        }


class GovernancePaidAssessmentResumableOperatorRunner:
    """
    Apply already-governed post-assessment events through the durable
    paid-assessment lifecycle.

    PA011 remains the read-only workflow projection.
    PA012 remains the lifecycle persistence authority.
    PA010 remains the closeout authority.

    This runner adds no new business-event authority and stores no second
    workflow state.
    """

    def __init__(
        self,
        *,
        repository: GovernanceAssessmentRepository,
    ) -> None:
        if not isinstance(repository, GovernanceAssessmentRepository):
            raise PaidAssessmentResumableOperatorRunnerError(
                "repository must be a GovernanceAssessmentRepository"
            )

        self._repository = repository
        self._workflow = GovernancePaidAssessmentOperatorWorkflowService(
            repository=repository
        )
        self._persistence = (
            GovernancePaidAssessmentLifecyclePersistenceService()
        )
        self._closeout = GovernancePaidAssessmentCloseoutService(
            repository=repository
        )

    def record_delivery(
        self,
        *,
        delivery_event: GovernedPaidAssessmentDeliveryEvent,
        created_at: datetime | None = None,
    ) -> PaidAssessmentOperatorActionResult:
        if not isinstance(
            delivery_event,
            GovernedPaidAssessmentDeliveryEvent,
        ):
            raise PaidAssessmentResumableOperatorRunnerError(
                "delivery_event must be a "
                "GovernedPaidAssessmentDeliveryEvent"
            )

        self._require_governed_payload_integrity(
            governed_object=delivery_event,
            hash_field="delivery_event_hash",
        )

        context = self._context(
            tenant_id=delivery_event.tenant_id,
            client_id=delivery_event.client_id,
            engagement_id=delivery_event.engagement_id,
            assessment_id=delivery_event.assessment_id,
        )

        return self._apply_lifecycle_event(
            context=context,
            requested_action=ACTION_RECORD_DELIVERY_EVENT,
            artifact_type=DELIVERY_ARTIFACT_TYPE,
            identity_field="delivery_event_id",
            identity_value=delivery_event.delivery_event_id,
            hash_field="delivery_event_hash",
            hash_value=delivery_event.delivery_event_hash,
            persist=lambda: self._persistence.persist_delivery(
                repository=self._repository,
                delivery_event=delivery_event,
                created_at=created_at,
            ),
        )

    def record_client_receipt(
        self,
        *,
        client_acknowledgment: (
            GovernedPaidAssessmentClientAcknowledgment
        ),
        created_at: datetime | None = None,
    ) -> PaidAssessmentOperatorActionResult:
        if not isinstance(
            client_acknowledgment,
            GovernedPaidAssessmentClientAcknowledgment,
        ):
            raise PaidAssessmentResumableOperatorRunnerError(
                "client_acknowledgment must be a "
                "GovernedPaidAssessmentClientAcknowledgment"
            )

        self._require_governed_payload_integrity(
            governed_object=client_acknowledgment,
            hash_field="acknowledgment_hash",
        )

        context = self._context(
            tenant_id=client_acknowledgment.tenant_id,
            client_id=client_acknowledgment.client_id,
            engagement_id=client_acknowledgment.engagement_id,
            assessment_id=client_acknowledgment.assessment_id,
        )

        return self._apply_lifecycle_event(
            context=context,
            requested_action=ACTION_RECORD_CLIENT_RECEIPT,
            artifact_type=ACKNOWLEDGMENT_ARTIFACT_TYPE,
            identity_field="acknowledgment_id",
            identity_value=client_acknowledgment.acknowledgment_id,
            hash_field="acknowledgment_hash",
            hash_value=client_acknowledgment.acknowledgment_hash,
            persist=lambda: self._persistence.persist_acknowledgment(
                repository=self._repository,
                client_acknowledgment=client_acknowledgment,
                created_at=created_at,
            ),
        )

    def record_client_response(
        self,
        *,
        client_response: GovernedPaidAssessmentClientResponse,
        created_at: datetime | None = None,
    ) -> PaidAssessmentOperatorActionResult:
        if not isinstance(
            client_response,
            GovernedPaidAssessmentClientResponse,
        ):
            raise PaidAssessmentResumableOperatorRunnerError(
                "client_response must be a "
                "GovernedPaidAssessmentClientResponse"
            )

        self._require_governed_payload_integrity(
            governed_object=client_response,
            hash_field="response_hash",
        )

        context = self._context(
            tenant_id=client_response.tenant_id,
            client_id=client_response.client_id,
            engagement_id=client_response.engagement_id,
            assessment_id=client_response.assessment_id,
        )

        return self._apply_lifecycle_event(
            context=context,
            requested_action=ACTION_RECORD_CLIENT_RESPONSE,
            artifact_type=CLIENT_RESPONSE_ARTIFACT_TYPE,
            identity_field="response_id",
            identity_value=client_response.response_id,
            hash_field="response_hash",
            hash_value=client_response.response_hash,
            persist=lambda: self._persistence.persist_client_response(
                repository=self._repository,
                client_response=client_response,
                created_at=created_at,
            ),
        )

    def confirm_administrative_closeout(
        self,
        *,
        request: PaidAssessmentCloseoutRequest,
        created_at: datetime | None = None,
    ) -> PaidAssessmentOperatorActionResult:
        if not isinstance(request, PaidAssessmentCloseoutRequest):
            raise PaidAssessmentResumableOperatorRunnerError(
                "request must be a PaidAssessmentCloseoutRequest"
            )

        context = request.context

        existing = self._single_artifact(
            context=context,
            artifact_type=PAID_ASSESSMENT_CLOSEOUT_ARTIFACT_TYPE,
        )

        if existing is not None:
            payload = existing.payload

            exact = (
                payload.get("report_id") == request.report_id
                and payload.get("closed_by") == request.closed_by
                and payload.get("closeout_reason")
                == request.closeout_reason
            )

            if not exact:
                raise PaidAssessmentOperatorActionConflictError(
                    "administrative closeout is already durable "
                    "with different request evidence"
                )

            return self._existing_result(
                context=context,
                requested_action=(
                    ACTION_CONFIRM_ADMINISTRATIVE_CLOSEOUT
                ),
                artifact=existing,
            )

        workflow = self._workflow.get_workflow(context=context)

        self._require_action_allowed(
            workflow=workflow,
            requested_action=(
                ACTION_CONFIRM_ADMINISTRATIVE_CLOSEOUT
            ),
        )

        closeout = self._closeout.close_assessment(
            request=request,
            created_at=created_at,
        )

        workflow_after = self._workflow.get_workflow(
            context=context
        )

        return PaidAssessmentOperatorActionResult(
            tenant_id=context.tenant_id,
            client_id=context.client_id,
            engagement_id=self._required_text(
                context.engagement_id,
                "engagement_id",
            ),
            assessment_id=self._required_text(
                context.assessment_id,
                "assessment_id",
            ),
            requested_action=(
                ACTION_CONFIRM_ADMINISTRATIVE_CLOSEOUT
            ),
            disposition=ACTION_RESULT_EXECUTED,
            artifact_type=PAID_ASSESSMENT_CLOSEOUT_ARTIFACT_TYPE,
            artifact_id=closeout.artifact_id,
            artifact_hash=closeout.artifact_hash,
            sequence_number=closeout.sequence_number,
            chain_hash=closeout.chain_hash,
            workflow_stage_after=workflow_after.workflow_stage,
            required_operator_action_after=(
                workflow_after.required_operator_action
            ),
            repository_chain_valid=(
                workflow_after.repository_chain_valid
            ),
        )

    def get_workflow(
        self,
        *,
        context: CommercialHierarchyContext,
    ) -> PaidAssessmentOperatorWorkflowState:
        return self._workflow.get_workflow(context=context)

    def _require_governed_payload_integrity(
        self,
        *,
        governed_object: Any,
        hash_field: str,
    ) -> None:
        if not hasattr(governed_object, "to_dict"):
            raise PaidAssessmentResumableOperatorRunnerError(
                "governed object must provide to_dict()"
            )

        payload = governed_object.to_dict()

        if not isinstance(payload, dict):
            raise PaidAssessmentResumableOperatorRunnerError(
                "governed object to_dict() must return a dictionary"
            )

        if hash_field not in payload:
            raise PaidAssessmentResumableOperatorRunnerError(
                f"governed payload is missing hash field: {hash_field}"
            )

        claimed_hash = payload[hash_field]

        if not isinstance(claimed_hash, str) or not claimed_hash.strip():
            raise PaidAssessmentResumableOperatorRunnerError(
                f"governed payload has invalid hash field: {hash_field}"
            )

        hash_payload = dict(payload)
        del hash_payload[hash_field]

        # hierarchy_key is a derived serialization projection and is
        # not part of the canonical PA005/PA006/PA007 business-event
        # hash payload defined by those domain authorities.
        hash_payload.pop("hierarchy_key", None)


        expected_hash = sha256_text(
            canonical_json(hash_payload)
        )

        if claimed_hash != expected_hash:
            raise PaidAssessmentOperatorActionConflictError(
                "supplied governed event payload does not match "
                f"its claimed {hash_field}"
            )
    def _apply_lifecycle_event(
        self,
        *,
        context: CommercialHierarchyContext,
        requested_action: str,
        artifact_type: str,
        identity_field: str,
        identity_value: str,
        hash_field: str,
        hash_value: str,
        persist: Callable[
            [],
            PaidAssessmentLifecycleEventPersistenceReceipt,
        ],
    ) -> PaidAssessmentOperatorActionResult:
        existing = self._single_artifact(
            context=context,
            artifact_type=artifact_type,
        )

        if existing is not None:
            payload = existing.payload

            if (
                payload.get(identity_field) == identity_value
                and payload.get(hash_field) == hash_value
            ):
                return self._existing_result(
                    context=context,
                    requested_action=requested_action,
                    artifact=existing,
                )

            raise PaidAssessmentOperatorActionConflictError(
                f"{artifact_type} is already durable with "
                "different governed event identity/hash"
            )

        workflow = self._workflow.get_workflow(
            context=context
        )

        self._require_action_allowed(
            workflow=workflow,
            requested_action=requested_action,
        )

        receipt = persist()

        workflow_after = self._workflow.get_workflow(
            context=context
        )

        return PaidAssessmentOperatorActionResult(
            tenant_id=context.tenant_id,
            client_id=context.client_id,
            engagement_id=self._required_text(
                context.engagement_id,
                "engagement_id",
            ),
            assessment_id=self._required_text(
                context.assessment_id,
                "assessment_id",
            ),
            requested_action=requested_action,
            disposition=ACTION_RESULT_EXECUTED,
            artifact_type=receipt.artifact_type,
            artifact_id=receipt.artifact_id,
            artifact_hash=receipt.artifact_hash,
            sequence_number=receipt.sequence_number,
            chain_hash=receipt.chain_hash,
            workflow_stage_after=workflow_after.workflow_stage,
            required_operator_action_after=(
                workflow_after.required_operator_action
            ),
            repository_chain_valid=(
                workflow_after.repository_chain_valid
            ),
        )

    def _existing_result(
        self,
        *,
        context: CommercialHierarchyContext,
        requested_action: str,
        artifact: ImmutableAssessmentArtifact,
    ) -> PaidAssessmentOperatorActionResult:
        workflow = self._workflow.get_workflow(
            context=context
        )

        return PaidAssessmentOperatorActionResult(
            tenant_id=context.tenant_id,
            client_id=context.client_id,
            engagement_id=self._required_text(
                context.engagement_id,
                "engagement_id",
            ),
            assessment_id=self._required_text(
                context.assessment_id,
                "assessment_id",
            ),
            requested_action=requested_action,
            disposition=ACTION_RESULT_ALREADY_DURABLE,
            artifact_type=artifact.artifact_type,
            artifact_id=artifact.artifact_id,
            artifact_hash=artifact.artifact_hash,
            sequence_number=artifact.sequence_number,
            chain_hash=artifact.chain_hash,
            workflow_stage_after=workflow.workflow_stage,
            required_operator_action_after=(
                workflow.required_operator_action
            ),
            repository_chain_valid=workflow.repository_chain_valid,
        )

    def _single_artifact(
        self,
        *,
        context: CommercialHierarchyContext,
        artifact_type: str,
    ) -> ImmutableAssessmentArtifact | None:
        artifacts = self._repository.list_artifacts(
            context=context,
            artifact_type=artifact_type,
        )

        if len(artifacts) > 1:
            raise PaidAssessmentResumableOperatorRunnerError(
                "duplicate governed artifacts for operator transition: "
                f"{artifact_type}"
            )

        if not artifacts:
            return None

        return artifacts[0]

    def _require_action_allowed(
        self,
        *,
        workflow: PaidAssessmentOperatorWorkflowState,
        requested_action: str,
    ) -> None:
        if requested_action not in workflow.allowed_operator_actions:
            raise PaidAssessmentOperatorActionNotAllowedError(
                "requested operator action is not allowed by "
                "current governed workflow: "
                f"{requested_action}; "
                f"current={workflow.required_operator_action}"
            )

    def _context(
        self,
        *,
        tenant_id: str,
        client_id: str,
        engagement_id: str,
        assessment_id: str,
    ) -> CommercialHierarchyContext:
        return CommercialHierarchyContext(
            tenant_id=tenant_id,
            client_id=client_id,
            engagement_id=engagement_id,
            assessment_id=assessment_id,
        )

    def _required_text(
        self,
        value: str | None,
        field_name: str,
    ) -> str:
        if not isinstance(value, str) or not value.strip():
            raise PaidAssessmentResumableOperatorRunnerError(
                f"{field_name} is required"
            )

        return value.strip()