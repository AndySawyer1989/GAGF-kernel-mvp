from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from backend.app.gagf.governance_assessment_repository import (
    canonical_json,
    sha256_text,
)


DIAGNOSTIC_CALIBRATION_SCENARIO_VERSION = "1.0.0"

DIAGNOSTIC_CALIBRATION_AUTHORITY = (
    "GAGF_FIP_CALIBRATION_ONLY"
)


class DiagnosticCalibrationScenarioError(
    RuntimeError
):
    """
    Raised when a calibration scenario violates
    public/oracle isolation or deterministic contract rules.
    """


class CalibrationDifficulty(
    str,
    Enum,
):
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"
    ADVERSARIAL = "ADVERSARIAL"


@dataclass(
    frozen=True,
    slots=True,
)
class CalibrationOrganizationContext:
    organization_type: str
    operating_model: str
    business_domain: str

    team_count: int
    actor_count: int
    workflow_count: int

    observation_days: int

    def to_dict(
        self,
    ) -> dict[str, Any]:
        return {
            "organization_type":
                self.organization_type,

            "operating_model":
                self.operating_model,

            "business_domain":
                self.business_domain,

            "team_count":
                self.team_count,

            "actor_count":
                self.actor_count,

            "workflow_count":
                self.workflow_count,

            "observation_days":
                self.observation_days,
        }


@dataclass(
    frozen=True,
    slots=True,
)
class CalibrationEvidenceGenerationContract:
    allowed_constraint_categories: tuple[
        str,
        ...,
    ]

    minimum_event_count: int
    maximum_event_count: int

    minimum_work_item_count: int
    maximum_work_item_count: int

    require_multiple_teams: bool
    require_multiple_lifecycles: bool
    require_temporal_ordering: bool

    evidence_quality_floor: float
    evidence_quality_ceiling: float

    def to_dict(
        self,
    ) -> dict[str, Any]:
        return {
            "allowed_constraint_categories":
                list(
                    self.allowed_constraint_categories
                ),

            "minimum_event_count":
                self.minimum_event_count,

            "maximum_event_count":
                self.maximum_event_count,

            "minimum_work_item_count":
                self.minimum_work_item_count,

            "maximum_work_item_count":
                self.maximum_work_item_count,

            "require_multiple_teams":
                self.require_multiple_teams,

            "require_multiple_lifecycles":
                self.require_multiple_lifecycles,

            "require_temporal_ordering":
                self.require_temporal_ordering,

            "evidence_quality_floor":
                self.evidence_quality_floor,

            "evidence_quality_ceiling":
                self.evidence_quality_ceiling,
        }


@dataclass(
    frozen=True,
    slots=True,
)
class CalibrationPublicScenario:
    scenario_id: str
    scenario_name: str

    organization: (
        CalibrationOrganizationContext
    )

    evidence_contract: (
        CalibrationEvidenceGenerationContract
    )

    narrative_seed: str

    public_hash: str

    schema_version: str = (
        DIAGNOSTIC_CALIBRATION_SCENARIO_VERSION
    )

    def to_dict(
        self,
    ) -> dict[str, Any]:
        return {
            "scenario_id":
                self.scenario_id,

            "scenario_name":
                self.scenario_name,

            "organization":
                self.organization.to_dict(),

            "evidence_contract":
                self.evidence_contract.to_dict(),

            "narrative_seed":
                self.narrative_seed,

            "public_hash":
                self.public_hash,

            "schema_version":
                self.schema_version,
        }


@dataclass(
    frozen=True,
    slots=True,
)
class CalibrationOracle:
    scenario_id: str

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

    public_hash: str

    oracle_hash: str

    authority: str = (
        DIAGNOSTIC_CALIBRATION_AUTHORITY
    )

    schema_version: str = (
        DIAGNOSTIC_CALIBRATION_SCENARIO_VERSION
    )

    def to_dict(
        self,
    ) -> dict[str, Any]:
        return {
            "scenario_id":
                self.scenario_id,

            "planted_primary_conditions":
                list(
                    self.planted_primary_conditions
                ),

            "planted_secondary_conditions":
                list(
                    self.planted_secondary_conditions
                ),

            "expected_top_k":
                self.expected_top_k,

            "intended_difficulty":
                self.intended_difficulty.value,

            "intended_ambiguity":
                self.intended_ambiguity,

            "oracle_notes":
                self.oracle_notes,

            "public_hash":
                self.public_hash,

            "oracle_hash":
                self.oracle_hash,

            "authority":
                self.authority,

            "schema_version":
                self.schema_version,
        }


