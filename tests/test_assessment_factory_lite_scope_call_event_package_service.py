from backend.app.gagf.assessment_factory_lite_formal_proposal_markdown_export_service import (
    AssessmentFactoryLiteFormalProposalMarkdownExportService,
)
from backend.app.gagf.assessment_factory_lite_scope_call_event_package_service import (
    AssessmentFactoryLiteScopeCallEventPackageService,
)


APPROVAL = {
    "approval_status": "operator_approved",
    "scope_approved": True,
    "evidence_boundary_approved": True,
    "commercial_terms_approved": True,
    "buyer_language_approved": True,
}


EVENT_CONTEXT = {
    "event_id": "buyer-delivery-event-001",
    "recorded_at": "2026-07-17T12:00:00+00:00",
    "human_operator_confirmed": True,
    "delivery_completed": True,
}


FOLLOW_UP_EVENT_CONTEXT = {
    "event_id": "buyer-follow-up-event-001",
    "recorded_at": "2026-07-21T12:00:00+00:00",
    "human_operator_confirmed": True,
    "follow_up_completed": True,
}


INTERESTED_CONTEXT = {
    "buyer_response_status": "interested",
    "response_received_at": "2026-07-18T09:00:00+00:00",
    "response_summary": "Buyer wants to schedule a scope call.",
    "buyer_questions": ["Can we start next week?"],
}


AGENDA_EVENT_CONTEXT = {
    "event_id": "scope-call-agenda-message-event-001",
    "recorded_at": "2026-07-22T12:00:00+00:00",
    "human_operator_confirmed": True,
    "agenda_message_sent": True,
    "recipient_confirmed": True,
    "email_status": "operator_confirmed",
    "delivery_channel": "manual_email",
}


SCOPE_CALL_EVENT_CONTEXT = {
    "scope_call_id": "scope-call-event-package-001",
    "prepared_at": "2026-07-23T12:00:00+00:00",
}


def build_ready_package():
    return AssessmentFactoryLiteScopeCallEventPackageService().build_package(
        operator_approval=APPROVAL,
        event_context=EVENT_CONTEXT,
        follow_up_context=INTERESTED_CONTEXT,
        follow_up_event_context=FOLLOW_UP_EVENT_CONTEXT,
        scope_call_message_event_context=AGENDA_EVENT_CONTEXT,
        scope_call_event_context=SCOPE_CALL_EVENT_CONTEXT,
    )


def test_assessment_factory_lite_scope_call_event_package_service_builds_contract():
    result = build_ready_package()

    assert result["status"] == "ok"
    assert result["event_type"] == "assessment_factory_lite_scope_call_event_package"
    assert result["package_name"] == "Assessment Factory Lite Demo Package"
    assert result["release"] == "assessment-factory-lite-scope-call-conversion"
    assert result["version"] == "2.3.0"
    assert result["package_stage"] == "scope_call_event_package"
    assert result["package_status"] == "ready_for_scope_call"
    assert result["scope_call_id"] == "scope-call-event-package-001"
    assert result["prepared_at"] == "2026-07-23T12:00:00+00:00"
    assert result["recommended_action"] == "prepare_scope_call_event_record"


def test_assessment_factory_lite_scope_call_event_package_service_summarizes_source_agenda_message_event_record():
    result = build_ready_package()

    assert result["source_scope_call_agenda_message_event_record"] == {
        "event_type": "assessment_factory_lite_scope_call_agenda_message_event_record",
        "event_stage": "scope_call_agenda_message_event_record",
        "event_status": "recorded",
        "release": "assessment-factory-lite-scope-call-conversion",
        "version": "2.3.0",
        "event_id": "scope-call-agenda-message-event-001",
        "recorded_at": "2026-07-22T12:00:00+00:00",
        "recommended_action": "prepare_scope_call_event_record",
    }


def test_assessment_factory_lite_scope_call_event_package_service_tracks_buyer_readiness():
    result = build_ready_package()

    assert result["buyer_readiness"] == {
        "buyer_response_status": "interested",
        "buyer_interested": True,
        "buyer_questions": ["Can we start next week?"],
        "buyer_questions_count": 1,
        "buyer_ready_for_scope_call": True,
        "source_recipient_confirmed": True,
    }


def test_assessment_factory_lite_scope_call_event_package_service_tracks_agenda_confirmation():
    result = build_ready_package()

    assert result["agenda_confirmation"]["agenda_message_event_recorded"] is True
    assert result["agenda_confirmation"]["agenda_message_sent"] is True
    assert result["agenda_confirmation"]["recipient_confirmed"] is True
    assert result["agenda_confirmation"]["agenda_item_count"] == 6
    assert result["agenda_confirmation"]["agenda_items_required"] is True
    assert result["agenda_confirmation"]["agenda_ready"] is True


def test_assessment_factory_lite_scope_call_event_package_service_tracks_human_approval_without_authorizing_execution():
    result = build_ready_package()

    assert result["human_approval"] == {
        "approval_status": "operator_approved",
        "operator_approved": True,
        "human_operator_required": True,
        "scope_call_execution_approved": False,
        "automatic_scheduling_approved": False,
        "paid_assessment_approved": False,
        "contract_execution_approved": False,
    }


def test_assessment_factory_lite_scope_call_event_package_service_builds_readiness_checklist_and_score():
    result = build_ready_package()

    assert result["readiness_checklist"] == {
        "agenda_message_event_recorded": True,
        "agenda_ready": True,
        "buyer_ready_for_scope_call": True,
        "recipient_confirmed": True,
        "human_operator_approved": True,
        "automated_send_not_used": True,
        "calendar_invite_not_created": True,
        "automatic_scheduling_not_used": True,
        "paid_assessment_not_authorized": True,
        "contract_not_executed": True,
        "scope_call_not_scheduled_by_system": True,
    }

    assert result["readiness_blockers"] == []
    assert result["readiness_score"] == {
        "passed": 11,
        "total": 11,
        "score": 1.0,
        "ready": True,
    }


