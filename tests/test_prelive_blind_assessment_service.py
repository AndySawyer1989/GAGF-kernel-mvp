from __future__ import annotations

import pytest

from backend.app.gagf.prelive_blind_assessment import (
    PreliveScenarioError,
)
from backend.app.gagf.prelive_blind_assessment_service import (
    PreliveBlindAssessmentService,
)
from tests.test_prelive_blind_assessment import (
    build_scenario,
)


def test_service_validates_scenario():
    service = (
        PreliveBlindAssessmentService()
    )

    result = service.validate(
        build_scenario()
    )

    assert result["valid"] is True
    assert (
        result["summary"]["event_count"]
        == 100
    )


def test_service_prepares_scenario():
    service = (
        PreliveBlindAssessmentService()
    )

    result = service.prepare(
        build_scenario()
    )

    assert (
        result["status"]
        == "prepared"
    )

    assert (
        result["test_program"]
        == "PRELIVE-001"
    )

    assert result["manifest"][
        "oracle_status"
    ] == "SEALED"

    assert result[
        "recommended_action"
    ] == (
        "execute_governed_assessment"
    )

    assert result[
        "csv_text"
    ].startswith(
        "event_id,event_type,"
        "occurred_at,work_item_id,"
    )


def test_service_refuses_oracle_leakage():
    scenario = build_scenario()

    scenario[
        "expected_conditions"
    ] = [
        {
            "condition":
                "hidden answer"
        }
    ]

    service = (
        PreliveBlindAssessmentService()
    )

    with pytest.raises(
        PreliveScenarioError
    ):
        service.prepare(scenario)


def test_service_refuses_ai_authority():
    scenario = build_scenario()

    scenario["events"][0][
        "governance_determination"
    ] = "intervene"

    service = (
        PreliveBlindAssessmentService()
    )

    with pytest.raises(
        PreliveScenarioError
    ):
        service.prepare(scenario)