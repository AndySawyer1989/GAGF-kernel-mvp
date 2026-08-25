from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from backend.app.gagf.governance_assessment_application import (
    ASSESSMENT_APPLICATION_VERSION,
    GovernanceAssessmentApplicationService,
)
from backend.app.gagf.governance_assessment_demonstration_persistence import (
    ARTIFACT_TYPE_ORDER,
    DEMONSTRATION_PERSISTENCE_VERSION,
)
from backend.app.gagf.governance_assessment_repository import (
    AssessmentRepositoryError,
    GovernanceAssessmentRepository,
    canonical_json,
    sha256_text,
)
from backend.app.gagf.governance_paid_assessment_execution_coordinator import (
    PAID_ASSESSMENT_EXECUTION_COORDINATOR_ID,
    PAID_ASSESSMENT_EXECUTION_COORDINATOR_SCHEMA_VERSION,
    PAID_ASSESSMENT_EXECUTION_COORDINATOR_VERSION,
)
from backend.app.gagf.prelive_blind_assessment import (
    FORBIDDEN_KEYS,
    PreliveScenarioError,
)
from backend.app.gagf.prelive_operator_execution_rehearsal import (
    PreliveOperatorExecutionRehearsalResult,
)


PRELIVE_REHEARSAL_VERIFICATION_VERSION = "1.0.0"

PRELIVE_REHEARSAL_VERIFICATION_STATUS = (
    "blind_rehearsal_verified"
)

PRELIVE_REHEARSAL_VERIFICATION_AUTHORITY = (
    "GAGF_FIP_ONLY"
)


def find_forbidden_keys(
    value: Any,
    *,
    path: str = "$",
) -> tuple[str, ...]:
    """
    Return paths containing PRELIVE oracle or planted-answer
    keys.

    This is intentionally recursive so verification covers
    every persisted artifact payload, not only top-level
    fields.
    """

    findings: list[str] = []

    if isinstance(value, Mapping):
        for raw_key, child in value.items():
            key = str(raw_key)
            normalized = key.strip().lower()
            child_path = f"{path}.{key}"

            if normalized in FORBIDDEN_KEYS:
                findings.append(child_path)

            findings.extend(
                find_forbidden_keys(
                    child,
                    path=child_path,
                )
            )

    elif isinstance(value, (list, tuple)):
        for index, child in enumerate(value):
            findings.extend(
                find_forbidden_keys(
                    child,
                    path=f"{path}[{index}]",
                )
            )

    return tuple(findings)


@dataclass(frozen=True, slots=True)
class PreliveRehearsalVerificationResult:
    """
    Deterministic verification receipt for one completed
    PRELIVE blind assessment rehearsal.

    Verification proves repository integrity and lineage.

    It does not prove:
    - customer outcome
    - intervention success
    - causation
    - ROI
    - remediation success
    - future action authority
    """

    hierarchy_key: str
    assessment_record_hash: str
    repository_summary_hash: str
    artifact_count: int
    artifact_types: tuple[str, ...]
    repository_chain_valid: bool

    request_hash: str
    handoff_hash: str
    demonstration_hash: str
    persistence_hash: str
    application_hash: str
    execution_result_hash: str
    report_id: str

    oracle_leakage_detected: bool
    oracle_leakage_paths: tuple[str, ...]

    verification_hash: str

    verification_status: str = (
        PRELIVE_REHEARSAL_VERIFICATION_STATUS
    )

    authority: str = (
        PRELIVE_REHEARSAL_VERIFICATION_AUTHORITY
    )

    verification_version: str = (
        PRELIVE_REHEARSAL_VERIFICATION_VERSION
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "verification_status":
                self.verification_status,
            "authority":
                self.authority,
            "verification_version":
                self.verification_version,
            "hierarchy_key":
                self.hierarchy_key,
            "assessment_record_hash":
                self.assessment_record_hash,
            "repository_summary_hash":
                self.repository_summary_hash,
            "artifact_count":
                self.artifact_count,
            "artifact_types":
                list(self.artifact_types),
            "repository_chain_valid":
                self.repository_chain_valid,
            "request_hash":
                self.request_hash,
            "handoff_hash":
                self.handoff_hash,
            "demonstration_hash":
                self.demonstration_hash,
            "persistence_hash":
                self.persistence_hash,
            "application_hash":
                self.application_hash,
            "execution_result_hash":
                self.execution_result_hash,
            "report_id":
                self.report_id,
            "oracle_leakage_detected":
                self.oracle_leakage_detected,
            "oracle_leakage_paths":
                list(self.oracle_leakage_paths),
            "verification_hash":
                self.verification_hash,
        }


