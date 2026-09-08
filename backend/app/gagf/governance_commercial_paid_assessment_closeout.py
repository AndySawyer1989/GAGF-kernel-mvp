from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from backend.app.gagf.governance_assessment_isolation import (
    CommercialHierarchyContext,
)
from backend.app.gagf.governance_assessment_repository import (
    GovernanceAssessmentRepository,
)
from backend.app.gagf.governance_commercial_paid_assessment_execution import (
    CommercialPaidAssessmentExecutionError,
    GovernanceCommercialPaidAssessmentExecutionService,
)
from backend.app.gagf.governance_paid_assessment_closeout import (
    PAID_ASSESSMENT_CLOSEOUT_STATUS,
)
from backend.app.gagf.governance_paid_assessment_lifecycle_persistence import (
    CLIENT_RESPONSE_ARTIFACT_TYPE,
)
from backend.app.gagf.governance_real_paid_assessment_closeout import (
    GovernanceRealPaidAssessmentCloseoutService,
    RealPaidAssessmentCloseoutError,
)


COMMERCIAL_PAID_ASSESSMENT_CLOSEOUT_ID = (
    "governance-commercial-paid-assessment-closeout"
)
COMMERCIAL_PAID_ASSESSMENT_CLOSEOUT_VERSION = "0.1.0"
COMMERCIAL_PAID_ASSESSMENT_CLOSEOUT_SCHEMA_VERSION = "1.0.0"


class CommercialPaidAssessmentCloseoutError(RuntimeError):
    """Raised when governed commercial closeout fails safely."""


@dataclass(frozen=True, slots=True)
class CommercialPaidAssessmentCloseoutResult:
    tenant_id: str
    client_id: str
    engagement_id: str
    assessment_id: str
    report_id: str

    closeout_status: str
    closed_by: str
    closeout_reason: str

    closeout_artifact_id: str
    closeout_artifact_hash: str

    repository_chain_valid: bool

    closeout_type: str = (
        COMMERCIAL_PAID_ASSESSMENT_CLOSEOUT_ID
    )
    version: str = (
        COMMERCIAL_PAID_ASSESSMENT_CLOSEOUT_VERSION
    )
    schema_version: str = (
        COMMERCIAL_PAID_ASSESSMENT_CLOSEOUT_SCHEMA_VERSION
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
            "closeout_type": self.closeout_type,
            "version": self.version,
            "schema_version": self.schema_version,
            "tenant_id": self.tenant_id,
            "client_id": self.client_id,
            "engagement_id": self.engagement_id,
            "assessment_id": self.assessment_id,
            "hierarchy_key": self.hierarchy_key,
            "report_id": self.report_id,
            "closeout_status": self.closeout_status,
            "administrative_closeout_recorded": True,
            "closed_by": self.closed_by,
            "closeout_reason": self.closeout_reason,
            "closeout_artifact_id": (
                self.closeout_artifact_id
            ),
            "closeout_artifact_hash": (
                self.closeout_artifact_hash
            ),
            "repository_chain_valid": (
                self.repository_chain_valid
            ),
            "boundaries": {
                "closeout_requires_explicit_human_confirmation": True,
                "response_is_not_closeout": True,
                "closeout_is_not_findings_validation": True,
                "closeout_is_not_recommendation_implementation": True,
                "closeout_is_not_intervention_request": True,
                "closeout_is_not_intervention_authorization": True,
                "closeout_is_not_execution_authority": True,
                "closeout_is_not_causation": True,
                "closeout_is_not_roi_verification": True,
                "closeout_is_not_remediation_success": True,
                "closeout_is_not_customer_outcome": True,
                "pa010_remains_closeout_authority": True,
                "pa013_remains_operator_coordination_authority": True,
            },
        }


