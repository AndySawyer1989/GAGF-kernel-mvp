from backend.app.gagf.assessment_factory_lite_buyer_delivery_package_service import (
    AssessmentFactoryLiteBuyerDeliveryPackageService,
)


class AssessmentFactoryLiteBuyerDeliveryMessageService:
    """Build an operator-reviewed buyer delivery message draft."""

    def __init__(
        self,
        delivery_package_service: AssessmentFactoryLiteBuyerDeliveryPackageService | None = None,
    ):
        self.delivery_package_service = (
            delivery_package_service or AssessmentFactoryLiteBuyerDeliveryPackageService()
        )

    def build_message(
        self,
        delivery_package: dict | None = None,
        export_package: dict | None = None,
        export: dict | None = None,
        document: dict | None = None,
        proposal: dict | None = None,
        offer: dict | None = None,
        buyer_context: dict | None = None,
        operator_approval: dict | None = None,
        message_context: dict | None = None,
    ) -> dict:
        source_delivery_package = (
            delivery_package
            or self.delivery_package_service.build_delivery_package(
                export_package=export_package,
                export=export,
                document=document,
                proposal=proposal,
                offer=offer,
                buyer_context=buyer_context,
                operator_approval=operator_approval,
            )
        )

        context = message_context or {}
        recipient_role = context.get("recipient_role", "operations_leader")
        sender_name = context.get("sender_name", "Assessment Factory Lite Operator")
        delivery_channel = context.get("delivery_channel", "email_draft")

        message_status = self._message_status(source_delivery_package)

        return {
            "status": "ok",
            "message_type": "assessment_factory_lite_buyer_delivery_message",
            "package_name": "Assessment Factory Lite Demo Package",
            "release": "assessment-factory-lite-proposal-export-package",
            "version": "2.1.0",
            "message_stage": "buyer_delivery_message_draft",
            "message_status": message_status,
            "delivery_channel": delivery_channel,
            "recipient": self._recipient(recipient_role),
            "sender": self._sender(sender_name),
            "subject": self._subject(source_delivery_package),
            "message_body": self._message_body(
                source_delivery_package=source_delivery_package,
                sender_name=sender_name,
            ),
            "source_delivery_package": self._source_delivery_package(
                source_delivery_package
            ),
            "delivery_summary": self._delivery_summary(source_delivery_package),
            "attachments": self._attachments(source_delivery_package),
            "operator_review": self._operator_review(source_delivery_package),
            "boundary_notices": source_delivery_package.get("boundary_notices", []),
            "send_policy": self._send_policy(source_delivery_package),
            "next_action": self._next_action(message_status),
            "operator_message": self._operator_message(message_status),
            "recommended_action": (
                "review_buyer_delivery_message"
                if message_status in {"draft_ready", "send_ready_draft"}
                else "resolve_buyer_delivery_message_gaps"
            ),
        }

    def _message_status(self, delivery_package: dict) -> str:
        delivery_status = delivery_package.get("delivery_status")

        if delivery_status == "send_ready":
            return "send_ready_draft"

        if delivery_status == "review_ready":
            return "draft_ready"

        return "blocked"

    def _recipient(self, recipient_role: str) -> dict:
        return {
            "recipient_type": "buyer_role",
            "recipient_role": recipient_role,
            "email_required": True,
            "email_status": "operator_to_provide",
        }

    def _sender(self, sender_name: str) -> dict:
        return {
            "sender_type": "operator",
            "sender_name": sender_name,
            "signature_required": True,
        }

    def _subject(self, delivery_package: dict) -> str:
        manifest = delivery_package.get("delivery_manifest", {})
        pdf_filename = manifest.get("pdf_filename", "proposal export package")

        return f"Assessment Factory Lite Proposal Package Ready for Review - {pdf_filename}"

    def _message_body(
        self,
        source_delivery_package: dict,
        sender_name: str,
    ) -> str:
        delivery_status = source_delivery_package.get("delivery_status")
        manifest = source_delivery_package.get("delivery_manifest", {})
        pdf_filename = manifest.get("pdf_filename", "proposal export package")

        greeting = "Hello,"
        intro = (
            "Attached is the Assessment Factory Lite proposal package prepared "
            "for your review."
        )
        scope = (
            "This package is based on a bounded paid-assessment workflow and is "
            "intended to support review of scope, evidence boundaries, commercial "
            "terms, and next steps."
        )
        boundary = (
            "This proposal package is non-binding and does not create a contract, "
            "invoice, compliance certification, or production onboarding commitment."
        )
        action = (
            "Please review the proposal package and confirm whether you would like "
            "to discuss the bounded assessment scope and next steps."
        )

        if delivery_status != "send_ready":
            action = (
                "This draft still requires operator approval before it can be sent "
                "as buyer-facing material."
            )

        closing = f"Thank you,\n{sender_name}"

        return "\n\n".join(
            [
                greeting,
                intro,
                f"Primary proposal artifact: {pdf_filename}",
                scope,
                boundary,
                action,
                closing,
            ]
        )

    def _source_delivery_package(self, delivery_package: dict) -> dict:
        return {
            "delivery_type": delivery_package.get("delivery_type"),
            "delivery_stage": delivery_package.get("delivery_stage"),
            "delivery_status": delivery_package.get("delivery_status"),
            "release": delivery_package.get("release"),
            "version": delivery_package.get("version"),
            "recommended_action": delivery_package.get("recommended_action"),
        }

    def _delivery_summary(self, delivery_package: dict) -> dict:
        send_readiness = delivery_package.get("send_readiness", {})

        return {
            "send_ready": send_readiness.get("send_ready"),
            "review_ready": send_readiness.get("review_ready"),
            "blocked": send_readiness.get("blocked"),
            "blocker_count": send_readiness.get("blocker_count"),
            "delivery_blockers": delivery_package.get("delivery_blockers", []),
        }

    def _attachments(self, delivery_package: dict) -> list[dict]:
        deliverables = delivery_package.get("buyer_facing_deliverables", [])

        attachments = []

        for deliverable in deliverables:
            attachments.append(
                {
                    "attachment": deliverable.get("deliverable"),
                    "filename": deliverable.get("filename"),
                    "format": deliverable.get("format"),
                    "ready": deliverable.get("ready"),
                    "buyer_facing": deliverable.get("buyer_facing"),
                    "attachment_status": (
                        "operator_review_required"
                        if deliverable.get("ready")
                        else "not_ready"
                    ),
                }
            )

        return attachments

    def _operator_review(self, delivery_package: dict) -> dict:
        approval = delivery_package.get("operator_approval", {})
        blockers = delivery_package.get("delivery_blockers", [])

        return {
            "approval_status": approval.get("approval_status"),
            "scope_approved": approval.get("scope_approved", False),
            "evidence_boundary_approved": approval.get(
                "evidence_boundary_approved",
                False,
            ),
            "commercial_terms_approved": approval.get(
                "commercial_terms_approved",
                False,
            ),
            "buyer_language_approved": approval.get(
                "buyer_language_approved",
                False,
            ),
            "delivery_blockers": blockers,
            "review_required": bool(blockers),
        }

    def _send_policy(self, delivery_package: dict) -> dict:
        send_readiness = delivery_package.get("send_readiness", {})

        return {
            "send_allowed": send_readiness.get("send_ready") is True,
            "send_blocked_reason": (
                ""
                if send_readiness.get("send_ready") is True
                else "Operator approval and delivery readiness are required before sending."
            ),
            "send_rule": send_readiness.get(
                "send_rule",
                "Buyer delivery requires operator approval.",
            ),
            "automated_send_allowed": False,
            "requires_human_operator": True,
        }

    def _next_action(self, message_status: str) -> dict:
        if message_status == "send_ready_draft":
            return {
                "action": "review_and_send_buyer_delivery_message",
                "operator_instruction": (
                    "Review the buyer delivery message, verify recipient details, "
                    "confirm approved attachments, and send only through an approved "
                    "human-operated channel."
                ),
                "future_action": "record_buyer_delivery_event",
            }

        if message_status == "draft_ready":
            return {
                "action": "complete_operator_approval_before_sending",
                "operator_instruction": (
                    "Complete operator approvals before sending this buyer delivery "
                    "message draft."
                ),
                "future_action": "review_and_send_buyer_delivery_message",
            }

        return {
            "action": "resolve_buyer_delivery_message_gaps",
            "operator_instruction": (
                "Resolve delivery package blockers before preparing a buyer-facing "
                "message."
            ),
            "future_action": "rerun_buyer_delivery_message",
        }

    def _operator_message(self, message_status: str) -> str:
        if message_status == "send_ready_draft":
            return (
                "Assessment Factory Lite buyer delivery message draft is ready "
                "for final human review and sending."
            )

        if message_status == "draft_ready":
            return (
                "Assessment Factory Lite buyer delivery message draft is ready "
                "for operator review but not approved for sending."
            )

        return (
            "Assessment Factory Lite buyer delivery message is blocked because "
            "delivery package requirements are not satisfied."
        )