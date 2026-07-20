from __future__ import annotations

from typing import Any

from backend.app.gagf.assessment_factory_lite_contract_execution_review_service import (
    AssessmentFactoryLiteContractExecutionReviewService,
)


class AssessmentFactoryLiteContractExecutionEventService:
    """Record a governed contract execution event.

    This event is created after contract execution review is ready. It may record
    that a contract has been executed, but it does not create an invoice, request
    payment, authorize paid work, or start production onboarding.
    """

    EVENT_TYPE = "assessment_factory_lite_contract_execution_event"
    EVENT_STAGE = "contract_execution_event"
    RELEASE = "assessment-factory-lite-scope-call-conversion"
    VERSION = "2.3.0"
    PACKAGE_NAME = "Assessment Factory Lite Demo Package"

    def record_event(
        self,
        *,
        contract_execution_review: dict[str, Any] | None = None,
        paid_assessment_agreement_review: dict[str, Any] | None = None,
        paid_assessment_authorization_package: dict[str, Any] | None = None,
        scope_call_event_record: dict[str, Any] | None = None,
        scope_call_event_package: dict[str, Any] | None = None,
        scope_call_agenda_message_event_record: dict[str, Any] | None = None,
        scope_call_agenda_message: dict[str, Any] | None = None,
        scope_call_package: dict[str, Any] | None = None,
        follow_up_event_record: dict[str, Any] | None = None,
        follow_up_message: dict[str, Any] | None = None,
        tracker: dict[str, Any] | None = None,
        event_record: dict[str, Any] | None = None,
        message: dict[str, Any] | None = None,
        delivery_package: dict[str, Any] | None = None,
        export_package: dict[str, Any] | None = None,
        export: dict[str, Any] | None = None,
        document: dict[str, Any] | None = None,
        proposal: dict[str, Any] | None = None,
        offer: dict[str, Any] | None = None,
        buyer_context: dict[str, Any] | None = None,
        operator_approval: dict[str, Any] | None = None,
        message_context: dict[str, Any] | None = None,
        event_context: dict[str, Any] | None = None,
        follow_up_context: dict[str, Any] | None = None,
        follow_up_message_context: dict[str, Any] | None = None,
        follow_up_event_context: dict[str, Any] | None = None,
        scope_call_context: dict[str, Any] | None = None,
        scope_call_message_context: dict[str, Any] | None = None,
        scope_call_message_event_context: dict[str, Any] | None = None,
        scope_call_event_context: dict[str, Any] | None = None,
        scope_call_record_context: dict[str, Any] | None = None,
        authorization_context: dict[str, Any] | None = None,
        agreement_context: dict[str, Any] | None = None,
        contract_context: dict[str, Any] | None = None,
        contract_execution_context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        contract_execution_context = contract_execution_context or {}

        review = (
            contract_execution_review
            or AssessmentFactoryLiteContractExecutionReviewService().build_review(
                paid_assessment_agreement_review=paid_assessment_agreement_review,
                paid_assessment_authorization_package=paid_assessment_authorization_package,
                scope_call_event_record=scope_call_event_record,
                scope_call_event_package=scope_call_event_package,
                scope_call_agenda_message_event_record=scope_call_agenda_message_event_record,
                scope_call_agenda_message=scope_call_agenda_message,
                scope_call_package=scope_call_package,
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
                scope_call_message_context=scope_call_message_context,
                scope_call_message_event_context=scope_call_message_event_context,
                scope_call_event_context=scope_call_event_context,
                scope_call_record_context=scope_call_record_context,
                authorization_context=authorization_context,
                agreement_context=agreement_context,
                contract_context=contract_context,
            )
        )

        event_identity = self._event_identity(contract_execution_context)
        source_summary = self._contract_review_summary(review)
        execution_evidence = self._execution_evidence(contract_execution_context)
        signature_record = self._signature_record(contract_execution_context)
        operator_confirmation = self._operator_confirmation(contract_execution_context)
        event_checklist = self._event_checklist(
            review=review,
            execution_evidence=execution_evidence,
            signature_record=signature_record,
            operator_confirmation=operator_confirmation,
        )
        event_blockers = [
            key for key, value in event_checklist.items() if value is not True
        ]
        event_status = self._event_status(
            review=review,
            execution_evidence=execution_evidence,
            signature_record=signature_record,
            operator_confirmation=operator_confirmation,
            event_blockers=event_blockers,
        )
        execution_score = self._execution_score(event_checklist)

        return {
            "status": "ok",
            "event_type": self.EVENT_TYPE,
            "package_name": self.PACKAGE_NAME,
            "release": self.RELEASE,
            "version": self.VERSION,
            "event_stage": self.EVENT_STAGE,
            "event_status": event_status,
            "contract_execution_event_id": event_identity[
                "contract_execution_event_id"
            ],
            "recorded_at": event_identity["recorded_at"],
            "source_contract_execution_review": source_summary,
            "execution_evidence": execution_evidence,
            "signature_record": signature_record,
            "operator_confirmation": operator_confirmation,
            "event_checklist": event_checklist,
            "event_blockers": event_blockers,
            "execution_score": execution_score,
            "contract_document_review": review.get("contract_document_review", {}),
            "signature_readiness": review.get("signature_readiness", {}),
            "agreement_terms": review.get("agreement_terms", {}),
            "buyer_acknowledgment": review.get("buyer_acknowledgment", {}),
            "buyer_request": review.get("buyer_request", {}),
            "commercial_review": review.get("commercial_review", {}),
            "evidence_review": review.get("evidence_review", {}),
            "human_authorization": review.get("human_authorization", {}),
            "scheduling_boundary": self._scheduling_boundary(),
            "commercial_boundary": self._commercial_boundary(event_status),
            "evidence_boundary": self._evidence_boundary(),
            "governance_boundary": self._governance_boundary(),
            "boundary_notices": self._boundary_notices(),
            "audit_notes": self._audit_notes(event_status),
            "next_action": self._next_action(event_status),
            "operator_message": self._operator_message(event_status),
            "recommended_action": self._recommended_action(event_status),
        }

    def _event_identity(
        self,
        contract_execution_context: dict[str, Any],
    ) -> dict[str, str]:
        return {
            "contract_execution_event_id": contract_execution_context.get(
                "contract_execution_event_id",
                "contract-execution-event-draft-001",
            ),
            "recorded_at": contract_execution_context.get(
                "recorded_at",
                "not_recorded",
            ),
        }

    def _contract_review_summary(self, review: dict[str, Any]) -> dict[str, Any]:
        return {
            "event_type": review.get("event_type"),
            "review_stage": review.get("review_stage"),
            "review_status": review.get("review_status"),
            "release": review.get("release"),
            "version": review.get("version"),
            "contract_review_id": review.get("contract_review_id"),
            "prepared_at": review.get("prepared_at"),
            "recommended_action": review.get("recommended_action"),
        }

    def _execution_evidence(
        self,
        contract_execution_context: dict[str, Any],
    ) -> dict[str, Any]:
        executed_contract_reference = contract_execution_context.get(
            "executed_contract_reference",
            "not_recorded",
        )
        executed_at = contract_execution_context.get("executed_at", "not_recorded")
        contract_execution_confirmed = (
            contract_execution_context.get("contract_execution_confirmed") is True
        )
        execution_method = contract_execution_context.get(
            "execution_method",
            "not_recorded",
        )

        return {
            "contract_execution_confirmed": contract_execution_confirmed,
            "executed_contract_reference": executed_contract_reference,
            "executed_at": executed_at,
            "execution_method": execution_method,
            "executed_contract_reference_recorded": executed_contract_reference
            != "not_recorded",
            "executed_at_recorded": executed_at != "not_recorded",
            "execution_method_recorded": execution_method != "not_recorded",
            "contract_executed": contract_execution_confirmed,
        }

    def _signature_record(
        self,
        contract_execution_context: dict[str, Any],
    ) -> dict[str, Any]:
        buyer_signed = contract_execution_context.get("buyer_signed") is True
        provider_signed = contract_execution_context.get("provider_signed") is True
        signature_evidence_recorded = (
            contract_execution_context.get("signature_evidence_recorded") is True
        )

        return {
            "buyer_signed": buyer_signed,
            "provider_signed": provider_signed,
            "signature_evidence_recorded": signature_evidence_recorded,
            "all_required_signatures_recorded": (
                buyer_signed and provider_signed and signature_evidence_recorded
            ),
            "signature_record_is_not_invoice": True,
            "signature_record_is_not_payment": True,
        }

    def _operator_confirmation(
        self,
        contract_execution_context: dict[str, Any],
    ) -> dict[str, Any]:
        return {
            "human_operator_required": True,
            "human_operator_confirmed_execution": contract_execution_context.get(
                "human_operator_confirmed_execution"
            )
            is True,
            "operator_name": contract_execution_context.get(
                "operator_name",
                "not_recorded",
            ),
            "operator_notes": contract_execution_context.get("operator_notes", []),
            "invoice_creation_approved": False,
            "payment_request_approved": False,
            "paid_assessment_authorized": False,
            "production_onboarding_approved": False,
        }

    def _event_checklist(
        self,
        *,
        review: dict[str, Any],
        execution_evidence: dict[str, Any],
        signature_record: dict[str, Any],
        operator_confirmation: dict[str, Any],
    ) -> dict[str, bool]:
        return {
            "contract_execution_review_ready": review.get("review_status")
            == "ready_for_contract_execution",
            "contract_execution_confirmed": execution_evidence[
                "contract_execution_confirmed"
            ],
            "executed_contract_reference_recorded": execution_evidence[
                "executed_contract_reference_recorded"
            ],
            "executed_at_recorded": execution_evidence["executed_at_recorded"],
            "execution_method_recorded": execution_evidence[
                "execution_method_recorded"
            ],
            "all_required_signatures_recorded": signature_record[
                "all_required_signatures_recorded"
            ],
            "human_operator_confirmed_execution": operator_confirmation[
                "human_operator_confirmed_execution"
            ],
            "signature_record_is_not_invoice": signature_record[
                "signature_record_is_not_invoice"
            ],
            "signature_record_is_not_payment": signature_record[
                "signature_record_is_not_payment"
            ],
            "invoice_not_created": operator_confirmation["invoice_creation_approved"]
            is False,
            "payment_not_requested": operator_confirmation["payment_request_approved"]
            is False,
            "paid_assessment_not_authorized": operator_confirmation[
                "paid_assessment_authorized"
            ]
            is False,
            "production_onboarding_not_started": operator_confirmation[
                "production_onboarding_approved"
            ]
            is False,
        }

    def _event_status(
        self,
        *,
        review: dict[str, Any],
        execution_evidence: dict[str, Any],
        signature_record: dict[str, Any],
        operator_confirmation: dict[str, Any],
        event_blockers: list[str],
    ) -> str:
        if review.get("review_status") == "blocked":
            return "blocked"

        if review.get("review_status") != "ready_for_contract_execution":
            return "pending_contract_execution_review"

        if execution_evidence["contract_execution_confirmed"] is not True:
            return "pending_contract_execution_confirmation"

        if not (
            execution_evidence["executed_contract_reference_recorded"]
            and execution_evidence["executed_at_recorded"]
            and execution_evidence["execution_method_recorded"]
        ):
            return "pending_execution_evidence"

        if signature_record["all_required_signatures_recorded"] is not True:
            return "pending_signature_record"

        if operator_confirmation["human_operator_confirmed_execution"] is not True:
            return "pending_operator_confirmation"

        if event_blockers:
            return "pending_contract_execution_event_review"

        return "contract_executed"

    def _execution_score(self, event_checklist: dict[str, bool]) -> dict[str, Any]:
        total = len(event_checklist)
        passed = sum(1 for value in event_checklist.values() if value is True)

        return {
            "passed": passed,
            "total": total,
            "score": round(passed / total, 4) if total else 0.0,
            "ready": passed == total,
        }

    def _scheduling_boundary(self) -> dict[str, Any]:
        return {
            "scope_call_scheduled_by_system": False,
            "calendar_invite_created": False,
            "automatic_scheduling_allowed": False,
            "manual_scheduling_required": True,
            "scheduling_authority": "human_operator",
        }

    def _commercial_boundary(self, event_status: str) -> dict[str, Any]:
        return {
            "contract_execution_recorded": event_status == "contract_executed",
            "contract_executed": event_status == "contract_executed",
            "invoice_created": False,
            "payment_requested": False,
            "paid_assessment_authorized": False,
            "production_onboarding_authorized": False,
            "requires_separate_invoice": True,
            "requires_separate_payment_confirmation": True,
            "requires_final_paid_work_authorization": True,
            "requires_separate_production_onboarding": True,
        }

    def _evidence_boundary(self) -> dict[str, Any]:
        return {
            "allowed_evidence": [
                "operator_scope_call_notes",
                "buyer_approved_scope_call_summary",
                "redacted_operational_examples",
                "non_sensitive_workflow_context",
                "operator_approved_assessment_scope",
                "agreement_review_notes",
                "contract_review_notes",
                "executed_contract_reference",
                "signature_evidence",
            ],
            "excluded_evidence": [
                "regulated_production_data",
                "secrets",
                "credentials",
                "unapproved_personal_data",
                "unapproved_customer_records",
            ],
            "production_data_requires_separate_approval": True,
        }

    def _governance_boundary(self) -> dict[str, Any]:
        return {
            "deterministic_status_required": True,
            "gagf_kernel_authoritative": True,
            "ai_override_allowed": False,
            "human_boundary_required": True,
            "release_marker_preserved": True,
            "contract_execution_event_is_not_invoice": True,
            "contract_execution_event_is_not_payment": True,
            "contract_execution_event_is_not_paid_work_authorization": True,
        }

    def _boundary_notices(self) -> list[str]:
        return [
            "contract_execution_event_records_contract_execution_only",
            "contract_execution_event_does_not_create_invoice",
            "contract_execution_event_does_not_request_payment",
            "contract_execution_event_does_not_authorize_paid_work",
            "contract_execution_event_does_not_start_production_onboarding",
            "contract_execution_event_requires_human_operator",
        ]

    def _audit_notes(self, event_status: str) -> list[str]:
        notes = [
            "contract_execution_event_built",
            "invoice_not_created",
            "payment_not_requested",
            "paid_assessment_not_authorized",
            "production_onboarding_not_started",
        ]

        if event_status == "contract_executed":
            notes.append("contract_execution_event_recorded")
        elif event_status == "pending_contract_execution_review":
            notes.append("contract_execution_event_pending_review")
        elif event_status == "pending_contract_execution_confirmation":
            notes.append("contract_execution_event_pending_execution_confirmation")
        elif event_status == "pending_execution_evidence":
            notes.append("contract_execution_event_pending_execution_evidence")
        elif event_status == "pending_signature_record":
            notes.append("contract_execution_event_pending_signature_record")
        elif event_status == "pending_operator_confirmation":
            notes.append("contract_execution_event_pending_operator_confirmation")
        elif event_status == "pending_contract_execution_event_review":
            notes.append("contract_execution_event_pending_event_review")
        else:
            notes.append("contract_execution_event_blocked")

        return notes

    def _next_action(self, event_status: str) -> dict[str, str]:
        if event_status == "contract_executed":
            return {
                "action": "prepare_invoice_creation_review",
                "operator_instruction": (
                    "Prepare invoice creation review. Do not request payment, "
                    "authorize paid work, or start production onboarding from "
                    "this contract execution event."
                ),
                "future_action": "build_invoice_creation_review",
            }

        if event_status == "pending_contract_execution_review":
            return {
                "action": "complete_contract_execution_review",
                "operator_instruction": (
                    "Complete contract execution review before recording contract "
                    "execution."
                ),
                "future_action": "rerun_contract_execution_event",
            }

        if event_status == "pending_contract_execution_confirmation":
            return {
                "action": "confirm_contract_execution",
                "operator_instruction": (
                    "Confirm that the contract was actually executed before "
                    "recording the event."
                ),
                "future_action": "rerun_contract_execution_event",
            }

        if event_status == "pending_execution_evidence":
            return {
                "action": "record_execution_evidence",
                "operator_instruction": (
                    "Record executed contract reference, executed_at, and execution "
                    "method before continuing."
                ),
                "future_action": "rerun_contract_execution_event",
            }

        if event_status == "pending_signature_record":
            return {
                "action": "record_signature_evidence",
                "operator_instruction": (
                    "Record buyer signature, provider signature, and signature "
                    "evidence before continuing."
                ),
                "future_action": "rerun_contract_execution_event",
            }

        if event_status == "pending_operator_confirmation":
            return {
                "action": "confirm_operator_contract_execution_event",
                "operator_instruction": (
                    "A human operator must confirm the contract execution event "
                    "before moving forward."
                ),
                "future_action": "rerun_contract_execution_event",
            }

        return {
            "action": "resolve_contract_execution_event_gaps",
            "operator_instruction": (
                "Resolve contract execution event blockers before moving forward."
            ),
            "future_action": "rerun_contract_execution_event",
        }

    def _operator_message(self, event_status: str) -> str:
        if event_status == "contract_executed":
            return (
                "Contract execution has been recorded. Invoice creation, payment "
                "request, paid work authorization, and production onboarding remain "
                "blocked."
            )

        if event_status == "pending_contract_execution_review":
            return (
                "Contract execution event is pending because contract execution "
                "review is not ready."
            )

        if event_status == "pending_contract_execution_confirmation":
            return "Contract execution event is pending execution confirmation."

        if event_status == "pending_execution_evidence":
            return "Contract execution event is pending execution evidence."

        if event_status == "pending_signature_record":
            return "Contract execution event is pending signature record."

        if event_status == "pending_operator_confirmation":
            return "Contract execution event is pending operator confirmation."

        if event_status == "pending_contract_execution_event_review":
            return "Contract execution event has unresolved event blockers."

        return (
            "Contract execution event is blocked. Resolve the listed blockers before "
            "moving forward."
        )

    def _recommended_action(self, event_status: str) -> str:
        if event_status == "contract_executed":
            return "prepare_invoice_creation_review"

        return "resolve_contract_execution_event_gaps"