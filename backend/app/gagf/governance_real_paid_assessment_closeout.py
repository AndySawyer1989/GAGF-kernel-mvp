from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from backend.app.gagf.governance_assessment_isolation import (
    CommercialHierarchyContext,
)
from backend.app.gagf.governance_assessment_repository import (
    GovernanceAssessmentRepository,
)
from backend.app.gagf.governance_paid_assessment_closeout import (
    PAID_ASSESSMENT_CLOSEOUT_ARTIFACT_TYPE,
    PAID_ASSESSMENT_CLOSEOUT_STATUS,
    PaidAssessmentCloseoutRequest,
)
from backend.app.gagf.governance_paid_assessment_lifecycle_persistence import (
    CLIENT_RESPONSE_ARTIFACT_TYPE,
)
from backend.app.gagf.governance_paid_assessment_resumable_operator_runner import (
    GovernancePaidAssessmentResumableOperatorRunner,
    PaidAssessmentOperatorActionResult,
)


REAL_PAID_ASSESSMENT_CLOSEOUT_ID = (
    "governance-real-paid-assessment-closeout"
)
REAL_PAID_ASSESSMENT_CLOSEOUT_VERSION = "0.1.0"
REAL_PAID_ASSESSMENT_CLOSEOUT_SCHEMA_VERSION = "1.0.0"


class RealPaidAssessmentCloseoutError(ValueError):
    """Raised when a real paid assessment cannot be closed safely."""


@dataclass(frozen=True, slots=True)
class RealPaidAssessmentCloseoutResult:
    tenant_id: str
    client_id: str
    engagement_id: str
    assessment_id: str
    report_id: str

    closed_by: str
    closeout_reason: str

    client_response_artifact_id: str
    client_response_artifact_hash: str

    closeout_artifact_id: str
    closeout_artifact_hash: str
    closeout_status: str

    operator_result: PaidAssessmentOperatorActionResult

    closeout_type: str = REAL_PAID_ASSESSMENT_CLOSEOUT_ID
    version: str = REAL_PAID_ASSESSMENT_CLOSEOUT_VERSION
    schema_version: str = REAL_PAID_ASSESSMENT_CLOSEOUT_SCHEMA_VERSION

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
            "closed_by": self.closed_by,
            "closeout_reason": self.closeout_reason,
            "administrative_closeout_confirmed": True,
            "client_response_artifact_id": (
                self.client_response_artifact_id
            ),
            "client_response_artifact_hash": (
                self.client_response_artifact_hash
            ),
            "closeout_artifact_id": self.closeout_artifact_id,
            "closeout_artifact_hash": self.closeout_artifact_hash,
            "closeout_status": self.closeout_status,
            "operator_result": self.operator_result.to_dict(),
            "administrative_closeout_recorded": True,
            "boundaries": {
                "pilot010_is_input_evidence_not_closeout_authority": True,
                "durable_repository_is_lifecycle_authority": True,
                "pa010_remains_closeout_authority": True,
                "pa013_remains_operator_coordination_authority": True,
                "closeout_is_not_recommendation_implementation": True,
                "closeout_is_not_intervention_request": True,
                "closeout_is_not_intervention_authorization": True,
                "closeout_is_not_execution": True,
                "closeout_is_not_causation": True,
                "closeout_is_not_roi_verification": True,
                "closeout_is_not_remediation_success": True,
                "closeout_is_not_customer_outcome": True,
            },
        }


