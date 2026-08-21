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
        "## Phase 2 — Run PILOT-004 Preflight",
        "## Phase 3 — Prepare PILOT-005 Execution Package",
        "## Phase 5 — Human Go/No-Go",
        "## Phase 6 — Execute the Exact PA015 argv",
        "## Phase 8 — Verify PA015 Result",
        "## Phase 10 — Stop Before Delivery",
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
    )

    for field in required_fields:
        assert field in content

    required_boundaries = (
        "PILOT-004 READY",
        "!= PILOT-005 package prepared",
        "!= human go/no-go",
        "!= PA015 invocation",
        "!= governed execution",
        "!= delivery approval",
        "!= customer outcome",
    )

    for boundary in required_boundaries:
        assert boundary in content

    assert (
        "It preserves a separate human go/no-go checkpoint "
        "and does not itself execute the assessment."
        in content
    )
