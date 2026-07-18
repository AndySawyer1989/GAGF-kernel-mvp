from backend.app.gagf.assessment_factory_lite_assessment_scope_call_package_service import (
    AssessmentFactoryLiteAssessmentScopeCallPackageService,
)
from backend.app.gagf.assessment_factory_lite_formal_proposal_markdown_export_service import (
    AssessmentFactoryLiteFormalProposalMarkdownExportService,
)


def service():
    return AssessmentFactoryLiteAssessmentScopeCallPackageService()


APPROVAL = {
    "approval_status": "operator_approved",
    "scope_approved": True,
    "evidence_boundary_approved": True,
    "commercial_terms_approved": True,
    "buyer_language_approved": True,
    "approval_note": "Operator approved package for buyer delivery.",
}


EVENT_CONTEXT = {
    "event_id": "buyer-delivery-event-001",
    "recorded_at": "2026-07-17T12:00:00+00:00",
    "human_operator_confirmed": True,
    "delivery_completed": True,
    "delivery_channel": "email_draft",
    "channel_status": "operator_recorded",
    "send_reference": "manual-send-log-001",
    "email_status": "operator_confirmed",
    "recipient_confirmed": True,
    "delivery_result": "delivered",
    "outcome_note": "Human operator sent the approved buyer delivery message.",
    "audit_notes": ["operator_review_completed"],
}


FOLLOW_UP_EVENT_CONTEXT = {
    "event_id": "buyer-follow-up-event-001",
    "recorded_at": "2026-07-21T12:00:00+00:00",
    "human_operator_confirmed": True,
    "follow_up_completed": True,
    "follow_up_channel": "email_draft",
    "channel_status": "operator_recorded",
    "send_reference": "manual-follow-up-log-001",
    "email_status": "operator_confirmed",
    "recipient_confirmed": True,
    "follow_up_result": "sent",
    "outcome_note": "Human operator sent the approved buyer follow-up message.",
    "audit_notes": ["follow_up_message_review_completed"],
}


INTERESTED_CONTEXT = {
    "buyer_response_status": "interested",
    "response_received_at": "2026-07-18T09:00:00+00:00",
    "response_summary": "Buyer wants to schedule a scope call.",
    "buyer_questions": ["Can we start next week?"],
}


def test_assessment_factory_lite_assessment_scope_call_package_builds_contract():
    result = service().build_package(
        operator_approval=APPROVAL,
        event_context=EVENT_CONTEXT,
        follow_up_context=INTERESTED_CONTEXT,
        follow_up_event_context=FOLLOW_UP_EVENT_CONTEXT,
        scope_call_context={
            "package_id": "assessment-scope-call-package-001",
            "created_at": "2026-07-21T12:30:00+00:00",
        },
    )

    assert result["status"] == "ok"
    assert result["package_type"] == "assessment_factory_lite_assessment_scope_call_package"
    assert result["package_name"] == "Assessment Factory Lite Demo Package"
    assert result["release"] == "assessment-factory-lite-buyer-delivery-follow-up"
    assert result["version"] == "2.2.0"
    assert result["package_stage"] == "assessment_scope_call_package"
    assert result["package_status"] == "ready"
    assert result["package_id"] == "assessment-scope-call-package-001"
    assert result["created_at"] == "2026-07-21T12:30:00+00:00"
    assert result["recommended_action"] == "review_assessment_scope_call_package"


def test_assessment_factory_lite_assessment_scope_call_package_includes_source_event_and_readiness():
    result = service().build_package(
        operator_approval=APPROVAL,
        event_context=EVENT_CONTEXT,
        follow_up_context=INTERESTED_CONTEXT,
        follow_up_event_context=FOLLOW_UP_EVENT_CONTEXT,
    )

    assert result["source_follow_up_event_record"] == {
        "event_type": "assessment_factory_lite_buyer_follow_up_event_record",
        "event_stage": "buyer_follow_up_event_record",
        "event_status": "recorded",
        "event_id": "buyer-follow-up-event-001",
        "recorded_at": "2026-07-21T12:00:00+00:00",
        "release": "assessment-factory-lite-proposal-export-package",
        "version": "2.1.0",
        "recommended_action": "review_buyer_follow_up_event_record",
    }

    assert result["scope_call_readiness"] == {
        "scope_call_ready": True,
        "event_recorded": True,
        "buyer_interested": True,
        "commercial_action_supported": True,
        "requires_operator_review": True,
        "automatic_scheduling_allowed": False,
    }


def test_assessment_factory_lite_assessment_scope_call_package_includes_agenda_and_boundaries():
    result = service().build_package(
        operator_approval=APPROVAL,
        event_context=EVENT_CONTEXT,
        follow_up_context=INTERESTED_CONTEXT,
        follow_up_event_context=FOLLOW_UP_EVENT_CONTEXT,
    )

    agenda_items = [item["item"] for item in result["scope_call_agenda"]]

    assert agenda_items == [
        "confirm workflow scope",
        "confirm evidence sources",
        "confirm evidence boundaries",
        "confirm timeline and deliverables",
        "confirm commercial terms",
        "confirm next approval step",
    ]

    assert all(item["required"] is True for item in result["scope_call_agenda"])
    assert all(item["owner"] == "operator" for item in result["scope_call_agenda"])

    assert result["evidence_boundary"] == {
        "allowed_evidence": [
            "non-sensitive sample workflow data",
            "redacted operational examples",
            "operator-approved buyer-provided context",
        ],
        "excluded_evidence": [
            "regulated production data",
            "secrets or credentials",
            "unapproved personal data",
            "unapproved customer records",
        ],
        "approval_required": True,
    }

    assert result["commercial_boundary"] == {
        "scope_call_is_non_binding": True,
        "not_a_contract": True,
        "not_an_invoice": True,
        "not_a_payment_request": True,
        "not_production_onboarding": True,
        "price_range": "USD 1500 - 3500",
        "final_terms_require_operator_approval": True,
    }


def test_assessment_factory_lite_assessment_scope_call_package_includes_approval_and_scheduling_boundaries():
    result = service().build_package(
        operator_approval=APPROVAL,
        event_context=EVENT_CONTEXT,
        follow_up_context=INTERESTED_CONTEXT,
        follow_up_event_context=FOLLOW_UP_EVENT_CONTEXT,
    )

    assert result["operator_approval_gate"] == {
        "approval_status": "operator_review_required",
        "agenda_approved": False,
        "evidence_boundary_approved": False,
        "commercial_terms_approved": False,
        "scheduling_language_approved": False,
    }

    assert result["scheduling_boundary"] == {
        "calendar_event_created": False,
        "calendar_invite_sent": False,
        "automatic_scheduling_allowed": False,
        "requires_human_operator": True,
        "scheduling_rule": (
            "The package may prepare scope-call material, but a human operator "
            "must approve and schedule the call."
        ),
    }


def test_assessment_factory_lite_assessment_scope_call_package_includes_checklist_and_no_blockers_when_ready():
    result = service().build_package(
        operator_approval=APPROVAL,
        event_context=EVENT_CONTEXT,
        follow_up_context=INTERESTED_CONTEXT,
        follow_up_event_context=FOLLOW_UP_EVENT_CONTEXT,
    )

    checks = {item["check"]: item for item in result["package_checklist"]}

    assert set(checks) == {
        "follow_up_event_recorded",
        "buyer_interested",
        "scope_call_action_supported",
        "agenda_present",
        "operator_review_required",
    }

    assert checks["follow_up_event_recorded"]["passed"] is True
    assert checks["buyer_interested"]["passed"] is True
    assert checks["scope_call_action_supported"]["passed"] is True
    assert checks["agenda_present"]["passed"] is True
    assert checks["operator_review_required"]["passed"] is True
    assert result["package_blockers"] == []


def test_assessment_factory_lite_assessment_scope_call_package_includes_audit_next_action_and_message():
    result = service().build_package(
        operator_approval=APPROVAL,
        event_context=EVENT_CONTEXT,
        follow_up_context=INTERESTED_CONTEXT,
        follow_up_event_context=FOLLOW_UP_EVENT_CONTEXT,
    )

    assert result["audit_notes"] == [
        "assessment_scope_call_package_ready",
        "automatic_scheduling_not_performed",
    ]

    assert result["next_action"] == {
        "action": "review_and_prepare_scope_call",
        "operator_instruction": (
            "Review the agenda, evidence boundary, commercial boundary, "
            "and scheduling language before manually scheduling the scope call."
        ),
        "future_action": "prepare_scope_call_agenda_message",
    }

    assert result["operator_message"] == (
        "Assessment Factory Lite assessment scope call package is ready "
        "for operator review."
    )


def test_assessment_factory_lite_assessment_scope_call_package_review_required_for_questions_response():
    result = service().build_package(
        operator_approval=APPROVAL,
        event_context=EVENT_CONTEXT,
        follow_up_context={
            "buyer_response_status": "questions",
            "response_summary": "Buyer has questions before scheduling.",
            "buyer_questions": ["Can you clarify evidence boundaries?"],
        },
        follow_up_event_context=FOLLOW_UP_EVENT_CONTEXT,
    )

    assert result["package_status"] == "review_required"
    assert result["recommended_action"] == "resolve_assessment_scope_call_package_gaps"
    assert result["scope_call_readiness"]["event_recorded"] is True
    assert result["scope_call_readiness"]["buyer_interested"] is False
    assert "buyer_interested" in result["package_blockers"]
    assert "scope_call_action_supported" in result["package_blockers"]
    assert result["next_action"] == {
        "action": "review_buyer_response_before_scope_call",
        "operator_instruction": (
            "Review buyer response and commercial next action before "
            "preparing a scope call package."
        ),
        "future_action": "rerun_assessment_scope_call_package",
    }


def test_assessment_factory_lite_assessment_scope_call_package_blocks_invalid_follow_up_event():
    export = AssessmentFactoryLiteFormalProposalMarkdownExportService().export_markdown()
    export["markdown"] = export["markdown"].replace(
        "Binding quote: False",
        "Binding quote: True",
    )

    result = service().build_package(
        export=export,
        event_context={
            "event_id": "buyer-delivery-event-003",
            "recorded_at": "2026-07-17T12:10:00+00:00",
            "human_operator_confirmed": True,
            "delivery_completed": True,
        },
        follow_up_event_context={
            "event_id": "buyer-follow-up-event-004",
            "recorded_at": "2026-07-21T12:15:00+00:00",
            "human_operator_confirmed": True,
            "follow_up_completed": True,
        },
    )

    assert result["package_status"] == "blocked"
    assert result["recommended_action"] == "resolve_assessment_scope_call_package_gaps"
    assert result["source_follow_up_event_record"]["event_status"] == "blocked"
    assert "follow_up_event_recorded" in result["package_blockers"]
    assert "buyer_interested" in result["package_blockers"]
    assert "scope_call_action_supported" in result["package_blockers"]
    assert result["next_action"] == {
        "action": "resolve_assessment_scope_call_package_gaps",
        "operator_instruction": (
            "Resolve follow-up event, buyer response, or commercial action gaps "
            "before preparing a scope call package."
        ),
        "future_action": "rerun_assessment_scope_call_package",
    }