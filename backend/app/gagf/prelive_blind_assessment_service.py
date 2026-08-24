from __future__ import annotations

from typing import Any, Mapping

from backend.app.gagf.prelive_blind_assessment import (
    PreliveScenarioError,
    build_pre_live_manifest,
    scenario_to_governed_csv,
    validate_pre_live_scenario,
)


PRELIVE_SERVICE_VERSION = "1.0.0"

PRELIVE_PREPARED_STATUS = "prepared"

PRELIVE_RECOMMENDED_ACTION = (
    "execute_governed_assessment"
)

PRELIVE_AUTHORITY = "GAGF_FIP_ONLY"


class PreliveBlindAssessmentService:
    """
    Boundary service for independently generated
    PRELIVE-001 evidence.

    The external AI contributes observations only.

    This service:
    - validates the synthetic scenario
    - blocks oracle leakage
    - blocks AI governance authority
    - canonicalizes the scenario
    - produces the governed CSV representation
    - returns a sealed public manifest

    This service does not:
    - execute an assessment
    - authorize paid work
    - confirm payment
    - authorize production onboarding
    - grant authority to an external AI

    A prepared scenario remains behind a separate
    human-controlled execution boundary.
    """

    def validate(
        self,
        scenario: Mapping[str, Any],
    ) -> dict[str, Any]:
        result = validate_pre_live_scenario(
            scenario
        )

        return result.to_dict()

    def prepare(
        self,
        scenario: Mapping[str, Any],
    ) -> dict[str, Any]:
        validation = (
            validate_pre_live_scenario(
                scenario
            )
        )

        if not validation.valid:
            raise PreliveScenarioError(
                "PRELIVE scenario failed "
                "blind-evidence validation."
            )

        csv_text = scenario_to_governed_csv(
            scenario
        )

        manifest = build_pre_live_manifest(
            scenario
        )

        return {
            "status":
                PRELIVE_PREPARED_STATUS,
            "test_program":
                "PRELIVE-001",
            "scenario_id":
                scenario["scenario_id"],
            "service_version":
                PRELIVE_SERVICE_VERSION,
            "manifest":
                manifest,
            "validation":
                validation.to_dict(),
            "csv_text":
                csv_text,
            "recommended_action":
                PRELIVE_RECOMMENDED_ACTION,
            "authority":
                PRELIVE_AUTHORITY,
            "execution_boundary": {
                "assessment_executed":
                    False,
                "execution_authorized":
                    False,
                "human_operator_required":
                    True,
                "automatic_execution_allowed":
                    False,
            },
            "commercial_boundary": {
                "payment_confirmed":
                    False,
                "paid_work_authorized":
                    False,
                "production_onboarding_authorized":
                    False,
            },
            "ai_boundary": {
                "external_ai_is_evidence_generator":
                    True,
                "external_ai_has_governance_authority":
                    False,
                "external_ai_can_execute":
                    False,
                "external_ai_can_override":
                    False,
            },
        }