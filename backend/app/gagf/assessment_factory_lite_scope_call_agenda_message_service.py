from backend.app.gagf.assessment_factory_lite_assessment_scope_call_package_service import (
    AssessmentFactoryLiteAssessmentScopeCallPackageService,
)


class AssessmentFactoryLiteScopeCallAgendaMessageService:
    """Build a human-reviewed scope-call agenda message draft."""

    def __init__(
        self,
        scope_call_package_service: AssessmentFactoryLiteAssessmentScopeCallPackageService | None = None,
    ):
        self.scope_call_package_service = (
            scope_call_package_service
            or AssessmentFactoryLiteAssessmentScopeCallPackageService()
        )

    def build_message(
        self,
        scope_call_package: dict | None = None,
        follow_up_event_record: dict | None = None,
        follow_up_message: dict | None = None,
        tracker: dict | None = None,
        event_record: dict | None = None,
        message: dict | None = None,
        delivery_package: dict | None = None,
        export_package: dict | None = None,
        export: dict | None = None,
        document: dict | None = None,
        proposal: dict | None = None,
        offer: dict | None = None,
        buyer_context: dict | None = None,
        operator_approval: dict | None = None,
        message_context: dict | None = None,
        event_context: dict | None = None,
        follow_up_context: dict | None = None,
        follow_up_message_context: dict | None = None,
        follow_up_event_context: dict | None = None,
        scope_call_context: dict | None = None,
        scope_call_message_context: dict | None = None,
    ) -> dict:
        source_package = scope_call_package or self.scope_call_package_service.build_package(
            follow_up_event_record=follow_up_event_record,
            follow_up_message=follow_up_message,
            tracker=tracker,
            event_record=event_record,
            message=message,
            delivery_package=delivery_package,
            export_package=export_package,
            export=export,
            document=document,
            proposal=proposal,
            offer=offer,
            buyer_context=buyer_context,
            operator_approval=operator_approval,
            message_context=message_context,
            event_context=event_context,
            follow_up_context=follow_up_context,
            follow_up_message_context=follow_up_message_context,
            follow_up_event_context=follow_up_event_context,
            scope_call_context=scope_call_context,
        )

        context = scope_call_message_context or {}
        message_status = self._message_status(source_package)

        return {
            "status": "ok",
            "message_type": "assessment_factory_lite_scope_call_agenda_message",
            "package_name": "Assessment Factory Lite Demo Package",
            "release": "assessment-factory-lite-scope-call-conversion",
            "version": "2.3.0",
            "message_stage": "scope_call_agenda_message_draft",
            "message_status": message_status,
            "delivery_channel": context.get("delivery_channel", "email_draft"),
            "recipient": self._recipient(context),
            "sender": self._sender(context),
            "subject": self._subject(source_package, context),
            "message_body": self._message_body(source_package, context, message_status),
            "source_scope_call_package": self._source_scope_call_package(source_package),
            "agenda_summary": self._agenda_summary(source_package),
            "buyer_response_summary": source_package.get("buyer_response_summary", {}),
            "commercial_next_action": source_package.get("commercial_next_action", {}),
            "evidence_boundary": source_package.get("evidence_boundary", {}),
            "commercial_boundary": source_package.get("commercial_boundary", {}),
            "scheduling_boundary": source_package.get("scheduling_boundary", {}),
            "operator_review": self._operator_review(source_package, message_status),
            "send_policy": self._send_policy(message_status),
            "boundary_notices": source_package.get("boundary_notices", []),
            "audit_notes": self._audit_notes(message_status),
            "next_action": self._next_action(message_status),
            "operator_message": self._operator_message(message_status),
            "recommended_action": (
                "review_scope_call_agenda_message"
                if message_status == "draft_ready"
                else "resolve_scope_call_agenda_message_gaps"
            ),
        }

    def _message_status(self, package: dict) -> str:
        if package.get("package_status") == "ready":
            return "draft_ready"

        return "blocked"

    def _recipient(self, context: dict) -> dict:
        return {
            "recipient_type": "buyer_role",
            "recipient_role": context.get("recipient_role", "operations_leader"),
            "email_required": True,
            "email_status": context.get("email_status", "operator_to_provide"),
        }

    def _sender(self, context: dict) -> dict:
        return {
            "sender_type": "operator",
            "sender_name": context.get("sender_name", "Assessment Factory Lite Operator"),
            "signature_required": True,
        }

    def _subject(self, package: dict, context: dict) -> str:
        return context.get(
            "subject",
            "Assessment Factory Lite Scope Call Agenda",
        )

    def _message_body(
        self,
        package: dict,
        context: dict,
        message_status: str,
    ) -> str:
        sender_name = context.get("sender_name", "Assessment Factory Lite Operator")

        if message_status == "blocked":
            return (
                "Hello,\n\n"
                "The Assessment Factory Lite scope-call agenda message is not ready "
                "because the scope-call package is not ready for agenda delivery.\n\n"
                "Please resolve the package blockers before preparing buyer-facing "
                "scope-call agenda language.\n\n"
                "This draft is non-binding and does not create a contract, invoice, "
                "payment request, calendar invite, or paid assessment start.\n\n"
                f"Thank you,\n{sender_name}"
            )

        agenda_lines = [
            f"- {item.get('item')}"
            for item in package.get("scope_call_agenda", [])
        ]

        agenda_text = "\n".join(agenda_lines)

        return (
            "Hello,\n\n"
            "Thank you for your interest in Assessment Factory Lite. "
            "For our bounded assessment scope call, I propose we use the agenda below:\n\n"
            f"{agenda_text}\n\n"
            "The call will focus on confirming the workflow scope, evidence sources, "
            "evidence boundaries, timeline, deliverables, commercial terms, and next "
            "approval step.\n\n"
            "Evidence boundary: please do not share regulated production data, secrets, "
            "credentials, unapproved personal data, or unapproved customer records. "
            "We can use non-sensitive sample workflow data, redacted examples, and "
            "operator-approved buyer-provided context.\n\n"
            "Commercial boundary: this scope-call agenda is non-binding and does not "
            "create a contract, invoice, payment request, calendar invite, paid "
            "assessment start, or production onboarding commitment.\n\n"
            "Scheduling boundary: I will only schedule the call after human operator "
            "review and buyer confirmation.\n\n"
            "Current commercial next action: schedule_assessment_scope_call.\n\n"
            f"Thank you,\n{sender_name}"
        )

    def _source_scope_call_package(self, package: dict) -> dict:
        return {
            "package_type": package.get("package_type"),
            "package_stage": package.get("package_stage"),
            "package_status": package.get("package_status"),
            "package_id": package.get("package_id"),
            "created_at": package.get("created_at"),
            "release": package.get("release"),
            "version": package.get("version"),
            "recommended_action": package.get("recommended_action"),
        }

    def _agenda_summary(self, package: dict) -> dict:
        agenda = package.get("scope_call_agenda", [])

        return {
            "agenda_item_count": len(agenda),
            "agenda_items": [item.get("item") for item in agenda],
            "all_items_required": all(item.get("required") is True for item in agenda),
            "agenda_owner": agenda[0].get("owner") if agenda else "",
        }

    def _operator_review(self, package: dict, message_status: str) -> dict:
        return {
            "package_status": package.get("package_status"),
            "package_blockers": package.get("package_blockers", []),
            "review_required": True,
            "human_operator_required": True,
            "approved_for_sending": False,
            "approved_for_scheduling": False,
            "message_ready": message_status == "draft_ready",
        }

    def _send_policy(self, message_status: str) -> dict:
        if message_status == "draft_ready":
            reason = (
                "Human operator review and buyer confirmation are required before "
                "scope-call agenda sending or scheduling."
            )
        else:
            reason = (
                "Scope-call package must be ready before agenda message drafting can proceed."
            )

        return {
            "send_allowed": False,
            "send_blocked_reason": reason,
            "automated_send_allowed": False,
            "calendar_invite_allowed": False,
            "automatic_scheduling_allowed": False,
            "requires_human_operator": True,
            "send_rule": (
                "Scope-call agenda messages are draft-only and must be reviewed, "
                "approved, and sent by a human operator."
            ),
        }

    def _audit_notes(self, message_status: str) -> list[str]:
        if message_status == "draft_ready":
            return [
                "scope_call_agenda_message_draft_ready",
                "automated_scope_call_sending_not_performed",
                "automatic_scheduling_not_performed",
            ]

        return [
            "scope_call_agenda_message_blocked",
            "automated_scope_call_sending_not_performed",
            "automatic_scheduling_not_performed",
        ]

    def _next_action(self, message_status: str) -> dict:
        if message_status == "draft_ready":
            return {
                "action": "review_scope_call_agenda_message",
                "operator_instruction": (
                    "Review the scope-call agenda message, confirm buyer details, "
                    "and send or schedule only through a human-operated channel."
                ),
                "future_action": "record_scope_call_agenda_message_event",
            }

        return {
            "action": "resolve_scope_call_agenda_message_gaps",
            "operator_instruction": (
                "Resolve scope-call package readiness gaps before preparing a "
                "buyer-facing agenda message."
            ),
            "future_action": "rerun_scope_call_agenda_message",
        }

    def _operator_message(self, message_status: str) -> str:
        if message_status == "draft_ready":
            return (
                "Assessment Factory Lite scope-call agenda message draft is ready "
                "for operator review."
            )

        return (
            "Assessment Factory Lite scope-call agenda message is blocked because "
            "the assessment scope call package is not ready."
        )