class PreliveRehearsalResultVerifier:
    """
    Independently verify one completed PRELIVE rehearsal
    from durable repository state.

    This verifier is read-only.

    It reloads persisted assessment state rather than
    trusting only the in-memory execution result.
    """

    def verify(
        self,
        *,
        database_path: str | Path,
        rehearsal_result:
            PreliveOperatorExecutionRehearsalResult,
    ) -> PreliveRehearsalVerificationResult:
        if not isinstance(
            rehearsal_result,
            PreliveOperatorExecutionRehearsalResult,
        ):
            raise PreliveScenarioError(
                "PRELIVE verification requires a completed "
                "operator execution rehearsal result."
            )

        prepared = rehearsal_result.handoff_bridge
        request = prepared.request_bridge.request
        handoff = prepared.handoff
        confirmation = (
            rehearsal_result.operator_confirmation
        )
        execution = rehearsal_result.execution_result
        context = request.context

        repository = GovernanceAssessmentRepository(
            database_path
        )

        application = GovernanceAssessmentApplicationService(
            repository=repository
        )

        try:
            summary = application.summarize(
                context=context
            )

            artifacts = repository.list_artifacts(
                context=context
            )

            chain_valid = repository.verify_chain(
                context=context
            )
        except AssessmentRepositoryError as exc:
            raise PreliveScenarioError(
                "PRELIVE persisted-result verification "
                f"failed: {exc}"
            ) from exc

        if summary.hierarchy_key != context.hierarchy_key:
            raise PreliveScenarioError(
                "PRELIVE persisted assessment hierarchy "
                "does not match the execution request."
            )

        if summary.assessment.status != "complete":
            raise PreliveScenarioError(
                "PRELIVE persisted assessment is not complete."
            )

        artifact_types = tuple(
            artifact.artifact_type
            for artifact in artifacts
        )

        if artifact_types != ARTIFACT_TYPE_ORDER:
            raise PreliveScenarioError(
                "PRELIVE persisted artifact order does not "
                "match the governed assessment contract."
            )

        if len(artifacts) != execution.artifact_count:
            raise PreliveScenarioError(
                "PRELIVE persisted artifact count does not "
                "match the execution result."
            )

        if summary.artifact_count != len(artifacts):
            raise PreliveScenarioError(
                "PRELIVE repository summary artifact count "
                "does not match persistence."
            )

        if chain_valid is not True:
            raise PreliveScenarioError(
                "PRELIVE repository artifact chain is invalid."
            )

        request_hash = sha256_text(
            canonical_json(
                request.to_dict()
            )
        )

        self._validate_request_binding(
            request_hash=request_hash,
            handoff_request_hash=(
                handoff.assessment_execution_request_hash
            ),
            confirmation_request_hash=(
                confirmation
                .assessment_execution_request_hash
            ),
            execution_request_hash=(
                execution
                .assessment_execution_request_hash
            ),
            application_request_hash=(
                execution.application_request_hash
            ),
        )

        self._validate_handoff_binding(
            handoff_hash=handoff.handoff_hash,
            confirmation_handoff_hash=(
                confirmation.handoff_hash
            ),
            execution_handoff_hash=(
                execution.handoff_hash
            ),
        )

        if execution.hierarchy_key != context.hierarchy_key:
            raise PreliveScenarioError(
                "PRELIVE execution-result hierarchy does "
                "not match persisted assessment hierarchy."
            )

        manifest_artifact = artifacts[-1]

        if (
            manifest_artifact.artifact_type
            != "demonstration-manifest"
        ):
            raise PreliveScenarioError(
                "PRELIVE final persisted artifact is not "
                "the demonstration manifest."
            )

        manifest = manifest_artifact.payload

        if not isinstance(manifest, Mapping):
            raise PreliveScenarioError(
                "PRELIVE persisted demonstration manifest "
                "is not an object."
            )

        demonstration_hash = str(
            manifest.get(
                "demonstration_hash",
                "",
            )
        )

        if (
            demonstration_hash
            != execution.demonstration_hash
        ):
            raise PreliveScenarioError(
                "PRELIVE persisted demonstration hash does "
                "not match the execution result."
            )

        report_artifacts = tuple(
            artifact
            for artifact in artifacts
            if artifact.artifact_type
            == "client-report-package"
        )

        if len(report_artifacts) != 1:
            raise PreliveScenarioError(
                "PRELIVE verification requires exactly one "
                "persisted client report package."
            )

        report_payload = report_artifacts[0].payload

        if not isinstance(report_payload, Mapping):
            raise PreliveScenarioError(
                "PRELIVE persisted report package is not "
                "an object."
            )

        persisted_report_id = str(
            report_payload.get(
                "report_id",
                "",
            )
        )

        if (
            not persisted_report_id
            or persisted_report_id
            != execution.report_id
        ):
            raise PreliveScenarioError(
                "PRELIVE persisted report identifier does "
                "not match the execution result."
            )

        persistence_hash = (
            self._reconstruct_persistence_hash(
                hierarchy_key=context.hierarchy_key,
                assessment=summary.assessment,
                artifacts=artifacts,
                demonstration_hash=demonstration_hash,
                repository_chain_valid=chain_valid,
            )
        )

        if persistence_hash != execution.persistence_hash:
            raise PreliveScenarioError(
                "PRELIVE reconstructed persistence hash "
                "does not match the execution result."
            )

        application_hash = (
            self._reconstruct_application_hash(
                hierarchy_key=context.hierarchy_key,
                request_hash=request_hash,
                demonstration_hash=(
                    demonstration_hash
                ),
                persistence_hash=persistence_hash,
                report_id=persisted_report_id,
            )
        )

        if application_hash != execution.application_hash:
            raise PreliveScenarioError(
                "PRELIVE reconstructed application hash "
                "does not match the execution result."
            )

        execution_result_hash = (
            self._reconstruct_execution_result_hash(
                execution=execution
            )
        )

        if (
            execution_result_hash
            != execution.execution_result_hash
        ):
            raise PreliveScenarioError(
                "PRELIVE reconstructed execution-result "
                "hash does not match the coordinator result."
            )

        oracle_leakage_paths: list[str] = []

        for artifact in artifacts:
            oracle_leakage_paths.extend(
                find_forbidden_keys(
                    artifact.payload,
                    path=(
                        "$.artifacts."
                        f"{artifact.artifact_type}"
                    ),
                )
            )

        oracle_paths = tuple(
            oracle_leakage_paths
        )

        if oracle_paths:
            raise PreliveScenarioError(
                "PRELIVE persisted assessment output "
                "contains forbidden oracle fields: "
                + ", ".join(oracle_paths)
            )

        verification_payload = {
            "verification_status": (
                PRELIVE_REHEARSAL_VERIFICATION_STATUS
            ),
            "authority": (
                PRELIVE_REHEARSAL_VERIFICATION_AUTHORITY
            ),
            "verification_version": (
                PRELIVE_REHEARSAL_VERIFICATION_VERSION
            ),
            "hierarchy_key":
                context.hierarchy_key,
            "assessment_record_hash":
                summary.assessment.record_hash,
            "repository_summary_hash":
                summary.summary_hash,
            "artifact_count":
                len(artifacts),
            "artifact_types":
                list(artifact_types),
            "repository_chain_valid":
                chain_valid,
            "request_hash":
                request_hash,
            "handoff_hash":
                handoff.handoff_hash,
            "demonstration_hash":
                demonstration_hash,
            "persistence_hash":
                persistence_hash,
            "application_hash":
                application_hash,
            "execution_result_hash":
                execution_result_hash,
            "report_id":
                persisted_report_id,
            "oracle_leakage_detected":
                False,
            "oracle_leakage_paths":
                [],
        }

        return PreliveRehearsalVerificationResult(
            hierarchy_key=(
                context.hierarchy_key
            ),
            assessment_record_hash=(
                summary.assessment.record_hash
            ),
            repository_summary_hash=(
                summary.summary_hash
            ),
            artifact_count=len(artifacts),
            artifact_types=artifact_types,
            repository_chain_valid=chain_valid,
            request_hash=request_hash,
            handoff_hash=handoff.handoff_hash,
            demonstration_hash=(
                demonstration_hash
            ),
            persistence_hash=(
                persistence_hash
            ),
            application_hash=(
                application_hash
            ),
            execution_result_hash=(
                execution_result_hash
            ),
            report_id=persisted_report_id,
            oracle_leakage_detected=False,
            oracle_leakage_paths=(),
            verification_hash=sha256_text(
                canonical_json(
                    verification_payload
                )
            ),
        )

    def _validate_request_binding(
        self,
        *,
        request_hash: str,
        handoff_request_hash: str,
        confirmation_request_hash: str,
        execution_request_hash: str,
        application_request_hash: str,
    ) -> None:
        expected = {
            request_hash,
            handoff_request_hash,
            confirmation_request_hash,
            execution_request_hash,
            application_request_hash,
        }

        if len(expected) != 1:
            raise PreliveScenarioError(
                "PRELIVE request lineage hashes do not match."
            )

    def _validate_handoff_binding(
        self,
        *,
        handoff_hash: str,
        confirmation_handoff_hash: str,
        execution_handoff_hash: str,
    ) -> None:
        expected = {
            handoff_hash,
            confirmation_handoff_hash,
            execution_handoff_hash,
        }

        if len(expected) != 1:
            raise PreliveScenarioError(
                "PRELIVE handoff lineage hashes do not match."
            )

    def _reconstruct_persistence_hash(
        self,
        *,
        hierarchy_key: str,
        assessment: Any,
        artifacts: tuple[Any, ...],
        demonstration_hash: str,
        repository_chain_valid: bool,
    ) -> str:
        payload = {
            "hierarchy_key":
                hierarchy_key,
            "demonstration_hash":
                demonstration_hash,
            "assessment_identity": {
                "tenant_id":
                    assessment.tenant_id,
                "client_id":
                    assessment.client_id,
                "engagement_id":
                    assessment.engagement_id,
                "assessment_id":
                    assessment.assessment_id,
                "assessment_name":
                    assessment.assessment_name,
                "status":
                    assessment.status,
            },
            "artifacts": [
                {
                    "artifact_type":
                        artifact.artifact_type,
                    "artifact_id":
                        artifact.artifact_id,
                    "artifact_hash":
                        artifact.artifact_hash,
                    "sequence_number":
                        artifact.sequence_number,
                }
                for artifact in artifacts
            ],
            "repository_chain_valid":
                repository_chain_valid,
            "schema_version":
                DEMONSTRATION_PERSISTENCE_VERSION,
        }

        return sha256_text(
            canonical_json(payload)
        )

    def _reconstruct_application_hash(
        self,
        *,
        hierarchy_key: str,
        request_hash: str,
        demonstration_hash: str,
        persistence_hash: str,
        report_id: str,
    ) -> str:
        payload = {
            "hierarchy_key":
                hierarchy_key,
            "request_hash":
                request_hash,
            "demonstration_hash":
                demonstration_hash,
            "persistence_hash":
                persistence_hash,
            "report_id":
                report_id,
            "schema_version":
                ASSESSMENT_APPLICATION_VERSION,
        }

        return sha256_text(
            canonical_json(payload)
        )

    def _reconstruct_execution_result_hash(
        self,
        *,
        execution: Any,
    ) -> str:
        payload = {
            "result_type": (
                PAID_ASSESSMENT_EXECUTION_COORDINATOR_ID
            ),
            "version": (
                PAID_ASSESSMENT_EXECUTION_COORDINATOR_VERSION
            ),
            "schema_version": (
                PAID_ASSESSMENT_EXECUTION_COORDINATOR_SCHEMA_VERSION
            ),
            "tenant_id":
                execution.tenant_id,
            "client_id":
                execution.client_id,
            "engagement_id":
                execution.engagement_id,
            "assessment_id":
                execution.assessment_id,
            "handoff_hash":
                execution.handoff_hash,
            "assessment_execution_request_hash": (
                execution
                .assessment_execution_request_hash
            ),
            "application_request_hash": (
                execution.application_request_hash
            ),
            "application_hash":
                execution.application_hash,
            "demonstration_hash":
                execution.demonstration_hash,
            "persistence_hash":
                execution.persistence_hash,
            "report_id":
                execution.report_id,
            "artifact_count":
                execution.artifact_count,
            "application_completed":
                execution.application_completed,
        }

        return sha256_text(
            canonical_json(payload)
        )