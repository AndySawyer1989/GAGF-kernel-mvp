from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import date
from enum import Enum
from typing import Any

from backend.app.gagf.governance_assessment_domain import (
    AssessmentScope,
    EvidenceSourceKind,
)
from backend.app.gagf.governance_assessment_isolation import (
    CommercialHierarchyContext,
)


ASSESSMENT_SCOPE_CONFIGURATION_VERSION = "1.0.0"


class ScopeConfigurationStatus(str, Enum):
    DRAFT = "draft"
    VALIDATED = "validated"
    LOCKED = "locked"


class ScopeConfigurationError(ValueError):
    """Raised when assessment scope configuration is invalid."""


def require_text(value: str, field_name: str) -> str:
    normalized = value.strip()

    if not normalized:
        raise ScopeConfigurationError(
            f"{field_name} must not be empty"
        )

    return normalized


def normalize_text_values(
    values: tuple[str, ...],
    *,
    field_name: str,
    required: bool = True,
) -> tuple[str, ...]:
    normalized = tuple(
        require_text(value, field_name)
        for value in values
    )

    if required and not normalized:
        raise ScopeConfigurationError(
            f"{field_name} must contain at least one value"
        )

    if len(normalized) != len(set(normalized)):
        raise ScopeConfigurationError(
            f"{field_name} contains duplicate values"
        )

    return normalized


def canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )


def sha256_text(value: str) -> str:
    return hashlib.sha256(
        value.encode("utf-8")
    ).hexdigest()


@dataclass(frozen=True, slots=True)
class EvidenceRequirement:
    requirement_id: str
    source_kind: EvidenceSourceKind
    description: str
    required: bool = True
    minimum_record_count: int = 1

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "requirement_id",
            require_text(
                self.requirement_id,
                "requirement_id",
            ),
        )
        object.__setattr__(
            self,
            "description",
            require_text(
                self.description,
                "description",
            ),
        )

        if self.minimum_record_count < 0:
            raise ScopeConfigurationError(
                "minimum_record_count must not be negative"
            )

        if self.required and self.minimum_record_count < 1:
            raise ScopeConfigurationError(
                "required evidence must have a minimum count of at least 1"
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "requirement_id": self.requirement_id,
            "source_kind": self.source_kind.value,
            "description": self.description,
            "required": self.required,
            "minimum_record_count": self.minimum_record_count,
        }


@dataclass(frozen=True, slots=True)
class AssessmentScopeConfiguration:
    tenant_id: str
    client_id: str
    engagement_id: str
    assessment_id: str
    assessment_name: str
    workflow_names: tuple[str, ...]
    organizational_units: tuple[str, ...]
    period_start: date
    period_end: date
    objectives: tuple[str, ...]
    expected_outcomes: tuple[str, ...]
    exclusions: tuple[str, ...]
    evidence_requirements: tuple[EvidenceRequirement, ...]
    status: ScopeConfigurationStatus
    configuration_hash: str
    schema_version: str = ASSESSMENT_SCOPE_CONFIGURATION_VERSION

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

    def to_scope(self) -> AssessmentScope:
        return AssessmentScope(
            workflow_names=self.workflow_names,
            organizational_units=self.organizational_units,
            period_start=self.period_start,
            period_end=self.period_end,
            objectives=self.objectives,
            exclusions=self.exclusions,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "tenant_id": self.tenant_id,
            "client_id": self.client_id,
            "engagement_id": self.engagement_id,
            "assessment_id": self.assessment_id,
            "assessment_name": self.assessment_name,
            "workflow_names": list(self.workflow_names),
            "organizational_units": list(
                self.organizational_units
            ),
            "period_start": self.period_start.isoformat(),
            "period_end": self.period_end.isoformat(),
            "objectives": list(self.objectives),
            "expected_outcomes": list(
                self.expected_outcomes
            ),
            "exclusions": list(self.exclusions),
            "evidence_requirements": [
                requirement.to_dict()
                for requirement in self.evidence_requirements
            ],
            "status": self.status.value,
            "configuration_hash": self.configuration_hash,
            "schema_version": self.schema_version,
        }