def test_assessment_factory_lite_scope_call_event_package_service_preserves_boundaries():
    result = build_ready_package()

    assert result["scheduling_boundary"] == {
        "scope_call_scheduled_by_system": False,
        "calendar_invite_created": False,
        "automatic_scheduling_allowed": False,
        "manual_scheduling_required": True,
        "scheduling_authority": "human_operator",
    }

    assert result["commercial_boundary"] == {
        "contract_created": False,
        "contract_executed": False,
        "invoice_created": False,
        "payment_requested": False,
        "paid_assessment_authorized": False,
        "production_onboarding_authorized": False,
        "scope_call_is_non_binding": True,
    }

    assert result["evidence_boundary"]["evidence_review_required_before_paid_assessment"] is True
    assert "regulated_production_data" in result["evidence_boundary"]["excluded_evidence"]

    assert result["governance_boundary"] == {
        "deterministic_status_required": True,
        "gagf_kernel_authoritative": True,
        "ai_override_allowed": False,
        "human_boundary_required": True,
        "release_marker_preserved": True,
    }

    assert result["boundary_notices"] == [
        "scope_call_event_package_does_not_schedule_call",
        "scope_call_event_package_does_not_create_calendar_invite",
        "scope_call_event_package_does_not_authorize_paid_assessment",
        "scope_call_event_package_does_not_execute_contract",
        "scope_call_event_package_requires_human_operator",
    ]


def test_assessment_factory_lite_scope_call_event_package_service_includes_audit_next_action_and_operator_message():
    result = build_ready_package()

    assert result["audit_notes"] == [
        "scope_call_event_package_built",
        "automatic_scheduling_not_performed",
        "calendar_invite_not_created",
        "paid_assessment_not_authorized",
        "contract_not_executed",
        "scope_call_event_package_ready",
    ]

    assert result["commercial_next_action"] == {
        "action": "prepare_human_operated_scope_call",
        "allowed_next_stage": "scope_call_event_record",
        "automatic_execution_allowed": False,
        "human_operator_required": True,
    }

    assert result["next_action"] == {
        "action": "prepare_scope_call_event_record",
        "operator_instruction": (
            "Prepare the human-operated scope-call event record after "
            "the scope call is completed or confirmed by the operator."
        ),
        "future_action": "build_scope_call_event_record",
    }

    assert result["operator_message"] == (
        "Scope-call readiness package is ready. The system has not "
        "scheduled the call, created a calendar invite, authorized paid "
        "work, or executed a contract."
    )


def test_assessment_factory_lite_scope_call_event_package_service_handles_pending_and_blocked_states():
    pending_agenda = dict(AGENDA_EVENT_CONTEXT)
    pending_agenda["agenda_message_sent"] = False

    result = AssessmentFactoryLiteScopeCallEventPackageService().build_package(
        operator_approval=APPROVAL,
        event_context=EVENT_CONTEXT,
        follow_up_context=INTERESTED_CONTEXT,
        follow_up_event_context=FOLLOW_UP_EVENT_CONTEXT,
        scope_call_message_event_context=pending_agenda,
    )

    assert result["package_status"] == "pending_agenda_message_event"
    assert "agenda_message_event_recorded" in result["readiness_blockers"]
    assert result["recommended_action"] == "resolve_scope_call_event_package_gaps"
    assert result["next_action"]["action"] == "record_scope_call_agenda_message_event"

    result = AssessmentFactoryLiteScopeCallEventPackageService().build_package(
        operator_approval=APPROVAL,
        event_context=EVENT_CONTEXT,
        follow_up_context={
            "buyer_response_status": "questions",
            "response_summary": "Buyer has questions before confirming a scope call.",
        },
        follow_up_event_context=FOLLOW_UP_EVENT_CONTEXT,
        scope_call_message_event_context=AGENDA_EVENT_CONTEXT,
    )

    assert result["package_status"] == "blocked"
    assert "agenda_message_event_recorded" in result["readiness_blockers"]
    assert result["recommended_action"] == "resolve_scope_call_event_package_gaps"

    result = AssessmentFactoryLiteScopeCallEventPackageService().build_package(
        operator_approval={
            "approval_status": "operator_review_required",
        },
        event_context=EVENT_CONTEXT,
        follow_up_context=INTERESTED_CONTEXT,
        follow_up_event_context=FOLLOW_UP_EVENT_CONTEXT,
        scope_call_message_event_context=AGENDA_EVENT_CONTEXT,
    )

    assert result["package_status"] == "pending_human_approval"
    assert "human_operator_approved" in result["readiness_blockers"]
    assert result["next_action"]["action"] == "confirm_human_operator_approval"


def test_assessment_factory_lite_scope_call_event_package_service_blocks_invalid_upstream_export():
    export = AssessmentFactoryLiteFormalProposalMarkdownExportService().export_markdown()
    export["markdown"] = export["markdown"].replace(
        "Binding quote: False",
        "Binding quote: True",
    )

    result = AssessmentFactoryLiteScopeCallEventPackageService().build_package(
        export=export,
        event_context=EVENT_CONTEXT,
        follow_up_event_context=FOLLOW_UP_EVENT_CONTEXT,
        scope_call_message_event_context=AGENDA_EVENT_CONTEXT,
        operator_approval=APPROVAL,
    )

    assert result["package_status"] == "blocked"
    assert result["source_scope_call_agenda_message_event_record"]["event_status"] == "blocked"
    assert result["recommended_action"] == "resolve_scope_call_event_package_gaps"