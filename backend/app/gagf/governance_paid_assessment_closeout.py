from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from backend.app.gagf.governance_assessment_isolation import (
    CommercialHierarchyContext,
)
from backend.app.gagf.governance_assessment_repository import (
    GovernanceAssessmentRepository,
    ImmutableAssessmentArtifact,
)
from backend.app.gagf.governance_paid_assessment_lifecycle_persistence import (
    CLIENT_RESPONSE_ARTIFACT_TYPE,
)
from backend.app.gagf.governance_paid_assessment_lifecycle_query import (
    GovernancePaidAssessmentLifecycleQueryService,
    LIFECYCLE_STAGE_CLIENT_RESPONSE_RECORDED,
    NEXT_STEP_NONE,
)


PAID_ASSESSMENT_CLOSEOUT_ID = "governance-paid-assessment-closeout"
PAID_ASSESSMENT_CLOSEOUT_VERSION = "0.1.0"
PAID_ASSESSMENT_CLOSEOUT_SCHEMA_VERSION = "1.0.0"

PAID_ASSESSMENT_CLOSEOUT_ARTIFACT_TYPE = "paid-assessment-closeout"
PAID_ASSESSMENT_CLOSEOUT_STATUS = "assessment_closed"

CLOSEOUT_BASIS_CLIENT_RESPONSE = "client_response_recorded"


class PaidAssessmentCloseoutError(ValueError):
    """Raised when a paid assessment cannot be closed safely."""


@dataclass(frozen=True, slots=True)
class PaidAssessmentCloseoutRequest:
    context: CommercialHierarchyContext
    report_id: str
    closed_by: str
    closeout_reason: str
    administrative_closeout_confirmed: bool

    def __post_init__(self) -> None:
        _require_context(self.context)
        _require_text(self.report_id, "report_id")
        _require_text(self.closed_by, "closed_by")
        _require_text(self.closeout_reason, "closeout_reason")

        if self.administrative_closeout_confirmed is not True:
            raise PaidAssessmentCloseoutError(
                "administrative_closeout_confirmed must be true"
            )


@dataclass(frozen=True, slots=True)
class GovernedPaidAssessmentCloseout:
    tenant_id: str
    client_id: str
    engagement_id: str
    assessment_id: str
    report_id: str

    closeout_id: str
    closeout_status: str
    closeout_basis: str
    closed_by: str
    closeout_reason: str
    closed_at: datetime

    client_response_artifact_id: str
    client_response_artifact_hash: str

    findings_disposition: str
    recommendations_disposition: str

    artifact_id: str
    artifact_hash: str
    sequence_number: int
    chain_hash: str
    repository_chain_valid: bool

    closeout_hash: str

    closeout_type: str = PAID_ASSESSMENT_CLOSEOUT_ID
    version: str = PAID_ASSESSMENT_CLOSEOUT_VERSION
    schema_version: str = PAID_ASSESSMENT_CLOSEOUT_SCHEMA_VERSION

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
            "closeout_id": self.closeout_id,
            "closeout_status": self.closeout_status,
            "closeout_basis": self.closeout_basis,
            "closed_by": self.closed_by,
            "closeout_reason": self.closeout_reason,
            "closed_at": self.closed_at.isoformat(),
            "client_response_artifact_id": (
                self.client_response_artifact_id
            ),
            "client_response_artifact_hash": (
                self.client_response_artifact_hash
            ),
            "findings_disposition": self.findings_disposition,
            "recommendations_disposition": (
                self.recommendations_disposition
            ),
            "artifact_id": self.artifact_id,
            "artifact_hash": self.artifact_hash,
            "sequence_number": self.sequence_number,
            "chain_hash": self.chain_hash,
            "repository_chain_valid": self.repository_chain_valid,
            "closeout_hash": self.closeout_hash,
        }