class GovernanceAssessmentScopeConfigurationService:
    def configure(
        self,
        *,
        context: CommercialHierarchyContext,
        assessment_name: str,
        workflow_names: tuple[str, ...],
        organizational_units: tuple[str, ...],
        period_start: date,
        period_end: date,
        objectives: tuple[str, ...],
        expected_outcomes: tuple[str, ...],
        exclusions: tuple[str, ...] = (),
        evidence_requirements: tuple[
            EvidenceRequirement, ...
        ] = (),
        status: ScopeConfigurationStatus = (
            ScopeConfigurationStatus.DRAFT
        ),
    ) -> AssessmentScopeConfiguration:
        if context.engagement_id is None:
            raise ScopeConfigurationError(
                "scope configuration requires engagement_id"
            )

        if context.assessment_id is None:
            raise ScopeConfigurationError(
                "scope configuration requires assessment_id"
            )

        normalized_name = require_text(
            assessment_name,
            "assessment_name",
        )
        normalized_workflows = normalize_text_values(
            workflow_names,
            field_name="workflow_names",
        )
        normalized_units = normalize_text_values(
            organizational_units,
            field_name="organizational_units",
        )
        normalized_objectives = normalize_text_values(
            objectives,
            field_name="objectives",
        )
        normalized_outcomes = normalize_text_values(
            expected_outcomes,
            field_name="expected_outcomes",
        )
        normalized_exclusions = normalize_text_values(
            exclusions,
            field_name="exclusions",
            required=False,
        )

        if period_end < period_start:
            raise ScopeConfigurationError(
                "period_end must not precede period_start"
            )

        requirement_ids = [
            requirement.requirement_id
            for requirement in evidence_requirements
        ]

        if len(requirement_ids) != len(set(requirement_ids)):
            raise ScopeConfigurationError(
                "evidence_requirements contains duplicate identifiers"
            )

        payload = {
            "tenant_id": context.tenant_id,
            "client_id": context.client_id,
            "engagement_id": context.engagement_id,
            "assessment_id": context.assessment_id,
            "assessment_name": normalized_name,
            "workflow_names": normalized_workflows,
            "organizational_units": normalized_units,
            "period_start": period_start.isoformat(),
            "period_end": period_end.isoformat(),
            "objectives": normalized_objectives,
            "expected_outcomes": normalized_outcomes,
            "exclusions": normalized_exclusions,
            "evidence_requirements": [
                requirement.to_dict()
                for requirement in evidence_requirements
            ],
            "status": status.value,
            "schema_version": (
                ASSESSMENT_SCOPE_CONFIGURATION_VERSION
            ),
        }

        return AssessmentScopeConfiguration(
            tenant_id=context.tenant_id,
            client_id=context.client_id,
            engagement_id=context.engagement_id,
            assessment_id=context.assessment_id,
            assessment_name=normalized_name,
            workflow_names=normalized_workflows,
            organizational_units=normalized_units,
            period_start=period_start,
            period_end=period_end,
            objectives=normalized_objectives,
            expected_outcomes=normalized_outcomes,
            exclusions=normalized_exclusions,
            evidence_requirements=evidence_requirements,
            status=status,
            configuration_hash=sha256_text(
                canonical_json(payload)
            ),
        )

    def validate_ready_for_evidence(
        self,
        configuration: AssessmentScopeConfiguration,
    ) -> AssessmentScopeConfiguration:
        if configuration.status not in (
            ScopeConfigurationStatus.VALIDATED,
            ScopeConfigurationStatus.LOCKED,
        ):
            raise ScopeConfigurationError(
                "scope must be validated or locked before evidence intake"
            )

        if not configuration.evidence_requirements:
            raise ScopeConfigurationError(
                "at least one evidence requirement is required"
            )

        return configuration

    def lock(
        self,
        configuration: AssessmentScopeConfiguration,
    ) -> AssessmentScopeConfiguration:
        if configuration.status is ScopeConfigurationStatus.LOCKED:
            return configuration

        return self.configure(
            context=CommercialHierarchyContext(
                tenant_id=configuration.tenant_id,
                client_id=configuration.client_id,
                engagement_id=configuration.engagement_id,
                assessment_id=configuration.assessment_id,
            ),
            assessment_name=configuration.assessment_name,
            workflow_names=configuration.workflow_names,
            organizational_units=(
                configuration.organizational_units
            ),
            period_start=configuration.period_start,
            period_end=configuration.period_end,
            objectives=configuration.objectives,
            expected_outcomes=(
                configuration.expected_outcomes
            ),
            exclusions=configuration.exclusions,
            evidence_requirements=(
                configuration.evidence_requirements
            ),
            status=ScopeConfigurationStatus.LOCKED,
        )
