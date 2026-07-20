from __future__ import annotations

from typing import Any

from backend.app.gagf.assessment_factory_lite_invoice_creation_review_service import (
    AssessmentFactoryLiteInvoiceCreationReviewService,
)


class AssessmentFactoryLiteInvoiceCreationEventService:
    """Record a governed invoice creation event.

    This event is created after invoice creation review is ready. It may record
    that an invoice has been created, but it does not request payment, confirm
    payment, authorize paid work, or start production onboarding.
    """

    EVENT_TYPE = "assessment_factory_lite_invoice_creation_event"
    EVENT_STAGE = "invoice_creation_event"
    RELEASE = "assessment-factory-lite-scope-call-conversion"
    VERSION = "2.3.0"
    PACKAGE_NAME = "Assessment Factory Lite Demo Package"

    def record_event(
        self,
        *,
        invoice_creation_review: dict[str, Any] | None = None,
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
        invoice_creation_context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        invoice_creation_context = invoice_creation_context or {}

        review = (
            invoice_creation_review
            or AssessmentFactoryLiteInvoiceCreationReviewService().build_review(
                contract_execution_event=contract_execution_event,
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
                invoice_context=invoice_context,
            )
        )

        event_identity = self._event_identity(invoice_creation_context)
        source_summary = self._invoice_creation_review_summary(review)
        invoice_record = self._invoice_record(invoice_creation_context)
        delivery_record = self._delivery_record(invoice_creation_context)
        operator_confirmation = self._operator_confirmation(invoice_creation_context)
        event_checklist = self._event_checklist(
            review=review,
            invoice_record=invoice_record,
            delivery_record=delivery_record,
            operator_confirmation=operator_confirmation,
        )
        event_blockers = [
            key for key, value in event_checklist.items() if value is not True
        ]
        event_status = self._event_status(
            review=review,
            invoice_record=invoice_record,
            delivery_record=delivery_record,
            operator_confirmation=operator_confirmation,
            event_blockers=event_blockers,
        )
        event_score = self._event_score(event_checklist)

        return {
            "status": "ok",
            "event_type": self.EVENT_TYPE,
            "package_name": self.PACKAGE_NAME,
            "release": self.RELEASE,
            "version": self.VERSION,
            "event_stage": self.EVENT_STAGE,
            "event_status": event_status,
            "invoice_creation_event_id": event_identity["invoice_creation_event_id"],
            "recorded_at": event_identity["recorded_at"],
            "source_invoice_creation_review": source_summary,
            "invoice_record": invoice_record,
            "delivery_record": delivery_record,
            "operator_confirmation": operator_confirmation,
            "event_checklist": event_checklist,
            "event_blockers": event_blockers,
            "event_score": event_score,
            "invoice_details_review": review.get("invoice_details_review", {}),
            "billing_readiness": review.get("billing_readiness", {}),
            "execution_evidence": review.get("execution_evidence", {}),
            "signature_record": review.get("signature_record", {}),
            "contract_document_review": review.get("contract_document_review", {}),
            "agreement_terms": review.get("agreement_terms", {}),
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
        invoice_creation_context: dict[str, Any],
    ) -> dict[str, str]:
        return {
            "invoice_creation_event_id": invoice_creation_context.get(
                "invoice_creation_event_id",
                "invoice-creation-event-draft-001",
            ),
            "recorded_at": invoice_creation_context.get("recorded_at", "not_recorded"),
        }

    def _invoice_creation_review_summary(self, review: dict[str, Any]) -> dict[str, Any]:
        return {
            "event_type": review.get("event_type"),
            "review_stage": review.get("review_stage"),
            "review_status": review.get("review_status"),
            "release": review.get("release"),
            "version": review.get("version"),
            "invoice_review_id": review.get("invoice_review_id"),
            "prepared_at": review.get("prepared_at"),
            "recommended_action": review.get("recommended_action"),
        }

    def _invoice_record(
        self,
        invoice_creation_context: dict[str, Any],
    ) -> dict[str, Any]:
        invoice_created = invoice_creation_context.get("invoice_created") is True
        invoice_reference = invoice_creation_context.get(
            "invoice_reference",
            "not_recorded",
        )
        invoice_created_at = invoice_creation_context.get(
            "invoice_created_at",
            "not_recorded",
        )
        invoice_amount = invoice_creation_context.get("invoice_amount", "not_recorded")

        return {
            "invoice_created": invoice_created,
            "invoice_reference": invoice_reference,
            "invoice_created_at": invoice_created_at,
            "invoice_amount": invoice_amount,
            "invoice_reference_recorded": invoice_reference != "not_recorded",
            "invoice_created_at_recorded": invoice_created_at != "not_recorded",
            "invoice_amount_recorded": invoice_amount != "not_recorded",
            "invoice_record_is_not_payment_request": True,
            "invoice_record_is_not_payment_confirmation": True,
            "invoice_record_is_not_paid_work_authorization": True,
        }

    def _delivery_record(
        self,
        invoice_creation_context: dict[str, Any],
    ) -> dict[str, Any]:
        invoice_delivered_to_buyer = (
            invoice_creation_context.get("invoice_delivered_to_buyer") is True
        )
        delivery_channel = invoice_creation_context.get(
            "delivery_channel",
            "not_recorded",
        )
        delivery_reference = invoice_creation_context.get(
            "delivery_reference",
            "not_recorded",
        )

        return {
            "invoice_delivered_to_buyer": invoice_delivered_to_buyer,
            "delivery_channel": delivery_channel,
            "delivery_reference": delivery_reference,
            "delivery_channel_recorded": delivery_channel != "not_recorded",
            "delivery_reference_recorded": delivery_reference != "not_recorded",
            "invoice_delivery_is_not_payment_request": True,
        }

    def _operator_confirmation(
        self,
        invoice_creation_context: dict[str, Any],
    ) -> dict[str, Any]:
        return {
            "human_operator_required": True,
            "human_operator_confirmed_invoice_creation": invoice_creation_context.get(
                "human_operator_confirmed_invoice_creation"
            )
            is True,
            "operator_name": invoice_creation_context.get(
                "operator_name",
                "not_recorded",
            ),
            "operator_notes": invoice_creation_context.get("operator_notes", []),
            "payment_requested": False,
            "payment_confirmed": False,
            "paid_assessment_authorized": False,
            "production_onboarding_approved": False,
        }

    def _event_checklist(
        self,
        *,
        review: dict[str, Any],
        invoice_record: dict[str, Any],
        delivery_record: dict[str, Any],
        operator_confirmation: dict[str, Any],
    ) -> dict[str, bool]:
        return {
            "invoice_creation_review_ready": review.get("review_status")
            == "ready_for_invoice_creation",
            "invoice_created": invoice_record["invoice_created"],
            "invoice_reference_recorded": invoice_record["invoice_reference_recorded"],
            "invoice_created_at_recorded": invoice_record[
                "invoice_created_at_recorded"
            ],
            "invoice_amount_recorded": invoice_record["invoice_amount_recorded"],
            "invoice_record_is_not_payment_request": invoice_record[
                "invoice_record_is_not_payment_request"
            ],
            "invoice_record_is_not_payment_confirmation": invoice_record[
                "invoice_record_is_not_payment_confirmation"
            ],
            "invoice_record_is_not_paid_work_authorization": invoice_record[
                "invoice_record_is_not_paid_work_authorization"
            ],
            "invoice_delivered_to_buyer": delivery_record[
                "invoice_delivered_to_buyer"
            ],
            "delivery_channel_recorded": delivery_record["delivery_channel_recorded"],
            "delivery_reference_recorded": delivery_record[
                "delivery_reference_recorded"
            ],
            "invoice_delivery_is_not_payment_request": delivery_record[
                "invoice_delivery_is_not_payment_request"
            ],
            "human_operator_confirmed_invoice_creation": operator_confirmation[
                "human_operator_confirmed_invoice_creation"
            ],
            "payment_not_requested": operator_confirmation["payment_requested"] is False,
            "payment_not_confirmed": operator_confirmation["payment_confirmed"] is False,
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
        invoice_record: dict[str, Any],
        delivery_record: dict[str, Any],
        operator_confirmation: dict[str, Any],
        event_blockers: list[str],
    ) -> str:
        if review.get("review_status") == "blocked":
            return "blocked"

        if review.get("review_status") != "ready_for_invoice_creation":
            return "pending_invoice_creation_review"

        if invoice_record["invoice_created"] is not True:
            return "pending_invoice_creation_confirmation"

        if not (
            invoice_record["invoice_reference_recorded"]
            and invoice_record["invoice_created_at_recorded"]
            and invoice_record["invoice_amount_recorded"]
        ):
            return "pending_invoice_record"

        if not (
            delivery_record["invoice_delivered_to_buyer"]
            and delivery_record["delivery_channel_recorded"]
            and delivery_record["delivery_reference_recorded"]
        ):
            return "pending_invoice_delivery"

        if operator_confirmation["human_operator_confirmed_invoice_creation"] is not True:
            return "pending_operator_confirmation"

        if event_blockers:
            return "pending_invoice_creation_event_review"

        return "invoice_created"

    def _event_score(self, event_checklist: dict[str, bool]) -> dict[str, Any]:
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
            "invoice_creation_recorded": event_status == "invoice_created",
            "invoice_created": event_status == "invoice_created",
            "payment_requested": False,
            "payment_confirmed": False,
            "paid_assessment_authorized": False,
            "production_onboarding_authorized": False,
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
                "invoice_review_notes",
                "billing_readiness_notes",
                "invoice_reference",
                "invoice_delivery_reference",
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
            "invoice_creation_event_is_not_payment_request": True,
            "invoice_creation_event_is_not_payment_confirmation": True,
            "invoice_creation_event_is_not_paid_work_authorization": True,
        }

    def _boundary_notices(self) -> list[str]:
        return [
            "invoice_creation_event_records_invoice_creation_only",
            "invoice_creation_event_does_not_request_payment",
            "invoice_creation_event_does_not_confirm_payment",
            "invoice_creation_event_does_not_authorize_paid_work",
            "invoice_creation_event_does_not_start_production_onboarding",
            "invoice_creation_event_requires_human_operator",
        ]

    def _audit_notes(self, event_status: str) -> list[str]:
        notes = [
            "invoice_creation_event_built",
            "payment_not_requested",
            "payment_not_confirmed",
            "paid_assessment_not_authorized",
            "production_onboarding_not_started",
        ]

        if event_status == "invoice_created":
            notes.append("invoice_creation_event_recorded")
        elif event_status == "pending_invoice_creation_review":
            notes.append("invoice_creation_event_pending_review")
        elif event_status == "pending_invoice_creation_confirmation":
            notes.append("invoice_creation_event_pending_creation_confirmation")
        elif event_status == "pending_invoice_record":
            notes.append("invoice_creation_event_pending_invoice_record")
        elif event_status == "pending_invoice_delivery":
            notes.append("invoice_creation_event_pending_invoice_delivery")
        elif event_status == "pending_operator_confirmation":
            notes.append("invoice_creation_event_pending_operator_confirmation")
        elif event_status == "pending_invoice_creation_event_review":
            notes.append("invoice_creation_event_pending_event_review")
        else:
            notes.append("invoice_creation_event_blocked")

        return notes

    def _next_action(self, event_status: str) -> dict[str, str]:
        if event_status == "invoice_created":
            return {
                "action": "prepare_payment_request_review",
                "operator_instruction": (
                    "Prepare payment request review. Do not confirm payment, "
                    "authorize paid work, or start production onboarding from "
                    "this invoice creation event."
                ),
                "future_action": "build_payment_request_review",
            }

        if event_status == "pending_invoice_creation_review":
            return {
                "action": "complete_invoice_creation_review",
                "operator_instruction": (
                    "Complete invoice creation review before recording invoice "
                    "creation."
                ),
                "future_action": "rerun_invoice_creation_event",
            }

        if event_status == "pending_invoice_creation_confirmation":
            return {
                "action": "confirm_invoice_creation",
                "operator_instruction": (
                    "Confirm that the invoice was actually created before "
                    "recording the event."
                ),
                "future_action": "rerun_invoice_creation_event",
            }

        if event_status == "pending_invoice_record":
            return {
                "action": "record_invoice_reference",
                "operator_instruction": (
                    "Record invoice reference, created_at timestamp, and amount "
                    "before continuing."
                ),
                "future_action": "rerun_invoice_creation_event",
            }

        if event_status == "pending_invoice_delivery":
            return {
                "action": "record_invoice_delivery",
                "operator_instruction": (
                    "Record invoice buyer delivery status, delivery channel, and "
                    "delivery reference before continuing."
                ),
                "future_action": "rerun_invoice_creation_event",
            }

        if event_status == "pending_operator_confirmation":
            return {
                "action": "confirm_operator_invoice_creation_event",
                "operator_instruction": (
                    "A human operator must confirm the invoice creation event before "
                    "moving forward."
                ),
                "future_action": "rerun_invoice_creation_event",
            }

        return {
            "action": "resolve_invoice_creation_event_gaps",
            "operator_instruction": (
                "Resolve invoice creation event blockers before moving forward."
            ),
            "future_action": "rerun_invoice_creation_event",
        }

    def _operator_message(self, event_status: str) -> str:
        if event_status == "invoice_created":
            return (
                "Invoice creation has been recorded. Payment request, payment "
                "confirmation, paid work authorization, and production onboarding "
                "remain blocked."
            )

        if event_status == "pending_invoice_creation_review":
            return (
                "Invoice creation event is pending because invoice creation review "
                "is not ready."
            )

        if event_status == "pending_invoice_creation_confirmation":
            return "Invoice creation event is pending invoice creation confirmation."

        if event_status == "pending_invoice_record":
            return "Invoice creation event is pending invoice record."

        if event_status == "pending_invoice_delivery":
            return "Invoice creation event is pending invoice delivery."

        if event_status == "pending_operator_confirmation":
            return "Invoice creation event is pending operator confirmation."

        if event_status == "pending_invoice_creation_event_review":
            return "Invoice creation event has unresolved event blockers."

        return (
            "Invoice creation event is blocked. Resolve the listed blockers before "
            "moving forward."
        )

    def _recommended_action(self, event_status: str) -> str:
        if event_status == "invoice_created":
            return "prepare_payment_request_review"

        return "resolve_invoice_creation_event_gaps"