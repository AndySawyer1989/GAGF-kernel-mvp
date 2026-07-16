from backend.app.gagf.assessment_factory_lite_formal_proposal_markdown_export_service import (
    AssessmentFactoryLiteFormalProposalMarkdownExportService,
)


class AssessmentFactoryLiteFormalProposalPDFReadinessService:
    """Check whether a formal proposal Markdown export is ready for future PDF generation."""

    def __init__(
        self,
        markdown_service: AssessmentFactoryLiteFormalProposalMarkdownExportService | None = None,
    ):
        self.markdown_service = (
            markdown_service or AssessmentFactoryLiteFormalProposalMarkdownExportService()
        )

    def check_readiness(
        self,
        export: dict | None = None,
        document: dict | None = None,
        proposal: dict | None = None,
        offer: dict | None = None,
        buyer_context: dict | None = None,
    ) -> dict:
        source_export = export or self.markdown_service.export_markdown(
            document=document,
            proposal=proposal,
            offer=offer,
            buyer_context=buyer_context,
        )

        markdown = source_export.get("markdown", "")
        checks = self._checks(source_export, markdown)
        passed = [check for check in checks if check["passed"]]
        failed = [check for check in checks if not check["passed"]]
        readiness_score = round(len(passed) / len(checks), 2) if checks else 0.0
        ready_for_pdf = readiness_score == 1.0

        return {
            "status": "ok",
            "readiness_type": "assessment_factory_lite_formal_proposal_pdf_readiness",
            "package_name": "Assessment Factory Lite Demo Package",
            "release": "assessment-factory-lite-proposal-package",
            "version": "2.0.0",
            "readiness_stage": "formal_proposal_pdf_readiness_check",
            "source_export": self._source_export(source_export),
            "required_sections": self._required_sections(),
            "checks": checks,
            "passed_checks": len(passed),
            "failed_checks": len(failed),
            "readiness_score": readiness_score,
            "ready_for_pdf": ready_for_pdf,
            "recommendation": self._recommendation(ready_for_pdf),
            "blocking_issues": [check["check"] for check in failed],
            "operator_message": self._operator_message(ready_for_pdf),
            "recommended_action": (
                "prepare_formal_proposal_pdf_export"
                if ready_for_pdf
                else "resolve_formal_proposal_pdf_readiness_gaps"
            ),
        }

    def _checks(self, export: dict, markdown: str) -> list[dict]:
        return [
            self._check(
                "export_contract_present",
                export.get("export_type")
                == "assessment_factory_lite_formal_proposal_markdown_export",
                "Markdown export contract must identify the formal proposal export type.",
            ),
            self._check(
                "export_format_is_markdown",
                export.get("format") == "markdown",
                "Source export must be Markdown before PDF conversion.",
            ),
            self._check(
                "filename_present",
                bool(export.get("filename", "").endswith(".md")),
                "Markdown filename must be present before PDF naming can be derived.",
            ),
            self._check(
                "required_sections_present",
                all(section in markdown for section in self._markdown_headings()),
                "All required Markdown headings must be present.",
            ),
            self._check(
                "commercial_terms_present",
                "## Commercial Terms" in markdown
                and "Binding quote: False" in markdown
                and "operator_to_finalize" in markdown,
                "Commercial terms must remain non-binding and operator-finalized.",
            ),
            self._check(
                "evidence_boundary_present",
                "## Evidence Boundary" in markdown
                and "safe_non_sensitive_workflow_evidence" in markdown
                and "Certification claims allowed: False" in markdown,
                "Evidence boundary must be visible before PDF export.",
            ),
            self._check(
                "approval_requirements_present",
                "## Approval Requirements" in markdown
                and "evidence_boundary_approval" in markdown
                and "commercial_terms_approval" in markdown
                and "buyer_scope_acknowledgement" in markdown,
                "Approval requirements must be visible before PDF export.",
            ),
            self._check(
                "operator_notes_present",
                "## Operator Notes" in markdown
                and "review_scope_before_sending" in markdown
                and "review_evidence_boundary_before_sending" in markdown
                and "review_terms_before_sending" in markdown,
                "Operator review notes must be visible before PDF export.",
            ),
            self._check(
                "boundary_notice_present",
                "## Boundary Notice" in markdown
                and "not a binding quote, sales contract, invoice" in markdown
                and "GAGF Kernel remains the authoritative decision" in markdown,
                "Boundary notice must be visible before PDF export.",
            ),
        ]

    def _check(self, name: str, passed: bool, description: str) -> dict:
        return {
            "check": name,
            "passed": bool(passed),
            "description": description,
        }

    def _required_sections(self) -> list[str]:
        return [
            "proposal_metadata",
            "buyer_summary",
            "problem_statement",
            "assessment_scope",
            "evidence_boundary",
            "deliverables",
            "timeline",
            "commercial_terms",
            "assumptions",
            "approval_requirements",
            "exclusions",
            "operator_notes",
            "next_action",
            "boundary_notice",
        ]

    def _markdown_headings(self) -> list[str]:
        return [
            "## Proposal Metadata",
            "## Buyer Summary",
            "## Problem Statement",
            "## Assessment Scope",
            "## Evidence Boundary",
            "## Deliverables",
            "## Timeline",
            "## Commercial Terms",
            "## Assumptions",
            "## Approval Requirements",
            "## Exclusions",
            "## Operator Notes",
            "## Next Action",
            "## Boundary Notice",
        ]

    def _source_export(self, export: dict) -> dict:
        return {
            "export_type": export.get("export_type"),
            "export_stage": export.get("export_stage"),
            "format": export.get("format"),
            "filename": export.get("filename"),
            "release": export.get("release"),
            "version": export.get("version"),
            "recommended_action": export.get("recommended_action"),
        }

    def _recommendation(self, ready_for_pdf: bool) -> str:
        if ready_for_pdf:
            return (
                "Markdown export is ready for operator-reviewed PDF generation."
            )

        return (
            "Markdown export is not ready for PDF generation. Resolve blocking "
            "readiness issues before creating a buyer-facing PDF."
        )

    def _operator_message(self, ready_for_pdf: bool) -> str:
        if ready_for_pdf:
            return (
                "Assessment Factory Lite formal proposal Markdown export passed "
                "PDF readiness checks."
            )

        return (
            "Assessment Factory Lite formal proposal Markdown export has blocking "
            "PDF readiness gaps."
        )