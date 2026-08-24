from __future__ import annotations

from backend.app.gagf.prelive_blind_assessment_service import (
    PRELIVE_AUTHORITY,
    PRELIVE_PREPARED_STATUS,
    PRELIVE_RECOMMENDED_ACTION,
    PRELIVE_SERVICE_VERSION,
    PreliveBlindAssessmentService,
)
from tests.test_prelive_blind_assessment import (
    build_scenario,
)


def test_prepare_remains_non_executing():
    service = (
        PreliveBlindAssessmentService()
    )

    result = service.prepare(
        build_scenario()
    )

    boundary = result[
        "execution_boundary"
    ]

    assert (
        boundary["assessment_executed"]
        is False
    )

    assert (
        boundary["execution_authorized"]
        is False
    )

    assert (
        boundary["human_operator_required"]
        is True
    )

    assert (
        boundary[
            "automatic_execution_allowed"
        ]
        is False
    )


def test_prepare_does_not_authorize_paid_work():
    service = (
        PreliveBlindAssessmentService()
    )

    result = service.prepare(
        build_scenario()
    )

    commercial = result[
        "commercial_boundary"
    ]

    assert (
        commercial["payment_confirmed"]
        is False
    )

    assert (
        commercial["paid_work_authorized"]
        is False
    )

    assert (
        commercial[
            "production_onboarding_authorized"
        ]
        is False
    )


def test_prepare_preserves_ai_advisory_boundary():
    service = (
        PreliveBlindAssessmentService()
    )

    result = service.prepare(
        build_scenario()
    )

    ai_boundary = result[
        "ai_boundary"
    ]

    assert (
        ai_boundary[
            "external_ai_is_evidence_generator"
        ]
        is True
    )

    assert (
        ai_boundary[
            "external_ai_has_governance_authority"
        ]
        is False
    )

    assert (
        ai_boundary[
            "external_ai_can_execute"
        ]
        is False
    )

    assert (
        ai_boundary[
            "external_ai_can_override"
        ]
        is False
    )


def test_prepare_keeps_gagf_fip_authoritative():
    service = (
        PreliveBlindAssessmentService()
    )

    result = service.prepare(
        build_scenario()
    )

    assert (
        result["authority"]
        == PRELIVE_AUTHORITY
    )

    assert (
        result["authority"]
        == "GAGF_FIP_ONLY"
    )

    assert (
        result["manifest"]["authority"]
        == "GAGF_FIP_ONLY"
    )


def test_prepare_is_only_a_handoff_recommendation():
    service = (
        PreliveBlindAssessmentService()
    )

    result = service.prepare(
        build_scenario()
    )

    assert (
        result["status"]
        == PRELIVE_PREPARED_STATUS
    )

    assert (
        result["status"]
        == "prepared"
    )

    assert (
        result["recommended_action"]
        == PRELIVE_RECOMMENDED_ACTION
    )

    assert (
        result["recommended_action"]
        == "execute_governed_assessment"
    )

    assert (
        result["execution_boundary"][
            "assessment_executed"
        ]
        is False
    )


def test_prepare_exposes_stable_service_contract():
    service = (
        PreliveBlindAssessmentService()
    )

    result = service.prepare(
        build_scenario()
    )

    assert (
        result["service_version"]
        == PRELIVE_SERVICE_VERSION
    )

    assert (
        result["service_version"]
        == "1.0.0"
    )

    assert (
        result["test_program"]
        == "PRELIVE-001"
    )

    assert (
        result["manifest"][
            "oracle_status"
        ]
        == "SEALED"
    )

    assert (
        len(
            result["manifest"][
                "scenario_sha256"
            ]
        )
        == 64
    )