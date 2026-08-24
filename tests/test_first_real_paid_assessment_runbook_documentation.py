from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]

RUNBOOK_PATH = (
    REPOSITORY_ROOT
    / "docs"
    / "FIRST_REAL_PAID_ASSESSMENT_RUNBOOK.md"
)


def test_first_real_paid_assessment_runbook_contract():
    content = RUNBOOK_PATH.read_text(
        encoding="utf-8"
    )

    required_sections = (
        "# First Real Paid Assessment Controlled Execution Runbook",
        "## Constitutional Boundary",
        "## Phase 2 - Run PILOT-004 Preflight",
        "## Phase 3 - Prepare PILOT-005 Execution Package",
        (
            "## Phase 5 - Run PILOT-012 "
            "Controlled-Execution Readiness"
        ),
        "## Phase 6 - Run PILOT-013 Launch Manifest",
        "## Phase 7 - Human Launch Review / Go-No-Go",
        "## Phase 8 - Execute the Exact PA015 argv",
        "## Phase 10 - Verify PA015 Result",
        "## Phase 12 - Stop Before Delivery",
        "## Failure Handling",
        "## Evidence Preservation Rule",
        "## First Real Client Safety Rule",
        "## Non-Claims",
        "## Safe Operational Claim",
    )

    for section in required_sections:
        assert section in content

    required_module_commands = (
        "-m scripts.run_real_paid_assessment_preflight",
        "-m scripts.prepare_real_paid_assessment_execution_package",
        (
            "-m scripts."
            "verify_first_real_paid_assessment_execution_readiness"
        ),
        (
            "-m scripts."
            "verify_first_real_paid_assessment_launch_manifest"
        ),
        "scripts.run_real_paid_assessment",
    )

    for command in required_module_commands:
        assert command in content

    required_fields = (
        "attempt_hash",
        "record_hash",
        "hierarchy_key",
        "disposition",
        "artifact_count_before",
        "artifact_count_after",
        "execution_result",
        "human_go_no_go_required = true",
        "automatically_execute = false",
        "artifact_count_after = 10",
        "status = ready_for_controlled_execution",
        "ready_for_controlled_execution = true",
        "status = ready_for_human_launch_review",
        "ready_for_human_launch_review = true",
        "perform_human_controlled_launch_review",
        "--payment-confirmation-json",
    )

    for field in required_fields:
        assert field in content

    required_boundaries = (
        "PILOT-004 READY",
        "!= PILOT-005 package prepared",
        "!= PILOT-012 READY",
        "!= PILOT-013 ready_for_human_launch_review",
        "!= human launch GO",
        "!= paid-work authorization",
        "!= PA015 invocation",
        "!= governed execution",
        "!= delivery approval",
        "!= customer outcome",
        "Payment confirmation is not paid-work authorization.",
        (
            "PILOT-012 READY is not human launch approval "
            "or execution authority."
        ),
        (
            "PILOT-013 ready_for_human_launch_review is not "
            "human launch approval or execution authority."
        ),
    )

    for boundary in required_boundaries:
        assert boundary in content

    assert (
        "PILOT-012 remains the execution-readiness authority."
        in content
    )

    assert (
        "PILOT-013 verifies launch-manifest convergence only."
        in content
    )

    assert (
        "It preserves a separate human launch decision "
        "and does not itself execute the assessment."
        in content
    )