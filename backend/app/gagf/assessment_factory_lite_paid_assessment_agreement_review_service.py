from __future__ import annotations

from typing import Any

from backend.app.gagf.assessment_factory_lite_paid_assessment_authorization_package_service import (
    AssessmentFactoryLitePaidAssessmentAuthorizationPackageService,
)


class AssessmentFactoryLitePaidAssessmentAgreementReviewService:
    """Build a governed paid assessment agreement review.

    This review is created after the paid assessment authorization package is
    ready. It reviews agreement readiness only. It does not execute a contract,
    create an invoice, request payment, authorize paid work, or start production
    onboarding.
    """

    EVENT_TYPE = "assessment_factory_lite_paid_assessment_agreement_review"
    REVIEW_STAGE = "paid_assessment_agreement_review"
    RELEASE = "assessment-factory-lite-scope-call-conversion"
    VERSION = "2.3.0"
    PACKAGE_NAME = "Assessment Factory Lite Demo Package"

    def build_review(
        self,
        *,
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
    ) -> dict[str, Any]:
        agreement_context = agreement_context or {}

        authorization_package = (
            paid_assessment_authorization_package
            or AssessmentFactoryLitePaidAssessmentAuthorizationPackageService().build_package(
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
            )
        )

        agreement_identity = self._agreement_identity(agreement_context)
        source_summary = self._authorization_package_summary(authorization_package)
        agreement_terms = self._agreement_terms(agreement_context)
        buyer_acknowledgment = self._buyer_acknowledgment(agreement_context)
        operator_review = self._operator_review(agreement_context)
        review_checklist = self._review_checklist(
            authorization_package=authorization_package,
            agreement_terms=agreement_terms,
            buyer_acknowledgment=buyer_acknowledgment,
            operator_review=operator_review,
        )
        review_blockers = [
            key for key, value in review_checklist.items() if value is not True
        ]
        review_status = self._review_status(
            authorization_package=authorization_package,
            agreement_terms=agreement_terms,
            buyer_acknowledgment=buyer_acknowledgment,
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
            "agreement_review_id": agreement_identity["agreement_review_id"],
            "prepared_at": agreement_identity["prepared_at"],
            "source_paid_assessment_authorization_package": source_summary,
            "agreement_terms": agreement_terms,
            "buyer_acknowledgment": buyer_acknowledgment,
            "operator_review": operator_review,
            "review_checklist": review_checklist,
            "review_blockers": review_blockers,
            "review_score": review_score,
            "buyer_request": authorization_package.get("buyer_request", {}),
            "commercial_review": authorization_package.get("commercial_review", {}),
            "evidence_review": authorization_package.get("evidence_review", {}),
            "human_authorization": authorization_package.get("human_authorization", {}),
            "call_outcome": authorization_package.get("call_outcome", {}),
            "buyer_decision": authorization_package.get("buyer_decision", {}),
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

    def _agreement_identity(self, agreement_context: dict[str, Any]) -> dict[str, str]:
        return {
            "agreement_review_id": agreement_context.get(
                "agreement_review_id",
                "paid-assessment-agreement-review-draft-001",
            ),
            "prepared_at": agreement_context.get("prepared_at", "not_recorded"),
        }

    def _authorization_package_summary(
        self,
        authorization_package: dict[str, Any],
    ) -> dict[str, Any]:
        return {
            "event_type": authorization_package.get("event_type"),
            "package_stage": authorization_package.get("package_stage"),
            "package_status": authorization_package.get("package_status"),
            "release": authorization_package.get("release"),
            "version": authorization_package.get("version"),
            "authorization_id": authorization_package.get("authorization_id"),
            "prepared_at": authorization_package.get("prepared_at"),
            "recommended_action": authorization_package.get("recommended_action"),
        }

    def _agreement_terms(self, agreement_context: dict[str, Any]) -> dict[str, Any]:
        service_scope_reviewed = agreement_context.get("service_scope_reviewed") is True
        price_confirmed = agreement_context.get("price_confirmed") is True
        deliverables_confirmed = agreement_context.get("deliverables_confirmed") is True
        limitations_confirmed = agreement_context.get("limitations_confirmed") is True

        return {
            "service_scope_reviewed": service_scope_reviewed,
            "price_confirmed": price_confirmed,
            "deliverables_confirmed": deliverables_confirmed,
            "limitations_confirmed": limitations_confirmed,
            "agreement_terms_ready": (
                service_scope_reviewed
                and price_confirmed
                and deliverables_confirmed
                and limitations_confirmed
            ),
            "contract_required_before_execution": True,
            "invoice_required_before_payment": True,
            "payment_required_before_paid_work": True,
        }

    def _buyer_acknowledgment(
        self,
        agreement_context: dict[str, Any],
    ) -> dict[str, Any]:
        return {
            "buyer_acknowledged_scope": agreement_context.get(
                "buyer_acknowledged_scope"
            )
            is True,
            "buyer_acknowledged_price": agreement_context.get(
                "buyer_acknowledged_price"
            )
            is True,
            "buyer_acknowledged_non_binding_review": agreement_context.get(
                "buyer_acknowledged_non_binding_review"
            )
            is True,
            "buyer_acknowledgment_ready": (
                agreement_context.get("buyer_acknowledged_scope") is True
                and agreement_context.get("buyer_acknowledged_price") is True
                and agreement_context.get("buyer_acknowledged_non_binding_review")
                is True
            ),
            "buyer_acknowledgment_is_not_signature": True,
            "buyer_acknowledgment_is_not_payment": True,
        }

    def _operator_review(self, agreement_context: dict[str, Any]) -> dict[str, Any]:
        return {
            "human_operator_required": True,
            "agreement_reviewed_by_operator": agreement_context.get(
                "agreement_reviewed_by_operator"
            )
            is True,
            "operator_review_status": agreement_context.get(
                "operator_review_status",
                "operator_review_required",
            ),
            "contract_execution_approved": False,
            "invoice_creation_approved": False,
            "payment_request_approved": False,
            "paid_assessment_authorized": False,
            "production_onboarding_approved": False,
        }

    def _review_checklist(
        self,
        *,
        authorization_package: dict[str, Any],
        agreement_terms: dict[str, Any],
        buyer_acknowledgment: dict[str, Any],
        operator_review: dict[str, Any],
    ) -> dict[str, bool]:
        return {
            "authorization_package_ready": authorization_package.get("package_status")
            == "ready_for_paid_assessment_authorization",
            "agreement_terms_ready": agreement_terms["agreement_terms_ready"],
            "buyer_acknowledgment_ready": buyer_acknowledgment[
                "buyer_acknowledgment_ready"
            ],
            "buyer_acknowledgment_is_not_signature": buyer_acknowledgment[
                "buyer_acknowledgment_is_not_signature"
            ],
            "buyer_acknowledgment_is_not_payment": buyer_acknowledgment[
                "buyer_acknowledgment_is_not_payment"
            ],
            "agreement_reviewed_by_operator": operator_review[
                "agreement_reviewed_by_operator"
            ],
            "contract_not_executed": operator_review["contract_execution_approved"]
            is False,
            "invoice_not_created": operator_review["invoice_creation_approved"]
            is False,
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
        authorization_package: dict[str, Any],
        agreement_terms: dict[str, Any],
        buyer_acknowledgment: dict[str, Any],
        operator_review: dict[str, Any],
        review_blockers: list[str],
    ) -> str:
        if authorization_package.get("package_status") == "blocked":
            return "blocked"

        if (
            authorization_package.get("package_status")
            != "ready_for_paid_assessment_authorization"
        ):
            return "pending_authorization_package"

        if agreement_terms["agreement_terms_ready"] is not True:
            return "pending_agreement_terms"

        if buyer_acknowledgment["buyer_acknowledgment_ready"] is not True:
            return "pending_buyer_acknowledgment"

        if operator_review["agreement_reviewed_by_operator"] is not True:
            return "pending_operator_review"

        if review_blockers:
            return "pending_agreement_review"

        return "ready_for_agreement_execution_review"

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
            "agreement_review_ready": review_status
            == "ready_for_agreement_execution_review",
            "contract_created": False,
            "contract_executed": False,
            "invoice_created": False,
            "payment_requested": False,
            "paid_assessment_authorized": False,
            "production_onboarding_authorized": False,
            "requires_separate_contract_execution": True,
            "requires_separate_invoice": True,
            "requires_separate_payment_confirmation": True,
            "requires_final_paid_work_authorization": True,
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
            "agreement_review_is_not_execution": True,
        }

    def _boundary_notices(self) -> list[str]:
        return [
            "paid_assessment_agreement_review_does_not_execute_contract",
            "paid_assessment_agreement_review_does_not_create_invoice",
            "paid_assessment_agreement_review_does_not_request_payment",
            "paid_assessment_agreement_review_does_not_authorize_paid_work",
            "paid_assessment_agreement_review_does_not_start_production_onboarding",
            "paid_assessment_agreement_review_requires_human_operator",
        ]

    def _audit_notes(self, review_status: str) -> list[str]:
        notes = [
            "paid_assessment_agreement_review_built",
            "agreement_review_is_not_contract_execution",
            "invoice_not_created",
            "payment_not_requested",
            "paid_assessment_not_authorized",
            "production_onboarding_not_started",
        ]

        if review_status == "ready_for_agreement_execution_review":
            notes.append("paid_assessment_agreement_review_ready")
        elif review_status == "pending_authorization_package":
            notes.append("paid_assessment_agreement_review_pending_authorization_package")
        elif review_status == "pending_agreement_terms":
            notes.append("paid_assessment_agreement_review_pending_terms")
        elif review_status == "pending_buyer_acknowledgment":
            notes.append("paid_assessment_agreement_review_pending_buyer_acknowledgment")
        elif review_status == "pending_operator_review":
            notes.append("paid_assessment_agreement_review_pending_operator_review")
        elif review_status == "pending_agreement_review":
            notes.append("paid_assessment_agreement_review_pending_review")
        else:
            notes.append("paid_assessment_agreement_review_blocked")

        return notes

    def _next_action(self, review_status: str) -> dict[str, str]:
        if review_status == "ready_for_agreement_execution_review":
            return {
                "action": "prepare_contract_execution_review",
                "operator_instruction": (
                    "Prepare contract execution review. Do not execute a contract, "
                    "create an invoice, request payment, authorize paid work, or "
                    "start production onboarding from this agreement review."
                ),
                "future_action": "build_contract_execution_review",
            }

        if review_status == "pending_authorization_package":
            return {
                "action": "complete_paid_assessment_authorization_package",
                "operator_instruction": (
                    "Complete the paid assessment authorization package before "
                    "building agreement review."
                ),
                "future_action": "rerun_paid_assessment_agreement_review",
            }

        if review_status == "pending_agreement_terms":
            return {
                "action": "complete_agreement_terms_review",
                "operator_instruction": (
                    "Review scope, price, deliverables, and limitations before "
                    "continuing."
                ),
                "future_action": "rerun_paid_assessment_agreement_review",
            }

        if review_status == "pending_buyer_acknowledgment":
            return {
                "action": "confirm_buyer_agreement_acknowledgment",
                "operator_instruction": (
                    "Confirm buyer acknowledgment of scope, price, and non-binding "
                    "review before continuing."
                ),
                "future_action": "rerun_paid_assessment_agreement_review",
            }

        if review_status == "pending_operator_review":
            return {
                "action": "complete_operator_agreement_review",
                "operator_instruction": (
                    "A human operator must review the agreement before moving "
                    "toward contract execution review."
                ),
                "future_action": "rerun_paid_assessment_agreement_review",
            }

        if review_status == "pending_agreement_review":
            return {
                "action": "resolve_agreement_review_gaps",
                "operator_instruction": (
                    "Resolve agreement review blockers before moving toward "
                    "contract execution review."
                ),
                "future_action": "rerun_paid_assessment_agreement_review",
            }

        return {
            "action": "resolve_paid_assessment_agreement_review_gaps",
            "operator_instruction": (
                "Resolve paid assessment agreement review blockers before moving "
                "forward."
            ),
            "future_action": "rerun_paid_assessment_agreement_review",
        }

    def _operator_message(self, review_status: str) -> str:
        if review_status == "ready_for_agreement_execution_review":
            return (
                "Paid assessment agreement review is ready for contract execution "
                "review. Contract execution, invoice creation, payment request, "
                "paid work authorization, and production onboarding remain blocked."
            )

        if review_status == "pending_authorization_package":
            return (
                "Paid assessment agreement review is pending because the paid "
                "assessment authorization package is not ready."
            )

        if review_status == "pending_agreement_terms":
            return "Paid assessment agreement review is pending agreement terms."

        if review_status == "pending_buyer_acknowledgment":
            return (
                "Paid assessment agreement review is pending buyer acknowledgment."
            )

        if review_status == "pending_operator_review":
            return "Paid assessment agreement review is pending operator review."

        if review_status == "pending_agreement_review":
            return (
                "Paid assessment agreement review has unresolved review blockers."
            )

        return (
            "Paid assessment agreement review is blocked. Resolve the listed "
            "blockers before moving forward."
        )

    def _recommended_action(self, review_status: str) -> str:
        if review_status == "ready_for_agreement_execution_review":
            return "prepare_contract_execution_review"

        return "resolve_paid_assessment_agreement_review_gaps"