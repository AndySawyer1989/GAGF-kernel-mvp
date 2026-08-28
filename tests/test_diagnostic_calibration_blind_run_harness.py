from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path

import pytest

from backend.app.gagf.diagnostic_calibration_blind_run_harness import (
    CALIBRATION_BLIND_RUN_HARNESS_AUTHORITY,
    CalibrationBlindRunHarnessError,
    CalibrationBlindRunPaths,
    DiagnosticCalibrationBlindRunHarnessService,
)
from backend.app.gagf.diagnostic_calibration_blind_evidence_intake_bridge import (
    CommercialHierarchyContext,
)


@dataclass
class FakeEvidence:
    scenario_id: str = "scenario-001"
    public_hash: str = "a" * 64
    generator_id: str = "Gemini"
    generation_id: str = "generation-001"
    evidence_hash: str = "b" * 64
    event_count: int = 4
    work_item_ids: tuple[str, ...] = (
        "work-1",
        "work-2",
    )
    team_ids: tuple[str, ...] = (
        "team-1",
        "team-2",
    )
    lifecycle_instance_ids: tuple[str, ...] = (
        "life-1",
        "life-2",
    )

    def to_dict(self):
        return {
            "scenario_id":
                self.scenario_id,

            "public_hash":
                self.public_hash,

            "generator_id":
                self.generator_id,

            "generation_id":
                self.generation_id,

            "evidence_hash":
                self.evidence_hash,
        }


@dataclass
class FakeIntake:
    hierarchy_key: str = (
        "tenant/client/engagement/assessment"
    )


@dataclass
class FakeExecution:
    scenario_id: str = "scenario-001"
    public_hash: str = "a" * 64

    generator_id: str = "Gemini"
    generation_id: str = "generation-001"

    hierarchy_key: str = (
        "tenant/client/engagement/assessment"
    )

    blind_evidence_hash: str = "b" * 64
    preflight_intake_hash: str = "c" * 64

    assessment_execution_request_hash: str = (
        "d" * 64
    )

    application_completed: bool = True
    repository_chain_valid: bool = True

    leading_candidate_category: str = (
        "APPROVAL_DELAYED"
    )

    primary_diagnosis_summary_hash: str = (
        "e" * 64
    )

    separation_summary_hash: str = (
        "f" * 64
    )


@dataclass
class FakeEvaluation:
    scenario_id: str = "scenario-001"

    leading_candidate_category: str = (
        "APPROVAL_DELAYED"
    )

    first_primary_rank: int = 1

    reciprocal_rank: float = 1.0

    rank_1_hit: bool = True
    top_2_hit: bool = True
    top_3_hit: bool = True

    candidate_count: int = 3

    leading_structural_level: str = "HIGH"

    leading_evidence_quality: float = 0.9

    absolute_separation: float = 0.1
    relative_separation: float = 0.12

    evaluation_hash: str = "9" * 64

    def to_dict(self):
        return {
            "scenario_id":
                self.scenario_id,

            "leading_candidate_category":
                self.leading_candidate_category,

            "first_primary_rank":
                self.first_primary_rank,

            "reciprocal_rank":
                self.reciprocal_rank,

            "rank_1_hit":
                self.rank_1_hit,

            "top_2_hit":
                self.top_2_hit,

            "top_3_hit":
                self.top_3_hit,

            "candidate_count":
                self.candidate_count,

            "leading_structural_level":
                self.leading_structural_level,

            "leading_evidence_quality":
                self.leading_evidence_quality,

            "absolute_separation":
                self.absolute_separation,

            "relative_separation":
                self.relative_separation,

            "evaluation_hash":
                self.evaluation_hash,
        }


class FakeEvidenceService:
    def __init__(self):
        self.calls = 0

    def validate(
        self,
        *,
        public_scenario,
        generator_payload,
    ):
        self.calls += 1

        return FakeEvidence(
            scenario_id=(
                generator_payload[
                    "scenario_id"
                ]
            ),
            public_hash=(
                generator_payload[
                    "public_hash"
                ]
            ),
            generator_id=(
                generator_payload[
                    "generator_id"
                ]
            ),
            generation_id=(
                generator_payload[
                    "generation_id"
                ]
            ),
        )


class FakeIntakeService:
    def __init__(self):
        self.calls = 0

    def ingest(
        self,
        *,
        context,
        evidence,
    ):
        self.calls += 1

        return FakeIntake()


