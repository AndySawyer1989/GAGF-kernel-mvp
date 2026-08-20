from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

from backend.app.gagf.governance_assessment_isolation import (
    CommercialHierarchyContext,
)


REAL_PAID_ASSESSMENT_READINESS_ID = (
    "governance-real-paid-assessment-readiness"
)
REAL_PAID_ASSESSMENT_READINESS_VERSION = "0.1.0"
REAL_PAID_ASSESSMENT_READINESS_SCHEMA_VERSION = "1.0.0"

READINESS_STATUS_READY = "ready_for_paid_work_authorization"
READINESS_STATUS_BLOCKED = "blocked"

ACTION_REQUEST_PAID_WORK_AUTHORIZATION = (
    "request_paid_work_authorization"
)
ACTION_RESOLVE_READINESS_BLOCKERS = (
    "resolve_readiness_blockers"
)


class RealPaidAssessmentReadinessError(ValueError):
    """Raised when real paid-assessment intake is structurally invalid."""


class EvidenceDataClassification(str, Enum):
    NON_SENSITIVE = "non_sensitive"
    SANITIZED = "sanitized"
    REDACTED = "redacted"
    PII = "pii"
    REGULATED = "regulated"
    FEDERAL = "federal"
    SECRET = "secret"


ALLOWED_PILOT_CLASSIFICATIONS = frozenset(
    {
        EvidenceDataClassification.NON_SENSITIVE,
        EvidenceDataClassification.SANITIZED,
        EvidenceDataClassification.REDACTED,
    }
)

BLOCKED_PILOT_CLASSIFICATIONS = frozenset(
    {
        EvidenceDataClassification.PII,
        EvidenceDataClassification.REGULATED,
        EvidenceDataClassification.FEDERAL,
        EvidenceDataClassification.SECRET,
    }
)


def _require_text(value: str, field_name: str) -> str:
    normalized = str(value).strip()

    if not normalized:
        raise RealPaidAssessmentReadinessError(
            f"{field_name} is required"
        )

    return normalized


@dataclass(frozen=True, slots=True)
class RealAssessmentEvidenceDeclaration:
    evidence_id: str
    source_kind: str
    description: str
    classification: EvidenceDataClassification

    client_authorized_for_assessment: bool
    minimization_review_completed: bool
    direct_identifiers_removed: bool

    def __post_init__(self) -> None:
        _require_text(self.evidence_id, "evidence_id")
        _require_text(self.source_kind, "source_kind")
        _require_text(self.description, "description")

        if not isinstance(
            self.classification,
            EvidenceDataClassification,
        ):
            raise RealPaidAssessmentReadinessError(
                "classification must be an EvidenceDataClassification"
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "evidence_id": self.evidence_id,
            "source_kind": self.source_kind,
            "description": self.description,
            "classification": self.classification.value,
            "client_authorized_for_assessment": (
                self.client_authorized_for_assessment
            ),
            "minimization_review_completed": (
                self.minimization_review_completed
            ),
            "direct_identifiers_removed": (
                self.direct_identifiers_removed
            ),
        }


@dataclass(frozen=True, slots=True)
class RealAssessmentStorageDeclaration:
    repository_path: str

    operator_controlled_location: bool
    access_restricted: bool
    storage_protection_confirmed: bool
    backup_plan_recorded: bool
    retention_period_recorded: bool
    deletion_plan_recorded: bool

    def __post_init__(self) -> None:
        _require_text(
            self.repository_path,
            "repository_path",
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "repository_path": self.repository_path,
            "operator_controlled_location": (
                self.operator_controlled_location
            ),
            "access_restricted": self.access_restricted,
            "storage_protection_confirmed": (
                self.storage_protection_confirmed
            ),
            "backup_plan_recorded": self.backup_plan_recorded,
            "retention_period_recorded": (
                self.retention_period_recorded
            ),
            "deletion_plan_recorded": (
                self.deletion_plan_recorded
            ),
        }


