from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Mapping

from backend.app.gagf.governance_assessment_application import (
    AssessmentExecutionRequest,
)
from backend.app.gagf.governance_assessment_demonstration import (
    DemonstrationEvidenceInput,
)
from backend.app.gagf.governance_assessment_domain import (
    EvidenceSourceKind,
    EvidenceSourceReference,
)
from backend.app.gagf.governance_assessment_isolation import (
    CommercialHierarchyContext,
)
from backend.app.gagf.governance_assessment_scope_configuration import (
    EvidenceRequirement,
)
from backend.app.gagf.prelive_blind_assessment import (
    PRELIVE_PROGRAM,
    PreliveScenarioError,
    scenario_to_governed_csv,
    validate_pre_live_scenario,
)


PRELIVE_EXECUTION_BRIDGE_VERSION = "1.0.0"

PRELIVE_EXECUTION_BRIDGE_STATUS = (
    "prepared_for_execution_request"
)

PRELIVE_EXECUTION_AUTHORITY = "GAGF_FIP_ONLY"


@dataclass(frozen=True, slots=True)
class PreliveAssessmentExecutionMetadata:
    """
    Human-supplied metadata used to bind validated PRELIVE
    evidence to the real governance assessment request contract.

    This metadata does not authorize execution.
    """

    tenant_id: str
    client_id: str
    engagement_id: str
    assessment_id: str

    assessment_name: str
    workflow_names: tuple[str, ...]
    organizational_units: tuple[str, ...]

    objectives: tuple[str, ...]
    expected_outcomes: tuple[str, ...]

    client_display_name: str
    prepared_by: str

    exclusions: tuple[str, ...] = ()
    maximum_priorities: int = 3


@dataclass(frozen=True, slots=True)
class PreliveAssessmentExecutionBridgeResult:
    """
    Deterministic handoff from validated PRELIVE evidence to the
    real AssessmentExecutionRequest domain type.

    Building this object does not execute an assessment.
    """

    scenario_id: str
    scenario_sha256: str
    event_count: int

    request: AssessmentExecutionRequest

    bridge_status: str = (
        PRELIVE_EXECUTION_BRIDGE_STATUS
    )

    authority: str = (
        PRELIVE_EXECUTION_AUTHORITY
    )

    human_execution_required: bool = True
    execution_authorized: bool = False
    assessment_executed: bool = False
    paid_work_authorized: bool = False
    production_onboarding_authorized: bool = False

    bridge_version: str = (
        PRELIVE_EXECUTION_BRIDGE_VERSION
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "scenario_id":
                self.scenario_id,
            "scenario_sha256":
                self.scenario_sha256,
            "event_count":
                self.event_count,
            "bridge_status":
                self.bridge_status,
            "authority":
                self.authority,
            "human_execution_required":
                self.human_execution_required,
            "execution_authorized":
                self.execution_authorized,
            "assessment_executed":
                self.assessment_executed,
            "paid_work_authorized":
                self.paid_work_authorized,
            "production_onboarding_authorized":
                self.production_onboarding_authorized,
            "bridge_version":
                self.bridge_version,
            "request":
                self.request.to_dict(),
        }


