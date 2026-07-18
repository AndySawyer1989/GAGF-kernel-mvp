from datetime import UTC, datetime

from backend.app.gagf.assessment_factory_lite_buyer_follow_up_event_record_service import (
    AssessmentFactoryLiteBuyerFollowUpEventRecordService,
)


class AssessmentFactoryLiteAssessmentScopeCallPackageService:
    """Build an operator-reviewed assessment scope call package."""

    def __init__(
        self,
        follow_up_event_record_service: AssessmentFactoryLiteBuyerFollowUpEventRecordService | None = None,
    ):
        self.follow_up_event_record_service = (
            follow_up_event_record_service
            or AssessmentFactoryLiteBuyerFollowUpEventRecordService()
        )

    def build_package(
        self,
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
    ) -> dict:
        source_event = (
            follow_up_event_record
            or self.follow_up_event_record_service.build_event_record(
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
            )
        )

        context = scope_call_context or {}
        package_status = self._package_status(source_event)

        return {
            "status": "ok",
            "package_type": "assessment_factory_lite_assessment_scope_call_package",
            "package_name": "Assessment Factory Lite Demo Package",
            "release": "assessment-factory-lite-buyer-delivery-follow-up",
            "version": "2.2.0",
            "package_stage": "assessment_scope_call_package",
            "package_status": package_status,
            "package_id": self._package_id(context),
            "created_at": self._created_at(context),
            "source_follow_up_event_record": self._source_follow_up_event_record(source_event),
            "buyer_response_summary": source_event.get("buyer_response_summary", {}),
            "commercial_next_action": source_event.get("commercial_next_action", {}),
            "scope_call_readiness": self._scope_call_readiness(source_event),
            "scope_call_agenda": self._scope_call_agenda(context),
            "evidence_boundary": self._evidence_boundary(context),
            "commercial_boundary": self._commercial_boundary(context),
            "operator_approval_gate": self._operator_approval_gate(context),
            "scheduling_boundary": self._scheduling_boundary(),
            "package_checklist": self._package_checklist(source_event, context),
            "package_blockers": self._package_blockers(source_event, context),
            "boundary_notices": source_event.get("boundary_notices", []),
            "audit_notes": self._audit_notes(package_status),
            "next_action": self._next_action(package_status),
            "operator_message": self._operator_message(package_status),
            "recommended_action": (
                "review_assessment_scope_call_package"
                if package_status == "ready"
                else "resolve_assessment_scope_call_package_gaps"
            ),
        }

    def _package_status(self, event_record: dict) -> str:
        if event_record.get("event_status") != "recorded":
            return "blocked"

        commercial_action = event_record.get("commercial_next_action", {}).get("action")
        buyer_response_status = event_record.get("buyer_response_summary", {}).get(
            "response_status"
        )

        if (
            commercial_action == "schedule_assessment_scope_call"
            and buyer_response_status == "interested"
        ):
            return "ready"

        return "review_required"

    def _package_id(self, context: dict) -> str:
        return context.get("package_id", "assessment-scope-call-package-draft-001")

    def _created_at(self, context: dict) -> str:
        return context.get(
            "created_at",
            datetime.now(UTC).replace(microsecond=0).isoformat(),
        )

    def _source_follow_up_event_record(self, event_record: dict) -> dict:
        return {
            "event_type": event_record.get("event_type"),
            "event_stage": event_record.get("event_stage"),
            "event_status": event_record.get("event_status"),
            "event_id": event_record.get("event_id"),
            "recorded_at": event_record.get("recorded_at"),
            "release": event_record.get("release"),
            "version": event_record.get("version"),
            "recommended_action": event_record.get("recommended_action"),
        }

    def _scope_call_readiness(self, event_record: dict) -> dict:
        commercial_action = event_record.get("commercial_next_action", {}).get("action")
        buyer_response_status = event_record.get("buyer_response_summary", {}).get(
            "response_status"
        )

        return {
            "scope_call_ready": (
                event_record.get("event_status") == "recorded"
                and commercial_action == "schedule_assessment_scope_call"
                and buyer_response_status == "interested"
            ),
            "event_recorded": event_record.get("event_status") == "recorded",
            "buyer_interested": buyer_response_status == "interested",
            "commercial_action_supported": commercial_action
            == "schedule_assessment_scope_call",
            "requires_operator_review": True,
            "automatic_scheduling_allowed": False,
        }

    def _scope_call_agenda(self, context: dict) -> list[dict]:
        agenda_items = context.get(
            "agenda_items",
            [
                "confirm workflow scope",
                "confirm evidence sources",
                "confirm evidence boundaries",
                "confirm timeline and deliverables",
                "confirm commercial terms",
                "confirm next approval step",
            ],
        )

        return [
            {
                "item": item,
                "required": True,
                "owner": context.get("agenda_owner", "operator"),
            }
            for item in agenda_items
        ]

    def _evidence_boundary(self, context: dict) -> dict:
        return {
            "allowed_evidence": context.get(
                "allowed_evidence",
                [
                    "non-sensitive sample workflow data",
                    "redacted operational examples",
                    "operator-approved buyer-provided context",
                ],
            ),
            "excluded_evidence": context.get(
                "excluded_evidence",
                [
                    "regulated production data",
                    "secrets or credentials",
                    "unapproved personal data",
                    "unapproved customer records",
                ],
            ),
            "approval_required": True,
        }

    def _commercial_boundary(self, context: dict) -> dict:
        return {
            "scope_call_is_non_binding": True,
            "not_a_contract": True,
            "not_an_invoice": True,
            "not_a_payment_request": True,
            "not_production_onboarding": True,
            "price_range": context.get("price_range", "USD 1500 - 3500"),
            "final_terms_require_operator_approval": True,
        }

    def _operator_approval_gate(self, context: dict) -> dict:
        return {
            "approval_status": context.get("approval_status", "operator_review_required"),
            "agenda_approved": context.get("agenda_approved", False),
            "evidence_boundary_approved": context.get(
                "evidence_boundary_approved",
                False,
            ),
            "commercial_terms_approved": context.get(
                "commercial_terms_approved",
                False,
            ),
            "scheduling_language_approved": context.get(
                "scheduling_language_approved",
                False,
            ),
        }

    def _scheduling_boundary(self) -> dict:
        return {
            "calendar_event_created": False,
            "calendar_invite_sent": False,
            "automatic_scheduling_allowed": False,
            "requires_human_operator": True,
            "scheduling_rule": (
                "The package may prepare scope-call material, but a human operator "
                "must approve and schedule the call."
            ),
        }

    def _package_checklist(self, event_record: dict, context: dict) -> list[dict]:
        commercial_action = event_record.get("commercial_next_action", {}).get("action")
        buyer_response_status = event_record.get("buyer_response_summary", {}).get(
            "response_status"
        )

        return [
            {
                "check": "follow_up_event_recorded",
                "passed": event_record.get("event_status") == "recorded",
                "description": "Buyer follow-up event must be recorded.",
            },
            {
                "check": "buyer_interested",
                "passed": buyer_response_status == "interested",
                "description": "Buyer response must indicate interest.",
            },
            {
                "check": "scope_call_action_supported",
                "passed": commercial_action == "schedule_assessment_scope_call",
                "description": "Commercial next action must be scope-call scheduling.",
            },
            {
                "check": "agenda_present",
                "passed": len(self._scope_call_agenda(context)) > 0,
                "description": "Scope-call agenda must be present.",
            },
            {
                "check": "operator_review_required",
                "passed": True,
                "description": "Operator review is required before scheduling.",
            },
        ]

    def _package_blockers(self, event_record: dict, context: dict) -> list[str]:
        return sorted(
            {
                item["check"]
                for item in self._package_checklist(event_record, context)
                if not item["passed"]
            }
        )

    def _audit_notes(self, package_status: str) -> list[str]:
        if package_status == "ready":
            return [
                "assessment_scope_call_package_ready",
                "automatic_scheduling_not_performed",
            ]

        if package_status == "review_required":
            return [
                "assessment_scope_call_package_review_required",
                "automatic_scheduling_not_performed",
            ]

        return [
            "assessment_scope_call_package_blocked",
            "automatic_scheduling_not_performed",
        ]

    def _next_action(self, package_status: str) -> dict:
        if package_status == "ready":
            return {
                "action": "review_and_prepare_scope_call",
                "operator_instruction": (
                    "Review the agenda, evidence boundary, commercial boundary, "
                    "and scheduling language before manually scheduling the scope call."
                ),
                "future_action": "prepare_scope_call_agenda_message",
            }

        if package_status == "review_required":
            return {
                "action": "review_buyer_response_before_scope_call",
                "operator_instruction": (
                    "Review buyer response and commercial next action before "
                    "preparing a scope call package."
                ),
                "future_action": "rerun_assessment_scope_call_package",
            }

        return {
            "action": "resolve_assessment_scope_call_package_gaps",
            "operator_instruction": (
                "Resolve follow-up event, buyer response, or commercial action gaps "
                "before preparing a scope call package."
            ),
            "future_action": "rerun_assessment_scope_call_package",
        }

    def _operator_message(self, package_status: str) -> str:
        if package_status == "ready":
            return (
                "Assessment Factory Lite assessment scope call package is ready "
                "for operator review."
            )

        if package_status == "review_required":
            return (
                "Assessment Factory Lite assessment scope call package requires "
                "operator review before scope-call preparation."
            )

        return (
            "Assessment Factory Lite assessment scope call package is blocked "
            "because the buyer follow-up event or buyer interest state is incomplete."
        )