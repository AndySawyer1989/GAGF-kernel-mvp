from dataclasses import FrozenInstanceError
from types import SimpleNamespace

import pytest

from backend.app.gagf.governance_paid_assessment_execution_handoff import (
    GovernancePaidAssessmentExecutionHandoffService,
    PaidAssessmentExecutionHandoffError,
    PaidAssessmentExecutionHandoffStatus,
    PaidAssessmentWorkAuthorization,
)


SERVICE = GovernancePaidAssessmentExecutionHandoffService()


class StubAssessmentExecutionRequest:
    def __init__(
        self,
        *,
        tenant_id: str = "tenant-alpha",
        client_id: str = "client-acme",
        engagement_id: str = "engagement-001",
        assessment_id: str = "assessment-001",
        assessment_name: str = "Governance Runway Assessment",
    ) -> None:
        self.context = SimpleNamespace(
            tenant_id=tenant_id,
            client_id=client_id,
            engagement_id=engagement_id,
            assessment_id=assessment_id,
        )
        self.assessment_name = assessment_name

    def to_dict(self) -> dict:
        return {
            "hierarchy_key": "/".join(
                (
                    self.context.tenant_id,
                    self.context.client_id,
                    self.context.engagement_id,
                    self.context.assessment_id,
                )
            ),
            "assessment_name": self.assessment_name,
            "workflow_names": ["approval workflow"],
            "organizational_units": ["operations"],
            "period_start": "2026-07-01",
            "period_end": "2026-07-31",
            "objectives": ["Reduce governance friction"],
            "expected_outcomes": ["Identify priority constraints"],
            "evidence_requirement_count": 1,
            "evidence_input_count": 1,
            "client_display_name": "Example Client",
            "prepared_by": "FIP Operator",
            "exclusions": [],
            "maximum_priorities": 3,
        }


def build_contract_event(**overrides):
    event = {
        "status": "ok",
        "event_type": (
            "assessment_factory_lite_contract_execution_event"
        ),
        "package_name": "assessment_factory_lite",
        "release": "assessment-factory-lite-scope-call-conversion",
        "version": "2.3.0",
        "event_stage": "contract_execution",
        "event_status": "contract_executed",
        "contract_execution_event_id": "contract-event-001",
        "recorded_at": "2026-08-18T15:00:00+00:00",
        "execution_evidence": {
            "executed_contract_reference": "contract-ref-001",
            "executed_at": "2026-08-18T14:30:00+00:00",
            "executed_contract_reference_recorded": True,
            "executed_at_recorded": True,
            "contract_execution_confirmed": True,
            "contract_executed": True,
        },
        "event_checklist": {
            "contract_execution_review_ready": True,
            "contract_execution_confirmed": True,
            "executed_contract_reference_recorded": True,
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
                "contract_execution_event_is_not_paid_work_authorization"
            ): True,
        },
    }
    event.update(overrides)
    return event


def build_authorization(**overrides):
    values = {
        "authorization_id": "paid-work-auth-001",
        "tenant_id": "tenant-alpha",
        "client_id": "client-acme",
        "engagement_id": "engagement-001",
        "assessment_id": "assessment-001",
        "contract_execution_event_id": "contract-event-001",
        "authorized_by": "Andy Sawyer",
        "authorized_at": "2026-08-18T15:10:00+00:00",
        "paid_assessment_authorized": True,
    }
    values.update(overrides)
    return PaidAssessmentWorkAuthorization(**values)


def build_handoff(
    *,
    event=None,
    authorization=None,
    request=None,
):
    return SERVICE.build_handoff(
        contract_execution_event=(
            event
            if event is not None
            else build_contract_event()
        ),
        paid_work_authorization=(
            authorization
            if authorization is not None
            else build_authorization()
        ),
        assessment_execution_request=(
            request
            if request is not None
            else StubAssessmentExecutionRequest()
        ),
    )


def test_handoff_builds_ready_artifact():
    handoff = build_handoff()

    assert handoff.status is (
        PaidAssessmentExecutionHandoffStatus.READY
    )
    assert handoff.hierarchy_key == (
        "tenant-alpha/client-acme/engagement-001/assessment-001"
    )


def test_handoff_preserves_exact_lineage():
    handoff = build_handoff()

    assert handoff.contract_execution_event_id == (
        "contract-event-001"
    )
    assert handoff.paid_work_authorization_id == (
        "paid-work-auth-001"
    )
    assert len(handoff.contract_execution_event_hash) == 64
    assert len(handoff.paid_work_authorization_hash) == 64
    assert len(handoff.assessment_execution_request_hash) == 64
    assert len(handoff.handoff_hash) == 64


def test_contract_execution_alone_does_not_authorize_handoff():
    event = build_contract_event()

    assert (
        event["commercial_boundary"][
            "paid_assessment_authorized"
        ]
        is False
    )

    with pytest.raises(
        PaidAssessmentExecutionHandoffError,
        match="paid_assessment_authorized",
    ):
        build_authorization(
            paid_assessment_authorized=False
        )


