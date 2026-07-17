from backend.app.gagf.assessment_factory_lite_proposal_export_package_service import (
    AssessmentFactoryLiteProposalExportPackageService,
)


class AssessmentFactoryLiteBuyerDeliveryPackageService:
    """Build a buyer delivery package object from a proposal export package."""

    def __init__(
        self,
        export_package_service: AssessmentFactoryLiteProposalExportPackageService | None = None,
    ):
        self.export_package_service = (
            export_package_service or AssessmentFactoryLiteProposalExportPackageService()
        )

    def build_delivery_package(
        self,
        export_package: dict | None = None,
        export: dict | None = None,
        document: dict | None = None,
        proposal: dict | None = None,
        offer: dict | None = None,
        buyer_context: dict | None = None,
        operator_approval: dict | None = None,
    ) -> dict:
        source_package = export_package or self.export_package_service.build_package(
            export=export,
            document=document,
            proposal=proposal,
            offer=offer,
            buyer_context=buyer_context,
            operator_approval=operator_approval,
        )

        delivery_status = self._delivery_status(source_package)
        checklist = self._delivery_checklist(source_package)
        blockers = self._delivery_blockers(source_package, checklist)

        return {
            "status": "ok",
            "delivery_type": "assessment_factory_lite_buyer_delivery_package",
            "package_name": "Assessment Factory Lite Demo Package",
            "release": "assessment-factory-lite-proposal-export-package",
            "version": "2.1.0",
            "delivery_stage": "buyer_delivery_package",
            "delivery_status": delivery_status,
            "source_export_package": self._source_export_package(source_package),
            "buyer_facing_deliverables": self._buyer_facing_deliverables(source_package),
            "operator_approval": source_package.get(
                "operator_approval",
                self._default_operator_approval(),
            ),
            "delivery_checklist": checklist,
            "delivery_blockers": blockers,
            "boundary_notices": source_package.get("boundary_notices", []),
            "send_readiness": self._send_readiness(delivery_status, blockers),
            "delivery_manifest": self._delivery_manifest(source_package, delivery_status),
            "next_action": self._next_action(delivery_status),
            "operator_message": self._operator_message(delivery_status),
            "recommended_action": (
                "review_buyer_delivery_package"
                if delivery_status == "review_ready"
                else "resolve_buyer_delivery_package_gaps"
            ),
        }

    def _delivery_status(self, package: dict) -> str:
        if package.get("package_status") != "ready":
            return "blocked"

        approval = package.get("operator_approval", {})

        approval_complete = all(
            approval.get(field) is True
            for field in [
                "scope_approved",
                "evidence_boundary_approved",
                "commercial_terms_approved",
                "buyer_language_approved",
            ]
        )

        if approval_complete:
            return "send_ready"

        return "review_ready"

    def _source_export_package(self, package: dict) -> dict:
        return {
            "package_type": package.get("package_type"),
            "package_stage": package.get("package_stage"),
            "package_status": package.get("package_status"),
            "release": package.get("release"),
            "version": package.get("version"),
            "recommended_action": package.get("recommended_action"),
        }

    def _buyer_facing_deliverables(self, package: dict) -> list[dict]:
        markdown = package.get("markdown_export", {})
        pdf = package.get("pdf_export", {})
        manifest = package.get("export_manifest", {})

        return [
            {
                "deliverable": "proposal_markdown_export",
                "format": markdown.get("format"),
                "filename": markdown.get("filename"),
                "ready": bool(markdown.get("markdown_present")),
                "buyer_facing": False,
                "review_note": (
                    "Markdown export is an operator-review source artifact unless "
                    "explicitly approved for buyer sharing."
                ),
            },
            {
                "deliverable": "proposal_pdf_export_object",
                "format": pdf.get("format"),
                "filename": pdf.get("filename"),
                "ready": pdf.get("status") == "ok",
                "buyer_facing": False,
                "review_note": (
                    "PDF export object is a draft representation and not a binary "
                    "PDF file yet."
                ),
            },
            {
                "deliverable": "proposal_export_manifest",
                "format": "json",
                "filename": manifest.get("pdf_filename"),
                "ready": manifest.get("ready_for_pdf") is True,
                "buyer_facing": False,
                "review_note": (
                    "Export manifest is internal package metadata for operator review."
                ),
            },
        ]

    def _delivery_checklist(self, package: dict) -> list[dict]:
        approval = package.get("operator_approval", {})

        return [
            {
                "check": "export_package_ready",
                "passed": package.get("package_status") == "ready",
                "description": "Proposal export package must be ready.",
            },
            {
                "check": "markdown_export_present",
                "passed": package.get("markdown_export", {}).get("markdown_present") is True,
                "description": "Markdown proposal export must be present.",
            },
            {
                "check": "pdf_export_object_ready",
                "passed": package.get("pdf_export", {}).get("status") == "ok",
                "description": "PDF export object must be ready.",
            },
            {
                "check": "readiness_passed",
                "passed": package.get("pdf_readiness", {}).get("ready_for_pdf") is True,
                "description": "PDF readiness must pass before delivery review.",
            },
            {
                "check": "scope_approved",
                "passed": approval.get("scope_approved") is True,
                "description": "Operator must approve the delivery scope.",
            },
            {
                "check": "evidence_boundary_approved",
                "passed": approval.get("evidence_boundary_approved") is True,
                "description": "Operator must approve the evidence boundary.",
            },
            {
                "check": "commercial_terms_approved",
                "passed": approval.get("commercial_terms_approved") is True,
                "description": "Operator must approve commercial terms.",
            },
            {
                "check": "buyer_language_approved",
                "passed": approval.get("buyer_language_approved") is True,
                "description": "Operator must approve buyer-facing language.",
            },
        ]

    def _delivery_blockers(self, package: dict, checklist: list[dict]) -> list[str]:
        blockers = list(package.get("blocking_issues", []))
        blockers.extend(check["check"] for check in checklist if not check["passed"])
        return sorted(set(blockers))

    def _send_readiness(self, delivery_status: str, blockers: list[str]) -> dict:
        return {
            "send_ready": delivery_status == "send_ready",
            "review_ready": delivery_status == "review_ready",
            "blocked": delivery_status == "blocked",
            "blocker_count": len(blockers),
            "requires_operator_approval": delivery_status != "send_ready",
            "send_rule": (
                "Buyer delivery is allowed only when export package is ready and "
                "scope, evidence boundary, commercial terms, and buyer language "
                "are operator-approved."
            ),
        }

    def _delivery_manifest(self, package: dict, delivery_status: str) -> dict:
        export_manifest = package.get("export_manifest", {})

        return {
            "delivery_manifest_type": "buyer_delivery_package_manifest",
            "source_package_type": package.get("package_type"),
            "source_package_status": package.get("package_status"),
            "delivery_status": delivery_status,
            "markdown_filename": export_manifest.get("markdown_filename"),
            "pdf_filename": export_manifest.get("pdf_filename"),
            "ready_for_pdf": export_manifest.get("ready_for_pdf"),
            "readiness_score": export_manifest.get("readiness_score"),
            "release": "assessment-factory-lite-proposal-export-package",
            "version": "2.1.0",
            "generated_by": "AssessmentFactoryLiteBuyerDeliveryPackageService",
        }

    def _default_operator_approval(self) -> dict:
        return {
            "approval_status": "operator_review_required",
            "scope_approved": False,
            "evidence_boundary_approved": False,
            "commercial_terms_approved": False,
            "buyer_language_approved": False,
        }

    def _next_action(self, delivery_status: str) -> dict:
        if delivery_status == "send_ready":
            return {
                "action": "prepare_buyer_delivery_message",
                "operator_instruction": (
                    "Prepare the buyer-facing delivery message and verify final "
                    "send channel before delivery."
                ),
                "future_action": "generate_buyer_delivery_message",
            }

        if delivery_status == "review_ready":
            return {
                "action": "complete_operator_delivery_approval",
                "operator_instruction": (
                    "Review deliverables, approve scope, evidence boundary, "
                    "commercial terms, and buyer-facing language before delivery."
                ),
                "future_action": "prepare_buyer_delivery_message",
            }

        return {
            "action": "resolve_buyer_delivery_package_gaps",
            "operator_instruction": (
                "Resolve export package or readiness gaps before buyer delivery review."
            ),
            "future_action": "rerun_buyer_delivery_package",
        }

    def _operator_message(self, delivery_status: str) -> str:
        if delivery_status == "send_ready":
            return (
                "Assessment Factory Lite buyer delivery package is send-ready "
                "after operator approval."
            )

        if delivery_status == "review_ready":
            return (
                "Assessment Factory Lite buyer delivery package is ready for "
                "operator approval review."
            )

        return (
            "Assessment Factory Lite buyer delivery package is blocked because "
            "one or more export or readiness checks failed."
        )