class GovernancePaidAssessmentCloseoutService:
    """
    Append an immutable administrative closeout artifact.

    Administrative closeout does not establish recommendation implementation,
    intervention request/authorization/execution, causation, ROI, remediation
    success, or verified customer outcome.
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
            raise PaidAssessmentCloseoutError(
                "repository must be a GovernanceAssessmentRepository"
            )

        self._repository = repository
        self._lifecycle_query = (
            GovernancePaidAssessmentLifecycleQueryService(
                repository=repository
            )
        )

    def close_assessment(
        self,
        *,
        request: PaidAssessmentCloseoutRequest,
        created_at: datetime | None = None,
    ) -> GovernedPaidAssessmentCloseout:
        if not isinstance(request, PaidAssessmentCloseoutRequest):
            raise PaidAssessmentCloseoutError(
                "request must be a PaidAssessmentCloseoutRequest"
            )

        context = request.context

        lifecycle = self._lifecycle_query.get_state(
            context=context
        )

        if (
            lifecycle.current_stage
            != LIFECYCLE_STAGE_CLIENT_RESPONSE_RECORDED
        ):
            raise PaidAssessmentCloseoutError(
                "paid assessment requires "
                "current_stage=client_response_recorded before closeout"
            )

        if lifecycle.pending_next_step != NEXT_STEP_NONE:
            raise PaidAssessmentCloseoutError(
                "paid assessment lifecycle has a pending next step"
            )

        if lifecycle.report_id != request.report_id:
            raise PaidAssessmentCloseoutError(
                "closeout report_id does not match lifecycle report_id"
            )

        if lifecycle.findings_disposition is None:
            raise PaidAssessmentCloseoutError(
                "closeout requires findings disposition"
            )

        if lifecycle.recommendations_disposition is None:
            raise PaidAssessmentCloseoutError(
                "closeout requires recommendations disposition"
            )

        if lifecycle.latest_lifecycle_artifact is None:
            raise PaidAssessmentCloseoutError(
                "closeout requires client-response evidence"
            )

        latest = lifecycle.latest_lifecycle_artifact

        if latest.artifact_type != CLIENT_RESPONSE_ARTIFACT_TYPE:
            raise PaidAssessmentCloseoutError(
                "latest lifecycle artifact must be the client response"
            )

        existing_closeout = self._repository.list_artifacts(
            context=context,
            artifact_type=PAID_ASSESSMENT_CLOSEOUT_ARTIFACT_TYPE,
        )

        if existing_closeout:
            raise PaidAssessmentCloseoutError(
                "paid assessment already has a closeout artifact"
            )

        timestamp = _normalize_datetime(created_at)

        engagement_id = _require_text(
            context.engagement_id,
            "engagement_id",
        )
        assessment_id = _require_text(
            context.assessment_id,
            "assessment_id",
        )

        closeout_id = _hash_payload(
            {
                "type": PAID_ASSESSMENT_CLOSEOUT_ARTIFACT_TYPE,
                "tenant_id": context.tenant_id,
                "client_id": context.client_id,
                "engagement_id": engagement_id,
                "assessment_id": assessment_id,
                "report_id": request.report_id,
                "client_response_artifact_id": latest.artifact_id,
                "client_response_artifact_hash": latest.artifact_hash,
                "closed_by": request.closed_by,
                "closeout_reason": request.closeout_reason,
                "closed_at": timestamp.isoformat(),
            }
        )

        payload = {
            "closeout_type": PAID_ASSESSMENT_CLOSEOUT_ID,
            "version": PAID_ASSESSMENT_CLOSEOUT_VERSION,
            "schema_version": PAID_ASSESSMENT_CLOSEOUT_SCHEMA_VERSION,
            "tenant_id": context.tenant_id,
            "client_id": context.client_id,
            "engagement_id": engagement_id,
            "assessment_id": assessment_id,
            "report_id": request.report_id,
            "closeout_id": closeout_id,
            "closeout_status": PAID_ASSESSMENT_CLOSEOUT_STATUS,
            "closeout_basis": CLOSEOUT_BASIS_CLIENT_RESPONSE,
            "closed_by": request.closed_by,
            "closeout_reason": request.closeout_reason,
            "closed_at": timestamp.isoformat(),
            "administrative_closeout_confirmed": True,
            "client_response_artifact_id": latest.artifact_id,
            "client_response_artifact_hash": latest.artifact_hash,
            "findings_disposition": lifecycle.findings_disposition,
            "recommendations_disposition": (
                lifecycle.recommendations_disposition
            ),
        }

        closeout_hash = _hash_payload(payload)

        payload["closeout_hash"] = closeout_hash

        artifact = self._repository.append_artifact(
            context=context,
            artifact_type=PAID_ASSESSMENT_CLOSEOUT_ARTIFACT_TYPE,
            payload=payload,
            created_at=timestamp,
        )

        chain_valid = self._repository.verify_chain(
            context=context
        )

        if chain_valid is not True:
            raise PaidAssessmentCloseoutError(
                "repository chain verification failed after closeout"
            )

        return self._build_result(
            request=request,
            timestamp=timestamp,
            latest=latest,
            artifact=artifact,
            findings_disposition=lifecycle.findings_disposition,
            recommendations_disposition=(
                lifecycle.recommendations_disposition
            ),
            closeout_id=closeout_id,
            closeout_hash=closeout_hash,
            chain_valid=chain_valid,
        )

    def _build_result(
        self,
        *,
        request: PaidAssessmentCloseoutRequest,
        timestamp: datetime,
        latest: Any,
        artifact: ImmutableAssessmentArtifact,
        findings_disposition: str,
        recommendations_disposition: str,
        closeout_id: str,
        closeout_hash: str,
        chain_valid: bool,
    ) -> GovernedPaidAssessmentCloseout:
        context = request.context

        return GovernedPaidAssessmentCloseout(
            tenant_id=context.tenant_id,
            client_id=context.client_id,
            engagement_id=_require_text(
                context.engagement_id,
                "engagement_id",
            ),
            assessment_id=_require_text(
                context.assessment_id,
                "assessment_id",
            ),
            report_id=request.report_id,
            closeout_id=closeout_id,
            closeout_status=PAID_ASSESSMENT_CLOSEOUT_STATUS,
            closeout_basis=CLOSEOUT_BASIS_CLIENT_RESPONSE,
            closed_by=request.closed_by,
            closeout_reason=request.closeout_reason,
            closed_at=timestamp,
            client_response_artifact_id=latest.artifact_id,
            client_response_artifact_hash=latest.artifact_hash,
            findings_disposition=findings_disposition,
            recommendations_disposition=(
                recommendations_disposition
            ),
            artifact_id=artifact.artifact_id,
            artifact_hash=artifact.artifact_hash,
            sequence_number=artifact.sequence_number,
            chain_hash=artifact.chain_hash,
            repository_chain_valid=chain_valid,
            closeout_hash=closeout_hash,
        )


def _require_context(
    context: CommercialHierarchyContext,
) -> None:
    if not isinstance(context, CommercialHierarchyContext):
        raise PaidAssessmentCloseoutError(
            "context must be a CommercialHierarchyContext"
        )

    _require_text(context.tenant_id, "tenant_id")
    _require_text(context.client_id, "client_id")
    _require_text(context.engagement_id, "engagement_id")
    _require_text(context.assessment_id, "assessment_id")


def _require_text(
    value: str | None,
    field_name: str,
) -> str:
    if value is None or not isinstance(value, str) or not value.strip():
        raise PaidAssessmentCloseoutError(
            f"{field_name} must be a non-empty string"
        )

    return value.strip()


def _normalize_datetime(
    value: datetime | None,
) -> datetime:
    timestamp = datetime.now(UTC) if value is None else value

    if timestamp.tzinfo is None:
        raise PaidAssessmentCloseoutError(
            "created_at must be timezone-aware"
        )

    return timestamp.astimezone(UTC)


def _hash_payload(payload: dict[str, Any]) -> str:
    canonical = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )

    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


SERVICE_TYPE = GovernancePaidAssessmentCloseoutService