@dataclass(
    frozen=True,
    slots=True,
)
class DiagnosticCalibrationScenarioBundle:
    public_scenario: (
        CalibrationPublicScenario
    )

    oracle: CalibrationOracle

    bundle_hash: str

    schema_version: str = (
        DIAGNOSTIC_CALIBRATION_SCENARIO_VERSION
    )

    def to_dict(
        self,
    ) -> dict[str, Any]:
        return {
            "public_scenario":
                self.public_scenario.to_dict(),

            "oracle":
                self.oracle.to_dict(),

            "bundle_hash":
                self.bundle_hash,

            "schema_version":
                self.schema_version,
        }


class DiagnosticCalibrationScenarioService:
    """
    Build deterministic calibration scenarios with a hard
    isolation boundary between public diagnostic input and
    calibration-only oracle information.

    The public scenario is safe to expose to evidence
    generation and diagnostic execution.

    The oracle must remain sealed until evaluation.

    Public Scenario != Oracle.
    Oracle != Diagnostic Input.
    Expected Diagnosis != Evidence.
    """

    def build(
        self,
        *,
        scenario_id: str,
        scenario_name: str,
        organization: (
            CalibrationOrganizationContext
        ),
        evidence_contract: (
            CalibrationEvidenceGenerationContract
        ),
        narrative_seed: str,
        planted_primary_conditions: tuple[
            str,
            ...,
        ],
        planted_secondary_conditions: tuple[
            str,
            ...,
        ],
        expected_top_k: int,
        intended_difficulty: (
            CalibrationDifficulty
        ),
        intended_ambiguity: str,
        oracle_notes: str,
    ) -> DiagnosticCalibrationScenarioBundle:
        self._validate_common(
            scenario_id=(
                scenario_id
            ),
            scenario_name=(
                scenario_name
            ),
            narrative_seed=(
                narrative_seed
            ),
            organization=(
                organization
            ),
            evidence_contract=(
                evidence_contract
            ),
        )

        self._validate_oracle(
            planted_primary_conditions=(
                planted_primary_conditions
            ),
            planted_secondary_conditions=(
                planted_secondary_conditions
            ),
            expected_top_k=(
                expected_top_k
            ),
            intended_ambiguity=(
                intended_ambiguity
            ),
            oracle_notes=(
                oracle_notes
            ),
        )

        public_payload = {
            "scenario_id":
                scenario_id,

            "scenario_name":
                scenario_name,

            "organization":
                organization.to_dict(),

            "evidence_contract":
                evidence_contract.to_dict(),

            "narrative_seed":
                narrative_seed,

            "schema_version":
                DIAGNOSTIC_CALIBRATION_SCENARIO_VERSION,
        }

        public_hash = sha256_text(
            canonical_json(
                public_payload
            )
        )

        public_scenario = (
            CalibrationPublicScenario(
                scenario_id=(
                    scenario_id
                ),

                scenario_name=(
                    scenario_name
                ),

                organization=(
                    organization
                ),

                evidence_contract=(
                    evidence_contract
                ),

                narrative_seed=(
                    narrative_seed
                ),

                public_hash=(
                    public_hash
                ),
            )
        )

        oracle_payload = {
            "scenario_id":
                scenario_id,

            "planted_primary_conditions":
                list(
                    planted_primary_conditions
                ),

            "planted_secondary_conditions":
                list(
                    planted_secondary_conditions
                ),

            "expected_top_k":
                expected_top_k,

            "intended_difficulty":
                intended_difficulty.value,

            "intended_ambiguity":
                intended_ambiguity,

            "oracle_notes":
                oracle_notes,

            "public_hash":
                public_hash,

            "authority":
                DIAGNOSTIC_CALIBRATION_AUTHORITY,

            "schema_version":
                DIAGNOSTIC_CALIBRATION_SCENARIO_VERSION,
        }

        oracle_hash = sha256_text(
            canonical_json(
                oracle_payload
            )
        )

        oracle = (
            CalibrationOracle(
                scenario_id=(
                    scenario_id
                ),

                planted_primary_conditions=(
                    planted_primary_conditions
                ),

                planted_secondary_conditions=(
                    planted_secondary_conditions
                ),

                expected_top_k=(
                    expected_top_k
                ),

                intended_difficulty=(
                    intended_difficulty
                ),

                intended_ambiguity=(
                    intended_ambiguity
                ),

                oracle_notes=(
                    oracle_notes
                ),

                public_hash=(
                    public_hash
                ),

                oracle_hash=(
                    oracle_hash
                ),
            )
        )

        bundle_payload = {
            "public_scenario":
                public_scenario.to_dict(),

            "oracle":
                oracle.to_dict(),

            "schema_version":
                DIAGNOSTIC_CALIBRATION_SCENARIO_VERSION,
        }

        bundle_hash = sha256_text(
            canonical_json(
                bundle_payload
            )
        )

        return (
            DiagnosticCalibrationScenarioBundle(
                public_scenario=(
                    public_scenario
                ),

                oracle=(
                    oracle
                ),

                bundle_hash=(
                    bundle_hash
                ),
            )
        )

    def public_payload(
        self,
        *,
        bundle: (
            DiagnosticCalibrationScenarioBundle
        ),
    ) -> dict[str, Any]:
        """
        Return the only payload permitted to cross into
        evidence generation or diagnostic execution.
        """

        return (
            bundle
            .public_scenario
            .to_dict()
        )

    def verify_bundle(
        self,
        *,
        bundle: (
            DiagnosticCalibrationScenarioBundle
        ),
    ) -> bool:
        public = (
            bundle.public_scenario
        )

        oracle = (
            bundle.oracle
        )

        if (
            public.scenario_id
            != oracle.scenario_id
        ):
            return False

        if (
            public.public_hash
            != oracle.public_hash
        ):
            return False

        public_payload = {
            "scenario_id":
                public.scenario_id,

            "scenario_name":
                public.scenario_name,

            "organization":
                public.organization.to_dict(),

            "evidence_contract":
                public.evidence_contract.to_dict(),

            "narrative_seed":
                public.narrative_seed,

            "schema_version":
                public.schema_version,
        }

        expected_public_hash = sha256_text(
            canonical_json(
                public_payload
            )
        )

        if (
            expected_public_hash
            != public.public_hash
        ):
            return False

        oracle_payload = {
            "scenario_id":
                oracle.scenario_id,

            "planted_primary_conditions":
                list(
                    oracle.planted_primary_conditions
                ),

            "planted_secondary_conditions":
                list(
                    oracle.planted_secondary_conditions
                ),

            "expected_top_k":
                oracle.expected_top_k,

            "intended_difficulty":
                oracle.intended_difficulty.value,

            "intended_ambiguity":
                oracle.intended_ambiguity,

            "oracle_notes":
                oracle.oracle_notes,

            "public_hash":
                oracle.public_hash,

            "authority":
                oracle.authority,

            "schema_version":
                oracle.schema_version,
        }

        expected_oracle_hash = sha256_text(
            canonical_json(
                oracle_payload
            )
        )

        if (
            expected_oracle_hash
            != oracle.oracle_hash
        ):
            return False

        bundle_payload = {
            "public_scenario":
                public.to_dict(),

            "oracle":
                oracle.to_dict(),

            "schema_version":
                bundle.schema_version,
        }

        expected_bundle_hash = sha256_text(
            canonical_json(
                bundle_payload
            )
        )

        return (
            expected_bundle_hash
            == bundle.bundle_hash
        )

    def _validate_common(
        self,
        *,
        scenario_id: str,
        scenario_name: str,
        narrative_seed: str,
        organization: (
            CalibrationOrganizationContext
        ),
        evidence_contract: (
            CalibrationEvidenceGenerationContract
        ),
    ) -> None:
        for field_name, value in (
            (
                "scenario_id",
                scenario_id,
            ),
            (
                "scenario_name",
                scenario_name,
            ),
            (
                "narrative_seed",
                narrative_seed,
            ),
        ):
            if (
                not isinstance(
                    value,
                    str,
                )
                or not value.strip()
            ):
                raise (
                    DiagnosticCalibrationScenarioError(
                        f"{field_name} must be a "
                        "non-empty string."
                    )
                )

        if organization.team_count < 1:
            raise (
                DiagnosticCalibrationScenarioError(
                    "team_count must be at least 1."
                )
            )

        if organization.actor_count < 1:
            raise (
                DiagnosticCalibrationScenarioError(
                    "actor_count must be at least 1."
                )
            )

        if organization.workflow_count < 1:
            raise (
                DiagnosticCalibrationScenarioError(
                    "workflow_count must be at least 1."
                )
            )

        if organization.observation_days < 1:
            raise (
                DiagnosticCalibrationScenarioError(
                    "observation_days must be at least 1."
                )
            )

        if (
            evidence_contract.minimum_event_count
            < 1
        ):
            raise (
                DiagnosticCalibrationScenarioError(
                    "minimum_event_count must be at least 1."
                )
            )

        if (
            evidence_contract.maximum_event_count
            <
            evidence_contract.minimum_event_count
        ):
            raise (
                DiagnosticCalibrationScenarioError(
                    "maximum_event_count must be greater "
                    "than or equal to minimum_event_count."
                )
            )

        if (
            evidence_contract.minimum_work_item_count
            < 1
        ):
            raise (
                DiagnosticCalibrationScenarioError(
                    "minimum_work_item_count must be "
                    "at least 1."
                )
            )

        if (
            evidence_contract.maximum_work_item_count
            <
            evidence_contract.minimum_work_item_count
        ):
            raise (
                DiagnosticCalibrationScenarioError(
                    "maximum_work_item_count must be "
                    "greater than or equal to "
                    "minimum_work_item_count."
                )
            )

        if not (
            0.0
            <=
            evidence_contract.evidence_quality_floor
            <=
            evidence_contract.evidence_quality_ceiling
            <=
            1.0
        ):
            raise (
                DiagnosticCalibrationScenarioError(
                    "evidence quality bounds must satisfy "
                    "0 <= floor <= ceiling <= 1."
                )
            )

        categories = (
            evidence_contract
            .allowed_constraint_categories
        )

        if not categories:
            raise (
                DiagnosticCalibrationScenarioError(
                    "allowed_constraint_categories "
                    "cannot be empty."
                )
            )

        if (
            len(
                categories
            )
            != len(
                set(
                    categories
                )
            )
        ):
            raise (
                DiagnosticCalibrationScenarioError(
                    "allowed_constraint_categories "
                    "cannot contain duplicates."
                )
            )

    def _validate_oracle(
        self,
        *,
        planted_primary_conditions: tuple[
            str,
            ...,
        ],
        planted_secondary_conditions: tuple[
            str,
            ...,
        ],
        expected_top_k: int,
        intended_ambiguity: str,
        oracle_notes: str,
    ) -> None:
        if not planted_primary_conditions:
            raise (
                DiagnosticCalibrationScenarioError(
                    "At least one planted primary "
                    "condition is required."
                )
            )

        if expected_top_k < 1:
            raise (
                DiagnosticCalibrationScenarioError(
                    "expected_top_k must be at least 1."
                )
            )

        if (
            expected_top_k
            <
            len(
                planted_primary_conditions
            )
        ):
            raise (
                DiagnosticCalibrationScenarioError(
                    "expected_top_k cannot be smaller "
                    "than the number of planted primary "
                    "conditions."
                )
            )

        all_conditions = (
            planted_primary_conditions
            +
            planted_secondary_conditions
        )

        if (
            len(
                all_conditions
            )
            != len(
                set(
                    all_conditions
                )
            )
        ):
            raise (
                DiagnosticCalibrationScenarioError(
                    "Primary and secondary planted "
                    "conditions must be unique."
                )
            )

        if (
            not intended_ambiguity.strip()
        ):
            raise (
                DiagnosticCalibrationScenarioError(
                    "intended_ambiguity must be "
                    "non-empty."
                )
            )

        if not oracle_notes.strip():
            raise (
                DiagnosticCalibrationScenarioError(
                    "oracle_notes must be non-empty."
                )
            )