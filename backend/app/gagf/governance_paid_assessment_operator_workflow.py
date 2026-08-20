from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from backend.app.gagf.governance_assessment_isolation import (
    CommercialHierarchyContext,
)
from backend.app.gagf.governance_assessment_repository import (
    GovernanceAssessmentRepository,
    ImmutableAssessmentArtifact,
)
from backend.app.gagf.governance_paid_assessment_closeout import (
    PAID_ASSESSMENT_CLOSEOUT_ARTIFACT_TYPE,
    PAID_ASSESSMENT_CLOSEOUT_STATUS,
)
from backend.app.gagf.governance_paid_assessment_lifecycle_query import (
    GovernancePaidAssessmentLifecycleQueryService,
    PaidAssessmentLifecycleArtifactReference,
)


PAID_ASSESSMENT_OPERATOR_WORKFLOW_ID = (
    "governance-paid-assessment-operator-workflow"
)
PAID_ASSESSMENT_OPERATOR_WORKFLOW_VERSION = "0.1.0"
PAID_ASSESSMENT_OPERATOR_WORKFLOW_SCHEMA_VERSION = "1.0.0"

WORKFLOW_STAGE_AWAITING_DELIVERY = "awaiting_delivery"
WORKFLOW_STAGE_AWAITING_CLIENT_RECEIPT = (
    "awaiting_client_receipt"
)
WORKFLOW_STAGE_AWAITING_CLIENT_RESPONSE = (
    "awaiting_client_response"
)
WORKFLOW_STAGE_READY_FOR_CLOSEOUT = "ready_for_closeout"
WORKFLOW_STAGE_CLOSED = "closed"

ACTION_RECORD_DELIVERY_EVENT = "record_delivery_event"
ACTION_RECORD_CLIENT_RECEIPT = (
    "record_client_receipt_acknowledgment"
)
ACTION_RECORD_CLIENT_RESPONSE = "record_client_response"
ACTION_CONFIRM_ADMINISTRATIVE_CLOSEOUT = (
    "confirm_administrative_closeout"
)
ACTION_NONE = "none"

LIFECYCLE_STAGE_NOT_STARTED = (
    "post_assessment_lifecycle_not_started"
)
LIFECYCLE_STAGE_DELIVERED = "delivered"
LIFECYCLE_STAGE_CLIENT_RECEIPT = (
    "client_receipt_acknowledged"
)
LIFECYCLE_STAGE_CLIENT_RESPONSE = "client_response_recorded"

EXPECTED_LIFECYCLE_PENDING_ACTIONS = {
    LIFECYCLE_STAGE_NOT_STARTED: ACTION_RECORD_DELIVERY_EVENT,
    LIFECYCLE_STAGE_DELIVERED: ACTION_RECORD_CLIENT_RECEIPT,
    LIFECYCLE_STAGE_CLIENT_RECEIPT: ACTION_RECORD_CLIENT_RESPONSE,
    LIFECYCLE_STAGE_CLIENT_RESPONSE: ACTION_NONE,
}


class PaidAssessmentOperatorWorkflowError(ValueError):
    """Raised when an operator workflow projection cannot be trusted."""


@dataclass(frozen=True, slots=True)
class PaidAssessmentOperatorEvidenceReference:
    artifact_id: str
    artifact_type: str
    artifact_hash: str
    sequence_number: int
    chain_hash: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "artifact_id": self.artifact_id,
            "artifact_type": self.artifact_type,
            "artifact_hash": self.artifact_hash,
            "sequence_number": self.sequence_number,
            "chain_hash": self.chain_hash,
        }


