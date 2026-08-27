from __future__ import annotations

import json

import pytest

from backend.app.gagf.diagnostic_calibration_blind_diagnostic_execution import (
    BLIND_CALIBRATION_DIAGNOSTIC_EXECUTION_AUTHORITY,
    BlindCalibrationDiagnosticExecutionError,
    DiagnosticCalibrationBlindDiagnosticExecutionService,
)
from backend.app.gagf.diagnostic_calibration_blind_evidence import (
    DiagnosticCalibrationBlindEvidenceService,
)
from backend.app.gagf.diagnostic_calibration_scenario import (
    CalibrationDifficulty,
    CalibrationEvidenceGenerationContract,
    CalibrationOrganizationContext,
    DiagnosticCalibrationScenarioService,
)
from backend.app.gagf.governance_assessment_isolation import (
    CommercialHierarchyContext,
)
from backend.app.gagf.governance_assessment_repository import (
    GovernanceAssessmentRepository,
)


def build_public_scenario():
    return (
        DiagnosticCalibrationScenarioService()
        .build(
            scenario_id=(
                "FIP-CAL-EXEC-001"
            ),

            scenario_name=(
                "Blind Diagnostic Execution Test"
            ),

            organization=(
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
                    team_count=2,
                    actor_count=12,
                    workflow_count=2,
                    observation_days=10,
                )
            ),

            evidence_contract=(
                CalibrationEvidenceGenerationContract(
                    allowed_constraint_categories=(
                        "APPROVAL_DELAYED",
                        "DEPENDENCY_WAIT",
                        "WORK_BLOCKED",
                    ),
                    minimum_event_count=8,
                    maximum_event_count=10,
                    minimum_work_item_count=4,
                    maximum_work_item_count=6,
                    require_multiple_teams=True,
                    require_multiple_lifecycles=True,
                    require_temporal_ordering=True,
                    evidence_quality_floor=0.80,
                    evidence_quality_ceiling=0.98,
                )
            ),

            narrative_seed=(
                "A synthetic organization experiences "
                "recurring delivery delays across "
                "multiple teams and workflows."
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
                "Hidden calibration ambiguity."
            ),

            oracle_notes=(
                "Hidden calibration-only notes."
            ),
        )
        .public_scenario
    )


def build_payload():
    public = (
        build_public_scenario()
    )

    event_types = (
        "APPROVAL_DELAYED",
        "APPROVAL_DELAYED",
        "DEPENDENCY_WAIT",
        "APPROVAL_DELAYED",
        "WORK_BLOCKED",
        "APPROVAL_DELAYED",
        "DEPENDENCY_WAIT",
        "WORK_BLOCKED",
    )

    records = []

    for index, event_type in enumerate(
        event_types,
        start=1,
    ):
        records.append(
            {
                "event_id":
                    f"event-{index:03d}",

                "event_type":
                    event_type,

                "occurred_at":
                    (
                        "2026-01-"
                        f"{index:02d}"
                        "T12:00:00Z"
                    ),

                "attributes": {
                    "work_item_id":
                        (
                            "work-"
                            f"{((index - 1) % 4) + 1}"
                        ),

                    "actor_id":
                        f"actor-{index}",

                    "team_id":
                        (
                            "team-"
                            f"{((index - 1) % 2) + 1}"
                        ),

                    "lifecycle_instance_id":
                        (
                            "lifecycle-"
                            f"{((index - 1) % 2) + 1}"
                        ),

                    "duration_minutes":
                        str(
                            20 + (
                                index * 10
                            )
                        ),

                    "evidence_quality":
                        (
                            "0.90"
                            if index % 2
                            else "0.92"
                        ),
                },
            }
        )

    return {
        "scenario_id":
            public.scenario_id,

        "public_hash":
            public.public_hash,

        "generator_id":
            "blind-calibration-generator",

        "generation_id":
            "generation-001",

        "evidence_records":
            records,
    }


def build_evidence():
    public = (
        build_public_scenario()
    )

    return (
        DiagnosticCalibrationBlindEvidenceService()
        .validate(
            public_scenario=(
                public
            ),
            generator_payload=(
                build_payload()
            ),
        )
    )


def build_context(
    *,
    assessment_id="assessment-001",
):
    return (
        CommercialHierarchyContext(
            tenant_id=(
                "calibration-tenant"
            ),
            client_id=(
                "calibration-client"
            ),
            engagement_id=(
                "calibration-engagement"
            ),
            assessment_id=(
                assessment_id
            ),
        )
    )


def execute(
    tmp_path,
    *,
    filename="calibration.sqlite3",
    assessment_id="assessment-001",
):
    return (
        DiagnosticCalibrationBlindDiagnosticExecutionService()
        .execute(
            database_path=(
                tmp_path
                / filename
            ),
            context=(
                build_context(
                    assessment_id=(
                        assessment_id
                    )
                )
            ),
            evidence=(
                build_evidence()
            ),
        )
    )


def test_executes_real_governance_application(
    tmp_path,
):
    result = execute(
        tmp_path
    )

    assert (
        result.application_completed
        is True
    )


def test_execution_preserves_hierarchy(
    tmp_path,
):
    result = execute(
        tmp_path
    )

    assert (
        result.hierarchy_key
        ==
        (
            "calibration-tenant/"
            "calibration-client/"
            "calibration-engagement/"
            "assessment-001"
        )
    )


def test_execution_creates_real_database(
    tmp_path,
):
    path = (
        tmp_path
        / "calibration.sqlite3"
    )

    execute(
        tmp_path
    )

    assert path.is_file()


def test_execution_persists_assessment_record(
    tmp_path,
):
    result = execute(
        tmp_path
    )

    repository = (
        GovernanceAssessmentRepository(
            result.database_path
        )
    )

    assessment = (
        repository.get_assessment(
            context=build_context()
        )
    )

    assert (
        assessment.status
        == "complete"
    )


