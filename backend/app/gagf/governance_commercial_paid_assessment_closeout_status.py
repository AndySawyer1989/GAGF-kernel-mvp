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
    GovernanceCommercialPaidAssessmentExecutionService,
)
from backend.app.gagf.governance_paid_assessment_closeout import (
    PAID_ASSESSMENT_CLOSEOUT_ARTIFACT_TYPE,
    PAID_ASSESSMENT_CLOSEOUT_STATUS,
)


COMMERCIAL_PAID_ASSESSMENT_CLOSEOUT_STATUS_ID = (
    "governance-commercial-paid-assessment-closeout-status"
)
COMMERCIAL_PAID_ASSESSMENT_CLOSEOUT_STATUS_VERSION = "0.1.0"
COMMERCIAL_PAID_ASSESSMENT_CLOSEOUT_STATUS_SCHEMA_VERSION = "1.0.0"


class CommercialPaidAssessmentCloseoutStatusError(ValueError):
    """Raised when governed closeout status cannot be projected safely."""


@dataclass(frozen=True, slots=True)
class CommercialPaidAssessmentCloseoutStatus:
    tenant_id: str
    client_id: str
    engagement_id: str
    assessment_id: str

    found: bool
    closeout_recorded: bool
    closeout_status: str | None

    report_id: str | None
    closed_by: str | None
    closed_at: str | None
    closeout_reason: str | None

    repository_chain_valid: bool

    status_type: str = (
        COMMERCIAL_PAID_ASSESSMENT_CLOSEOUT_STATUS_ID
    )
    version: str = (
        COMMERCIAL_PAID_ASSESSMENT_CLOSEOUT_STATUS_VERSION
    )
    schema_version: str = (
        COMMERCIAL_PAID_ASSESSMENT_CLOSEOUT_STATUS_SCHEMA_VERSION
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
            "status_type": self.status_type,
            "version": self.version,
            "schema_version": self.schema_version,
            "tenant_id": self.tenant_id,
            "client_id": self.client_id,
            "engagement_id": self.engagement_id,
            "assessment_id": self.assessment_id,
            "hierarchy_key": self.hierarchy_key,
            "found": self.found,
            "closeout_recorded": self.closeout_recorded,
            "closeout_status": self.closeout_status,
            "report_id": self.report_id,
            "closed_by": self.closed_by,
            "closed_at": self.closed_at,
            "closeout_reason": self.closeout_reason,
            "repository_chain_valid": (
                self.repository_chain_valid
            ),
            "boundaries": {
                "closeout_status_is_read_only_projection": True,
                "client_response_is_not_closeout": True,
                "closeout_requires_explicit_human_confirmation": True,
                "closeout_is_not_findings_validation": True,
                "closeout_is_not_recommendation_implementation": True,
                "closeout_is_not_intervention_request": True,
                "closeout_is_not_intervention_authorization": True,
                "closeout_is_not_execution_authority": True,
                "closeout_is_not_causation": True,
                "closeout_is_not_roi_verification": True,
                "closeout_is_not_remediation_success": True,
                "closeout_is_not_customer_outcome": True,
                "repository_integrity_is_not_closeout_correctness": True,
                "pa010_remains_closeout_authority": True,
                "pa013_remains_operator_coordination_authority": True,
            },
        }


