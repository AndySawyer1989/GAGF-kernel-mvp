from __future__ import annotations

import pytest

from backend.app.gagf.governance_assessment_application import (
    AssessmentExecutionRequest,
)
from backend.app.gagf.governance_assessment_domain import (
    EvidenceSourceKind,
)
from backend.app.gagf.prelive_assessment_execution_bridge import (
    PRELIVE_EXECUTION_AUTHORITY,
    PRELIVE_EXECUTION_BRIDGE_STATUS,
    PRELIVE_EXECUTION_BRIDGE_VERSION,
    PreliveAssessmentExecutionBridge,
    PreliveAssessmentExecutionMetadata,
)
from backend.app.gagf.prelive_blind_assessment import (
    PreliveScenarioError,
)
from tests.test_prelive_blind_assessment import (
    build_scenario,
)


def build_metadata(
    *,
    tenant_id: str = "synthetic-tenant",
) -> PreliveAssessmentExecutionMetadata:
    return PreliveAssessmentExecutionMetadata(
        tenant_id=tenant_id,
        client_id="prelive-client",
        engagement_id="prelive-engagement",
        assessment_id="prelive-assessment",
        assessment_name=(
            "PRELIVE Blind Governance Assessment"
        ),
        workflow_names=(
            "Synthetic Workflow",
        ),
        organizational_units=(
            "Synthetic Operations",
        ),
        objectives=(
            "Evaluate governance friction detection.",
        ),
        expected_outcomes=(
            "Produce deterministic FIP "
            "assessment output.",
        ),
        client_display_name=(
            "Synthetic Test Organization"
        ),
        prepared_by=(
            "PRELIVE Test Operator"
        ),
        exclusions=(
            "Production actions",
        ),
        maximum_priorities=3,
    )


def test_bridge_builds_real_assessment_execution_request():
    bridge = (
        PreliveAssessmentExecutionBridge()
    )

    result = bridge.build_request(
        scenario=build_scenario(),
        metadata=build_metadata(),
    )

    assert isinstance(
        result.request,
        AssessmentExecutionRequest,
    )

    assert (
        result.bridge_status
        == PRELIVE_EXECUTION_BRIDGE_STATUS
    )

    assert (
        result.bridge_version
        == PRELIVE_EXECUTION_BRIDGE_VERSION
    )

    assert (
        result.authority
        == PRELIVE_EXECUTION_AUTHORITY
    )

    assert (
        result.authority
        == "GAGF_FIP_ONLY"
    )


def test_bridge_preserves_commercial_hierarchy():
    bridge = (
        PreliveAssessmentExecutionBridge()
    )

    result = bridge.build_request(
        scenario=build_scenario(),
        metadata=build_metadata(),
    )

    context = result.request.context

    assert (
        context.tenant_id
        == "synthetic-tenant"
    )

    assert (
        context.client_id
        == "prelive-client"
    )

    assert (
        context.engagement_id
        == "prelive-engagement"
    )

    assert (
        context.assessment_id
        == "prelive-assessment"
    )

    assert (
        context.hierarchy_key
        == (
            "synthetic-tenant/"
            "prelive-client/"
            "prelive-engagement/"
            "prelive-assessment"
        )
    )


def test_bridge_uses_governed_csv_as_real_evidence():
    bridge = (
        PreliveAssessmentExecutionBridge()
    )

    result = bridge.build_request(
        scenario=build_scenario(),
        metadata=build_metadata(),
    )

    request = result.request

    assert (
        len(
            request.evidence_requirements
        )
        == 1
    )

    assert (
        len(
            request.evidence_inputs
        )
        == 1
    )

    requirement = (
        request.evidence_requirements[0]
    )

    evidence_input = (
        request.evidence_inputs[0]
    )

    assert (
        requirement.source_kind
        == EvidenceSourceKind.CSV
    )

    assert (
        requirement.required
        is True
    )

    assert (
        requirement.minimum_record_count
        == 100
    )

    assert (
        evidence_input.source.kind
        == EvidenceSourceKind.CSV
    )

    assert (
        evidence_input.csv_text.startswith(
            "event_id,event_type,"
            "occurred_at,work_item_id,"
        )
    )

    assert (
        "APPROVAL_DELAYED"
        in evidence_input.csv_text
    )

    assert (
        "WORK_BLOCKED"
        in evidence_input.csv_text
    )


def test_bridge_binds_hash_count_and_evidence_period():
    bridge = (
        PreliveAssessmentExecutionBridge()
    )

    result = bridge.build_request(
        scenario=build_scenario(),
        metadata=build_metadata(),
    )

    assert result.event_count == 100

    assert (
        len(result.scenario_sha256)
        == 64
    )

    assert (
        result.request.period_start.isoformat()
        == "2026-08-01"
    )

    assert (
        result.request.period_end.isoformat()
        == "2026-08-01"
    )

    assert (
        result.request.maximum_priorities
        == 3
    )


def test_bridge_rejects_cross_tenant_evidence():
    bridge = (
        PreliveAssessmentExecutionBridge()
    )

    with pytest.raises(
        PreliveScenarioError,
        match="tenant binding",
    ):
        bridge.build_request(
            scenario=build_scenario(),
            metadata=build_metadata(
                tenant_id=(
                    "different-tenant"
                )
            ),
        )


def test_bridge_cannot_execute_or_authorize_assessment():
    bridge = (
        PreliveAssessmentExecutionBridge()
    )

    result = bridge.build_request(
        scenario=build_scenario(),
        metadata=build_metadata(),
    )

    assert (
        result.human_execution_required
        is True
    )

    assert (
        result.execution_authorized
        is False
    )

    assert (
        result.assessment_executed
        is False
    )

    assert (
        result.paid_work_authorized
        is False
    )

    assert (
        result.production_onboarding_authorized
        is False
    )

    assert not hasattr(
        bridge,
        "execute",
    )