def test_execution_persists_evidence_intake_batch(
    tmp_path,
):
    result = execute(
        tmp_path
    )

    repository = (
        GovernanceAssessmentRepository(
            result.database_path
        )
    )

    artifacts = (
        repository.list_artifacts(
            context=build_context(),
            artifact_type=(
                "evidence-intake-batch"
            ),
        )
    )

    assert len(
        artifacts
    ) == 1


def test_execution_persists_friction_summary(
    tmp_path,
):
    result = execute(
        tmp_path
    )

    repository = (
        GovernanceAssessmentRepository(
            result.database_path
        )
    )

    artifacts = (
        repository.list_artifacts(
            context=build_context(),
            artifact_type=(
                "friction-summary"
            ),
        )
    )

    assert len(
        artifacts
    ) == 1


def test_execution_persists_diagnostic_separation(
    tmp_path,
):
    result = execute(
        tmp_path
    )

    repository = (
        GovernanceAssessmentRepository(
            result.database_path
        )
    )

    artifacts = (
        repository.list_artifacts(
            context=build_context(),
            artifact_type=(
                "diagnostic-separation-evidence"
            ),
        )
    )

    assert len(
        artifacts
    ) == 1


def test_execution_repository_chain_is_valid(
    tmp_path,
):
    result = execute(
        tmp_path
    )

    repository = (
        GovernanceAssessmentRepository(
            result.database_path
        )
    )

    assert (
        repository.verify_chain(
            context=build_context()
        )
        is True
    )

    assert (
        result.repository_chain_valid
        is True
    )


def test_primary_projection_is_verified(
    tmp_path,
):
    result = execute(
        tmp_path
    )

    assert (
        result.separation_projection
        .primary_projection_verified
        is True
    )


def test_structural_projection_is_verified(
    tmp_path,
):
    result = execute(
        tmp_path
    )

    assert (
        result.separation_projection
        .structural_projection_verified
        is True
    )


def test_structural_classification_is_verified(
    tmp_path,
):
    result = execute(
        tmp_path
    )

    assert (
        result.separation_projection
        .structural_classification_verified
        is True
    )


def test_execution_produces_ranked_candidate(
    tmp_path,
):
    result = execute(
        tmp_path
    )

    assert (
        result.leading_candidate_category
        is not None
    )


def test_execution_preserves_blind_evidence_hash(
    tmp_path,
):
    evidence = (
        build_evidence()
    )

    result = (
        DiagnosticCalibrationBlindDiagnosticExecutionService()
        .execute(
            database_path=(
                tmp_path
                / "calibration.sqlite3"
            ),
            context=(
                build_context()
            ),
            evidence=(
                evidence
            ),
        )
    )

    assert (
        result.blind_evidence_hash
        ==
        evidence.evidence_hash
    )


def test_execution_records_real_preflight_intake_hash(
    tmp_path,
):
    result = execute(
        tmp_path
    )

    assert (
        isinstance(
            result.preflight_intake_hash,
            str,
        )
    )

    assert (
        len(
            result.preflight_intake_hash
        )
        == 64
    )


def test_execution_request_hash_is_present(
    tmp_path,
):
    result = execute(
        tmp_path
    )

    assert (
        len(
            result
            .assessment_execution_request_hash
        )
        == 64
    )


def test_execution_uses_calibration_diagnostic_authority(
    tmp_path,
):
    result = execute(
        tmp_path
    )

    assert (
        result.authority
        ==
        BLIND_CALIBRATION_DIAGNOSTIC_EXECUTION_AUTHORITY
    )


def test_execution_rejects_existing_database(
    tmp_path,
):
    path = (
        tmp_path
        / "calibration.sqlite3"
    )

    path.write_text(
        "existing",
        encoding="utf-8",
    )

    with pytest.raises(
        BlindCalibrationDiagnosticExecutionError,
        match="fresh database",
    ):
        (
            DiagnosticCalibrationBlindDiagnosticExecutionService()
            .execute(
                database_path=path,
                context=build_context(),
                evidence=build_evidence(),
            )
        )


def test_same_evidence_produces_same_separation_summary(
    tmp_path,
):
    first = execute(
        tmp_path,
        filename="first.sqlite3",
        assessment_id="assessment-001",
    )

    second = execute(
        tmp_path,
        filename="second.sqlite3",
        assessment_id="assessment-001",
    )

    assert (
        first.separation_summary_hash
        ==
        second.separation_summary_hash
    )


def test_result_contains_no_oracle_or_confidence_fields(
    tmp_path,
):
    payload = (
        execute(
            tmp_path
        )
        .to_dict()
    )

    serialized = (
        json.dumps(
            payload,
            sort_keys=True,
        )
        .lower()
    )

    forbidden = (
        "sealed_oracle",
        "oracle_hash",
        "oracle_notes",
        "planted_primary_conditions",
        "planted_secondary_conditions",
        "expected_top_k",
        "expected_rank",
        "confidence_level",
        "confidence_threshold",
        "root_cause",
        "intervention_authority",
    )

    for field in forbidden:
        assert (
            field
            not in serialized
        )


def test_result_does_not_claim_correctness(
    tmp_path,
):
    payload = (
        execute(
            tmp_path
        )
        .to_dict()
    )

    assert (
        "correctness"
        not in payload
    )

    assert (
        "correct"
        not in payload
    )


def test_result_exposes_separation_hashes(
    tmp_path,
):
    result = execute(
        tmp_path
    )

    assert (
        len(
            result.separation_summary_hash
        )
        == 64
    )

    assert (
        len(
            result
            .primary_diagnosis_summary_hash
        )
        == 64
    )