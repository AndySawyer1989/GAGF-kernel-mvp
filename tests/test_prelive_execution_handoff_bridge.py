from __future__ import annotations

import pytest

from backend.app.gagf.governance_paid_assessment_execution_handoff import (
    PaidAssessmentExecutionHandoffStatus,
    PaidAssessmentWorkAuthorization,
)
from backend.app.gagf.prelive_assessment_execution_bridge import (
    PreliveAssessmentExecutionMetadata,
)
from backend.app.gagf.prelive_blind_assessment import (
    PreliveScenarioError,
)
from backend.app.gagf.prelive_execution_handoff_bridge import (
    PRELIVE_EXECUTION_HANDOFF_AUTHORITY,
    PRELIVE_EXECUTION_HANDOFF_STATUS,
    PreliveExecutionHandoffBridge,
)
from tests.test_prelive_blind_assessment import (
    build_scenario,
)


def build_metadata(
    **overrides,
) -> PreliveAssessmentExecutionMetadata:
    values = {
        "tenant_id": "synthetic-tenant",
        "client_id": "prelive-client",
        "engagement_id": "prelive-engagement",
        "assessment_id": "prelive-assessment",
        "assessment_name": (
            "PRELIVE Blind Governance Assessment"
        ),
        "workflow_names": (
            "Synthetic Workflow",
        ),
        "organizational_units": (
            "Synthetic Operations",
        ),
        "objectives": (
            "Evaluate governance friction detection.",
        ),
        "expected_outcomes": (
            "Produce deterministic FIP assessment output.",
        ),
        "client_display_name": (
            "Synthetic Test Organization"
        ),
        "prepared_by": "PRELIVE Test Operator",
        "exclusions": (
            "Production actions",
        ),
        "maximum_priorities": 3,
    }

    values.update(overrides)

    return PreliveAssessmentExecutionMetadata(
        **values
    )


def build_contract_event(
    **overrides,
) -> dict:
    event = {
        "status": "ok",
        "event_type": (
            "assessment_factory_lite_"
            "contract_execution_event"
        ),
        "package_name": (
            "assessment_factory_lite"
        ),
        "release": (
            "assessment-factory-lite-"
            "scope-call-conversion"
        ),
        "version": "2.3.0",
        "event_stage": (
            "contract_execution"
        ),
        "event_status": (
            "contract_executed"
        ),
        "contract_execution_event_id": (
            "contract-event-prelive-001"
        ),
        "recorded_at": (
            "2026-08-24T18:30:00+00:00"
        ),
        "execution_evidence": {
            "executed_contract_reference": (
                "contract-ref-prelive-001"
            ),
            "executed_at": (
                "2026-08-24T18:25:00+00:00"
            ),
            "executed_contract_reference_recorded": (
                True
            ),
            "executed_at_recorded": True,
            "contract_execution_confirmed": True,
            "contract_executed": True,
        },
        "event_checklist": {
            "contract_execution_review_ready": True,
            "contract_execution_confirmed": True,
            "executed_contract_reference_recorded": (
                True
            ),
            "executed_at_recorded": True,
            "execution_method_recorded": True,
            "all_required_signatures_recorded": True,
            "human_operator_confirmed_execution": True,
            "signature_record_is_not_invoice": True,
            "signature_record_is_not_payment": True,
            "invoice_not_created": True,
            "payment_not_requested": True,
            "paid_assessment_not_authorized": True,
            "production_onboarding_not_started": True,
        },
        "event_blockers": [],
        "commercial_boundary": {
            "contract_execution_recorded": True,
            "contract_executed": True,
            "invoice_created": False,
            "payment_requested": False,
            "paid_assessment_authorized": False,
            "production_onboarding_authorized": False,
            "requires_separate_invoice": True,
            "requires_separate_payment_confirmation": True,
            "requires_final_paid_work_authorization": True,
            "requires_separate_production_onboarding": True,
        },
        "governance_boundary": {
            "deterministic_status_required": True,
            "gagf_kernel_authoritative": True,
            "ai_override_allowed": False,
            "human_boundary_required": True,
            "release_marker_preserved": True,
            "contract_execution_event_is_not_invoice": True,
            "contract_execution_event_is_not_payment": True,
            (
                "contract_execution_event_is_not_"
                "paid_work_authorization"
            ): True,
        },
    }

    event.update(overrides)

    return event