class FakeExecutionService:
    def __init__(self):
        self.calls = 0

    def execute(
        self,
        *,
        database_path,
        context,
        evidence,
    ):
        self.calls += 1

        return FakeExecution(
            scenario_id=(
                evidence.scenario_id
            ),
            public_hash=(
                evidence.public_hash
            ),
            generator_id=(
                evidence.generator_id
            ),
            generation_id=(
                evidence.generation_id
            ),
            blind_evidence_hash=(
                evidence.evidence_hash
            ),
        )


class FakeEvaluationService:
    def __init__(self):
        self.calls = 0
        self.oracle_seen = None

    def evaluate(
        self,
        *,
        execution,
        oracle,
    ):
        self.calls += 1
        self.oracle_seen = oracle

        return FakeEvaluation(
            scenario_id=(
                execution.scenario_id
            )
        )


class OracleBoundaryEvaluationService(
    FakeEvaluationService
):
    def __init__(
        self,
        *,
        freeze_path: Path,
    ):
        super().__init__()

        self.freeze_path = (
            freeze_path
        )

    def evaluate(
        self,
        *,
        execution,
        oracle,
    ):
        assert (
            self.freeze_path.exists()
        )

        freeze_payload = json.loads(
            self.freeze_path.read_text(
                encoding="utf-8"
            )
        )

        assert (
            freeze_payload[
                "oracle_opened"
            ]
            is False
        )

        assert (
            freeze_payload[
                "boundary"
            ]
            ==
            "DIAGNOSTIC_FROZEN_BEFORE_ORACLE"
        )

        return super().evaluate(
            execution=execution,
            oracle=oracle,
        )


def write_json(
    path: Path,
    payload,
):
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    path.write_text(
        json.dumps(
            payload
        ),
        encoding="utf-8",
    )


def public_payload():
    return {
        "scenario_id":
            "scenario-001",

        "scenario_name":
            "Harness Test",

        "organization": {
            "organization_type":
                "Synthetic",

            "operating_model":
                "Cross-functional",

            "business_domain":
                "Services",

            "team_count":
                3,

            "actor_count":
                12,

            "workflow_count":
                4,

            "observation_days":
                10,
        },

        "evidence_contract": {
            "allowed_constraint_categories": [
                "APPROVAL_DELAYED",
                "DEPENDENCY_WAIT",
                "WORK_BLOCKED",
            ],

            "minimum_event_count":
                4,

            "maximum_event_count":
                8,

            "minimum_work_item_count":
                2,

            "maximum_work_item_count":
                4,

            "require_multiple_teams":
                True,

            "require_multiple_lifecycles":
                True,

            "require_temporal_ordering":
                True,

            "evidence_quality_floor":
                0.75,

            "evidence_quality_ceiling":
                0.98,
        },

        "narrative_seed":
            "Synthetic harness scenario.",

        "public_hash":
            "a" * 64,

        "schema_version":
            "1.0.0",
    }


def generator_payload():
    return {
        "scenario_id":
            "scenario-001",

        "public_hash":
            "a" * 64,

        "generator_id":
            "Gemini",

        "generation_id":
            "generation-001",

        "evidence_records": [],
    }


def oracle_payload():
    return {
        "scenario_id":
            "scenario-001",

        "public_hash":
            "a" * 64,

        "oracle_hash":
            "8" * 64,

        "planted_primary_conditions": [
            "APPROVAL_DELAYED",
        ],

        "planted_secondary_conditions": [
            "DEPENDENCY_WAIT",
        ],

        "expected_top_k":
            3,

        "intended_difficulty":
            "moderate",

        "intended_ambiguity":
            "moderate",
    }


def context():
    return (
        CommercialHierarchyContext(
            tenant_id="tenant",
            client_id="client",
            engagement_id="engagement",
            assessment_id="assessment",
        )
    )


def paths(
    tmp_path: Path,
):
    return (
        CalibrationBlindRunPaths(
            public_scenario_path=(
                tmp_path
                / "public.json"
            ),

            generator_payload_path=(
                tmp_path
                / "generated.json"
            ),

            sealed_oracle_path=(
                tmp_path
                / "oracle.json"
            ),

            database_path=(
                tmp_path
                / "assessment.sqlite3"
            ),

            validated_evidence_path=(
                tmp_path
                / "validated.json"
            ),

            diagnostic_freeze_path=(
                tmp_path
                / "freeze.json"
            ),

            evaluation_path=(
                tmp_path
                / "evaluation.json"
            ),
        )
    )