class GovernanceCommercialPaidAssessmentCloseoutStatusService:
    """
    Read-only restart-safe projection of governed administrative closeout.

    The PA015 execution service derives the repository location
    server-side from the authoritative hierarchy.

    This service does not:
    - create closeout,
    - infer closeout from client response,
    - validate findings,
    - authorize recommendations,
    - authorize interventions,
    - establish execution authority,
    - establish causation,
    - establish ROI,
    - establish remediation success,
    - establish customer outcomes.

    PA010 remains closeout authority.
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
            raise CommercialPaidAssessmentCloseoutStatusError(
                "execution_service must be a "
                "GovernanceCommercialPaidAssessmentExecutionService"
            )

        self._execution_service = execution_service

    def get_status(
        self,
        *,
        tenant_id: str,
        client_id: str,
        engagement_id: str,
        assessment_id: str,
    ) -> CommercialPaidAssessmentCloseoutStatus:
        hierarchy = self._validate_hierarchy(
            tenant_id=tenant_id,
            client_id=client_id,
            engagement_id=engagement_id,
            assessment_id=assessment_id,
        )

        database_path = (
            self._execution_service
            .database_path_for_hierarchy(
                tenant_id=hierarchy.tenant_id,
                client_id=hierarchy.client_id,
                engagement_id=hierarchy.engagement_id,
                assessment_id=hierarchy.assessment_id,
            )
        )

        if not database_path.exists():
            return self._not_found(
                hierarchy=hierarchy,
            )

        if not database_path.is_file():
            raise CommercialPaidAssessmentCloseoutStatusError(
                "governed assessment database path is not a file"
            )

        try:
            repository = GovernanceAssessmentRepository(
                database_path
            )

            repository.get_assessment(
                context=hierarchy
            )

            if (
                repository.verify_chain(
                    context=hierarchy
                )
                is not True
            ):
                raise CommercialPaidAssessmentCloseoutStatusError(
                    "governed assessment repository chain is invalid"
                )

            closeout_artifacts = (
                repository.list_artifacts(
                    context=hierarchy,
                    artifact_type=(
                        PAID_ASSESSMENT_CLOSEOUT_ARTIFACT_TYPE
                    ),
                )
            )

        except CommercialPaidAssessmentCloseoutStatusError:
            raise

        except Exception as exc:
            raise CommercialPaidAssessmentCloseoutStatusError(
                "governed closeout status could not be read: "
                f"{exc}"
            ) from exc

        if len(closeout_artifacts) == 0:
            return self._not_found(
                hierarchy=hierarchy,
                repository_chain_valid=True,
            )

        if len(closeout_artifacts) != 1:
            raise CommercialPaidAssessmentCloseoutStatusError(
                "expected exactly one persisted closeout artifact"
            )

        artifact = closeout_artifacts[0]
        payload = artifact.payload

        self._validate_closeout_payload(
            payload=payload,
            hierarchy=hierarchy,
        )

        return CommercialPaidAssessmentCloseoutStatus(
            tenant_id=hierarchy.tenant_id,
            client_id=hierarchy.client_id,
            engagement_id=hierarchy.engagement_id,
            assessment_id=hierarchy.assessment_id,
            found=True,
            closeout_recorded=True,
            closeout_status=(
                PAID_ASSESSMENT_CLOSEOUT_STATUS
            ),
            report_id=self._require_payload_text(
                payload,
                "report_id",
            ),
            closed_by=self._require_payload_text(
                payload,
                "closed_by",
            ),
            closed_at=self._require_payload_text(
                payload,
                "closed_at",
            ),
            closeout_reason=self._require_payload_text(
                payload,
                "closeout_reason",
            ),
            repository_chain_valid=True,
        )

    @staticmethod
    def _validate_hierarchy(
        *,
        tenant_id: str,
        client_id: str,
        engagement_id: str,
        assessment_id: str,
    ) -> CommercialHierarchyContext:
        values = (
            ("tenant_id", tenant_id),
            ("client_id", client_id),
            ("engagement_id", engagement_id),
            ("assessment_id", assessment_id),
        )

        normalized: dict[str, str] = {}

        for field_name, value in values:
            if (
                not isinstance(value, str)
                or not value.strip()
            ):
                raise CommercialPaidAssessmentCloseoutStatusError(
                    f"{field_name} must be non-empty"
                )

            normalized[field_name] = value.strip()

        return CommercialHierarchyContext(
            tenant_id=normalized["tenant_id"],
            client_id=normalized["client_id"],
            engagement_id=normalized["engagement_id"],
            assessment_id=normalized["assessment_id"],
        )

    def _validate_closeout_payload(
        self,
        *,
        payload: dict[str, Any],
        hierarchy: CommercialHierarchyContext,
    ) -> None:
        if not isinstance(payload, dict):
            raise CommercialPaidAssessmentCloseoutStatusError(
                "persisted closeout payload must be an object"
            )

        expected = {
            "tenant_id": hierarchy.tenant_id,
            "client_id": hierarchy.client_id,
            "engagement_id": hierarchy.engagement_id,
            "assessment_id": hierarchy.assessment_id,
        }

        for field_name, expected_value in expected.items():
            actual_value = self._require_payload_text(
                payload,
                field_name,
            )

            if actual_value != expected_value:
                raise CommercialPaidAssessmentCloseoutStatusError(
                    "persisted closeout hierarchy mismatch: "
                    f"{field_name}"
                )

        closeout_status = self._require_payload_text(
            payload,
            "closeout_status",
        )

        if (
            closeout_status
            != PAID_ASSESSMENT_CLOSEOUT_STATUS
        ):
            raise CommercialPaidAssessmentCloseoutStatusError(
                "persisted closeout artifact must have "
                "closeout_status=assessment_closed"
            )

        if (
            payload.get(
                "administrative_closeout_confirmed"
            )
            is not True
        ):
            raise CommercialPaidAssessmentCloseoutStatusError(
                "persisted closeout artifact must have "
                "administrative_closeout_confirmed=true"
            )

        self._require_payload_text(
            payload,
            "report_id",
        )

        self._require_payload_text(
            payload,
            "closed_by",
        )

        self._require_payload_text(
            payload,
            "closed_at",
        )

        self._require_payload_text(
            payload,
            "closeout_reason",
        )

        self._require_payload_text(
            payload,
            "client_response_artifact_id",
        )

        self._require_payload_text(
            payload,
            "client_response_artifact_hash",
        )

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
            raise CommercialPaidAssessmentCloseoutStatusError(
                f"persisted closeout {field_name} "
                "must be non-empty"
            )

        return value.strip()

    @staticmethod
    def _not_found(
        *,
        hierarchy: CommercialHierarchyContext,
        repository_chain_valid: bool = False,
    ) -> CommercialPaidAssessmentCloseoutStatus:
        return CommercialPaidAssessmentCloseoutStatus(
            tenant_id=hierarchy.tenant_id,
            client_id=hierarchy.client_id,
            engagement_id=hierarchy.engagement_id,
            assessment_id=hierarchy.assessment_id,
            found=False,
            closeout_recorded=False,
            closeout_status=None,
            report_id=None,
            closed_by=None,
            closed_at=None,
            closeout_reason=None,
            repository_chain_valid=repository_chain_valid,
        )


SERVICE_TYPE = GovernanceCommercialPaidAssessmentCloseoutStatusService
