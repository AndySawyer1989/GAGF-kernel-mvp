from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from enum import Enum
from typing import Any

from backend.app.gagf.governance_assessment_executive_projection import (
    ExecutiveAssessmentProjection,
)


ASSESSMENT_REPORT_PACKAGE_VERSION = "1.0.0"


class AssessmentReportPackageError(ValueError):
    """Raised when a client report package cannot be generated."""


class ReportSectionKind(str, Enum):
    EXECUTIVE_SUMMARY = "executive-summary"
    ASSESSMENT_SCOPE = "assessment-scope"
    EVIDENCE_QUALITY = "evidence-quality"
    GOVERNANCE_DEBT = "governance-debt"
    KEY_FINDINGS = "key-findings"
    PRIORITIES = "priorities"
    ROADMAP = "roadmap"
    EVIDENCE_APPENDIX = "evidence-appendix"


def canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )


def sha256_text(value: str) -> str:
    return hashlib.sha256(
        value.encode("utf-8")
    ).hexdigest()


def require_text(value: str, field_name: str) -> str:
    normalized = value.strip()

    if not normalized:
        raise AssessmentReportPackageError(
            f"{field_name} must not be empty"
        )

    return normalized


@dataclass(frozen=True, slots=True)
class ReportSection:
    section_id: str
    kind: ReportSectionKind
    title: str
    order: int
    markdown: str

    def __post_init__(self) -> None:
        if self.order < 1:
            raise AssessmentReportPackageError(
                "section order must be at least 1"
            )

        require_text(self.section_id, "section_id")
        require_text(self.title, "title")
        require_text(self.markdown, "markdown")

    def to_dict(self) -> dict[str, Any]:
        return {
            "section_id": self.section_id,
            "kind": self.kind.value,
            "title": self.title,
            "order": self.order,
            "markdown": self.markdown,
        }


@dataclass(frozen=True, slots=True)
class ClientReportManifest:
    report_id: str
    tenant_id: str
    client_id: str
    engagement_id: str
    assessment_id: str
    assessment_name: str
    section_count: int
    section_ids: tuple[str, ...]
    source_commitments: dict[str, str]
    markdown_hash: str
    package_hash: str
    schema_version: str = ASSESSMENT_REPORT_PACKAGE_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "report_id": self.report_id,
            "tenant_id": self.tenant_id,
            "client_id": self.client_id,
            "engagement_id": self.engagement_id,
            "assessment_id": self.assessment_id,
            "assessment_name": self.assessment_name,
            "section_count": self.section_count,
            "section_ids": list(self.section_ids),
            "source_commitments": dict(
                self.source_commitments
            ),
            "markdown_hash": self.markdown_hash,
            "package_hash": self.package_hash,
            "schema_version": self.schema_version,
        }


@dataclass(frozen=True, slots=True)
class ClientReadyReportPackage:
    report_id: str
    hierarchy_key: str
    title: str
    sections: tuple[ReportSection, ...]
    markdown: str
    manifest: ClientReportManifest

    def to_dict(self) -> dict[str, Any]:
        return {
            "report_id": self.report_id,
            "hierarchy_key": self.hierarchy_key,
            "title": self.title,
            "sections": [
                section.to_dict()
                for section in self.sections
            ],
            "markdown": self.markdown,
            "manifest": self.manifest.to_dict(),
        }