@dataclass(frozen=True, slots=True)
class PaidAssessmentOperatorWorkflowState:
    tenant_id: str
    client_id: str
    engagement_id: str
    assessment_id: str

    workflow_stage: str
    lifecycle_stage: str
    lifecycle_pending_next_step: str

    required_operator_action: str
    allowed_operator_actions: tuple[str, ...]
    operator_message: str

    assessment_closed: bool
    report_id: str | None
    findings_disposition: str | None
    recommendations_disposition: str | None

    lifecycle_artifact_count: int
    repository_artifact_count: int
    repository_chain_valid: bool

    latest_lifecycle_artifact: (
        PaidAssessmentOperatorEvidenceReference | None
    )
    closeout_artifact: (
        PaidAssessmentOperatorEvidenceReference | None
    )
    evidence_artifacts: tuple[
        PaidAssessmentOperatorEvidenceReference, ...
    ]

    workflow_type: str = PAID_ASSESSMENT_OPERATOR_WORKFLOW_ID
    version: str = PAID_ASSESSMENT_OPERATOR_WORKFLOW_VERSION
    schema_version: str = (
        PAID_ASSESSMENT_OPERATOR_WORKFLOW_SCHEMA_VERSION
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
            "workflow_type": self.workflow_type,
            "version": self.version,
            "schema_version": self.schema_version,
            "tenant_id": self.tenant_id,
            "client_id": self.client_id,
            "engagement_id": self.engagement_id,
            "assessment_id": self.assessment_id,
            "hierarchy_key": self.hierarchy_key,
            "workflow_stage": self.workflow_stage,
            "lifecycle_stage": self.lifecycle_stage,
            "lifecycle_pending_next_step": (
                self.lifecycle_pending_next_step
            ),
            "required_operator_action": (
                self.required_operator_action
            ),
            "allowed_operator_actions": list(
                self.allowed_operator_actions
            ),
            "operator_message": self.operator_message,
            "assessment_closed": self.assessment_closed,
            "report_id": self.report_id,
            "findings_disposition": self.findings_disposition,
            "recommendations_disposition": (
                self.recommendations_disposition
            ),
            "lifecycle_artifact_count": (
                self.lifecycle_artifact_count
            ),
            "repository_artifact_count": (
                self.repository_artifact_count
            ),
            "repository_chain_valid": (
                self.repository_chain_valid
            ),
            "latest_lifecycle_artifact": (
                None
                if self.latest_lifecycle_artifact is None
                else self.latest_lifecycle_artifact.to_dict()
            ),
            "closeout_artifact": (
                None
                if self.closeout_artifact is None
                else self.closeout_artifact.to_dict()
            ),
            "evidence_artifacts": [
                artifact.to_dict()
                for artifact in self.evidence_artifacts
            ],
        }