class PreliveAssessmentExecutionBridge:
    """
    Converts independently generated PRELIVE evidence into the
    repository's real AssessmentExecutionRequest contract.

    Constitutional boundaries:

    - PRELIVE validation must pass first.
    - External AI remains an evidence generator only.
    - Evidence tenant identity must equal request tenant identity.
    - Governed CSV is the application evidence payload.
    - This bridge cannot execute an assessment.
    - This bridge cannot authorize paid work.
    - This bridge cannot authorize production onboarding.
    - GAGF/FIP remains authoritative.
    """

    def build_request(
        self,
        *,
        scenario: Mapping[str, Any],
        metadata: PreliveAssessmentExecutionMetadata,
    ) -> PreliveAssessmentExecutionBridgeResult:
        validation = validate_pre_live_scenario(
            scenario
        )

        if not validation.valid:
            raise PreliveScenarioError(
                "PRELIVE scenario failed blind-evidence "
                "validation and cannot enter the "
                "assessment execution-request boundary."
            )

        scenario_dict = dict(scenario)

        self._validate_metadata(
            metadata
        )

        self._validate_tenant_binding(
            scenario=scenario_dict,
            tenant_id=metadata.tenant_id,
        )

        if validation.scenario_sha256 is None:
            raise PreliveScenarioError(
                "Validated PRELIVE scenario did not "
                "produce a canonical SHA-256."
            )

        csv_text = scenario_to_governed_csv(
            scenario_dict
        )

        context = CommercialHierarchyContext(
            tenant_id=metadata.tenant_id,
            client_id=metadata.client_id,
            engagement_id=metadata.engagement_id,
            assessment_id=metadata.assessment_id,
        )

        scenario_id = str(
            scenario_dict["scenario_id"]
        ).strip()

        generator = scenario_dict["generator"]

        generator_label = str(
            generator["model_label"]
        ).strip()

        period_start = self._timestamp_to_date(
            validation.summary.start_timestamp,
            field_name="start_timestamp",
        )

        period_end = self._timestamp_to_date(
            validation.summary.end_timestamp,
            field_name="end_timestamp",
        )

        evidence_requirement = EvidenceRequirement(
            requirement_id=(
                f"{scenario_id}-prelive-evidence"
            ),
            source_kind=EvidenceSourceKind.CSV,
            description=(
                "Validated blind synthetic evidence "
                f"for {PRELIVE_PROGRAM}."
            ),
            required=True,
            minimum_record_count=(
                validation.summary.event_count
            ),
        )

        evidence_input = DemonstrationEvidenceInput(
            source=EvidenceSourceReference(
                source_id=(
                    f"prelive-{scenario_id}"
                ),
                kind=EvidenceSourceKind.CSV,
                display_name=(
                    f"{PRELIVE_PROGRAM} Blind Evidence "
                    f"({generator_label})"
                ),
                source_location=None,
            ),
            csv_text=csv_text,
        )

        request = AssessmentExecutionRequest(
            context=context,
            assessment_name=(
                metadata.assessment_name
            ),
            workflow_names=(
                metadata.workflow_names
            ),
            organizational_units=(
                metadata.organizational_units
            ),
            period_start=period_start,
            period_end=period_end,
            objectives=metadata.objectives,
            expected_outcomes=(
                metadata.expected_outcomes
            ),
            evidence_requirements=(
                evidence_requirement,
            ),
            evidence_inputs=(
                evidence_input,
            ),
            client_display_name=(
                metadata.client_display_name
            ),
            prepared_by=metadata.prepared_by,
            exclusions=metadata.exclusions,
            maximum_priorities=(
                metadata.maximum_priorities
            ),
        )

        return (
            PreliveAssessmentExecutionBridgeResult(
                scenario_id=scenario_id,
                scenario_sha256=(
                    validation.scenario_sha256
                ),
                event_count=(
                    validation.summary.event_count
                ),
                request=request,
            )
        )

    def _validate_metadata(
        self,
        metadata: PreliveAssessmentExecutionMetadata,
    ) -> None:
        required_text_fields = {
            "tenant_id":
                metadata.tenant_id,
            "client_id":
                metadata.client_id,
            "engagement_id":
                metadata.engagement_id,
            "assessment_id":
                metadata.assessment_id,
            "assessment_name":
                metadata.assessment_name,
            "client_display_name":
                metadata.client_display_name,
            "prepared_by":
                metadata.prepared_by,
        }

        for field_name, value in (
            required_text_fields.items()
        ):
            if (
                not isinstance(value, str)
                or not value.strip()
            ):
                raise PreliveScenarioError(
                    f"{field_name} is required "
                    "for PRELIVE execution-request "
                    "binding."
                )

        if not metadata.workflow_names:
            raise PreliveScenarioError(
                "workflow_names must not be empty."
            )

        if not metadata.organizational_units:
            raise PreliveScenarioError(
                "organizational_units must not be empty."
            )

        if not metadata.objectives:
            raise PreliveScenarioError(
                "objectives must not be empty."
            )

        if not metadata.expected_outcomes:
            raise PreliveScenarioError(
                "expected_outcomes must not be empty."
            )

        if (
            not isinstance(
                metadata.maximum_priorities,
                int,
            )
            or isinstance(
                metadata.maximum_priorities,
                bool,
            )
            or metadata.maximum_priorities < 1
        ):
            raise PreliveScenarioError(
                "maximum_priorities must be "
                "a positive integer."
            )

    def _validate_tenant_binding(
        self,
        *,
        scenario: Mapping[str, Any],
        tenant_id: str,
    ) -> None:
        events = scenario.get("events")

        if not isinstance(events, list):
            raise PreliveScenarioError(
                "PRELIVE events are required "
                "for tenant binding."
            )

        scenario_tenants = {
            str(event["tenant_id"]).strip()
            for event in events
            if isinstance(event, Mapping)
            and isinstance(
                event.get("tenant_id"),
                str,
            )
            and event["tenant_id"].strip()
        }

        if scenario_tenants != {
            tenant_id.strip()
        }:
            raise PreliveScenarioError(
                "PRELIVE evidence tenant binding "
                "does not match the assessment "
                "execution-request tenant."
            )

    def _timestamp_to_date(
        self,
        timestamp: str | None,
        *,
        field_name: str,
    ) -> date:
        if timestamp is None:
            raise PreliveScenarioError(
                f"PRELIVE {field_name} is required."
            )

        normalized = timestamp.strip()

        if normalized.endswith("Z"):
            normalized = (
                normalized[:-1]
                + "+00:00"
            )

        try:
            parsed = datetime.fromisoformat(
                normalized
            )
        except ValueError as exc:
            raise PreliveScenarioError(
                f"PRELIVE {field_name} "
                "cannot be converted to an "
                "assessment date."
            ) from exc

        return parsed.date()