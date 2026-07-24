from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from backend.app.gagf.governance_assessment_domain import (
    ClientRecord,
    EngagementRecord,
    GovernanceAssessment,
)


class GovernanceAssessmentIsolationError(ValueError):
    """Raised when commercial hierarchy isolation is violated."""


class ClientNotFoundError(LookupError):
    """Raised when a client is not visible in the supplied tenant."""


class EngagementNotFoundError(LookupError):
    """Raised when an engagement is not visible in the supplied client."""


class AssessmentNotFoundError(LookupError):
    """Raised when an assessment is not visible in the supplied engagement."""


@dataclass(frozen=True, slots=True)
class CommercialHierarchyContext:
    tenant_id: str
    client_id: str
    engagement_id: str | None = None
    assessment_id: str | None = None

    def __post_init__(self) -> None:
        for field_name in (
            "tenant_id",
            "client_id",
        ):
            value = getattr(self, field_name).strip()

            if not value:
                raise GovernanceAssessmentIsolationError(
                    f"{field_name} must not be empty"
                )

            object.__setattr__(self, field_name, value)

        for field_name in (
            "engagement_id",
            "assessment_id",
        ):
            value = getattr(self, field_name)

            if value is None:
                continue

            normalized = value.strip()

            if not normalized:
                raise GovernanceAssessmentIsolationError(
                    f"{field_name} must not be empty when supplied"
                )

            object.__setattr__(
                self,
                field_name,
                normalized,
            )

        if (
            self.assessment_id is not None
            and self.engagement_id is None
        ):
            raise GovernanceAssessmentIsolationError(
                "assessment_id requires engagement_id"
            )

    @property
    def hierarchy_key(self) -> str:
        parts = [
            self.tenant_id,
            self.client_id,
        ]

        if self.engagement_id is not None:
            parts.append(self.engagement_id)

        if self.assessment_id is not None:
            parts.append(self.assessment_id)

        return "/".join(parts)


class GovernanceAssessmentIsolationService:
    def validate_client(
        self,
        *,
        context: CommercialHierarchyContext,
        client: ClientRecord,
    ) -> ClientRecord:
        if client.tenant_id != context.tenant_id:
            raise GovernanceAssessmentIsolationError(
                "client tenant does not match hierarchy context"
            )

        if client.client_id != context.client_id:
            raise GovernanceAssessmentIsolationError(
                "client identifier does not match hierarchy context"
            )

        return client

    def validate_engagement(
        self,
        *,
        context: CommercialHierarchyContext,
        engagement: EngagementRecord,
    ) -> EngagementRecord:
        if context.engagement_id is None:
            raise GovernanceAssessmentIsolationError(
                "engagement validation requires engagement_id"
            )

        if engagement.tenant_id != context.tenant_id:
            raise GovernanceAssessmentIsolationError(
                "engagement tenant does not match hierarchy context"
            )

        if engagement.client_id != context.client_id:
            raise GovernanceAssessmentIsolationError(
                "engagement client does not match hierarchy context"
            )

        if engagement.engagement_id != context.engagement_id:
            raise GovernanceAssessmentIsolationError(
                "engagement identifier does not match hierarchy context"
            )

        return engagement

    def validate_assessment(
        self,
        *,
        context: CommercialHierarchyContext,
        assessment: GovernanceAssessment,
    ) -> GovernanceAssessment:
        if context.engagement_id is None:
            raise GovernanceAssessmentIsolationError(
                "assessment validation requires engagement_id"
            )

        if context.assessment_id is None:
            raise GovernanceAssessmentIsolationError(
                "assessment validation requires assessment_id"
            )

        expected = (
            context.tenant_id,
            context.client_id,
            context.engagement_id,
            context.assessment_id,
        )
        actual = (
            assessment.tenant_id,
            assessment.client_id,
            assessment.engagement_id,
            assessment.assessment_id,
        )

        if actual != expected:
            raise GovernanceAssessmentIsolationError(
                "assessment hierarchy does not match context"
            )

        return assessment

    def resolve_client(
        self,
        *,
        tenant_id: str,
        client_id: str,
        clients: Iterable[ClientRecord],
    ) -> ClientRecord:
        for client in clients:
            if (
                client.tenant_id == tenant_id
                and client.client_id == client_id
            ):
                return client

        raise ClientNotFoundError("client not found")

    def resolve_engagement(
        self,
        *,
        tenant_id: str,
        client_id: str,
        engagement_id: str,
        engagements: Iterable[EngagementRecord],
    ) -> EngagementRecord:
        for engagement in engagements:
            if (
                engagement.tenant_id == tenant_id
                and engagement.client_id == client_id
                and engagement.engagement_id == engagement_id
            ):
                return engagement

        raise EngagementNotFoundError(
            "engagement not found"
        )

    def resolve_assessment(
        self,
        *,
        tenant_id: str,
        client_id: str,
        engagement_id: str,
        assessment_id: str,
        assessments: Iterable[GovernanceAssessment],
    ) -> GovernanceAssessment:
        for assessment in assessments:
            if (
                assessment.tenant_id == tenant_id
                and assessment.client_id == client_id
                and assessment.engagement_id == engagement_id
                and assessment.assessment_id == assessment_id
            ):
                return assessment

        raise AssessmentNotFoundError(
            "assessment not found"
        )

    def visible_clients(
        self,
        *,
        tenant_id: str,
        clients: Iterable[ClientRecord],
    ) -> tuple[ClientRecord, ...]:
        return tuple(
            client
            for client in clients
            if client.tenant_id == tenant_id
        )

    def visible_engagements(
        self,
        *,
        tenant_id: str,
        client_id: str,
        engagements: Iterable[EngagementRecord],
    ) -> tuple[EngagementRecord, ...]:
        return tuple(
            engagement
            for engagement in engagements
            if engagement.tenant_id == tenant_id
            and engagement.client_id == client_id
        )

    def visible_assessments(
        self,
        *,
        tenant_id: str,
        client_id: str,
        engagement_id: str,
        assessments: Iterable[GovernanceAssessment],
    ) -> tuple[GovernanceAssessment, ...]:
        return tuple(
            assessment
            for assessment in assessments
            if assessment.tenant_id == tenant_id
            and assessment.client_id == client_id
            and assessment.engagement_id == engagement_id
        )