class GovernancePaidAssessmentOperatorWorkflowService:
    """
    Project the next operator-facing step from governed paid-assessment
    evidence.

    This service is read-only. It does not authorize, execute, deliver,
    acknowledge, respond, close, remediate, or verify customer outcomes.
    """

    def __init__(
        self,
        *,
        repository: GovernanceAssessmentRepository,
    ) -> None:
        if not isinstance(
            repository,
            GovernanceAssessmentRepository,
        ):
            raise PaidAssessmentOperatorWorkflowError(
                "repository must be a GovernanceAssessmentRepository"
            )

        self._repository = repository
        self._lifecycle_query = (
            GovernancePaidAssessmentLifecycleQueryService(
                repository=repository
            )
        )

    def get_workflow(
        self,
        *,
        context: CommercialHierarchyContext,
    ) -> PaidAssessmentOperatorWorkflowState:
        self._require_context(context)

        lifecycle = self._lifecycle_query.get_state(
            context=context
        )

        if lifecycle.repository_chain_valid is not True:
            raise PaidAssessmentOperatorWorkflowError(
                "repository chain must be valid"
            )

        self._validate_lifecycle_pending_action(
            current_stage=lifecycle.current_stage,
            pending_next_step=lifecycle.pending_next_step,
        )

        closeout_artifacts = self._repository.list_artifacts(
            context=context,
            artifact_type=PAID_ASSESSMENT_CLOSEOUT_ARTIFACT_TYPE,
        )

        if len(closeout_artifacts) > 1:
            raise PaidAssessmentOperatorWorkflowError(
                "duplicate paid-assessment closeout artifacts"
            )

        closeout = (
            None
            if not closeout_artifacts
            else closeout_artifacts[0]
        )

        if closeout is not None:
            self._validate_closeout(
                context=context,
                lifecycle=lifecycle,
                closeout=closeout,
            )

        (
            workflow_stage,
            required_action,
            allowed_actions,
            operator_message,
        ) = self._derive_workflow(
            lifecycle_stage=lifecycle.current_stage,
            closeout_present=closeout is not None,
        )

        lifecycle_references = tuple(
            self._from_lifecycle_reference(reference)
            for reference in lifecycle.lifecycle_artifacts
        )

        closeout_reference = (
            None
            if closeout is None
            else self._from_artifact(closeout)
        )

        evidence_artifacts = lifecycle_references

        if closeout_reference is not None:
            evidence_artifacts = (
                *evidence_artifacts,
                closeout_reference,
            )

        latest_lifecycle_reference = (
            None
            if lifecycle.latest_lifecycle_artifact is None
            else self._from_lifecycle_reference(
                lifecycle.latest_lifecycle_artifact
            )
        )

        return PaidAssessmentOperatorWorkflowState(
            tenant_id=context.tenant_id,
            client_id=context.client_id,
            engagement_id=self._require_text(
                context.engagement_id,
                "engagement_id",
            ),
            assessment_id=self._require_text(
                context.assessment_id,
                "assessment_id",
            ),
            workflow_stage=workflow_stage,
            lifecycle_stage=lifecycle.current_stage,
            lifecycle_pending_next_step=(
                lifecycle.pending_next_step
            ),
            required_operator_action=required_action,
            allowed_operator_actions=allowed_actions,
            operator_message=operator_message,
            assessment_closed=closeout is not None,
            report_id=lifecycle.report_id,
            findings_disposition=(
                lifecycle.findings_disposition
            ),
            recommendations_disposition=(
                lifecycle.recommendations_disposition
            ),
            lifecycle_artifact_count=(
                lifecycle.lifecycle_artifact_count
            ),
            repository_artifact_count=(
                lifecycle.repository_artifact_count
            ),
            repository_chain_valid=True,
            latest_lifecycle_artifact=(
                latest_lifecycle_reference
            ),
            closeout_artifact=closeout_reference,
            evidence_artifacts=evidence_artifacts,
        )

    def _derive_workflow(
        self,
        *,
        lifecycle_stage: str,
        closeout_present: bool,
    ) -> tuple[str, str, tuple[str, ...], str]:
        if closeout_present:
            if lifecycle_stage != LIFECYCLE_STAGE_CLIENT_RESPONSE:
                raise PaidAssessmentOperatorWorkflowError(
                    "closeout requires "
                    "lifecycle_stage=client_response_recorded"
                )

            return (
                WORKFLOW_STAGE_CLOSED,
                ACTION_NONE,
                (),
                (
                    "Assessment is administratively closed. "
                    "No paid-assessment lifecycle action is pending."
                ),
            )

        mapping = {
            LIFECYCLE_STAGE_NOT_STARTED: (
                WORKFLOW_STAGE_AWAITING_DELIVERY,
                ACTION_RECORD_DELIVERY_EVENT,
                (ACTION_RECORD_DELIVERY_EVENT,),
                (
                    "Record governed human delivery only after the "
                    "separate delivery-approval requirements are satisfied."
                ),
            ),
            LIFECYCLE_STAGE_DELIVERED: (
                WORKFLOW_STAGE_AWAITING_CLIENT_RECEIPT,
                ACTION_RECORD_CLIENT_RECEIPT,
                (ACTION_RECORD_CLIENT_RECEIPT,),
                (
                    "Delivery is recorded. Await and record explicit "
                    "client receipt acknowledgment."
                ),
            ),
            LIFECYCLE_STAGE_CLIENT_RECEIPT: (
                WORKFLOW_STAGE_AWAITING_CLIENT_RESPONSE,
                ACTION_RECORD_CLIENT_RESPONSE,
                (ACTION_RECORD_CLIENT_RESPONSE,),
                (
                    "Client receipt is acknowledged. Await and record "
                    "the client's findings and recommendation disposition."
                ),
            ),
            LIFECYCLE_STAGE_CLIENT_RESPONSE: (
                WORKFLOW_STAGE_READY_FOR_CLOSEOUT,
                ACTION_CONFIRM_ADMINISTRATIVE_CLOSEOUT,
                (ACTION_CONFIRM_ADMINISTRATIVE_CLOSEOUT,),
                (
                    "Client response is recorded. The assessment is "
                    "eligible for explicit human administrative closeout."
                ),
            ),
        }

        result = mapping.get(lifecycle_stage)

        if result is None:
            raise PaidAssessmentOperatorWorkflowError(
                "unsupported paid-assessment lifecycle stage: "
                f"{lifecycle_stage}"
            )

        return result

    def _validate_lifecycle_pending_action(
        self,
        *,
        current_stage: str,
        pending_next_step: str,
    ) -> None:
        expected = EXPECTED_LIFECYCLE_PENDING_ACTIONS.get(
            current_stage
        )

        if expected is None:
            raise PaidAssessmentOperatorWorkflowError(
                "unsupported paid-assessment lifecycle stage: "
                f"{current_stage}"
            )

        if pending_next_step != expected:
            raise PaidAssessmentOperatorWorkflowError(
                "lifecycle stage/pending-next-step mismatch: "
                f"{current_stage} requires {expected}"
            )

    def _validate_closeout(
        self,
        *,
        context: CommercialHierarchyContext,
        lifecycle: Any,
        closeout: ImmutableAssessmentArtifact,
    ) -> None:
        if (
            lifecycle.current_stage
            != LIFECYCLE_STAGE_CLIENT_RESPONSE
        ):
            raise PaidAssessmentOperatorWorkflowError(
                "closeout cannot precede client_response_recorded"
            )

        payload = closeout.payload

        if not isinstance(payload, dict):
            raise PaidAssessmentOperatorWorkflowError(
                "closeout payload must be an object"
            )

        if (
            payload.get("closeout_status")
            != PAID_ASSESSMENT_CLOSEOUT_STATUS
        ):
            raise PaidAssessmentOperatorWorkflowError(
                "closeout artifact must have "
                "closeout_status=assessment_closed"
            )

        expected_context = {
            "tenant_id": context.tenant_id,
            "client_id": context.client_id,
            "engagement_id": self._require_text(
                context.engagement_id,
                "engagement_id",
            ),
            "assessment_id": self._require_text(
                context.assessment_id,
                "assessment_id",
            ),
        }

        for field_name, expected_value in expected_context.items():
            if payload.get(field_name) != expected_value:
                raise PaidAssessmentOperatorWorkflowError(
                    "closeout hierarchy mismatch for "
                    f"{field_name}"
                )

        if payload.get("report_id") != lifecycle.report_id:
            raise PaidAssessmentOperatorWorkflowError(
                "closeout report_id does not match lifecycle"
            )

        latest = lifecycle.latest_lifecycle_artifact

        if latest is None:
            raise PaidAssessmentOperatorWorkflowError(
                "closeout requires client-response lineage"
            )

        if (
            payload.get("client_response_artifact_id")
            != latest.artifact_id
        ):
            raise PaidAssessmentOperatorWorkflowError(
                "closeout client-response artifact id mismatch"
            )

        if (
            payload.get("client_response_artifact_hash")
            != latest.artifact_hash
        ):
            raise PaidAssessmentOperatorWorkflowError(
                "closeout client-response artifact hash mismatch"
            )

    @staticmethod
    def _from_lifecycle_reference(
        reference: PaidAssessmentLifecycleArtifactReference,
    ) -> PaidAssessmentOperatorEvidenceReference:
        return PaidAssessmentOperatorEvidenceReference(
            artifact_id=reference.artifact_id,
            artifact_type=reference.artifact_type,
            artifact_hash=reference.artifact_hash,
            sequence_number=reference.sequence_number,
            chain_hash=reference.chain_hash,
        )

    @staticmethod
    def _from_artifact(
        artifact: ImmutableAssessmentArtifact,
    ) -> PaidAssessmentOperatorEvidenceReference:
        return PaidAssessmentOperatorEvidenceReference(
            artifact_id=artifact.artifact_id,
            artifact_type=artifact.artifact_type,
            artifact_hash=artifact.artifact_hash,
            sequence_number=artifact.sequence_number,
            chain_hash=artifact.chain_hash,
        )

    def _require_context(
        self,
        context: CommercialHierarchyContext,
    ) -> None:
        if not isinstance(
            context,
            CommercialHierarchyContext,
        ):
            raise PaidAssessmentOperatorWorkflowError(
                "context must be a CommercialHierarchyContext"
            )

        self._require_text(context.tenant_id, "tenant_id")
        self._require_text(context.client_id, "client_id")
        self._require_text(context.engagement_id, "engagement_id")
        self._require_text(context.assessment_id, "assessment_id")

    @staticmethod
    def _require_text(
        value: str | None,
        field_name: str,
    ) -> str:
        if (
            value is None
            or not isinstance(value, str)
            or not value.strip()
        ):
            raise PaidAssessmentOperatorWorkflowError(
                f"{field_name} must be a non-empty string"
            )

        return value.strip()


SERVICE_TYPE = GovernancePaidAssessmentOperatorWorkflowService