def test_rejects_non_executed_contract_event():
    event = build_contract_event(
        event_status="pending_contract_execution_confirmation"
    )

    with pytest.raises(
        PaidAssessmentExecutionHandoffError,
        match="contract_executed",
    ):
        build_handoff(event=event)


def test_rejects_contract_event_with_blockers():
    event = build_contract_event(
        event_blockers=["signature_missing"]
    )

    with pytest.raises(
        PaidAssessmentExecutionHandoffError,
        match="contains blockers",
    ):
        build_handoff(event=event)


def test_rejects_event_that_claims_paid_work_authorization():
    event = build_contract_event()
    event["commercial_boundary"] = dict(
        event["commercial_boundary"]
    )
    event["commercial_boundary"][
        "paid_assessment_authorized"
    ] = True

    with pytest.raises(
        PaidAssessmentExecutionHandoffError,
        match="must not itself authorize",
    ):
        build_handoff(event=event)


def test_rejects_missing_final_authorization_boundary():
    event = build_contract_event()
    event["commercial_boundary"] = dict(
        event["commercial_boundary"]
    )
    event["commercial_boundary"][
        "requires_final_paid_work_authorization"
    ] = False

    with pytest.raises(
        PaidAssessmentExecutionHandoffError,
        match="requires_final_paid_work_authorization",
    ):
        build_handoff(event=event)


def test_rejects_ai_override_boundary():
    event = build_contract_event()
    event["governance_boundary"] = dict(
        event["governance_boundary"]
    )
    event["governance_boundary"][
        "ai_override_allowed"
    ] = True

    with pytest.raises(
        PaidAssessmentExecutionHandoffError,
        match="prohibit AI override",
    ):
        build_handoff(event=event)


def test_rejects_authorization_for_different_contract_event():
    authorization = build_authorization(
        contract_execution_event_id="other-contract-event"
    )

    with pytest.raises(
        PaidAssessmentExecutionHandoffError,
        match="different contract_execution_event_id",
    ):
        build_handoff(authorization=authorization)


def test_rejects_cross_tenant_authorization():
    authorization = build_authorization(
        tenant_id="tenant-beta"
    )

    with pytest.raises(
        PaidAssessmentExecutionHandoffError,
        match="hierarchy does not match",
    ):
        build_handoff(authorization=authorization)


def test_rejects_cross_client_authorization():
    authorization = build_authorization(
        client_id="client-other"
    )

    with pytest.raises(
        PaidAssessmentExecutionHandoffError,
        match="hierarchy does not match",
    ):
        build_handoff(authorization=authorization)

def test_rejects_cross_engagement_authorization():
    authorization = build_authorization(
        engagement_id="engagement-999"
    )

    with pytest.raises(
        PaidAssessmentExecutionHandoffError,
        match="hierarchy does not match",
    ):
        build_handoff(authorization=authorization)


def test_rejects_cross_assessment_authorization():
    authorization = build_authorization(
        assessment_id="assessment-999"
    )

    with pytest.raises(
        PaidAssessmentExecutionHandoffError,
        match="hierarchy does not match",
    ):
        build_handoff(authorization=authorization)


def test_handoff_hash_is_deterministic():
    first = build_handoff()
    second = build_handoff()

    assert first.handoff_hash == second.handoff_hash


def test_request_change_changes_handoff_hash():
    first = build_handoff()

    changed_request = StubAssessmentExecutionRequest(
        assessment_name="Different Assessment"
    )

    second = build_handoff(
        request=changed_request
    )

    assert (
        first.assessment_execution_request_hash
        != second.assessment_execution_request_hash
    )
    assert first.handoff_hash != second.handoff_hash


def test_contract_event_change_changes_handoff_hash():
    first = build_handoff()

    changed_event = build_contract_event()
    changed_event["recorded_at"] = (
        "2026-08-18T15:01:00+00:00"
    )

    second = build_handoff(
        event=changed_event
    )

    assert (
        first.contract_execution_event_hash
        != second.contract_execution_event_hash
    )
    assert first.handoff_hash != second.handoff_hash


def test_authorization_is_immutable():
    authorization = build_authorization()

    with pytest.raises(FrozenInstanceError):
        authorization.authorized_by = "Someone Else"


def test_handoff_is_immutable():
    handoff = build_handoff()

    with pytest.raises(FrozenInstanceError):
        handoff.status = (
            PaidAssessmentExecutionHandoffStatus.READY
        )


def test_serialized_handoff_contains_no_execution_claim():
    payload = build_handoff().to_dict()

    assert payload["status"] == "ready_for_assessment_execution"

    forbidden_keys = {
        "assessment_executed",
        "assessment_completed",
        "execution_completed",
        "findings_generated",
        "report_generated",
        "intervention_authorized",
    }

    assert forbidden_keys.isdisjoint(payload)