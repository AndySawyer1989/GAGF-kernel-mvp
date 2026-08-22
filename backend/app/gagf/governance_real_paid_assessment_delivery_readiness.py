"""Read-only post-execution rehydration and delivery-readiness verification.

PILOT-006 reconstructs the existing governed delivery inputs from:
- serialized PA015/PA014 execution evidence; and
- canonical immutable assessment persistence.

This module does not approve delivery, create a delivery envelope, deliver
anything, or mutate assessment persistence.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from backend.app.gagf.governance_assessment_isolation import (
    CommercialHierarchyContext,
)
from backend.app.gagf.governance_assessment_demonstration_persistence import (
    ARTIFACT_TYPE_ORDER,
)
from backend.app.gagf.governance_assessment_report_package import (
    ClientReadyReportPackage,
    ClientReportManifest,
    ReportSection,
    ReportSectionKind,
    sha256_text,
)
from backend.app.gagf.governance_assessment_repository import (
    AssessmentRecordNotFoundError,
    GovernanceAssessmentRepository,
)
from backend.app.gagf.governance_paid_assessment_execution_coordinator import (
    PaidAssessmentExecutionResult,
)
from backend.app.gagf.governance_real_paid_assessment_execution import (
    EXPECTED_CORE_ARTIFACT_COUNT,
    REAL_EXECUTION_STATUS_COMPLETE,
)


REAL_PAID_ASSESSMENT_DELIVERY_READINESS_ID = (
    "governance-real-paid-assessment-delivery-readiness"
)
REAL_PAID_ASSESSMENT_DELIVERY_READINESS_VERSION = "0.1.0"
REAL_PAID_ASSESSMENT_DELIVERY_READINESS_SCHEMA_VERSION = "1.0.0"

READY_FOR_DELIVERY_APPROVAL_REVIEW = (
    "ready_for_delivery_approval_review"
)

ALLOWED_RECOVERY_DISPOSITIONS = frozenset(
    {
        "executed",
        "resumed",
        "reconciled",
    }
)


class RealPaidAssessmentDeliveryReadinessError(RuntimeError):
    """Raised when post-execution delivery readiness cannot be verified."""


@dataclass(frozen=True, slots=True)
class RealPaidAssessmentDeliveryReadinessResult:
    execution_result: PaidAssessmentExecutionResult
    report_package: ClientReadyReportPackage
    recovery_disposition: str
    attempt_hash: str
    recovery_record_hash: str
    artifact_count: int
    repository_chain_valid: bool
    delivery_readiness_status: str = (
        READY_FOR_DELIVERY_APPROVAL_REVIEW
    )
    result_type: str = REAL_PAID_ASSESSMENT_DELIVERY_READINESS_ID
    version: str = REAL_PAID_ASSESSMENT_DELIVERY_READINESS_VERSION
    schema_version: str = (
        REAL_PAID_ASSESSMENT_DELIVERY_READINESS_SCHEMA_VERSION
    )

    @property
    def hierarchy_key(self) -> str:
        return self.execution_result.hierarchy_key

    def to_dict(self) -> dict[str, Any]:
        return {
            "result_type": self.result_type,
            "version": self.version,
            "schema_version": self.schema_version,
            "hierarchy_key": self.hierarchy_key,
            "delivery_readiness_status": self.delivery_readiness_status,
            "ready_for_delivery_approval_review": True,
            "attempt_hash": self.attempt_hash,
            "recovery_record_hash": self.recovery_record_hash,
            "recovery_disposition": self.recovery_disposition,
            "artifact_count": self.artifact_count,
            "repository_chain_valid": self.repository_chain_valid,
            "execution_result": self.execution_result.to_dict(),
            "report_package": self.report_package.to_dict(),
            "boundaries": {
                "operator_success_is_not_delivery_readiness": True,
                "rehydration_is_not_new_assessment_execution": True,
                "delivery_readiness_is_not_delivery_approval": True,
                "delivery_readiness_is_not_approved_for_human_delivery": True,
                "delivery_readiness_is_not_delivery": True,
                "delivery_readiness_is_not_client_receipt": True,
                "delivery_readiness_is_not_client_acceptance": True,
                "delivery_readiness_is_not_customer_outcome": True,
                "pa003_remains_delivery_envelope_authority": True,
            },
        }


class GovernanceRealPaidAssessmentDeliveryReadinessService:
    """Rehydrate and verify existing PA-003 inputs without mutation."""

    def verify(
        self,
        *,
        database_path: str | Path,
        operator_payload: dict[str, Any],
    ) -> RealPaidAssessmentDeliveryReadinessResult:
        database = Path(database_path)

        if not database.exists():
            raise RealPaidAssessmentDeliveryReadinessError(
                "assessment database does not exist"
            )

        if not database.is_file():
            raise RealPaidAssessmentDeliveryReadinessError(
                "assessment database path is not a file"
            )

        if not isinstance(operator_payload, dict):
            raise RealPaidAssessmentDeliveryReadinessError(
                "operator_payload must be an object"
            )

        if operator_payload.get("operator_run_passed") is not True:
            raise RealPaidAssessmentDeliveryReadinessError(
                "PA015 operator result is not successful"
            )

        recovery = operator_payload.get("result")

        if not isinstance(recovery, dict):
            raise RealPaidAssessmentDeliveryReadinessError(
                "PA015 result must contain a recovery object"
            )

        recovery_disposition = self._require_text(
            recovery.get("disposition"),
            "result.disposition",
        )

        if recovery_disposition not in ALLOWED_RECOVERY_DISPOSITIONS:
            raise RealPaidAssessmentDeliveryReadinessError(
                "unsupported recovery disposition"
            )

        attempt_hash = self._require_hash(
            recovery.get("attempt_hash"),
            "result.attempt_hash",
        )

        recovery_record_hash = self._require_hash(
            recovery.get("record_hash"),
            "result.record_hash",
        )

        recovery_hierarchy_key = self._require_text(
            recovery.get("hierarchy_key"),
            "result.hierarchy_key",
        )

        artifact_count_after = recovery.get("artifact_count_after")

        if artifact_count_after != EXPECTED_CORE_ARTIFACT_COUNT:
            raise RealPaidAssessmentDeliveryReadinessError(
                "PA015 recovery artifact_count_after must equal "
                f"{EXPECTED_CORE_ARTIFACT_COUNT}"
            )

        serialized_execution = recovery.get("execution_result")

        if not isinstance(serialized_execution, dict):
            raise RealPaidAssessmentDeliveryReadinessError(
                "result.execution_result must be an object"
            )

        execution_result = self._rehydrate_execution_result(
            serialized_execution
        )

        if execution_result.hierarchy_key != recovery_hierarchy_key:
            raise RealPaidAssessmentDeliveryReadinessError(
                "recovery hierarchy does not match execution result"
            )

        context = CommercialHierarchyContext(
            tenant_id=execution_result.tenant_id,
            client_id=execution_result.client_id,
            engagement_id=execution_result.engagement_id,
            assessment_id=execution_result.assessment_id,
        )

        repository = GovernanceAssessmentRepository(database)

        try:
            assessment = repository.get_assessment(context=context)
        except AssessmentRecordNotFoundError as exc:
            raise RealPaidAssessmentDeliveryReadinessError(
                "completed assessment record was not found"
            ) from exc

        if assessment.status != "complete":
            raise RealPaidAssessmentDeliveryReadinessError(
                "assessment status is not complete"
            )

        artifacts = repository.list_artifacts(context=context)

        if len(artifacts) != EXPECTED_CORE_ARTIFACT_COUNT:
            raise RealPaidAssessmentDeliveryReadinessError(
                "canonical assessment artifact count is not "
                f"{EXPECTED_CORE_ARTIFACT_COUNT}"
            )

        artifact_types = tuple(
            artifact.artifact_type
            for artifact in artifacts
        )

        if artifact_types != tuple(ARTIFACT_TYPE_ORDER):
            raise RealPaidAssessmentDeliveryReadinessError(
                "canonical assessment artifact order is invalid"
            )

        if len(set(artifact_types)) != len(artifact_types):
            raise RealPaidAssessmentDeliveryReadinessError(
                "canonical assessment contains duplicate artifact types"
            )

        for artifact in artifacts:
            repository.verify_artifact(artifact)

        if repository.verify_chain(context=context) is not True:
            raise RealPaidAssessmentDeliveryReadinessError(
                "canonical assessment artifact chain is invalid"
            )

        artifact_by_type = {
            artifact.artifact_type: artifact
            for artifact in artifacts
        }

        report_artifact = artifact_by_type.get(
            "client-report-package"
        )
        demonstration_manifest_artifact = artifact_by_type.get(
            "demonstration-manifest"
        )

        if report_artifact is None:
            raise RealPaidAssessmentDeliveryReadinessError(
                "client-report-package artifact is missing"
            )

        if demonstration_manifest_artifact is None:
            raise RealPaidAssessmentDeliveryReadinessError(
                "demonstration-manifest artifact is missing"
            )

        report_package = self._rehydrate_report_package(
            report_artifact.payload
        )

        demonstration_manifest = (
            demonstration_manifest_artifact.payload
        )

        if not isinstance(demonstration_manifest, dict):
            raise RealPaidAssessmentDeliveryReadinessError(
                "demonstration-manifest payload must be an object"
            )

        if (
            report_package.hierarchy_key
            != execution_result.hierarchy_key
        ):
            raise RealPaidAssessmentDeliveryReadinessError(
                "persisted report hierarchy does not match execution"
            )

        if report_package.report_id != execution_result.report_id:
            raise RealPaidAssessmentDeliveryReadinessError(
                "persisted report_id does not match execution"
            )

        if (
            report_package.manifest.package_hash
            != self._require_hash(
                serialized_execution.get("report_package_hash"),
                "execution_result.report_package_hash",
            )
        ):
            raise RealPaidAssessmentDeliveryReadinessError(
                "persisted report package hash does not match execution"
            )

        actual_markdown_hash = sha256_text(
            report_package.markdown
        )

        if (
            actual_markdown_hash
            != report_package.manifest.markdown_hash
        ):
            raise RealPaidAssessmentDeliveryReadinessError(
                "persisted report markdown hash is invalid"
            )

        manifest_hierarchy = self._require_text(
            demonstration_manifest.get("hierarchy_key"),
            "demonstration-manifest.hierarchy_key",
        )

        if manifest_hierarchy != execution_result.hierarchy_key:
            raise RealPaidAssessmentDeliveryReadinessError(
                "demonstration manifest hierarchy does not match execution"
            )

        manifest_demonstration_hash = self._require_hash(
            demonstration_manifest.get("demonstration_hash"),
            "demonstration-manifest.demonstration_hash",
        )

        if (
            manifest_demonstration_hash
            != execution_result.demonstration_hash
        ):
            raise RealPaidAssessmentDeliveryReadinessError(
                "demonstration hash does not match persisted manifest"
            )

        commitments = demonstration_manifest.get(
            "artifact_commitments"
        )

        if not isinstance(commitments, dict):
            raise RealPaidAssessmentDeliveryReadinessError(
                "demonstration artifact commitments must be an object"
            )

        committed_report_hash = self._require_hash(
            commitments.get("report_package_hash"),
            (
                "demonstration-manifest."
                "artifact_commitments.report_package_hash"
            ),
        )

        if (
            committed_report_hash
            != report_package.manifest.package_hash
        ):
            raise RealPaidAssessmentDeliveryReadinessError(
                "report package hash does not match demonstration commitment"
            )

        if execution_result.artifact_count != len(artifacts):
            raise RealPaidAssessmentDeliveryReadinessError(
                "execution artifact_count does not match repository"
            )

        if execution_result.application_completed is not True:
            raise RealPaidAssessmentDeliveryReadinessError(
                "execution result is not application-complete"
            )

        return RealPaidAssessmentDeliveryReadinessResult(
            execution_result=execution_result,
            report_package=report_package,
            recovery_disposition=recovery_disposition,
            attempt_hash=attempt_hash,
            recovery_record_hash=recovery_record_hash,
            artifact_count=len(artifacts),
            repository_chain_valid=True,
        )

    def _rehydrate_execution_result(
        self,
        payload: dict[str, Any],
    ) -> PaidAssessmentExecutionResult:
        if (
            payload.get("execution_status")
            != REAL_EXECUTION_STATUS_COMPLETE
        ):
            raise RealPaidAssessmentDeliveryReadinessError(
                "execution result status is not complete"
            )

        if (
            payload.get("application_completed")
            is not True
        ):
            raise RealPaidAssessmentDeliveryReadinessError(
                "serialized execution is not application-complete"
            )

        if (
            payload.get("repository_chain_valid")
            is not True
        ):
            raise RealPaidAssessmentDeliveryReadinessError(
                "serialized execution does not report a valid repository chain"
            )

        if payload.get("artifact_count") != EXPECTED_CORE_ARTIFACT_COUNT:
            raise RealPaidAssessmentDeliveryReadinessError(
                "serialized execution artifact_count is invalid"
            )

        execution_result = PaidAssessmentExecutionResult(
            tenant_id=self._require_text(
                payload.get("tenant_id"),
                "execution_result.tenant_id",
            ),
            client_id=self._require_text(
                payload.get("client_id"),
                "execution_result.client_id",
            ),
            engagement_id=self._require_text(
                payload.get("engagement_id"),
                "execution_result.engagement_id",
            ),
            assessment_id=self._require_text(
                payload.get("assessment_id"),
                "execution_result.assessment_id",
            ),
            handoff_hash=self._require_hash(
                payload.get("handoff_hash"),
                "execution_result.handoff_hash",
            ),
            assessment_execution_request_hash=self._require_hash(
                payload.get("assessment_execution_request_hash"),
                "execution_result.assessment_execution_request_hash",
            ),
            application_request_hash=self._require_hash(
                payload.get("application_request_hash"),
                "execution_result.application_request_hash",
            ),
            application_hash=self._require_hash(
                payload.get("application_hash"),
                "execution_result.application_hash",
            ),
            demonstration_hash=self._require_hash(
                payload.get("demonstration_hash"),
                "execution_result.demonstration_hash",
            ),
            persistence_hash=self._require_hash(
                payload.get("persistence_hash"),
                "execution_result.persistence_hash",
            ),
            report_id=self._require_text(
                payload.get("report_id"),
                "execution_result.report_id",
            ),
            artifact_count=payload["artifact_count"],
            application_completed=True,
            execution_result_hash=self._require_hash(
                payload.get("execution_result_hash"),
                "execution_result.execution_result_hash",
            ),
        )

        serialized_hierarchy = self._require_text(
            payload.get("hierarchy_key"),
            "execution_result.hierarchy_key",
        )

        if serialized_hierarchy != execution_result.hierarchy_key:
            raise RealPaidAssessmentDeliveryReadinessError(
                "serialized execution hierarchy is invalid"
            )

        return execution_result

    def _rehydrate_report_package(
        self,
        payload: Any,
    ) -> ClientReadyReportPackage:
        if not isinstance(payload, dict):
            raise RealPaidAssessmentDeliveryReadinessError(
                "client-report-package payload must be an object"
            )

        sections_payload = payload.get("sections")

        if not isinstance(sections_payload, list):
            raise RealPaidAssessmentDeliveryReadinessError(
                "report sections must be an array"
            )

        sections: list[ReportSection] = []

        for raw_section in sections_payload:
            if not isinstance(raw_section, dict):
                raise RealPaidAssessmentDeliveryReadinessError(
                    "report section must be an object"
                )

            try:
                kind = ReportSectionKind(
                    self._require_text(
                        raw_section.get("kind"),
                        "report section kind",
                    )
                )
            except ValueError as exc:
                raise RealPaidAssessmentDeliveryReadinessError(
                    "report section kind is invalid"
                ) from exc

            order = raw_section.get("order")

            if not isinstance(order, int) or isinstance(order, bool):
                raise RealPaidAssessmentDeliveryReadinessError(
                    "report section order must be an integer"
                )

            sections.append(
                ReportSection(
                    section_id=self._require_text(
                        raw_section.get("section_id"),
                        "report section_id",
                    ),
                    kind=kind,
                    title=self._require_text(
                        raw_section.get("title"),
                        "report section title",
                    ),
                    order=order,
                    markdown=self._require_preserved_text(
                        raw_section.get("markdown"),
                        "report section markdown",
                    ),
                )
            )

        manifest_payload = payload.get("manifest")

        if not isinstance(manifest_payload, dict):
            raise RealPaidAssessmentDeliveryReadinessError(
                "report manifest must be an object"
            )

        section_ids = manifest_payload.get("section_ids")

        if not isinstance(section_ids, list) or not all(
            isinstance(value, str)
            for value in section_ids
        ):
            raise RealPaidAssessmentDeliveryReadinessError(
                "report manifest section_ids must be an array of strings"
            )

        source_commitments = manifest_payload.get(
            "source_commitments"
        )

        if not isinstance(source_commitments, dict) or not all(
            isinstance(key, str)
            and isinstance(value, str)
            for key, value in source_commitments.items()
        ):
            raise RealPaidAssessmentDeliveryReadinessError(
                "report manifest source_commitments must be string hashes"
            )

        section_count = manifest_payload.get(
            "section_count"
        )

        if (
            not isinstance(section_count, int)
            or isinstance(section_count, bool)
        ):
            raise RealPaidAssessmentDeliveryReadinessError(
                "report manifest section_count must be an integer"
            )

        manifest = ClientReportManifest(
            report_id=self._require_text(
                manifest_payload.get("report_id"),
                "report manifest report_id",
            ),
            tenant_id=self._require_text(
                manifest_payload.get("tenant_id"),
                "report manifest tenant_id",
            ),
            client_id=self._require_text(
                manifest_payload.get("client_id"),
                "report manifest client_id",
            ),
            engagement_id=self._require_text(
                manifest_payload.get("engagement_id"),
                "report manifest engagement_id",
            ),
            assessment_id=self._require_text(
                manifest_payload.get("assessment_id"),
                "report manifest assessment_id",
            ),
            assessment_name=self._require_text(
                manifest_payload.get("assessment_name"),
                "report manifest assessment_name",
            ),
            section_count=section_count,
            section_ids=tuple(section_ids),
            source_commitments=dict(source_commitments),
            markdown_hash=self._require_hash(
                manifest_payload.get("markdown_hash"),
                "report manifest markdown_hash",
            ),
            package_hash=self._require_hash(
                manifest_payload.get("package_hash"),
                "report manifest package_hash",
            ),
            schema_version=self._require_text(
                manifest_payload.get("schema_version"),
                "report manifest schema_version",
            ),
        )

        package = ClientReadyReportPackage(
            report_id=self._require_text(
                payload.get("report_id"),
                "report package report_id",
            ),
            hierarchy_key=self._require_text(
                payload.get("hierarchy_key"),
                "report package hierarchy_key",
            ),
            title=self._require_text(
                payload.get("title"),
                "report package title",
            ),
            sections=tuple(sections),
            markdown=self._require_preserved_text(
                payload.get("markdown"),
                "report package markdown",
            ),
            manifest=manifest,
        )

        if manifest.report_id != package.report_id:
            raise RealPaidAssessmentDeliveryReadinessError(
                "report manifest report_id does not match package"
            )

        if manifest.section_count != len(package.sections):
            raise RealPaidAssessmentDeliveryReadinessError(
                "report manifest section_count does not match sections"
            )

        actual_section_ids = tuple(
            section.section_id
            for section in package.sections
        )

        if manifest.section_ids != actual_section_ids:
            raise RealPaidAssessmentDeliveryReadinessError(
                "report manifest section_ids do not match sections"
            )

        return package

    @staticmethod
    def _require_text(
        value: Any,
        field_name: str,
    ) -> str:
        if not isinstance(value, str) or not value.strip():
            raise RealPaidAssessmentDeliveryReadinessError(
                f"{field_name} must be non-empty text"
            )

        return value.strip()

    @staticmethod
    def _require_preserved_text(
        value: Any,
        field_name: str,
    ) -> str:
        if not isinstance(value, str) or not value.strip():
            raise RealPaidAssessmentDeliveryReadinessError(
                f"{field_name} must be non-empty text"
            )

        return value

    @staticmethod
    def _require_hash(
        value: Any,
        field_name: str,
    ) -> str:
        normalized = (
            GovernanceRealPaidAssessmentDeliveryReadinessService
            ._require_text(value, field_name)
        )

        if (
            len(normalized) != 64
            or any(
                character not in "0123456789abcdef"
                for character in normalized
            )
        ):
            raise RealPaidAssessmentDeliveryReadinessError(
                f"{field_name} must be a lowercase SHA-256 hash"
            )

        return normalized


SERVICE_TYPE = GovernanceRealPaidAssessmentDeliveryReadinessService