from __future__ import annotations

from typing import Any

from backend.app.gagf.assessment_factory_lite_contract_execution_event_service import (
    AssessmentFactoryLiteContractExecutionEventService,
)


class AssessmentFactoryLiteInvoiceCreationReviewService:
    """Build a governed invoice creation review.

    This review is created after contract execution is recorded. It reviews
    invoice readiness only. It does not create an invoice, request payment,
    authorize paid work, or start production onboarding.
    """

    EVENT_TYPE = "assessment_factory_lite_invoice_creation_review"
    REVIEW_STAGE = "invoice_creation_review"
    RELEASE = "assessment-factory-lite-scope-call-conversion"
    VERSION = "2.3.0"
    PACKAGE_NAME = "Assessment Factory Lite Demo Package"

    def build_review(
        self,
        *,
        contract_execution_event: dict[str, Any] | None = None,
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
        invoice_context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        invoice_context = invoice_context or {}

        event = (
            contract_execution_event
            or AssessmentFactoryLiteContractExecutionEventService().record_event(
                contract_execution_review=contract_execution_review,
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
                contract_execution_context=contract_execution_context,
            )
        )

        invoice_identity = self._invoice_identity(invoice_context)
        source_summary = self._contract_execution_event_summary(event)
        invoice_details_review = self._invoice_details_review(invoice_context)
        billing_readiness = self._billing_readiness(invoice_context)
        operator_review = self._operator_review(invoice_context)
        review_checklist = self._review_checklist(
            event=event,
            invoice_details_review=invoice_details_review,
            billing_readiness=billing_readiness,
            operator_review=operator_review,
        )
        review_blockers = [
            key for key, value in review_checklist.items() if value is not True
        ]
        review_status = self._review_status(
            event=event,
            invoice_details_review=invoice_details_review,
            billing_readiness=billing_readiness,
            operator_review=operator_review,
            review_blockers=review_blockers,
        )
        review_score = self._review_score(review_checklist)

        return {
            "status": "ok",
            "event_type": self.EVENT_TYPE,
            "package_name": self.PACKAGE_NAME,
            "release": self.RELEASE,
            "version": self.VERSION,
            "review_stage": self.REVIEW_STAGE,
            "review_status": review_status,
            "invoice_review_id": invoice_identity["invoice_review_id"],
            "prepared_at": invoice_identity["prepared_at"],
            "source_contract_execution_event": source_summary,
            "invoice_details_review": invoice_details_review,
            "billing_readiness": billing_readiness,
            "operator_review": operator_review,
            "review_checklist": review_checklist,
            "review_blockers": review_blockers,
            "review_score": review_score,
            "execution_evidence": event.get("execution_evidence", {}),
            "signature_record": event.get("signature_record", {}),
            "contract_document_review": event.get("contract_document_review", {}),
            "agreement_terms": event.get("agreement_terms", {}),
            "buyer_request": event.get("buyer_request", {}),
            "commercial_review": event.get("commercial_review", {}),
            "evidence_review": event.get("evidence_review", {}),
            "human_authorization": event.get("human_authorization", {}),
            "scheduling_boundary": self._scheduling_boundary(),
            "commercial_boundary": self._commercial_boundary(review_status),
            "evidence_boundary": self._evidence_boundary(),
            "governance_boundary": self._governance_boundary(),
            "boundary_notices": self._boundary_notices(),
            "audit_notes": self._audit_notes(review_status),
            "next_action": self._next_action(review_status),
            "operator_message": self._operator_message(review_status),
            "recommended_action": self._recommended_action(review_status),
        }

    def _invoice_identity(self, invoice_context: dict[str, Any]) -> dict[str, str]:
        return {
            "invoice_review_id": invoice_context.get(
                "invoice_review_id",
                "invoice-creation-review-draft-001",
            ),
            "prepared_at": invoice_context.get("prepared_at", "not_recorded"),
        }

    def _contract_execution_event_summary(self, event: dict[str, Any]) -> dict[str, Any]:
        return {
            "event_type": event.get("event_type"),
            "event_stage": event.get("event_stage"),
            "event_status": event.get("event_status"),
            "release": event.get("release"),
            "version": event.get("version"),
            "contract_execution_event_id": event.get("contract_execution_event_id"),
            "recorded_at": event.get("recorded_at"),
            "recommended_action": event.get("recommended_action"),
        }

    def _invoice_details_review(
        self,
        invoice_context: dict[str, Any],
    ) -> dict[str, Any]:
        invoice_amount_confirmed = invoice_context.get("invoice_amount_confirmed") is True
        invoice_recipient_confirmed = (
            invoice_context.get("invoice_recipient_confirmed") is True
        )
        invoice_description_confirmed = (
            invoice_context.get("invoice_description_confirmed") is True
        )
        invoice_terms_confirmed = invoice_context.get("invoice_terms_confirmed") is True

        return {
            "invoice_amount_confirmed": invoice_amount_confirmed,
            "invoice_recipient_confirmed": invoice_recipient_confirmed,
            "invoice_description_confirmed": invoice_description_confirmed,
            "invoice_terms_confirmed": invoice_terms_confirmed,
            "invoice_details_ready": (
                invoice_amount_confirmed
                and invoice_recipient_confirmed
                and invoice_description_confirmed
                and invoice_terms_confirmed
            ),
            "invoice_creation_required_before_payment_request": True,
            "payment_confirmation_required_before_paid_work": True,
        }

    def _billing_readiness(self, invoice_context: dict[str, Any]) -> dict[str, Any]:
        billing_system_ready = invoice_context.get("billing_system_ready") is True
        tax_or_business_details_checked = (
            invoice_context.get("tax_or_business_details_checked") is True
        )
        payment_instructions_reviewed = (
            invoice_context.get("payment_instructions_reviewed") is True
        )

        return {
            "billing_system_ready": billing_system_ready,
            "tax_or_business_details_checked": tax_or_business_details_checked,
            "payment_instructions_reviewed": payment_instructions_reviewed,
            "billing_ready": (
                billing_system_ready
                and tax_or_business_details_checked
                and payment_instructions_reviewed
            ),
            "billing_readiness_is_not_payment_request": True,
            "billing_readiness_is_not_paid_work_authorization": True,
        }

    def _operator_review(self, invoice_context: dict[str, Any]) -> dict[str, Any]:
        return {
            "human_operator_required": True,
            "invoice_creation_reviewed_by_operator": invoice_context.get(
                "invoice_creation_reviewed_by_operator"
            )
            is True,
            "operator_review_status": invoice_context.get(
                "operator_review_status",
                "invoice_creation_review_required",
            ),
            "invoice_created": False,
            "payment_request_approved": False,
            "paid_assessment_authorized": False,
            "production_onboarding_approved": False,
        }

    def _review_checklist(
        self,
        *,
        event: dict[str, Any],
        invoice_details_review: dict[str, Any],
        billing_readiness: dict[str, Any],
        operator_review: dict[str, Any],
    ) -> dict[str, bool]:
        return {
            "contract_execution_event_recorded": event.get("event_status")
            == "contract_executed",
            "invoice_details_ready": invoice_details_review["invoice_details_ready"],
            "billing_ready": billing_readiness["billing_ready"],
            "billing_readiness_is_not_payment_request": billing_readiness[
                "billing_readiness_is_not_payment_request"
            ],
            "billing_readiness_is_not_paid_work_authorization": billing_readiness[
                "billing_readiness_is_not_paid_work_authorization"
            ],
            "invoice_creation_reviewed_by_operator": operator_review[
                "invoice_creation_reviewed_by_operator"
            ],
            "invoice_not_created": operator_review["invoice_created"] is False,
            "payment_not_requested": operator_review["payment_request_approved"]
            is False,
            "paid_assessment_not_authorized": operator_review[
                "paid_assessment_authorized"
            ]
            is False,
            "production_onboarding_not_started": operator_review[
                "production_onboarding_approved"
            ]
            is False,
        }

    def _review_status(
        self,
        *,
        event: dict[str, Any],
        invoice_details_review: dict[str, Any],
        billing_readiness: dict[str, Any],
        operator_review: dict[str, Any],
        review_blockers: list[str],
    ) -> str:
        if event.get("event_status") == "blocked":
            return "blocked"

        if event.get("event_status") != "contract_executed":
            return "pending_contract_execution_event"

        if invoice_details_review["invoice_details_ready"] is not True:
            return "pending_invoice_details_review"

        if billing_readiness["billing_ready"] is not True:
            return "pending_billing_readiness"

        if operator_review["invoice_creation_reviewed_by_operator"] is not True:
            return "pending_operator_review"

        if review_blockers:
            return "pending_invoice_creation_review"

        return "ready_for_invoice_creation"

    def _review_score(self, review_checklist: dict[str, bool]) -> dict[str, Any]:
        total = len(review_checklist)
        passed = sum(1 for value in review_checklist.values() if value is True)

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

    def _commercial_boundary(self, review_status: str) -> dict[str, Any]:
        return {
            "invoice_creation_ready": review_status == "ready_for_invoice_creation",
            "invoice_created": False,
            "payment_requested": False,
            "paid_assessment_authorized": False,
            "production_onboarding_authorized": False,
            "requires_actual_invoice_creation": True,
            "requires_separate_payment_request": True,
            "requires_separate_payment_confirmation": True,
            "requires_final_paid_work_authorization": True,
            "requires_separate_production_onboarding": True,
        }

    def _evidence_boundary(self) -> dict[str, Any]:
        return {
            "allowed_evidence": [
                "executed_contract_reference",
                "signature_evidence",
                "contract_review_notes",
                "invoice_review_notes",
                "billing_readiness_notes",
                "non_sensitive_workflow_context",
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
            "invoice_creation_review_is_not_invoice": True,
            "invoice_creation_review_is_not_payment_request": True,
            "invoice_creation_review_is_not_paid_work_authorization": True,
        }

    def _boundary_notices(self) -> list[str]:
        return [
            "invoice_creation_review_does_not_create_invoice",
            "invoice_creation_review_does_not_request_payment",
            "invoice_creation_review_does_not_authorize_paid_work",
            "invoice_creation_review_does_not_start_production_onboarding",
            "invoice_creation_review_requires_human_operator",
        ]

    def _audit_notes(self, review_status: str) -> list[str]:
        notes = [
            "invoice_creation_review_built",
            "invoice_not_created",
            "payment_not_requested",
            "paid_assessment_not_authorized",
            "production_onboarding_not_started",
        ]

        if review_status == "ready_for_invoice_creation":
            notes.append("invoice_creation_review_ready")
        elif review_status == "pending_contract_execution_event":
            notes.append("invoice_creation_review_pending_contract_execution_event")
        elif review_status == "pending_invoice_details_review":
            notes.append("invoice_creation_review_pending_invoice_details")
        elif review_status == "pending_billing_readiness":
            notes.append("invoice_creation_review_pending_billing_readiness")
        elif review_status == "pending_operator_review":
            notes.append("invoice_creation_review_pending_operator_review")
        elif review_status == "pending_invoice_creation_review":
            notes.append("invoice_creation_review_pending_review")
        else:
            notes.append("invoice_creation_review_blocked")

        return notes

    def _next_action(self, review_status: str) -> dict[str, str]:
        if review_status == "ready_for_invoice_creation":
            return {
                "action": "prepare_invoice_creation_event",
                "operator_instruction": (
                    "Prepare invoice creation event. Do not request payment, "
                    "authorize paid work, or start production onboarding from "
                    "this review."
                ),
                "future_action": "build_invoice_creation_event",
            }

        if review_status == "pending_contract_execution_event":
            return {
                "action": "complete_contract_execution_event",
                "operator_instruction": (
                    "Complete contract execution event before invoice creation "
                    "review can become ready."
                ),
                "future_action": "rerun_invoice_creation_review",
            }

        if review_status == "pending_invoice_details_review":
            return {
                "action": "complete_invoice_details_review",
                "operator_instruction": (
                    "Confirm invoice amount, recipient, description, and terms "
                    "before moving forward."
                ),
                "future_action": "rerun_invoice_creation_review",
            }

        if review_status == "pending_billing_readiness":
            return {
                "action": "confirm_billing_readiness",
                "operator_instruction": (
                    "Confirm billing system, business details, and payment "
                    "instructions before moving forward."
                ),
                "future_action": "rerun_invoice_creation_review",
            }

        if review_status == "pending_operator_review":
            return {
                "action": "complete_operator_invoice_creation_review",
                "operator_instruction": (
                    "A human operator must complete invoice creation review before "
                    "moving forward."
                ),
                "future_action": "rerun_invoice_creation_review",
            }

        return {
            "action": "resolve_invoice_creation_review_gaps",
            "operator_instruction": (
                "Resolve invoice creation review blockers before moving forward."
            ),
            "future_action": "rerun_invoice_creation_review",
        }

    def _operator_message(self, review_status: str) -> str:
        if review_status == "ready_for_invoice_creation":
            return (
                "Invoice creation review is ready for invoice creation event. "
                "Payment request, paid work authorization, and production "
                "onboarding remain blocked."
            )

        if review_status == "pending_contract_execution_event":
            return (
                "Invoice creation review is pending because contract execution "
                "event is not recorded."
            )

        if review_status == "pending_invoice_details_review":
            return "Invoice creation review is pending invoice details review."

        if review_status == "pending_billing_readiness":
            return "Invoice creation review is pending billing readiness."

        if review_status == "pending_operator_review":
            return "Invoice creation review is pending operator review."

        if review_status == "pending_invoice_creation_review":
            return "Invoice creation review has unresolved review blockers."

        return (
            "Invoice creation review is blocked. Resolve the listed blockers before "
            "moving forward."
        )

    def _recommended_action(self, review_status: str) -> str:
        if review_status == "ready_for_invoice_creation":
            return "prepare_invoice_creation_event"

        return "resolve_invoice_creation_review_gaps"