def prepare(
    tmp_path: Path,
):
    result = paths(
        tmp_path
    )

    write_json(
        result.public_scenario_path,
        public_payload(),
    )

    write_json(
        result.generator_payload_path,
        generator_payload(),
    )

    write_json(
        result.sealed_oracle_path,
        oracle_payload(),
    )

    return result


def service(
    *,
    evaluation_service=None,
):
    return (
        DiagnosticCalibrationBlindRunHarnessService(
            blind_evidence_service=(
                FakeEvidenceService()
            ),

            intake_bridge_service=(
                FakeIntakeService()
            ),

            execution_service=(
                FakeExecutionService()
            ),

            evaluation_service=(
                evaluation_service
                or
                FakeEvaluationService()
            ),
        )
    )


def test_runs_complete_blind_calibration(
    tmp_path,
):
    run_paths = prepare(
        tmp_path
    )

    result = service().run(
        context=context(),
        paths=run_paths,
    )

    assert (
        result.scenario_id
        == "scenario-001"
    )

    assert (
        result.generator_id
        == "Gemini"
    )

    assert (
        result.rank_1_hit
        is True
    )


def test_validated_evidence_is_persisted(
    tmp_path,
):
    run_paths = prepare(
        tmp_path
    )

    service().run(
        context=context(),
        paths=run_paths,
    )

    assert (
        run_paths
        .validated_evidence_path
        .exists()
    )


def test_diagnostic_freeze_is_persisted(
    tmp_path,
):
    run_paths = prepare(
        tmp_path
    )

    service().run(
        context=context(),
        paths=run_paths,
    )

    assert (
        run_paths
        .diagnostic_freeze_path
        .exists()
    )


def test_evaluation_is_persisted(
    tmp_path,
):
    run_paths = prepare(
        tmp_path
    )

    service().run(
        context=context(),
        paths=run_paths,
    )

    assert (
        run_paths
        .evaluation_path
        .exists()
    )


def test_freeze_occurs_before_oracle_evaluation(
    tmp_path,
):
    run_paths = prepare(
        tmp_path
    )

    evaluator = (
        OracleBoundaryEvaluationService(
            freeze_path=(
                run_paths
                .diagnostic_freeze_path
            )
        )
    )

    service(
        evaluation_service=(
            evaluator
        )
    ).run(
        context=context(),
        paths=run_paths,
    )

    assert evaluator.calls == 1


def test_freeze_marks_oracle_unopened(
    tmp_path,
):
    run_paths = prepare(
        tmp_path
    )

    result = service().run(
        context=context(),
        paths=run_paths,
    )

    assert (
        result.freeze.oracle_opened
        is False
    )


def test_freeze_uses_explicit_boundary(
    tmp_path,
):
    run_paths = prepare(
        tmp_path
    )

    result = service().run(
        context=context(),
        paths=run_paths,
    )

    assert (
        result.freeze.boundary
        ==
        "DIAGNOSTIC_FROZEN_BEFORE_ORACLE"
    )


def test_freeze_hash_is_deterministic(
    tmp_path,
):
    first_paths = prepare(
        tmp_path / "first"
    )

    second_paths = prepare(
        tmp_path / "second"
    )

    first = service().run(
        context=context(),
        paths=first_paths,
    )

    second = service().run(
        context=context(),
        paths=second_paths,
    )

    assert (
        first.freeze.freeze_hash
        ==
        second.freeze.freeze_hash
    )


def test_freeze_binds_evidence_hash(
    tmp_path,
):
    run_paths = prepare(
        tmp_path
    )

    result = service().run(
        context=context(),
        paths=run_paths,
    )

    assert (
        result.freeze
        .blind_evidence_hash
        ==
        result.evidence.evidence_hash
    )


def test_refuses_existing_database(
    tmp_path,
):
    run_paths = prepare(
        tmp_path
    )

    run_paths.database_path.write_text(
        "existing",
        encoding="utf-8",
    )

    with pytest.raises(
        CalibrationBlindRunHarnessError,
        match="Refusing to overwrite",
    ):
        service().run(
            context=context(),
            paths=run_paths,
        )


def test_refuses_existing_freeze(
    tmp_path,
):
    run_paths = prepare(
        tmp_path
    )

    run_paths.diagnostic_freeze_path.write_text(
        "{}",
        encoding="utf-8",
    )

    with pytest.raises(
        CalibrationBlindRunHarnessError,
        match="Refusing to overwrite",
    ):
        service().run(
            context=context(),
            paths=run_paths,
        )


