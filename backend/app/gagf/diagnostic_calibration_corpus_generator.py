from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from backend.app.gagf.diagnostic_calibration_corpus import (
    DiagnosticCalibrationCorpusService,
    DiagnosticCalibrationCorpusWriteResult,
)
from backend.app.gagf.diagnostic_calibration_scenario import (
    CalibrationDifficulty,
    CalibrationEvidenceGenerationContract,
    CalibrationOrganizationContext,
    DiagnosticCalibrationScenarioBundle,
    DiagnosticCalibrationScenarioService,
)
from backend.app.gagf.governance_assessment_repository import (
    canonical_json,
    sha256_text,
)


DIAGNOSTIC_CALIBRATION_CORPUS_GENERATOR_VERSION = (
    "1.0.0"
)

DIAGNOSTIC_CALIBRATION_CORPUS_GENERATOR_AUTHORITY = (
    "GAGF_FIP_CALIBRATION_ONLY"
)

CALIBRATION_CORPUS_MANIFEST_FILENAME = (
    "corpus_manifest.json"
)


class DiagnosticCalibrationCorpusGeneratorError(
    RuntimeError
):
    """
    Raised when a deterministic calibration corpus
    cannot be generated or verified safely.
    """


@dataclass(
    frozen=True,
    slots=True,
)
class CalibrationScenarioTemplate:
    scenario_id: str
    scenario_name: str

    organization: (
        CalibrationOrganizationContext
    )

    evidence_contract: (
        CalibrationEvidenceGenerationContract
    )

    narrative_seed: str

    planted_primary_conditions: tuple[
        str,
        ...,
    ]

    planted_secondary_conditions: tuple[
        str,
        ...,
    ]

    expected_top_k: int

    intended_difficulty: (
        CalibrationDifficulty
    )

    intended_ambiguity: str

    oracle_notes: str


@dataclass(
    frozen=True,
    slots=True,
)
class CalibrationGeneratedScenarioReceipt:
    scenario_id: str

    public_hash: str
    oracle_hash: str
    bundle_hash: str
    manifest_hash: str

    scenario_directory: str

    reused_existing: bool

    def to_dict(
        self,
    ) -> dict[str, Any]:
        return {
            "scenario_id":
                self.scenario_id,

            "public_hash":
                self.public_hash,

            "oracle_hash":
                self.oracle_hash,

            "bundle_hash":
                self.bundle_hash,

            "manifest_hash":
                self.manifest_hash,

            "scenario_directory":
                self.scenario_directory,

            "reused_existing":
                self.reused_existing,
        }


@dataclass(
    frozen=True,
    slots=True,
)
class DiagnosticCalibrationCorpusGenerationResult:
    corpus_id: str

    corpus_root: str

    scenarios: tuple[
        CalibrationGeneratedScenarioReceipt,
        ...,
    ]

    corpus_hash: str

    manifest_path: str

    authority: str = (
        DIAGNOSTIC_CALIBRATION_CORPUS_GENERATOR_AUTHORITY
    )

    version: str = (
        DIAGNOSTIC_CALIBRATION_CORPUS_GENERATOR_VERSION
    )

    @property
    def scenario_count(
        self,
    ) -> int:
        return len(
            self.scenarios
        )

    @property
    def scenario_ids(
        self,
    ) -> tuple[str, ...]:
        return tuple(
            scenario.scenario_id
            for scenario
            in self.scenarios
        )

    def to_dict(
        self,
    ) -> dict[str, Any]:
        return {
            "corpus_id":
                self.corpus_id,

            "corpus_root":
                self.corpus_root,

            "scenario_count":
                self.scenario_count,

            "scenario_ids":
                list(
                    self.scenario_ids
                ),

            "scenarios": [
                scenario.to_dict()
                for scenario
                in self.scenarios
            ],

            "corpus_hash":
                self.corpus_hash,

            "manifest_path":
                self.manifest_path,

            "authority":
                self.authority,

            "version":
                self.version,
        }


