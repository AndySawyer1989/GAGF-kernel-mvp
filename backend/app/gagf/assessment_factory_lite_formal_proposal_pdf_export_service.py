from backend.app.gagf.assessment_factory_lite_formal_proposal_pdf_readiness_service import (
    AssessmentFactoryLiteFormalProposalPDFReadinessService,
)


class AssessmentFactoryLiteFormalProposalPDFExportService:
    """Build a guarded PDF export object from a PDF-ready Markdown proposal export."""

    def __init__(
        self,
        readiness_service: AssessmentFactoryLiteFormalProposalPDFReadinessService | None = None,
    ):
        self.readiness_service = (
            readiness_service or AssessmentFactoryLiteFormalProposalPDFReadinessService()
        )

    def export_pdf(
        self,
        export: dict | None = None,
        document: dict | None = None,
        proposal: dict | None = None,
        offer: dict | None = None,
        buyer_context: dict | None = None,
        operator_approval: dict | None = None,
    ) -> dict:
        readiness = self.readiness_service.check_readiness(
            export=export,
            document=document,
            proposal=proposal,
            offer=offer,
            buyer_context=buyer_context,
        )

        if not readiness["ready_for_pdf"]:
            return self._blocked_export(readiness)

        approval = operator_approval or self._default_operator_approval()
        source_export = readiness["source_export"]
        pdf_filename = self._pdf_filename(source_export.get("filename", ""))

        return {
            "status": "ok",
            "export_type": "assessment_factory_lite_formal_proposal_pdf_export",
            "package_name": "Assessment Factory Lite Demo Package",
            "release": "assessment-factory-lite-proposal-package",
            "version": "2.0.0",
            "export_stage": "formal_proposal_pdf_export",
            "format": "pdf",
            "content_type": "application/pdf",
            "filename": pdf_filename,
            "source_markdown_filename": source_export.get("filename"),
            "readiness": self._readiness_summary(readiness),
            "operator_approval": approval,
            "pdf_document": self._pdf_document(readiness, pdf_filename),
            "export_manifest": self._export_manifest(readiness, pdf_filename),
            "boundary_notice": self._boundary_notice(),
            "operator_message": (
                "Assessment Factory Lite formal proposal PDF export object is "
                "ready for operator review."
            ),
            "recommended_action": "review_formal_proposal_pdf_export",
        }

    def _blocked_export(self, readiness: dict) -> dict:
        return {
            "status": "blocked",
            "export_type": "assessment_factory_lite_formal_proposal_pdf_export",
            "package_name": "Assessment Factory Lite Demo Package",
            "release": "assessment-factory-lite-proposal-package",
            "version": "2.0.0",
            "export_stage": "formal_proposal_pdf_export_blocked",
            "format": "pdf",
            "content_type": "application/pdf",
            "readiness": self._readiness_summary(readiness),
            "blocking_issues": readiness.get("blocking_issues", []),
            "boundary_notice": self._boundary_notice(),
            "operator_message": (
                "Assessment Factory Lite formal proposal PDF export is blocked "
                "because readiness checks failed."
            ),
            "recommended_action": "resolve_formal_proposal_pdf_readiness_gaps",
        }

    def _pdf_filename(self, markdown_filename: str) -> str:
        if markdown_filename.endswith(".md"):
            return markdown_filename[:-3] + ".pdf"

        if markdown_filename:
            return markdown_filename + ".pdf"

        return "assessment-factory-lite-proposal-workflow.pdf"

    def _default_operator_approval(self) -> dict:
        return {
            "approval_status": "operator_review_required",
            "scope_approved": False,
            "evidence_boundary_approved": False,
            "commercial_terms_approved": False,
            "buyer_language_approved": False,
            "approval_note": (
                "PDF export object is generated for review only. Operator must "
                "approve scope, evidence boundary, commercial terms, and buyer-facing "
                "language before sending."
            ),
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

    def _pdf_document(self, readiness: dict, pdf_filename: str) -> dict:
        return {
            "document_kind": "buyer_facing_pdf_proposal_draft",
            "filename": pdf_filename,
            "render_source": "formal_proposal_markdown_export",
            "render_status": "pdf_export_object_ready",
            "page_model": "markdown_sections_to_pdf_pages",
            "required_sections": readiness.get("required_sections", []),
            "watermark": "Draft - Operator Review Required",
            "footer_notice": (
                "Non-binding proposal draft. Final scope, price, and terms require "
                "operator approval."
            ),
        }

    def _export_manifest(self, readiness: dict, pdf_filename: str) -> dict:
        source = readiness.get("source_export", {})

        return {
            "pdf_filename": pdf_filename,
            "source_markdown_filename": source.get("filename"),
            "source_export_type": source.get("export_type"),
            "source_export_stage": source.get("export_stage"),
            "source_release": source.get("release"),
            "source_version": source.get("version"),
            "readiness_score": readiness.get("readiness_score"),
            "ready_for_pdf": readiness.get("ready_for_pdf"),
            "generated_by": "AssessmentFactoryLiteFormalProposalPDFExportService",
        }

    def _boundary_notice(self) -> dict:
        return {
            "non_binding": True,
            "operator_review_required": True,
            "not_a_contract": True,
            "not_an_invoice": True,
            "not_a_compliance_certification": True,
            "not_production_onboarding": True,
            "message": (
                "This PDF export object is a draft artifact. It does not create a "
                "binding quote, sales contract, invoice, legal agreement, production "
                "onboarding plan, or compliance certification."
            ),
            "constitutional_rule": (
                "The deterministic GAGF Kernel remains the authoritative decision "
                "and verification layer."
            ),
        }