class GovernanceAssessmentReportPackageService:
    def build(
        self,
        *,
        projection: ExecutiveAssessmentProjection,
        client_display_name: str,
        prepared_by: str,
    ) -> ClientReadyReportPackage:
        client_name = require_text(
            client_display_name,
            "client_display_name",
        )
        preparer = require_text(prepared_by, "prepared_by")

        sections = self._build_sections(
            projection=projection,
            client_display_name=client_name,
            prepared_by=preparer,
        )

        section_ids = tuple(
            section.section_id
            for section in sections
        )

        if len(section_ids) != len(set(section_ids)):
            raise AssessmentReportPackageError(
                "report sections contain duplicate identifiers"
            )

        expected_orders = tuple(
            range(1, len(sections) + 1)
        )
        actual_orders = tuple(
            section.order
            for section in sections
        )

        if actual_orders != expected_orders:
            raise AssessmentReportPackageError(
                "report sections are not sequentially ordered"
            )

        title = (
            f"{projection.assessment_name} — {client_name}"
        )

        markdown = self._render_markdown(
            title=title,
            prepared_by=preparer,
            sections=sections,
        )
        markdown_hash = sha256_text(markdown)

        report_id = sha256_text(
            canonical_json(
                {
                    "tenant_id": projection.tenant_id,
                    "client_id": projection.client_id,
                    "engagement_id": projection.engagement_id,
                    "assessment_id": projection.assessment_id,
                    "projection_hash": projection.projection_hash,
                    "client_display_name": client_name,
                    "prepared_by": preparer,
                }
            )
        )[:24]

        manifest_payload = {
            "report_id": report_id,
            "tenant_id": projection.tenant_id,
            "client_id": projection.client_id,
            "engagement_id": projection.engagement_id,
            "assessment_id": projection.assessment_id,
            "assessment_name": projection.assessment_name,
            "section_count": len(sections),
            "section_ids": section_ids,
            "source_commitments": (
                projection.source_commitments
            ),
            "projection_hash": projection.projection_hash,
            "markdown_hash": markdown_hash,
            "schema_version": (
                ASSESSMENT_REPORT_PACKAGE_VERSION
            ),
        }
        package_hash = sha256_text(
            canonical_json(manifest_payload)
        )

        manifest = ClientReportManifest(
            report_id=report_id,
            tenant_id=projection.tenant_id,
            client_id=projection.client_id,
            engagement_id=projection.engagement_id,
            assessment_id=projection.assessment_id,
            assessment_name=projection.assessment_name,
            section_count=len(sections),
            section_ids=section_ids,
            source_commitments={
                **projection.source_commitments,
                "executive_projection_hash": (
                    projection.projection_hash
                ),
            },
            markdown_hash=markdown_hash,
            package_hash=package_hash,
        )

        return ClientReadyReportPackage(
            report_id=report_id,
            hierarchy_key=projection.hierarchy_key,
            title=title,
            sections=sections,
            markdown=markdown,
            manifest=manifest,
        )

    def _build_sections(
        self,
        *,
        projection: ExecutiveAssessmentProjection,
        client_display_name: str,
        prepared_by: str,
    ) -> tuple[ReportSection, ...]:
        priorities = self._priority_lines(projection)
        roadmap = self._roadmap_lines(projection)
        commitments = self._commitment_lines(projection)

        return (
            ReportSection(
                section_id="executive-summary",
                kind=ReportSectionKind.EXECUTIVE_SUMMARY,
                title="Executive Summary",
                order=1,
                markdown=projection.executive_summary,
            ),
            ReportSection(
                section_id="assessment-scope",
                kind=ReportSectionKind.ASSESSMENT_SCOPE,
                title="Assessment Scope",
                order=2,
                markdown=(
                    f"- Client: {client_display_name}\n"
                    f"- Assessment period: "
                    f"{projection.assessment_period}\n"
                    f"- Workflows assessed: "
                    f"{projection.workflow_count}\n"
                    f"- Organizational units assessed: "
                    f"{projection.organizational_unit_count}\n"
                    f"- Prepared by: {prepared_by}"
                ),
            ),
            ReportSection(
                section_id="evidence-quality",
                kind=ReportSectionKind.EVIDENCE_QUALITY,
                title="Evidence Quality",
                order=3,
                markdown=(
                    f"- Grade: "
                    f"{projection.evidence_quality_grade}\n"
                    f"- Score: "
                    f"{projection.evidence_quality_score:.2f}\n"
                    f"- Ready for analysis: "
                    f"{projection.evidence_ready_for_analysis}"
                ),
            ),
            ReportSection(
                section_id="governance-debt",
                kind=ReportSectionKind.GOVERNANCE_DEBT,
                title="Governance Debt",
                order=4,
                markdown=(
                    f"- Score: "
                    f"{projection.governance_debt_score:.2f}\n"
                    f"- Band: {projection.governance_debt_band}\n"
                    f"- Total weighted friction: "
                    f"{projection.total_friction_score:.2f}\n"
                    f"- Affected work items: "
                    f"{projection.affected_work_item_count}\n"
                    f"- Dominant constraint: "
                    f"{projection.dominant_constraint or 'None'}"
                ),
            ),
            ReportSection(
                section_id="key-findings",
                kind=ReportSectionKind.KEY_FINDINGS,
                title="Key Findings",
                order=5,
                markdown="\n".join(
                    f"- {finding}"
                    for finding in projection.key_findings
                ),
            ),
            ReportSection(
                section_id="priorities",
                kind=ReportSectionKind.PRIORITIES,
                title="Priority Interventions",
                order=6,
                markdown=priorities,
            ),
            ReportSection(
                section_id="roadmap",
                kind=ReportSectionKind.ROADMAP,
                title="30/60/90-Day Roadmap",
                order=7,
                markdown=roadmap,
            ),
            ReportSection(
                section_id="evidence-appendix",
                kind=ReportSectionKind.EVIDENCE_APPENDIX,
                title="Evidence Commitments",
                order=8,
                markdown=commitments,
            ),
        )

    def _priority_lines(
        self,
        projection: ExecutiveAssessmentProjection,
    ) -> str:
        if not projection.priorities:
            return "No priority interventions were generated."

        return "\n".join(
            (
                f"{priority.rank}. **{priority.title}** "
                f"({priority.priority}, "
                f"value {priority.value_score:.2f}) — "
                f"Owner: {priority.owner_role or 'Unassigned'}; "
                f"Target: "
                f"{priority.target_horizon or 'Unscheduled'}"
            )
            for priority in projection.priorities
        )

    def _roadmap_lines(
        self,
        projection: ExecutiveAssessmentProjection,
    ) -> str:
        return "\n".join(
            f"- {horizon}: {count} planned intervention(s)"
            for horizon, count in (
                projection.roadmap_phase_counts.items()
            )
        )

    def _commitment_lines(
        self,
        projection: ExecutiveAssessmentProjection,
    ) -> str:
        commitments = {
            **projection.source_commitments,
            "executive_projection_hash": (
                projection.projection_hash
            ),
        }

        return "\n".join(
            f"- `{name}`: `{value}`"
            for name, value in sorted(commitments.items())
        )

    def _render_markdown(
        self,
        *,
        title: str,
        prepared_by: str,
        sections: tuple[ReportSection, ...],
    ) -> str:
        body = [
            f"# {title}",
            "",
            f"Prepared by: {prepared_by}",
            "",
        ]

        for section in sections:
            body.extend(
                (
                    f"## {section.title}",
                    "",
                    section.markdown,
                    "",
                )
            )

        return "\n".join(body).rstrip() + "\n"
