from __future__ import annotations

from typing import Any, Mapping

from backend.app.gagf.prelive_blind_assessment import (
    PreliveScenarioError,
    build_pre_live_manifest,
    scenario_to_governed_csv,
    validate_pre_live_scenario,
)


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

    It does not determine diagnostic findings.
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

        csv_text = (
            scenario_to_governed_csv(
                scenario
            )
        )

        manifest = (
            build_pre_live_manifest(
                scenario
            )
        )

        return {
            "status": "prepared",
            "test_program":
                "PRELIVE-001",
            "scenario_id":
                scenario["scenario_id"],
            "manifest":
                manifest,
            "validation":
                validation.to_dict(),
            "csv_text":
                csv_text,
            "recommended_action":
                "execute_governed_assessment",
        }