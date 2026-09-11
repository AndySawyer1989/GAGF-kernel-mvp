from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


CUSTOMER_TRIAL_PROGRAM = "FIP-CUSTOMER-TRIAL-001"
CUSTOMER_TRIAL_SCHEMA_VERSION = "1.0"


SUPPORTED_DATA_CLASSIFICATIONS = (
    "non_sensitive",
    "sanitized",
    "redacted",
)


@dataclass(frozen=True)
class CustomerTrialEvidenceRequirement:
    requirement_id: str
    description: str
    minimum_records: int
    accepted_formats: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.requirement_id.strip():
            raise ValueError(
                "requirement_id must not be empty"
            )

        if not self.description.strip():
            raise ValueError(
                "description must not be empty"
            )

        if self.minimum_records < 1:
            raise ValueError(
                "minimum_records must be at least 1"
            )

        if not self.accepted_formats:
            raise ValueError(
                "accepted_formats must not be empty"
            )


@dataclass(frozen=True)
class CustomerTrialEngagementPackage:
    tenant_id: str
    client_id: str
    client_display_name: str
    engagement_id: str
    assessment_id: str
    assessment_name: str

    period_start: str
    period_end: str

    workflows: tuple[str, ...]
    organizational_units: tuple[str, ...]
    objectives: tuple[str, ...]
    expected_outcomes: tuple[str, ...]

    evidence_requirements: tuple[
        CustomerTrialEvidenceRequirement,
        ...
    ]

    data_classification: str
    prepared_by: str

    customer_deliverables: tuple[str, ...]
    trial_boundaries: tuple[str, ...]
    completion_criteria: tuple[str, ...]

    program: str = CUSTOMER_TRIAL_PROGRAM
    schema_version: str = CUSTOMER_TRIAL_SCHEMA_VERSION

    def __post_init__(self) -> None:
        required_text = {
            "tenant_id": self.tenant_id,
            "client_id": self.client_id,
            "client_display_name":
                self.client_display_name,
            "engagement_id": self.engagement_id,
            "assessment_id": self.assessment_id,
            "assessment_name": self.assessment_name,
            "period_start": self.period_start,
            "period_end": self.period_end,
            "prepared_by": self.prepared_by,
        }

        for name, value in required_text.items():
            if not value.strip():
                raise ValueError(
                    f"{name} must not be empty"
                )

        if (
            self.data_classification
            not in SUPPORTED_DATA_CLASSIFICATIONS
        ):
            raise ValueError(
                "unsupported data_classification"
            )

        required_collections = {
            "workflows": self.workflows,
            "organizational_units":
                self.organizational_units,
            "objectives": self.objectives,
            "expected_outcomes":
                self.expected_outcomes,
            "evidence_requirements":
                self.evidence_requirements,
            "customer_deliverables":
                self.customer_deliverables,
            "trial_boundaries":
                self.trial_boundaries,
            "completion_criteria":
                self.completion_criteria,
        }

        for name, values in required_collections.items():
            if not values:
                raise ValueError(
                    f"{name} must not be empty"
                )

    def to_dict(
        self
    ) -> dict[str, Any]:
        return asdict(self)