@dataclass(frozen=True, slots=True)
class RealPaidAssessmentIntake:
    tenant_id: str
    client_id: str
    engagement_id: str
    assessment_id: str

    client_display_name: str
    assessment_name: str

    operator_name: str
    client_contact_name: str

    assessment_scope_confirmed: bool
    evidence_scope_confirmed: bool
    client_data_use_confirmed: bool
    operator_readiness_confirmed: bool

    evidence: tuple[RealAssessmentEvidenceDeclaration, ...]
    storage: RealAssessmentStorageDeclaration

    def __post_init__(self) -> None:
        for field_name in (
            "tenant_id",
            "client_id",
            "engagement_id",
            "assessment_id",
            "client_display_name",
            "assessment_name",
            "operator_name",
            "client_contact_name",
        ):
            _require_text(
                getattr(self, field_name),
                field_name,
            )

        if not self.evidence:
            raise RealPaidAssessmentReadinessError(
                "at least one evidence declaration is required"
            )

        if not isinstance(
            self.storage,
            RealAssessmentStorageDeclaration,
        ):
            raise RealPaidAssessmentReadinessError(
                "storage must be a RealAssessmentStorageDeclaration"
            )

    @property
    def context(self) -> CommercialHierarchyContext:
        return CommercialHierarchyContext(
            tenant_id=self.tenant_id,
            client_id=self.client_id,
            engagement_id=self.engagement_id,
            assessment_id=self.assessment_id,
        )

    @property
    def hierarchy_key(self) -> str:
        return self.context.hierarchy_key

    def to_dict(self) -> dict[str, Any]:
        return {
            "tenant_id": self.tenant_id,
            "client_id": self.client_id,
            "engagement_id": self.engagement_id,
            "assessment_id": self.assessment_id,
            "hierarchy_key": self.hierarchy_key,
            "client_display_name": self.client_display_name,
            "assessment_name": self.assessment_name,
            "operator_name": self.operator_name,
            "client_contact_name": self.client_contact_name,
            "assessment_scope_confirmed": (
                self.assessment_scope_confirmed
            ),
            "evidence_scope_confirmed": (
                self.evidence_scope_confirmed
            ),
            "client_data_use_confirmed": (
                self.client_data_use_confirmed
            ),
            "operator_readiness_confirmed": (
                self.operator_readiness_confirmed
            ),
            "evidence": tuple(
                item.to_dict()
                for item in self.evidence
            ),
            "storage": self.storage.to_dict(),
        }


@dataclass(frozen=True, slots=True)
class RealPaidAssessmentReadinessResult:
    tenant_id: str
    client_id: str
    engagement_id: str
    assessment_id: str

    readiness_status: str
    required_operator_action: str

    ready_for_paid_work_authorization: bool
    blockers: tuple[str, ...]

    evidence_count: int
    permitted_evidence_count: int
    blocked_evidence_count: int

    assessment_scope_confirmed: bool
    evidence_scope_confirmed: bool
    client_data_use_confirmed: bool
    operator_readiness_confirmed: bool

    storage_location_declared: bool
    storage_controls_declared: bool

    readiness_type: str = REAL_PAID_ASSESSMENT_READINESS_ID
    version: str = REAL_PAID_ASSESSMENT_READINESS_VERSION
    schema_version: str = (
        REAL_PAID_ASSESSMENT_READINESS_SCHEMA_VERSION
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
            "readiness_type": self.readiness_type,
            "version": self.version,
            "schema_version": self.schema_version,
            "tenant_id": self.tenant_id,
            "client_id": self.client_id,
            "engagement_id": self.engagement_id,
            "assessment_id": self.assessment_id,
            "hierarchy_key": self.hierarchy_key,
            "readiness_status": self.readiness_status,
            "required_operator_action": (
                self.required_operator_action
            ),
            "ready_for_paid_work_authorization": (
                self.ready_for_paid_work_authorization
            ),
            "blockers": self.blockers,
            "evidence_count": self.evidence_count,
            "permitted_evidence_count": (
                self.permitted_evidence_count
            ),
            "blocked_evidence_count": (
                self.blocked_evidence_count
            ),
            "assessment_scope_confirmed": (
                self.assessment_scope_confirmed
            ),
            "evidence_scope_confirmed": (
                self.evidence_scope_confirmed
            ),
            "client_data_use_confirmed": (
                self.client_data_use_confirmed
            ),
            "operator_readiness_confirmed": (
                self.operator_readiness_confirmed
            ),
            "storage_location_declared": (
                self.storage_location_declared
            ),
            "storage_controls_declared": (
                self.storage_controls_declared
            ),
            "boundaries": {
                "intake_is_not_paid_work_authorization": True,
                "readiness_is_not_paid_work_authorization": True,
                "readiness_is_not_assessment_execution": True,
                "readiness_is_not_production_onboarding": True,
                "client_data_use_confirmation_is_not_client_consent": True,
                "classification_is_not_evidence_truth": True,
                "storage_declaration_is_not_technical_verification": True,
                "ready_does_not_authorize_sensitive_data": True,
                "ready_does_not_certify_compliance": True,
            },
        }