def test_refuses_existing_evaluation(
    tmp_path,
):
    run_paths = prepare(
        tmp_path
    )

    run_paths.evaluation_path.write_text(
        "{}",
        encoding="utf-8",
    )

    with pytest.raises(
        CalibrationBlindRunHarnessError,
        match="Refusing to overwrite",
    ):
        service().run(
            context=context(),
            paths=run_paths,
        )


def test_missing_public_scenario_is_rejected(
    tmp_path,
):
    run_paths = prepare(
        tmp_path
    )

    run_paths.public_scenario_path.unlink()

    with pytest.raises(
        CalibrationBlindRunHarnessError,
        match="does not exist",
    ):
        service().run(
            context=context(),
            paths=run_paths,
        )


def test_missing_generator_payload_is_rejected(
    tmp_path,
):
    run_paths = prepare(
        tmp_path
    )

    run_paths.generator_payload_path.unlink()

    with pytest.raises(
        CalibrationBlindRunHarnessError,
        match="does not exist",
    ):
        service().run(
            context=context(),
            paths=run_paths,
        )


def test_missing_oracle_is_rejected(
    tmp_path,
):
    run_paths = prepare(
        tmp_path
    )

    run_paths.sealed_oracle_path.unlink()

    with pytest.raises(
        CalibrationBlindRunHarnessError,
        match="does not exist",
    ):
        service().run(
            context=context(),
            paths=run_paths,
        )


def test_invalid_repository_chain_is_rejected(
    tmp_path,
):
    class InvalidExecutionService(
        FakeExecutionService
    ):
        def execute(
            self,
            *,
            database_path,
            context,
            evidence,
        ):
            result = super().execute(
                database_path=database_path,
                context=context,
                evidence=evidence,
            )

            result.repository_chain_valid = False

            return result

    run_paths = prepare(
        tmp_path
    )

    harness = (
        DiagnosticCalibrationBlindRunHarnessService(
            blind_evidence_service=(
                FakeEvidenceService()
            ),
            intake_bridge_service=(
                FakeIntakeService()
            ),
            execution_service=(
                InvalidExecutionService()
            ),
            evaluation_service=(
                FakeEvaluationService()
            ),
        )
    )

    with pytest.raises(
        CalibrationBlindRunHarnessError,
        match="repository chain",
    ):
        harness.run(
            context=context(),
            paths=run_paths,
        )


def test_evidence_hash_mismatch_is_rejected(
    tmp_path,
):
    class WrongHashExecutionService(
        FakeExecutionService
    ):
        def execute(
            self,
            *,
            database_path,
            context,
            evidence,
        ):
            result = super().execute(
                database_path=database_path,
                context=context,
                evidence=evidence,
            )

            result.blind_evidence_hash = (
                "0" * 64
            )

            return result

    run_paths = prepare(
        tmp_path
    )

    harness = (
        DiagnosticCalibrationBlindRunHarnessService(
            blind_evidence_service=(
                FakeEvidenceService()
            ),
            intake_bridge_service=(
                FakeIntakeService()
            ),
            execution_service=(
                WrongHashExecutionService()
            ),
            evaluation_service=(
                FakeEvaluationService()
            ),
        )
    )

    with pytest.raises(
        CalibrationBlindRunHarnessError,
        match="evidence hash",
    ):
        harness.run(
            context=context(),
            paths=run_paths,
        )


def test_result_has_calibration_only_authority(
    tmp_path,
):
    run_paths = prepare(
        tmp_path
    )

    result = service().run(
        context=context(),
        paths=run_paths,
    )

    assert (
        result.authority
        ==
        CALIBRATION_BLIND_RUN_HARNESS_AUTHORITY
    )


def test_result_contains_no_confidence(
    tmp_path,
):
    run_paths = prepare(
        tmp_path
    )

    result = service().run(
        context=context(),
        paths=run_paths,
    )

    payload = result.to_dict()

    assert "confidence" not in payload

    assert (
        "confidence_band"
        not in payload
    )

    assert (
        "confidence_threshold"
        not in payload
    )


def test_result_contains_no_root_cause(
    tmp_path,
):
    run_paths = prepare(
        tmp_path
    )

    result = service().run(
        context=context(),
        paths=run_paths,
    )

    payload = result.to_dict()

    assert "root_cause" not in payload

    assert (
        "intervention_authority"
        not in payload
    )