def build_authorization(
    **overrides,
) -> PaidAssessmentWorkAuthorization:
    values = {
        "authorization_id": (
            "paid-work-auth-prelive-001"
        ),
        "tenant_id": "synthetic-tenant",
        "client_id": "prelive-client",
        "engagement_id": "prelive-engagement",
        "assessment_id": "prelive-assessment",
        "contract_execution_event_id": (
            "contract-event-prelive-001"
        ),
        "authorized_by": (
            "PRELIVE Human Operator"
        ),
        "authorized_at": (
            "2026-08-24T18:35:00+00:00"
        ),
        "paid_assessment_authorized": True,
    }

    values.update(overrides)

    return PaidAssessmentWorkAuthorization(
        **values
    )


def build_result():
    return (
        PreliveExecutionHandoffBridge()
        .prepare_handoff(
            scenario=build_scenario(),
            metadata=build_metadata(),
            contract_execution_event=(
                build_contract_event()
            ),
            paid_work_authorization=(
                build_authorization()
            ),
        )
    )


def test_prepares_ready_existing_handoff():
    result = build_result()

    assert (
        result.handoff.status
        == PaidAssessmentExecutionHandoffStatus.READY
    )

    assert (
        result.bridge_status
        == PRELIVE_EXECUTION_HANDOFF_STATUS
    )

    assert (
        result.authority
        == PRELIVE_EXECUTION_HANDOFF_AUTHORITY
    )


def test_preserves_commercial_hierarchy():
    result = build_result()

    assert (
        result.handoff.hierarchy_key
        == (
            "synthetic-tenant/"
            "prelive-client/"
            "prelive-engagement/"
            "prelive-assessment"
        )
    )


def test_binds_exact_assessment_request_hash():
    result = build_result()

    assert (
        len(
            result.handoff
            .assessment_execution_request_hash
        )
        == 64
    )


def test_binds_paid_work_authorization():
    result = build_result()
    authorization = build_authorization()

    assert (
        result.handoff
        .paid_work_authorization_id
        == authorization.authorization_id
    )

    assert (
        result.handoff
        .paid_work_authorization_hash
        == authorization.authorization_hash
    )


def test_binds_contract_execution_event():
    result = build_result()

    assert (
        result.handoff
        .contract_execution_event_id
        == "contract-event-prelive-001"
    )

    assert (
        len(
            result.handoff
            .contract_execution_event_hash
        )
        == 64
    )


def test_rejects_authorization_hierarchy_mismatch():
    with pytest.raises(
        PreliveScenarioError,
    ):
        (
            PreliveExecutionHandoffBridge()
            .prepare_handoff(
                scenario=build_scenario(),
                metadata=build_metadata(),
                contract_execution_event=(
                    build_contract_event()
                ),
                paid_work_authorization=(
                    build_authorization(
                        tenant_id=(
                            "different-tenant"
                        )
                    )
                ),
            )
        )


def test_rejects_authorization_contract_event_mismatch():
    with pytest.raises(
        PreliveScenarioError,
    ):
        (
            PreliveExecutionHandoffBridge()
            .prepare_handoff(
                scenario=build_scenario(),
                metadata=build_metadata(),
                contract_execution_event=(
                    build_contract_event()
                ),
                paid_work_authorization=(
                    build_authorization(
                        contract_execution_event_id=(
                            "different-event"
                        )
                    )
                ),
            )
        )


def test_rejects_missing_human_execution_confirmation():
    contract_event = build_contract_event()

    contract_event[
        "event_checklist"
    ][
        "human_operator_confirmed_execution"
    ] = False

    with pytest.raises(
        PreliveScenarioError,
    ):
        (
            PreliveExecutionHandoffBridge()
            .prepare_handoff(
                scenario=build_scenario(),
                metadata=build_metadata(),
                contract_execution_event=(
                    contract_event
                ),
                paid_work_authorization=(
                    build_authorization()
                ),
            )
        )


def test_rejects_unexecuted_contract():
    contract_event = build_contract_event()

    contract_event[
        "commercial_boundary"
    ][
        "contract_executed"
    ] = False

    with pytest.raises(
        PreliveScenarioError,
    ):
        (
            PreliveExecutionHandoffBridge()
            .prepare_handoff(
                scenario=build_scenario(),
                metadata=build_metadata(),
                contract_execution_event=(
                    contract_event
                ),
                paid_work_authorization=(
                    build_authorization()
                ),
            )
        )


def test_bridge_does_not_execute_assessment():
    result = build_result()
    payload = result.to_dict()

    assert (
        payload["assessment_executed"]
        is False
    )

    assert (
        "execution_result"
        not in payload
    )

    assert (
        "customer_outcome_verified"
        not in payload
    )

    assert (
        "production_onboarding_authorized"
        not in payload
    )


def test_result_serializes_ready_handoff():
    payload = build_result().to_dict()

    assert (
        payload["handoff"]["status"]
        == "ready_for_assessment_execution"
    )

    assert (
        len(
            payload["handoff"][
                "handoff_hash"
            ]
        )
        == 64
    )