class DiagnosticCalibrationCorpusGeneratorService:
    """
    Generate a deterministic sealed calibration corpus.

    This layer creates scenario specifications only.

    It does not:

    - generate diagnostic evidence;
    - execute FIP diagnostics;
    - expose oracle information to evidence generation;
    - calibrate confidence;
    - tune diagnostic thresholds.

    Scenario specification generation is kept separate
    from later blind evidence generation.
    """

    def __init__(
        self,
        *,
        scenario_service: (
            DiagnosticCalibrationScenarioService
            | None
        ) = None,
        corpus_service: (
            DiagnosticCalibrationCorpusService
            | None
        ) = None,
    ) -> None:
        self._scenario_service = (
            scenario_service
            or
            DiagnosticCalibrationScenarioService()
        )

        self._corpus_service = (
            corpus_service
            or
            DiagnosticCalibrationCorpusService()
        )

    def generate_default_corpus(
        self,
        *,
        corpus_root: str | Path,
        corpus_id: str = (
            "FIP-CAL-001-CORPUS-001"
        ),
    ) -> DiagnosticCalibrationCorpusGenerationResult:
        return self.generate(
            corpus_root=corpus_root,
            corpus_id=corpus_id,
            templates=(
                self.default_templates()
            ),
        )

    def generate(
        self,
        *,
        corpus_root: str | Path,
        corpus_id: str,
        templates: tuple[
            CalibrationScenarioTemplate,
            ...,
        ],
    ) -> DiagnosticCalibrationCorpusGenerationResult:
        if (
            not isinstance(
                corpus_id,
                str,
            )
            or not corpus_id.strip()
        ):
            raise (
                DiagnosticCalibrationCorpusGeneratorError(
                    "corpus_id must be a non-empty string."
                )
            )

        if not templates:
            raise (
                DiagnosticCalibrationCorpusGeneratorError(
                    "At least one calibration scenario "
                    "template is required."
                )
            )

        self._validate_templates(
            templates
        )

        root = Path(
            corpus_root
        )

        root.mkdir(
            parents=True,
            exist_ok=True,
        )

        receipts: list[
            CalibrationGeneratedScenarioReceipt
        ] = []

        for template in sorted(
            templates,
            key=lambda item:
                item.scenario_id,
        ):
            bundle = (
                self._build_bundle(
                    template
                )
            )

            write_result = (
                self._corpus_service
                .write_bundle(
                    bundle=bundle,
                    corpus_root=root,
                )
            )

            receipts.append(
                self._receipt_from_write(
                    bundle=bundle,
                    write_result=(
                        write_result
                    ),
                )
            )

        ordered_receipts = tuple(
            receipts
        )

        hash_payload = {
            "corpus_id":
                corpus_id.strip(),

            "scenarios": [
                self._stable_receipt_dict(
                    receipt
                )
                for receipt
                in ordered_receipts
            ],

            "authority":
                DIAGNOSTIC_CALIBRATION_CORPUS_GENERATOR_AUTHORITY,

            "version":
                DIAGNOSTIC_CALIBRATION_CORPUS_GENERATOR_VERSION,
        }

        corpus_hash = sha256_text(
            canonical_json(
                hash_payload
            )
        )

        manifest_path = (
            root
            / CALIBRATION_CORPUS_MANIFEST_FILENAME
        )

        result = (
            DiagnosticCalibrationCorpusGenerationResult(
                corpus_id=(
                    corpus_id.strip()
                ),

                corpus_root=str(
                    root
                ),

                scenarios=(
                    ordered_receipts
                ),

                corpus_hash=(
                    corpus_hash
                ),

                manifest_path=str(
                    manifest_path
                ),
            )
        )

        self._write_corpus_manifest(
            path=(
                manifest_path
            ),
            result=result,
        )

        return result

    def default_templates(
        self,
    ) -> tuple[
        CalibrationScenarioTemplate,
        ...,
    ]:
        organization = (
            CalibrationOrganizationContext(
                organization_type=(
                    "Synthetic Enterprise"
                ),
                operating_model=(
                    "Cross-functional delivery"
                ),
                business_domain=(
                    "Professional Services"
                ),
                team_count=6,
                actor_count=30,
                workflow_count=8,
                observation_days=45,
            )
        )

        common_categories = (
            "APPROVAL_REQUIRED",
            "APPROVAL_DELAYED",
            "APPROVAL_REJECTED",
            "WORK_BLOCKED",
            "DEPENDENCY_WAIT",
            "OWNERSHIP_GAP",
            "SECURITY_REVIEW",
            "ENVIRONMENT_FAILURE",
            "ESCALATION",
            "OVERRIDE",
        )

        evidence_contract = (
            CalibrationEvidenceGenerationContract(
                allowed_constraint_categories=(
                    common_categories
                ),
                minimum_event_count=90,
                maximum_event_count=180,
                minimum_work_item_count=25,
                maximum_work_item_count=70,
                require_multiple_teams=True,
                require_multiple_lifecycles=True,
                require_temporal_ordering=True,
                evidence_quality_floor=0.75,
                evidence_quality_ceiling=0.98,
            )
        )

        return (
            CalibrationScenarioTemplate(
                scenario_id=(
                    "FIP-CAL-001-001"
                ),
                scenario_name=(
                    "Approval Delay With "
                    "Dependency Competition"
                ),
                organization=(
                    organization
                ),
                evidence_contract=(
                    evidence_contract
                ),
                narrative_seed=(
                    "Delivery teams experience recurring "
                    "decision latency across several "
                    "workflows while dependency waiting "
                    "also appears frequently."
                ),
                planted_primary_conditions=(
                    "APPROVAL_DELAYED",
                ),
                planted_secondary_conditions=(
                    "DEPENDENCY_WAIT",
                    "WORK_BLOCKED",
                ),
                expected_top_k=2,
                intended_difficulty=(
                    CalibrationDifficulty.MODERATE
                ),
                intended_ambiguity=(
                    "Dependency waiting is deliberately "
                    "plausible but secondary."
                ),
                oracle_notes=(
                    "Approval delay should occupy the "
                    "strongest explanatory position."
                ),
            ),

            CalibrationScenarioTemplate(
                scenario_id=(
                    "FIP-CAL-001-002"
                ),
                scenario_name=(
                    "Dependency Wait With "
                    "Approval Competition"
                ),
                organization=(
                    organization
                ),
                evidence_contract=(
                    evidence_contract
                ),
                narrative_seed=(
                    "Work moves across several teams and "
                    "often pauses while upstream "
                    "dependencies remain unresolved."
                ),
                planted_primary_conditions=(
                    "DEPENDENCY_WAIT",
                ),
                planted_secondary_conditions=(
                    "APPROVAL_DELAYED",
                    "WORK_BLOCKED",
                ),
                expected_top_k=2,
                intended_difficulty=(
                    CalibrationDifficulty.MODERATE
                ),
                intended_ambiguity=(
                    "Approval delay is intentionally "
                    "credible as a competing explanation."
                ),
                oracle_notes=(
                    "Dependency wait should remain the "
                    "strongest planted explanation."
                ),
            ),

            CalibrationScenarioTemplate(
                scenario_id=(
                    "FIP-CAL-001-003"
                ),
                scenario_name=(
                    "Approval Required "
                    "Across Distributed Work"
                ),
                organization=(
                    organization
                ),
                evidence_contract=(
                    evidence_contract
                ),
                narrative_seed=(
                    "Multiple workflows repeatedly pause "
                    "until formal authorization is "
                    "obtained from designated approvers."
                ),
                planted_primary_conditions=(
                    "APPROVAL_REQUIRED",
                ),
                planted_secondary_conditions=(
                    "APPROVAL_DELAYED",
                    "ESCALATION",
                ),
                expected_top_k=2,
                intended_difficulty=(
                    CalibrationDifficulty.LOW
                ),
                intended_ambiguity=(
                    "Approval delay may appear downstream "
                    "but authorization requirement is "
                    "intended to dominate."
                ),
                oracle_notes=(
                    "Approval requirement is the planted "
                    "primary structural condition."
                ),
            ),

            CalibrationScenarioTemplate(
                scenario_id=(
                    "FIP-CAL-001-004"
                ),
                scenario_name=(
                    "Security Review Bottleneck"
                ),
                organization=(
                    organization
                ),
                evidence_contract=(
                    evidence_contract
                ),
                narrative_seed=(
                    "Operational work repeatedly enters "
                    "security review before progressing "
                    "into downstream delivery stages."
                ),
                planted_primary_conditions=(
                    "SECURITY_REVIEW",
                ),
                planted_secondary_conditions=(
                    "APPROVAL_DELAYED",
                    "WORK_BLOCKED",
                ),
                expected_top_k=2,
                intended_difficulty=(
                    CalibrationDifficulty.MODERATE
                ),
                intended_ambiguity=(
                    "Downstream blocking should make the "
                    "causal interpretation non-trivial "
                    "without changing the planted primary."
                ),
                oracle_notes=(
                    "Security review is planted as the "
                    "strongest explanatory condition."
                ),
            ),

            CalibrationScenarioTemplate(
                scenario_id=(
                    "FIP-CAL-001-005"
                ),
                scenario_name=(
                    "Ownership Gap With "
                    "Escalation Competition"
                ),
                organization=(
                    organization
                ),
                evidence_contract=(
                    evidence_contract
                ),
                narrative_seed=(
                    "Work frequently reaches boundaries "
                    "where responsibility is unclear and "
                    "requires repeated reassignment."
                ),
                planted_primary_conditions=(
                    "OWNERSHIP_GAP",
                ),
                planted_secondary_conditions=(
                    "ESCALATION",
                    "DEPENDENCY_WAIT",
                ),
                expected_top_k=2,
                intended_difficulty=(
                    CalibrationDifficulty.HIGH
                ),
                intended_ambiguity=(
                    "Escalation should be prominent enough "
                    "to compete with ownership gaps."
                ),
                oracle_notes=(
                    "Ownership gap remains the planted "
                    "primary explanatory condition."
                ),
            ),

            CalibrationScenarioTemplate(
                scenario_id=(
                    "FIP-CAL-001-006"
                ),
                scenario_name=(
                    "Environment Failure "
                    "With Work Blocking"
                ),
                organization=(
                    organization
                ),
                evidence_contract=(
                    evidence_contract
                ),
                narrative_seed=(
                    "Delivery work repeatedly stops when "
                    "required execution environments are "
                    "unavailable or fail."
                ),
                planted_primary_conditions=(
                    "ENVIRONMENT_FAILURE",
                ),
                planted_secondary_conditions=(
                    "WORK_BLOCKED",
                    "ESCALATION",
                ),
                expected_top_k=2,
                intended_difficulty=(
                    CalibrationDifficulty.MODERATE
                ),
                intended_ambiguity=(
                    "Work blocking is intentionally common "
                    "as a downstream observable."
                ),
                oracle_notes=(
                    "Environment failure is planted as "
                    "the primary explanatory condition."
                ),
            ),

            CalibrationScenarioTemplate(
                scenario_id=(
                    "FIP-CAL-001-007"
                ),
                scenario_name=(
                    "Work Blocking With "
                    "Multiple Competing Causes"
                ),
                organization=(
                    organization
                ),
                evidence_contract=(
                    evidence_contract
                ),
                narrative_seed=(
                    "Multiple workflows accumulate periods "
                    "of blocked work with several weaker "
                    "governance conditions surrounding "
                    "those interruptions."
                ),
                planted_primary_conditions=(
                    "WORK_BLOCKED",
                ),
                planted_secondary_conditions=(
                    "DEPENDENCY_WAIT",
                    "APPROVAL_DELAYED",
                    "ENVIRONMENT_FAILURE",
                ),
                expected_top_k=3,
                intended_difficulty=(
                    CalibrationDifficulty.HIGH
                ),
                intended_ambiguity=(
                    "Several plausible competing "
                    "conditions intentionally reduce "
                    "diagnostic separation."
                ),
                oracle_notes=(
                    "Work blocked is planted as primary "
                    "despite multiple credible competitors."
                ),
            ),

            CalibrationScenarioTemplate(
                scenario_id=(
                    "FIP-CAL-001-008"
                ),
                scenario_name=(
                    "Dual Primary Approval "
                    "And Dependency Friction"
                ),
                organization=(
                    organization
                ),
                evidence_contract=(
                    evidence_contract
                ),
                narrative_seed=(
                    "A deliberately ambiguous organization "
                    "shows both approval latency and "
                    "dependency waiting as major recurring "
                    "constraints."
                ),
                planted_primary_conditions=(
                    "APPROVAL_DELAYED",
                    "DEPENDENCY_WAIT",
                ),
                planted_secondary_conditions=(
                    "WORK_BLOCKED",
                ),
                expected_top_k=2,
                intended_difficulty=(
                    CalibrationDifficulty.ADVERSARIAL
                ),
                intended_ambiguity=(
                    "Two planted primary conditions are "
                    "intentionally designed to compete."
                ),
                oracle_notes=(
                    "This scenario tests whether FIP can "
                    "represent competing primary "
                    "diagnostic candidates."
                ),
            ),
        )

    def _build_bundle(
        self,
        template: (
            CalibrationScenarioTemplate
        ),
    ) -> DiagnosticCalibrationScenarioBundle:
        return (
            self._scenario_service
            .build(
                scenario_id=(
                    template.scenario_id
                ),

                scenario_name=(
                    template.scenario_name
                ),

                organization=(
                    template.organization
                ),

                evidence_contract=(
                    template
                    .evidence_contract
                ),

                narrative_seed=(
                    template.narrative_seed
                ),

                planted_primary_conditions=(
                    template
                    .planted_primary_conditions
                ),

                planted_secondary_conditions=(
                    template
                    .planted_secondary_conditions
                ),

                expected_top_k=(
                    template.expected_top_k
                ),

                intended_difficulty=(
                    template
                    .intended_difficulty
                ),

                intended_ambiguity=(
                    template
                    .intended_ambiguity
                ),

                oracle_notes=(
                    template.oracle_notes
                ),
            )
        )

    def _receipt_from_write(
        self,
        *,
        bundle: (
            DiagnosticCalibrationScenarioBundle
        ),
        write_result: (
            DiagnosticCalibrationCorpusWriteResult
        ),
    ) -> CalibrationGeneratedScenarioReceipt:
        return (
            CalibrationGeneratedScenarioReceipt(
                scenario_id=(
                    bundle
                    .public_scenario
                    .scenario_id
                ),

                public_hash=(
                    bundle
                    .public_scenario
                    .public_hash
                ),

                oracle_hash=(
                    bundle
                    .oracle
                    .oracle_hash
                ),

                bundle_hash=(
                    bundle
                    .bundle_hash
                ),

                manifest_hash=(
                    write_result
                    .manifest
                    .manifest_hash
                ),

                scenario_directory=(
                    write_result
                    .scenario_directory
                ),

                reused_existing=(
                    write_result
                    .reused_existing
                ),
            )
        )

    def _stable_receipt_dict(
        self,
        receipt: (
            CalibrationGeneratedScenarioReceipt
        ),
    ) -> dict[str, Any]:
        payload = (
            receipt.to_dict()
        )

        payload.pop(
            "reused_existing",
            None,
        )

        return payload

    def _validate_templates(
        self,
        templates: tuple[
            CalibrationScenarioTemplate,
            ...,
        ],
    ) -> None:
        scenario_ids = [
            template.scenario_id
            for template
            in templates
        ]

        if (
            len(
                scenario_ids
            )
            != len(
                set(
                    scenario_ids
                )
            )
        ):
            raise (
                DiagnosticCalibrationCorpusGeneratorError(
                    "Calibration templates contain "
                    "duplicate scenario_id values."
                )
            )

        for template in templates:
            if (
                not isinstance(
                    template.scenario_id,
                    str,
                )
                or not template
                .scenario_id
                .strip()
            ):
                raise (
                    DiagnosticCalibrationCorpusGeneratorError(
                        "Each calibration template must "
                        "have a non-empty scenario_id."
                    )
                )

    def _write_corpus_manifest(
        self,
        *,
        path: Path,
        result: (
            DiagnosticCalibrationCorpusGenerationResult
        ),
    ) -> None:
        payload = (
            result.to_dict()
        )

        stable_payload = dict(
            payload
        )

        stable_payload[
            "scenarios"
        ] = [
            self._stable_receipt_dict(
                scenario
            )
            for scenario
            in result.scenarios
        ]

        if path.exists():
            try:
                existing = json.loads(
                    path.read_text(
                        encoding="utf-8"
                    )
                )

            except (
                OSError,
                json.JSONDecodeError,
            ) as exc:
                raise (
                    DiagnosticCalibrationCorpusGeneratorError(
                        "Unable to read existing "
                        "calibration corpus manifest."
                    )
                ) from exc

            if canonical_json(
                existing
            ) != canonical_json(
                stable_payload
            ):
                raise (
                    DiagnosticCalibrationCorpusGeneratorError(
                        "Existing calibration corpus "
                        "manifest does not match "
                        "deterministic generation."
                    )
                )

            return

        path.write_text(
            json.dumps(
                stable_payload,
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )