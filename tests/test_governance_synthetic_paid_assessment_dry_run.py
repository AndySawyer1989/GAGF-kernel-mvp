from pathlib import Path

import pytest

from backend.app.gagf.governance_assessment_repository import (
    GovernanceAssessmentRepository,
)
from backend.app.gagf.governance_synthetic_paid_assessment_dry_run import (
    EXPECTED_FINAL_ARTIFACT_COUNT,
    SYNTHETIC_SCENARIO_TYPE,
    SyntheticPaidAssessmentDryRunError,
    SyntheticPaidAssessmentDryRunService,
    SyntheticPaidAssessmentScenario,
)


def test_runs_complete_synthetic_paid_assessment(tmp_path):
    database_path = tmp_path / "synthetic-paid-assessment.sqlite3"

    result = SyntheticPaidAssessmentDryRunService().run(
        database_path=database_path
    )

    assert result.scenario_type == SYNTHETIC_SCENARIO_TYPE
    assert result.synthetic is True
    assert result.dry_run_passed is True

    assert result.paid_work_authorized is True
    assert result.execution_handoff_ready is True
    assert result.assessment_execution_complete is True
    assert result.report_ready is True
    assert result.delivery_approved is True
    assert result.delivery_recorded is True
    assert result.client_receipt_acknowledged is True
    assert result.client_response_recorded is True
    assert result.lifecycle_persisted is True
    assert result.assessment_closed is True

    assert result.operator_workflow_stage == "closed"
    assert result.operator_required_action == "none"

    assert result.core_artifact_count == 10
    assert result.final_artifact_count == 14
    assert result.repository_chain_valid is True

    assert result.findings_disposition == "acknowledged"
    assert result.recommendations_disposition == "accepted"

    assert database_path.exists()


def test_dry_run_uses_same_four_part_hierarchy(tmp_path):
    scenario = SyntheticPaidAssessmentScenario(
        tenant_id="tenant-pilot",
        client_id="client-pilot",
        engagement_id="engagement-pilot-001",
        assessment_id="assessment-pilot-001",
    )

    result = SyntheticPaidAssessmentDryRunService().run(
        database_path=tmp_path / "hierarchy.sqlite3",
        scenario=scenario,
    )

    assert (
        result.hierarchy_key
        == "tenant-pilot/client-pilot/"
        "engagement-pilot-001/assessment-pilot-001"
    )


def test_final_repository_contains_exactly_fourteen_artifacts(
    tmp_path,
):
    database_path = tmp_path / "artifact-count.sqlite3"

    result = SyntheticPaidAssessmentDryRunService().run(
        database_path=database_path
    )

    repository = GovernanceAssessmentRepository(database_path)

    artifacts = repository.list_artifacts(
        context=SyntheticPaidAssessmentScenario().context
    )

    assert len(artifacts) == EXPECTED_FINAL_ARTIFACT_COUNT
    assert [item.sequence_number for item in artifacts] == list(
        range(1, 15)
    )
    assert repository.verify_chain(
        context=SyntheticPaidAssessmentScenario().context
    ) is True

    assert result.final_artifact_count == len(artifacts)


def test_operator_projection_does_not_create_artifact_fifteen(
    tmp_path,
):
    database_path = tmp_path / "no-artifact-fifteen.sqlite3"

    SyntheticPaidAssessmentDryRunService().run(
        database_path=database_path
    )

    repository = GovernanceAssessmentRepository(database_path)
    context = SyntheticPaidAssessmentScenario().context

    artifacts = repository.list_artifacts(context=context)

    assert len(artifacts) == 14
    assert artifacts[-1].sequence_number == 14
    assert artifacts[-1].artifact_type == "paid-assessment-closeout"


def test_result_preserves_constitutional_boundaries(tmp_path):
    result = SyntheticPaidAssessmentDryRunService().run(
        database_path=tmp_path / "boundaries.sqlite3"
    )

    payload = result.to_dict()

    assert payload["synthetic"] is True
    assert payload["dry_run_passed"] is True

    boundaries = payload["boundaries"]

    assert (
        boundaries[
            "synthetic_dry_run_is_not_real_customer_acceptance"
        ]
        is True
    )
    assert (
        boundaries[
            "assessment_closed_is_not_recommendations_implemented"
        ]
        is True
    )
    assert (
        boundaries[
            "assessment_closed_is_not_intervention_authorized"
        ]
        is True
    )
    assert (
        boundaries[
            "assessment_closed_is_not_remediation_success"
        ]
        is True
    )
    assert (
        boundaries["assessment_closed_is_not_roi_verified"]
        is True
    )
    assert (
        boundaries[
            "assessment_closed_is_not_customer_outcome_verified"
        ]
        is True
    )

    assert "real_customer_accepted" not in payload
    assert "recommendations_implemented" not in payload
    assert "intervention_authorized" not in payload
    assert "remediation_success" not in payload
    assert "roi_verified" not in payload
    assert "customer_outcome_verified" not in payload


def test_rejects_non_synthetic_scenario(tmp_path):
    scenario = SyntheticPaidAssessmentScenario(
        synthetic=False
    )

    with pytest.raises(
        SyntheticPaidAssessmentDryRunError,
        match="explicitly synthetic",
    ):
        SyntheticPaidAssessmentDryRunService().run(
            database_path=tmp_path / "not-synthetic.sqlite3",
            scenario=scenario,
        )


def test_refuses_to_overwrite_existing_database(tmp_path):
    database_path = tmp_path / "existing.sqlite3"
    database_path.write_text("do not overwrite", encoding="utf-8")

    with pytest.raises(
        SyntheticPaidAssessmentDryRunError,
        match="already exists",
    ):
        SyntheticPaidAssessmentDryRunService().run(
            database_path=database_path
        )

def test_cli_executes_synthetic_paid_assessment(
    tmp_path,
):
    import json
    import subprocess
    import sys

    database_path = tmp_path / "cli-paid-assessment.sqlite3"
    output_path = tmp_path / "cli-result.json"

    completed = subprocess.run(
        [
            sys.executable,
            "scripts/run_synthetic_paid_assessment.py",
            "--database",
            str(database_path),
            "--output-json",
            str(output_path),
        ],
        cwd=Path(__file__).resolve().parents[1],
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    assert database_path.exists()
    assert output_path.exists()

    stdout_payload = json.loads(completed.stdout)
    file_payload = json.loads(
        output_path.read_text(encoding="utf-8")
    )

    assert stdout_payload == file_payload

    assert stdout_payload["synthetic"] is True
    assert stdout_payload["dry_run_passed"] is True
    assert (
        stdout_payload["assessment_execution_complete"]
        is True
    )
    assert stdout_payload["assessment_closed"] is True
    assert (
        stdout_payload["operator_workflow_stage"]
        == "closed"
    )
    assert stdout_payload["operator_required_action"] == "none"
    assert stdout_payload["core_artifact_count"] == 10
    assert stdout_payload["final_artifact_count"] == 14
    assert stdout_payload["repository_chain_valid"] is True


def test_cli_fails_closed_for_existing_database(
    tmp_path,
):
    import json
    import subprocess
    import sys

    database_path = tmp_path / "existing-cli.sqlite3"
    database_path.write_text(
        "preserve this file",
        encoding="utf-8",
    )

    original = database_path.read_bytes()

    completed = subprocess.run(
        [
            sys.executable,
            "scripts/run_synthetic_paid_assessment.py",
            "--database",
            str(database_path),
        ],
        cwd=Path(__file__).resolve().parents[1],
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 1

    payload = json.loads(completed.stderr)

    assert payload["dry_run_passed"] is False
    assert "already exists" in payload["error"]

    assert database_path.read_bytes() == original

def test_cli_refuses_existing_output_json_before_service_execution(
    tmp_path,
):
    import json
    import subprocess
    import sys

    database_path = tmp_path / "must-not-be-created.sqlite3"
    output_path = tmp_path / "existing-result.json"

    original_output = b'{"preserve":"this evidence exactly"}\n'
    output_path.write_bytes(original_output)

    assert database_path.exists() is False

    completed = subprocess.run(
        [
            sys.executable,
            "scripts/run_synthetic_paid_assessment.py",
            "--database",
            str(database_path),
            "--output-json",
            str(output_path),
        ],
        cwd=Path(__file__).resolve().parents[1],
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 1

    error_payload = json.loads(completed.stderr)

    assert error_payload["dry_run_passed"] is False
    assert "output JSON already exists" in error_payload["error"]
    assert "refusing to overwrite evidence" in error_payload["error"]

    # The output collision must be detected before the governed
    # dry-run service is invoked.
    assert database_path.exists() is False

    # Existing evidence is byte-for-byte immutable.
    assert output_path.read_bytes() == original_output

    # Failure is emitted only as structured stderr evidence.
    assert completed.stdout == ""