class GovernanceRealPaidAssessmentCloseoutService:
    """
    Record an explicit administrative closeout after PILOT-010.

    PILOT-010 serialized output supplies lineage evidence.
    The durable repository remains authoritative for the actual
    client-response lifecycle state.

    PA013 remains operator coordination authority.
    PA010 remains administrative closeout authority.
    """

    def record(
        self,
        *,
        database_path: Path,
        client_response_payload: dict[str, Any],
        closeout_payload: dict[str, Any],
    ) -> RealPaidAssessmentCloseoutResult:
        database_path = Path(database_path)

        if not database_path.exists():
            raise RealPaidAssessmentCloseoutError(
                f"database does not exist: {database_path}"
            )

        if not database_path.is_file():
            raise RealPaidAssessmentCloseoutError(
                f"database is not a file: {database_path}"
            )

        if not isinstance(client_response_payload, dict):
            raise RealPaidAssessmentCloseoutError(
                "client_response_payload must be a JSON object"
            )

        if not isinstance(closeout_payload, dict):
            raise RealPaidAssessmentCloseoutError(
                "closeout_payload must be a JSON object"
            )

        client_response = self._extract_pilot010_result(
            client_response_payload
        )

        context = CommercialHierarchyContext(
            tenant_id=self._require_text(
                client_response,
                "tenant_id",
            ),
            client_id=self._require_text(
                client_response,
                "client_id",
            ),
            engagement_id=self._require_text(
                client_response,
                "engagement_id",
            ),
            assessment_id=self._require_text(
                client_response,
                "assessment_id",
            ),
        )

        report_id = self._require_text(
            client_response,
            "report_id",
        )

        self._require_closeout_identity(
            closeout_payload=closeout_payload,
            context=context,
            report_id=report_id,
        )

        administrative_closeout_confirmed = closeout_payload.get(
            "administrative_closeout_confirmed"
        )

        if administrative_closeout_confirmed is not True:
            raise RealPaidAssessmentCloseoutError(
                "administrative_closeout_confirmed must be true"
            )

        closed_by = self._require_text(
            closeout_payload,
            "closed_by",
        )

        closeout_reason = self._require_text(
            closeout_payload,
            "closeout_reason",
        )

        repository = GovernanceAssessmentRepository(
            database_path
        )

        client_response_artifacts = repository.list_artifacts(
            context=context,
            artifact_type=CLIENT_RESPONSE_ARTIFACT_TYPE,
        )

        if len(client_response_artifacts) != 1:
            raise RealPaidAssessmentCloseoutError(
                "durable repository must contain exactly one "
                "client-response lifecycle artifact before closeout"
            )

        durable_client_response = client_response_artifacts[0]

        serialized_response_id = self._require_text(
            client_response,
            "response_id",
        )

        serialized_response_hash = self._require_text(
            client_response,
            "response_hash",
        )

        if (
            durable_client_response.payload.get("response_id")
            != serialized_response_id
        ):
            raise RealPaidAssessmentCloseoutError(
                "serialized PILOT-010 response_id does not match "
                "durable client-response artifact"
            )

        if (
            durable_client_response.payload.get("response_hash")
            != serialized_response_hash
        ):
            raise RealPaidAssessmentCloseoutError(
                "serialized PILOT-010 response_hash does not match "
                "durable client-response artifact"
            )

        request = PaidAssessmentCloseoutRequest(
            context=context,
            report_id=report_id,
            closed_by=closed_by,
            closeout_reason=closeout_reason,
            administrative_closeout_confirmed=True,
        )

        runner = GovernancePaidAssessmentResumableOperatorRunner(
            repository=repository
        )

        operator_result = runner.confirm_administrative_closeout(
            request=request
        )

        closeout_artifacts = repository.list_artifacts(
            context=context,
            artifact_type=PAID_ASSESSMENT_CLOSEOUT_ARTIFACT_TYPE,
        )

        if len(closeout_artifacts) != 1:
            raise RealPaidAssessmentCloseoutError(
                "administrative closeout did not produce exactly "
                "one durable closeout artifact"
            )

        closeout_artifact = closeout_artifacts[0]
        closeout = closeout_artifact.payload

        if (
            closeout.get("closeout_status")
            != PAID_ASSESSMENT_CLOSEOUT_STATUS
        ):
            raise RealPaidAssessmentCloseoutError(
                "durable closeout artifact does not have "
                "closeout_status=assessment_closed"
            )

        if closeout.get("report_id") != report_id:
            raise RealPaidAssessmentCloseoutError(
                "durable closeout report_id mismatch"
            )

        if (
            closeout.get("client_response_artifact_id")
            != durable_client_response.artifact_id
        ):
            raise RealPaidAssessmentCloseoutError(
                "closeout is not bound to the durable "
                "client-response artifact id"
            )

        if (
            closeout.get("client_response_artifact_hash")
            != durable_client_response.artifact_hash
        ):
            raise RealPaidAssessmentCloseoutError(
                "closeout is not bound to the durable "
                "client-response artifact hash"
            )

        if repository.verify_chain(context=context) is not True:
            raise RealPaidAssessmentCloseoutError(
                "repository chain verification failed after closeout"
            )

        return RealPaidAssessmentCloseoutResult(
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
            report_id=report_id,
            closed_by=closed_by,
            closeout_reason=closeout_reason,
            client_response_artifact_id=(
                durable_client_response.artifact_id
            ),
            client_response_artifact_hash=(
                durable_client_response.artifact_hash
            ),
            closeout_artifact_id=closeout_artifact.artifact_id,
            closeout_artifact_hash=closeout_artifact.artifact_hash,
            closeout_status=PAID_ASSESSMENT_CLOSEOUT_STATUS,
            operator_result=operator_result,
        )

    def _extract_pilot010_result(
        self,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        if payload.get("client_response_recording_passed") is not True:
            raise RealPaidAssessmentCloseoutError(
                "PILOT-010 client response recording is not successful"
            )

        if payload.get("client_response_recorded") is not True:
            raise RealPaidAssessmentCloseoutError(
                "PILOT-010 client response is not recorded"
            )

        result = payload.get("result")

        if not isinstance(result, dict):
            raise RealPaidAssessmentCloseoutError(
                "PILOT-010 result must be a JSON object"
            )

        if result.get("client_response_recorded") is not True:
            raise RealPaidAssessmentCloseoutError(
                "PILOT-010 result does not confirm client response"
            )

        if result.get("response_status") != "client_response_recorded":
            raise RealPaidAssessmentCloseoutError(
                "PILOT-010 result must have "
                "response_status=client_response_recorded"
            )

        client_response = result.get("client_response")

        if not isinstance(client_response, dict):
            raise RealPaidAssessmentCloseoutError(
                "PILOT-010 result.client_response must be a JSON object"
            )

        if (
            client_response.get("response_status")
            != "client_response_recorded"
        ):
            raise RealPaidAssessmentCloseoutError(
                "PILOT-010 governed client response must have "
                "response_status=client_response_recorded"
            )

        return client_response

    def _require_closeout_identity(
        self,
        *,
        closeout_payload: dict[str, Any],
        context: CommercialHierarchyContext,
        report_id: str,
    ) -> None:
        expected = {
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
            "report_id": report_id,
        }

        for field_name, expected_value in expected.items():
            actual_value = self._require_text(
                closeout_payload,
                field_name,
            )

            if actual_value != expected_value:
                raise RealPaidAssessmentCloseoutError(
                    f"{field_name} does not match PILOT-010 "
                    "client-response lineage"
                )

    @staticmethod
    def _require_text(
        payload: dict[str, Any],
        field_name: str,
    ) -> str:
        value = payload.get(field_name)

        if not isinstance(value, str) or not value.strip():
            raise RealPaidAssessmentCloseoutError(
                f"{field_name} must be a non-empty string"
            )

        return value.strip()

    @staticmethod
    def _require_context_text(
        value: str | None,
        field_name: str,
    ) -> str:
        if not isinstance(value, str) or not value.strip():
            raise RealPaidAssessmentCloseoutError(
                f"{field_name} must be a non-empty string"
            )

        return value.strip()


SERVICE_TYPE = GovernanceRealPaidAssessmentCloseoutService