class GovernanceCommercialPaidAssessmentCloseoutService:
    """
    Thin commercial adapter over the existing real paid-assessment
    administrative-closeout path.

    The path hierarchy is authoritative for assessment identity.
    The browser never supplies a repository path.

    The PA015 execution service derives the governed database
    server-side.

    Durable PA007 client-response evidence is rehydrated from the
    repository and used to reconstruct only the serialized lineage
    wrapper required by the existing real-closeout bridge.

    PA010 remains administrative-closeout authority.
    PA013 remains operator-coordination authority.
    """

    def __init__(
        self,
        *,
        execution_service: (
            GovernanceCommercialPaidAssessmentExecutionService
        ),
    ) -> None:
        if not isinstance(
            execution_service,
            GovernanceCommercialPaidAssessmentExecutionService,
        ):
            raise CommercialPaidAssessmentCloseoutError(
                "execution_service must be a "
                "GovernanceCommercialPaidAssessmentExecutionService"
            )

        self._execution_service = execution_service

    def record(
        self,
        *,
        tenant_id: str,
        client_id: str,
        engagement_id: str,
        assessment_id: str,
        closeout_payload: dict[str, Any],
    ) -> CommercialPaidAssessmentCloseoutResult:
        context = CommercialHierarchyContext(
            tenant_id=self._require_text(
                tenant_id,
                "tenant_id",
            ),
            client_id=self._require_text(
                client_id,
                "client_id",
            ),
            engagement_id=self._require_text(
                engagement_id,
                "engagement_id",
            ),
            assessment_id=self._require_text(
                assessment_id,
                "assessment_id",
            ),
        )

        if not isinstance(closeout_payload, dict):
            raise CommercialPaidAssessmentCloseoutError(
                "closeout_payload must be a JSON object"
            )

        closed_by = self._require_payload_text(
            closeout_payload,
            "closed_by",
        )

        closeout_reason = self._require_payload_text(
            closeout_payload,
            "closeout_reason",
        )

        if (
            closeout_payload.get(
                "administrative_closeout_confirmed"
            )
            is not True
        ):
            raise CommercialPaidAssessmentCloseoutError(
                "administrative_closeout_confirmed must be true"
            )

        try:
            database_path = (
                self._execution_service
                .database_path_for_hierarchy(
                    tenant_id=context.tenant_id,
                    client_id=context.client_id,
                    engagement_id=self._require_context_text(
                        context.engagement_id,
                        "engagement_id",
                    ),
                    assessment_id=self._require_context_text(
                        context.assessment_id,
                        "assessment_id",
                    ),
                )
            )
        except CommercialPaidAssessmentExecutionError as exc:
            raise CommercialPaidAssessmentCloseoutError(
                str(exc)
            ) from exc

        if not database_path.exists():
            raise CommercialPaidAssessmentCloseoutError(
                "governed paid-assessment repository was not found"
            )

        repository = GovernanceAssessmentRepository(
            database_path
        )

        try:
            repository.get_assessment(
                context=context
            )
        except Exception as exc:
            raise CommercialPaidAssessmentCloseoutError(
                "governed paid-assessment hierarchy "
                "was not found in the repository"
            ) from exc

        if repository.verify_chain(
            context=context
        ) is not True:
            raise CommercialPaidAssessmentCloseoutError(
                "repository chain verification failed before closeout"
            )

        response_artifacts = repository.list_artifacts(
            context=context,
            artifact_type=CLIENT_RESPONSE_ARTIFACT_TYPE,
        )

        if len(response_artifacts) != 1:
            raise CommercialPaidAssessmentCloseoutError(
                "governed closeout requires exactly one "
                "persisted client-response artifact"
            )

        response_artifact = response_artifacts[0]

        response = response_artifact.payload

        if not isinstance(response, dict):
            raise CommercialPaidAssessmentCloseoutError(
                "persisted client-response payload "
                "must be a JSON object"
            )

        if (
            response.get("response_status")
            != "client_response_recorded"
        ):
            raise CommercialPaidAssessmentCloseoutError(
                "persisted client response must have "
                "response_status=client_response_recorded"
            )

        report_id = self._require_payload_text(
            response,
            "report_id",
        )

        self._require_payload_text(
            response,
            "response_id",
        )

        self._require_payload_text(
            response,
            "response_hash",
        )

        expected_hierarchy = {
            "tenant_id": context.tenant_id,
            "client_id": context.client_id,
            "engagement_id": self._require_context_text(
                context.engagement_id,
                "engagement_id",
            ),
            "assessment_id": self._require_context_text(
                context.assessment_id,
                "assessment_id",
            ),
        }

        for (
            field_name,
            expected_value,
        ) in expected_hierarchy.items():
            actual_value = self._require_payload_text(
                response,
                field_name,
            )

            if actual_value != expected_value:
                raise CommercialPaidAssessmentCloseoutError(
                    "persisted client-response hierarchy "
                    f"mismatch for {field_name}"
                )

        #
        # Reconstruct only the lineage wrapper expected by
        # GovernanceRealPaidAssessmentCloseoutService.
        #
        # report_id, response_id, response_hash, hierarchy,
        # and repository location all come from governed
        # server-side state, never browser authority.
        #
        client_response_payload = {
            "client_response_recording_passed": True,
            "client_response_recorded": True,
            "result": {
                "client_response_recorded": True,
                "response_status": (
                    "client_response_recorded"
                ),
                "client_response": dict(response),
            },
        }

        real_closeout_payload = {
            "tenant_id": context.tenant_id,
            "client_id": context.client_id,
            "engagement_id": (
                self._require_context_text(
                    context.engagement_id,
                    "engagement_id",
                )
            ),
            "assessment_id": (
                self._require_context_text(
                    context.assessment_id,
                    "assessment_id",
                )
            ),
            "report_id": report_id,
            "closed_by": closed_by,
            "closeout_reason": closeout_reason,
            "administrative_closeout_confirmed": True,
        }

        try:
            result = (
                GovernanceRealPaidAssessmentCloseoutService()
                .record(
                    database_path=database_path,
                    client_response_payload=(
                        client_response_payload
                    ),
                    closeout_payload=(
                        real_closeout_payload
                    ),
                )
            )
        except RealPaidAssessmentCloseoutError as exc:
            raise CommercialPaidAssessmentCloseoutError(
                str(exc)
            ) from exc

        if (
            result.closeout_status
            != PAID_ASSESSMENT_CLOSEOUT_STATUS
        ):
            raise CommercialPaidAssessmentCloseoutError(
                "governed closeout did not return "
                "closeout_status=assessment_closed"
            )

        if result.report_id != report_id:
            raise CommercialPaidAssessmentCloseoutError(
                "governed closeout report lineage mismatch"
            )

        if (
            result.client_response_artifact_id
            != response_artifact.artifact_id
        ):
            raise CommercialPaidAssessmentCloseoutError(
                "governed closeout client-response "
                "artifact id mismatch"
            )

        if (
            result.client_response_artifact_hash
            != response_artifact.artifact_hash
        ):
            raise CommercialPaidAssessmentCloseoutError(
                "governed closeout client-response "
                "artifact hash mismatch"
            )

        if (
            result.operator_result.artifact_id
            != result.closeout_artifact_id
        ):
            raise CommercialPaidAssessmentCloseoutError(
                "PA013 closeout artifact id does not "
                "match real closeout result"
            )

        if (
            result.operator_result.artifact_hash
            != result.closeout_artifact_hash
        ):
            raise CommercialPaidAssessmentCloseoutError(
                "PA013 closeout artifact hash does not "
                "match real closeout result"
            )

        if repository.verify_chain(
            context=context
        ) is not True:
            raise CommercialPaidAssessmentCloseoutError(
                "repository chain verification failed after closeout"
            )

        return CommercialPaidAssessmentCloseoutResult(
            tenant_id=context.tenant_id,
            client_id=context.client_id,
            engagement_id=self._require_context_text(
                context.engagement_id,
                "engagement_id",
            ),
            assessment_id=self._require_context_text(
                context.assessment_id,
                "assessment_id",
            ),
            report_id=result.report_id,
            closeout_status=result.closeout_status,
            closed_by=result.closed_by,
            closeout_reason=result.closeout_reason,
            closeout_artifact_id=(
                result.closeout_artifact_id
            ),
            closeout_artifact_hash=(
                result.closeout_artifact_hash
            ),
            repository_chain_valid=True,
        )

    @staticmethod
    def _require_text(
        value: str,
        field_name: str,
    ) -> str:
        if (
            not isinstance(value, str)
            or not value.strip()
        ):
            raise CommercialPaidAssessmentCloseoutError(
                f"{field_name} must be a non-empty string"
            )

        return value.strip()

    @staticmethod
    def _require_payload_text(
        payload: dict[str, Any],
        field_name: str,
    ) -> str:
        value = payload.get(field_name)

        if (
            not isinstance(value, str)
            or not value.strip()
        ):
            raise CommercialPaidAssessmentCloseoutError(
                f"{field_name} must be a non-empty string"
            )

        return value.strip()

    @staticmethod
    def _require_context_text(
        value: str | None,
        field_name: str,
    ) -> str:
        if (
            not isinstance(value, str)
            or not value.strip()
        ):
            raise CommercialPaidAssessmentCloseoutError(
                f"context requires {field_name}"
            )

        return value.strip()


SERVICE_TYPE = GovernanceCommercialPaidAssessmentCloseoutService
