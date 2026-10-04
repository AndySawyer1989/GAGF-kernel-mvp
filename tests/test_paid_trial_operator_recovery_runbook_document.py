from pathlib import Path


RUNBOOK_PATH = (
    Path(__file__).resolve().parents[1]
    / "docs"
    / "PAID_TRIAL_OPERATOR_RECOVERY_RUNBOOK.md"
)


def load_runbook() -> str:
    return RUNBOOK_PATH.read_text(
        encoding="utf-8"
    )


def test_paid_trial_operator_recovery_runbook_exists(
) -> None:
    assert RUNBOOK_PATH.is_file()


def test_paid_trial_operator_recovery_runbook_has_required_headings(
) -> None:
    content = load_runbook()

    required_headings = (
        "# Paid-Trial Operator Recovery Runbook",
        "## Purpose",
        "## Constitutional Boundary",
        "## Required Release Environment",
        "## Recovery Evidence Chain",
        "## Operator Recovery Contract",
        "## Operator Action Matrix",
        "## Required Operator Sequence",
        "## Step 1 — Stop and Preserve Evidence",
        "## Step 2 — Review the Recovery Contract",
        "## Step 3 — Review the Action Matrix",
        "## Step 4 — Resolve Governed Blockers",
        "## Step 5 — Rerun Applicable Readiness Checks",
        "## Step 6 — Interpret Recovery Verified Correctly",
        "## Paid-Assessment Recovery Boundary",
        "## Failure Stop Conditions",
        "## Evidence Freshness Rule",
        "## No Silent Repair Rule",
        "## Secret Handling Rule",
        "## Operator Record",
        "## Successful Recovery Criteria",
        "## Relationship to 04K Release Hardening",
        "## Relationship to Future Release Gates",
        "## Constitutional Summary",
    )

    for heading in required_headings:
        assert heading in content


def test_paid_trial_operator_recovery_runbook_preserves_core_boundary(
) -> None:
    content = load_runbook()

    assert (
        "Recovery readiness is not operational authority."
        in content
    )

    assert (
        "Recovery verification proves recovery evidence. "
        "It does not grant authority to resume governed work."
        in content
    )


def test_paid_trial_operator_recovery_runbook_requires_paid_trial(
) -> None:
    content = load_runbook()

    assert (
        "GAGF_RELEASE_ENVIRONMENT=paid_trial"
        in content
    )

    assert (
        "not `paid_trial`"
        in content
    )


def test_paid_trial_operator_recovery_runbook_documents_contract_dispositions(
) -> None:
    content = load_runbook()

    assert "`recovery_verified`" in content
    assert "`blocked`" in content

    assert (
        "It is not resume authority."
        in content
    )


def test_paid_trial_operator_recovery_runbook_documents_action_matrix(
) -> None:
    content = load_runbook()

    required_actions = (
        "`recovery_verified`",
        "`stop_and_preserve`",
        "`inspect_backup_recovery`",
        "`inspect_runtime_readiness`",
        "`inspect_security_readiness`",
        "`resolve_environment_mismatch`",
    )

    for action in required_actions:
        assert action in content


def test_paid_trial_operator_recovery_runbook_documents_operator_sequence(
) -> None:
    content = load_runbook()

    sequence = (
        "`stop_and_preserve_evidence`",
        "`review_recovery_contract`",
        "`review_action_matrix`",
        "`resolve_governed_blockers`",
        "`rerun_applicable_readiness_checks`",
        "`stop_before_resume_authority`",
    )

    positions = [
        content.index(step)
        for step in sequence
    ]

    assert positions == sorted(
        positions
    )


def test_paid_trial_operator_recovery_runbook_preserves_evidence_rule(
) -> None:
    content = load_runbook()

    assert (
        "Do not overwrite existing evidence."
        in content
    )

    assert (
        "Use fresh output locations for new evaluations"
        in content
    )


def test_paid_trial_operator_recovery_runbook_preserves_no_silent_repair_rule(
) -> None:
    content = load_runbook()

    required_rules = (
        "edit a failed JSON result into a passing result",
        "modify backup content to satisfy integrity checks",
        "modify manifest hashes",
        "suppress failure reasons",
        "remove failed checks from a result",
        "substitute development configuration for paid-trial configuration",
    )

    for rule in required_rules:
        assert rule in content


def test_paid_trial_operator_recovery_runbook_preserves_secret_handling_rule(
) -> None:
    content = load_runbook()

    assert (
        "Never include raw secret material"
        in content
    )

    assert (
        "Secret references and redacted metadata"
        in content
    )


def test_paid_trial_operator_recovery_runbook_preserves_paid_assessment_boundary(
) -> None:
    content = load_runbook()

    assert "`executed`" in content
    assert "`resumed`" in content
    assert "`reconciled`" in content

    assert (
        "Execution recovery is not second execution authority."
        in content
    )

    assert (
        "Completion is not a customer outcome."
        in content
    )


def test_paid_trial_operator_recovery_runbook_preserves_future_release_boundary(
) -> None:
    content = load_runbook()

    assert (
        "04K-06 — Full Paid-Trial Release Acceptance Suite"
        in content
    )

    assert (
        "04K-07 — Release Manifest / Trial Authorization Gate"
        in content
    )

    assert (
        "04K-07 remains the later trial-authorization boundary."
        in content
    )

    assert (
        "04K-05 must not preempt it."
        in content
    )


def test_paid_trial_operator_recovery_runbook_preserves_final_recovery_model(
) -> None:
    content = load_runbook()

    assert (
        "failure → stop → preserve evidence → classify → "
        "resolve governed blocker → regenerate affected evidence → "
        "verify recovery → stop before resume authority"
        in content
    )

    assert (
        "failure → retry → continue automatically"
        in content
    )