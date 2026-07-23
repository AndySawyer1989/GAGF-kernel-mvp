from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date, datetime, timezone
from enum import Enum
from typing import Any


GOVERNANCE_ASSESSMENT_SCHEMA_VERSION = "1.0.0"


class AssessmentStatus(str, Enum):
    DRAFT = "draft"
    SCOPED = "scoped"
    EVIDENCE_COLLECTION = "evidence-collection"
    ANALYSIS = "analysis"
    REVIEW = "review"
    COMPLETE = "complete"
    ARCHIVED = "archived"


class EvidenceSourceKind(str, Enum):
    CSV = "csv"
    API = "api"
    JIRA = "jira"
    SERVICENOW = "servicenow"
    GITHUB = "github"
    INTERVIEW = "interview"
    POLICY = "policy"
    MANUAL = "manual"


class InterventionStatus(str, Enum):
    PROPOSED = "proposed"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    IN_PROGRESS = "in-progress"
    COMPLETE = "complete"


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def require_text(value: str, field_name: str) -> str:
    normalized = value.strip()

    if not normalized:
        raise ValueError(f"{field_name} must not be empty")

    return normalized


def require_unique_identifiers(
    values: tuple[Any, ...],
    *,
    attribute_name: str,
    collection_name: str,
) -> None:
    identifiers = [
        getattr(value, attribute_name)
        for value in values
    ]

    if len(identifiers) != len(set(identifiers)):
        raise ValueError(
            f"{collection_name} contains duplicate identifiers"
        )


def serialize_domain_value(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value

    if isinstance(value, datetime):
        return value.isoformat()

    if isinstance(value, date):
        return value.isoformat()

    if isinstance(value, tuple):
        return [
            serialize_domain_value(item)
            for item in value
        ]

    if isinstance(value, list):
        return [
            serialize_domain_value(item)
            for item in value
        ]

    if isinstance(value, dict):
        return {
            key: serialize_domain_value(item)
            for key, item in value.items()
        }

    return value


@dataclass(frozen=True, slots=True)
class ClientRecord:
    tenant_id: str
    client_id: str
    name: str
    created_at: datetime
    schema_version: str = GOVERNANCE_ASSESSMENT_SCHEMA_VERSION

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "tenant_id",
            require_text(self.tenant_id, "tenant_id"),
        )
        object.__setattr__(
            self,
            "client_id",
            require_text(self.client_id, "client_id"),
        )
        object.__setattr__(
            self,
            "name",
            require_text(self.name, "name"),
        )


@dataclass(frozen=True, slots=True)
class EngagementRecord:
    tenant_id: str
    client_id: str
    engagement_id: str
    name: str
    created_at: datetime

    def __post_init__(self) -> None:
        for field_name in (
            "tenant_id",
            "client_id",
            "engagement_id",
            "name",
        ):
            object.__setattr__(
                self,
                field_name,
                require_text(
                    getattr(self, field_name),
                    field_name,
                ),
            )


@dataclass(frozen=True, slots=True)
class AssessmentScope:
    workflow_names: tuple[str, ...]
    organizational_units: tuple[str, ...]
    period_start: date
    period_end: date
    objectives: tuple[str, ...]
    exclusions: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.workflow_names:
            raise ValueError(
                "workflow_names must contain at least one workflow"
            )

        if not self.organizational_units:
            raise ValueError(
                "organizational_units must contain at least one unit"
            )

        if not self.objectives:
            raise ValueError(
                "objectives must contain at least one objective"
            )

        if self.period_end < self.period_start:
            raise ValueError(
                "period_end must not precede period_start"
            )


@dataclass(frozen=True, slots=True)
class EvidenceSourceReference:
    source_id: str
    kind: EvidenceSourceKind
    display_name: str
    source_location: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "source_id",
            require_text(self.source_id, "source_id"),
        )
        object.__setattr__(
            self,
            "display_name",
            require_text(self.display_name, "display_name"),
        )


@dataclass(frozen=True, slots=True)
class FindingReference:
    finding_id: str
    category: str
    title: str
    severity: int
    confidence: float

    def __post_init__(self) -> None:
        if not 1 <= self.severity <= 5:
            raise ValueError("severity must be between 1 and 5")

        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(
                "confidence must be between 0.0 and 1.0"
            )


@dataclass(frozen=True, slots=True)
class MetricReference:
    metric_id: str
    name: str
    value: float
    unit: str


@dataclass(frozen=True, slots=True)
class InterventionReference:
    intervention_id: str
    title: str
    related_finding_ids: tuple[str, ...]
    priority: int
    status: InterventionStatus = InterventionStatus.PROPOSED

    def __post_init__(self) -> None:
        if not 1 <= self.priority <= 5:
            raise ValueError("priority must be between 1 and 5")

        if not self.related_finding_ids:
            raise ValueError(
                "related_finding_ids must not be empty"
            )


@dataclass(frozen=True, slots=True)
class ReportReference:
    report_id: str
    report_format: str
    location: str
    generated_at: datetime


@dataclass(frozen=True, slots=True)
class GovernanceAssessment:
    tenant_id: str
    client_id: str
    engagement_id: str
    assessment_id: str
    name: str
    status: AssessmentStatus
    scope: AssessmentScope
    evidence_sources: tuple[EvidenceSourceReference, ...]
    findings: tuple[FindingReference, ...]
    metrics: tuple[MetricReference, ...]
    interventions: tuple[InterventionReference, ...]
    reports: tuple[ReportReference, ...]
    created_at: datetime
    updated_at: datetime
    schema_version: str = GOVERNANCE_ASSESSMENT_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for field_name in (
            "tenant_id",
            "client_id",
            "engagement_id",
            "assessment_id",
            "name",
        ):
            object.__setattr__(
                self,
                field_name,
                require_text(
                    getattr(self, field_name),
                    field_name,
                ),
            )

        if self.updated_at < self.created_at:
            raise ValueError(
                "updated_at must not precede created_at"
            )

        require_unique_identifiers(
            self.evidence_sources,
            attribute_name="source_id",
            collection_name="evidence_sources",
        )
        require_unique_identifiers(
            self.findings,
            attribute_name="finding_id",
            collection_name="findings",
        )
        require_unique_identifiers(
            self.metrics,
            attribute_name="metric_id",
            collection_name="metrics",
        )
        require_unique_identifiers(
            self.interventions,
            attribute_name="intervention_id",
            collection_name="interventions",
        )
        require_unique_identifiers(
            self.reports,
            attribute_name="report_id",
            collection_name="reports",
        )

        known_findings = {
            finding.finding_id
            for finding in self.findings
        }

        for intervention in self.interventions:
            unknown_findings = (
                set(intervention.related_finding_ids)
                - known_findings
            )

            if unknown_findings:
                raise ValueError(
                    "intervention references unknown findings: "
                    + ", ".join(sorted(unknown_findings))
                )

    def to_dict(self) -> dict[str, Any]:
        return serialize_domain_value(asdict(self))

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
