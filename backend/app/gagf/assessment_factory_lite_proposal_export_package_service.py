from backend.app.gagf.assessment_factory_lite_formal_proposal_markdown_export_service import (
    AssessmentFactoryLiteFormalProposalMarkdownExportService,
)
from backend.app.gagf.assessment_factory_lite_formal_proposal_pdf_export_service import (
    AssessmentFactoryLiteFormalProposalPDFExportService,
)
from backend.app.gagf.assessment_factory_lite_formal_proposal_pdf_readiness_service import (
    AssessmentFactoryLiteFormalProposalPDFReadinessService,
)


class AssessmentFactoryLiteProposalExportPackageService:
    """Bundle proposal export artifacts into one guarded package object."""

    def __init__(
        self,
        markdown_service: AssessmentFactoryLiteFormalProposalMarkdownExportService | None = None,
        readiness_service: AssessmentFactoryLiteFormalProposalPDFReadinessService | None = None,
        pdf_service: AssessmentFactoryLiteFormalProposalPDFExportService | None = None,
    ):
        self.markdown_service = (
            markdown_service or AssessmentFactoryLiteFormalProposalMarkdownExportService()
        )
        self.readiness_service = (
            readiness_service or AssessmentFactoryLiteFormalProposalPDFReadinessService()
        )
        self.pdf_service = pdf_service or AssessmentFactoryLiteFormalProposalPDFExportService()

    def build_package(
        self,
        export: dict | None = None,
        document: dict | None = None,
        proposal: dict | None = None,
        offer: dict | None = None,
        buyer_context: dict | None = None,
        operator_approval: dict | None = None,
    ) -> dict:
        markdown_export = export or self.markdown_service.export_markdown(
            document=document,
            proposal=proposal,
            offer=offer,
            buyer_context=buyer_context,
        )

        readiness = self.readiness_service.check_readiness(export=markdown_export)

        pdf_export = self.pdf_service.export_pdf(
            export=markdown_export,
            operator_approval=operator_approval,
        )

        package_status = "ready" if readiness["ready_for_pdf"] else "blocked"

        return {
            "status": "ok",
            "package_type": "assessment_factory_lite_proposal_export_package",
            "package_name": "Assessment Factory Lite Demo Package",
            "release": "assessment-factory-lite-proposal-package",
            "version": "2.0.0",
            "package_stage": "proposal_export_package",
            "package_status": package_status,
            "markdown_export": self._markdown_summary(markdown_export),
            "pdf_readiness": self._readiness_summary(readiness),
            "pdf_export": self._pdf_summary(pdf_export),
            "export_manifest": self._export_manifest(
                markdown_export=markdown_export,
                readiness=readiness,
                pdf_export=pdf_export,
            ),
            "operator_approval": pdf_export.get(
                "operator_approval",
                self._default_operator_approval(),
            ),
            "boundary_notices": self._boundary_notices(pdf_export),
            "package_contents": self._package_contents(),
            "blocking_issues": readiness.get("blocking_issues", []),
            "next_action": self._next_action(package_status),
            "operator_message": self._operator_message(package_status),
            "recommended_action": (
                "review_proposal_export_package"
                if package_status == "ready"
                else "resolve_proposal_export_package_gaps"
            ),
        }

    def _markdown_summary(self, markdown_export: dict) -> dict:
        return {
            "export_type": markdown_export.get("export_type"),
            "export_stage": markdown_export.get("export_stage"),
            "format": markdown_export.get("format"),
            "filename": markdown_export.get("filename"),
            "release": markdown_export.get("release"),
            "version": markdown_export.get("version"),
            "recommended_action": markdown_export.get("recommended_action"),
            "section_count": len(markdown_export.get("export_sections", [])),
            "markdown_present": bool(markdown_export.get("markdown")),
        }

    def _readiness_summary(self, readiness: dict) -> dict:
        return {
            "readiness_type": readiness.get("readiness_type"),
            "readiness_stage": readiness.get("readiness_stage"),
            "passed_checks": readiness.get("passed_checks"),
            "failed_checks": readiness.get("failed_checks"),
            "readiness_score": readiness.get("readiness_score"),
            "ready_for_pdf": readiness.get("ready_for_pdf"),
            "blocking_issues": readiness.get("blocking_issues", []),
            "recommended_action": readiness.get("recommended_action"),
        }

    def _pdf_summary(self, pdf_export: dict) -> dict:
        return {
            "status": pdf_export.get("status"),
            "export_type": pdf_export.get("export_type"),
            "export_stage": pdf_export.get("export_stage"),
            "format": pdf_export.get("format"),
            "content_type": pdf_export.get("content_type"),
            "filename": pdf_export.get("filename"),
            "source_markdown_filename": pdf_export.get("source_markdown_filename"),
            "recommended_action": pdf_export.get("recommended_action"),
        }

    def _export_manifest(
        self,
        markdown_export: dict,
        readiness: dict,
        pdf_export: dict,
    ) -> dict:
        return {
            "package_manifest_type": "proposal_export_package_manifest",
            "markdown_filename": markdown_export.get("filename"),
            "pdf_filename": pdf_export.get("filename"),
            "markdown_export_type": markdown_export.get("export_type"),
            "pdf_export_type": pdf_export.get("export_type"),
            "pdf_export_status": pdf_export.get("status"),
            "readiness_score": readiness.get("readiness_score"),
            "ready_for_pdf": readiness.get("ready_for_pdf"),
            "release": "assessment-factory-lite-proposal-package",
            "version": "2.0.0",
            "generated_by": "AssessmentFactoryLiteProposalExportPackageService",
        }

    def _default_operator_approval(self) -> dict:
        return {
            "approval_status": "operator_review_required",
            "scope_approved": False,
            "evidence_boundary_approved": False,
            "commercial_terms_approved": False,
            "buyer_language_approved": False,
        }

    def _boundary_notices(self, pdf_export: dict) -> list[dict]:
        pdf_boundary = pdf_export.get("boundary_notice", {})

        return [
            {
                "notice": "commercial_boundary",
                "message": (
                    "Proposal export package is non-binding until final scope, "
                    "price, payment terms, and buyer-facing language are approved."
                ),
                "required": True,
            },
            {
                "notice": "evidence_boundary",
                "message": (
                    "Proposal export package must use safe, non-sensitive evidence "
                    "only unless a future approved policy expands the boundary."
                ),
                "required": True,
            },
            {
                "notice": "pdf_boundary",
                "message": pdf_boundary.get(
                    "message",
                    "PDF export object is a draft artifact requiring operator review.",
                ),
                "required": True,
            },
            {
                "notice": "constitutional_boundary",
                "message": pdf_boundary.get(
                    "constitutional_rule",
                    "The deterministic GAGF Kernel remains the authoritative decision and verification layer.",
                ),
                "required": True,
            },
        ]

    def _package_contents(self) -> list[str]:
        return [
            "formal_proposal_markdown_export",
            "formal_proposal_pdf_readiness",
            "formal_proposal_pdf_export_object",
            "operator_approval_gate",
            "export_manifest",
            "boundary_notices",
            "blocking_issues",
            "next_action",
        ]

    def _next_action(self, package_status: str) -> dict:
        if package_status == "ready":
            return {
                "action": "review_and_prepare_buyer_delivery_package",
                "operator_instruction": (
                    "Review Markdown export, PDF export object, approval gate, "
                    "manifest, and boundary notices before preparing buyer delivery."
                ),
                "future_action": "prepare_buyer_delivery_package",
            }

        return {
            "action": "resolve_export_package_gaps",
            "operator_instruction": (
                "Resolve readiness or boundary gaps before preparing buyer delivery."
            ),
            "future_action": "rerun_proposal_export_package",
        }

    def _operator_message(self, package_status: str) -> str:
        if package_status == "ready":
            return (
                "Assessment Factory Lite proposal export package is ready for "
                "operator review."
            )

        return (
            "Assessment Factory Lite proposal export package is blocked because "
            "one or more readiness checks failed."
        )