class GovernanceRealPaidAssessmentReadinessService:
    """
    Evaluate whether a controlled real paid assessment may advance to the
    separate existing paid-work authorization boundary.

    PILOT-002 v0.1 permits only non-sensitive, sanitized, or redacted
    evidence. PII, regulated, federal, and secret evidence remain blocked.
    """

    def evaluate(
        self,
        *,
        intake: RealPaidAssessmentIntake,
    ) -> RealPaidAssessmentReadinessResult:
        if not isinstance(
            intake,
            RealPaidAssessmentIntake,
        ):
            raise RealPaidAssessmentReadinessError(
                "intake must be a RealPaidAssessmentIntake"
            )

        blockers: list[str] = []

        if intake.assessment_scope_confirmed is not True:
            blockers.append(
                "assessment_scope_not_confirmed"
            )

        if intake.evidence_scope_confirmed is not True:
            blockers.append(
                "evidence_scope_not_confirmed"
            )

        if intake.client_data_use_confirmed is not True:
            blockers.append(
                "client_data_use_not_confirmed"
            )

        if intake.operator_readiness_confirmed is not True:
            blockers.append(
                "operator_readiness_not_confirmed"
            )

        storage = intake.storage

        if not storage.operator_controlled_location:
            blockers.append(
                "storage_not_operator_controlled"
            )

        if not storage.access_restricted:
            blockers.append(
                "storage_access_not_restricted"
            )

        if not storage.storage_protection_confirmed:
            blockers.append(
                "storage_protection_not_confirmed"
            )

        if not storage.backup_plan_recorded:
            blockers.append(
                "backup_plan_not_recorded"
            )

        if not storage.retention_period_recorded:
            blockers.append(
                "retention_period_not_recorded"
            )

        if not storage.deletion_plan_recorded:
            blockers.append(
                "deletion_plan_not_recorded"
            )

        repository_path = Path(storage.repository_path)

        if repository_path.name.strip() == "":
            blockers.append(
                "repository_path_invalid"
            )

        permitted_count = 0
        blocked_count = 0

        for item in intake.evidence:
            if item.classification in BLOCKED_PILOT_CLASSIFICATIONS:
                blocked_count += 1
                blockers.append(
                    "evidence_classification_not_permitted:"
                    f"{item.evidence_id}:"
                    f"{item.classification.value}"
                )
                continue

            if item.classification not in ALLOWED_PILOT_CLASSIFICATIONS:
                blocked_count += 1
                blockers.append(
                    "evidence_classification_unknown:"
                    f"{item.evidence_id}"
                )
                continue

            if item.client_authorized_for_assessment is not True:
                blocked_count += 1
                blockers.append(
                    "evidence_not_client_authorized:"
                    f"{item.evidence_id}"
                )
                continue

            if item.minimization_review_completed is not True:
                blocked_count += 1
                blockers.append(
                    "evidence_minimization_not_completed:"
                    f"{item.evidence_id}"
                )
                continue

            if (
                item.classification
                in {
                    EvidenceDataClassification.SANITIZED,
                    EvidenceDataClassification.REDACTED,
                }
                and item.direct_identifiers_removed is not True
            ):
                blocked_count += 1
                blockers.append(
                    "direct_identifiers_not_removed:"
                    f"{item.evidence_id}"
                )
                continue

            permitted_count += 1

        ready = len(blockers) == 0

        return RealPaidAssessmentReadinessResult(
            tenant_id=intake.tenant_id,
            client_id=intake.client_id,
            engagement_id=intake.engagement_id,
            assessment_id=intake.assessment_id,
            readiness_status=(
                READINESS_STATUS_READY
                if ready
                else READINESS_STATUS_BLOCKED
            ),
            required_operator_action=(
                ACTION_REQUEST_PAID_WORK_AUTHORIZATION
                if ready
                else ACTION_RESOLVE_READINESS_BLOCKERS
            ),
            ready_for_paid_work_authorization=ready,
            blockers=tuple(blockers),
            evidence_count=len(intake.evidence),
            permitted_evidence_count=permitted_count,
            blocked_evidence_count=blocked_count,
            assessment_scope_confirmed=(
                intake.assessment_scope_confirmed
            ),
            evidence_scope_confirmed=(
                intake.evidence_scope_confirmed
            ),
            client_data_use_confirmed=(
                intake.client_data_use_confirmed
            ),
            operator_readiness_confirmed=(
                intake.operator_readiness_confirmed
            ),
            storage_location_declared=bool(
                storage.repository_path.strip()
            ),
            storage_controls_declared=all(
                (
                    storage.operator_controlled_location,
                    storage.access_restricted,
                    storage.storage_protection_confirmed,
                    storage.backup_plan_recorded,
                    storage.retention_period_recorded,
                    storage.deletion_plan_recorded,
                )
            ),
        )


SERVICE_TYPE = GovernanceRealPaidAssessmentReadinessService