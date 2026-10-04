# Paid-Trial Operator Recovery Runbook

## Purpose

This runbook defines the operator procedure for handling paid-trial release failures and verifying recovery evidence.

It is the human-operable companion to these deterministic release authorities:

- `governance_release_backup_recovery.py`
- `governance_release_recovery_validation.py`
- `governance_release_backup_recovery_gate.py`
- `governance_release_runtime_failure_probe.py`
- `governance_release_runtime_gate.py`
- `governance_release_security_gate.py`
- `governance_release_operator_recovery_contract.py`
- `governance_release_operator_recovery_action_matrix.py`
- `governance_release_operator_recovery_runbook.py`

This runbook does not replace those authorities.

The software contracts remain authoritative for machine-evaluated recovery state.

---

## Constitutional Boundary

Recovery readiness is not operational authority.

A successful recovery evaluation does not authorize:

- deployment activation
- customer trial execution
- paid-assessment execution
- delivery
- production activation
- intervention
- credential creation
- credential rotation
- actor authorization
- PA014 execution
- PA015 execution
- automatic resume

The operator recovery contract is read-only.

The action matrix classifies existing failure reasons only.

The runbook projection presents existing governed evidence only.

A separate governed authority is required before any customer-facing or execution action resumes.

---

## Required Release Environment

This runbook applies to `GAGF_RELEASE_ENVIRONMENT=paid_trial`.

The operator recovery contract must reject any evidence set whose authoritative recovery environment is not `paid_trial`.

The runtime and security evidence must identify the same release environment as the backup-recovery evidence.

Environment mismatch is a blocking condition.

---

## Recovery Evidence Chain

The operator must treat the following as separate evidence layers.

### 1. Backup Recovery Evidence

Backup recovery proves that a verified backup package was restored into an isolated recovery destination.

Recovery does not mean production activation, trial authorization, or storage migration.

The backup itself must not be mutated. Integrity verification must precede restore.

### 2. Recovery Validation Evidence

Recovery validation verifies the recovered file inventory and applicable SQLite integrity.

Validation does not mean restore execution, production activation, trial authorization, or business-semantic correctness.

The package hash provides lineage. The package hash is not activation authority.

### 3. Backup-Recovery Gate

The backup-recovery gate evaluates already-produced recovery evidence.

It does not execute a backup, execute a restore, activate deployment, authorize a trial, or activate production.

A passing gate means only that the evaluated backup/recovery evidence passed its deterministic checks.

### 4. Runtime Evidence

Runtime evidence covers release preflight, clean process start, process restart, restart persistence, invalid configuration failure behavior, and runtime gate evaluation.

Runtime readiness does not authorize a customer trial.

### 5. Security Evidence

Security evidence covers secret configuration preflight, environment security preflight, identity/tenant boundary validation, secret redaction proof, invalid security configuration proof, and security gate evaluation.

Security readiness does not authorize a customer trial.

---

## Operator Recovery Contract

The deterministic operator recovery contract evaluates the existing backup-recovery, runtime, and security gates, requires `paid_trial`, and requires matching release environments.

The two possible contract dispositions are:

- `recovery_verified`
- `blocked`

`recovery_verified` means only that the existing recovery evidence chain passed the operator recovery contract. It is not resume authority.

---

## Operator Action Matrix

The deterministic action matrix maps contract failure reasons to bounded operator actions.

Possible actions are:

- `recovery_verified`
- `stop_and_preserve`
- `inspect_backup_recovery`
- `inspect_runtime_readiness`
- `inspect_security_readiness`
- `resolve_environment_mismatch`

The action matrix never executes those actions automatically.

It does not restore data, retry a process, restart a process, resume a paid assessment, invoke PA014, invoke PA015, authorize a trial, authorize deployment, or authorize delivery.

---

## Required Operator Sequence

The canonical operator sequence is:

1. `stop_and_preserve_evidence`
2. `review_recovery_contract`
3. `review_action_matrix`
4. `resolve_governed_blockers`
5. `rerun_applicable_readiness_checks`
6. `stop_before_resume_authority`

Do not skip directly from failure detection to retry or resume.

---

## Step 1 — Stop and Preserve Evidence

When a paid-trial release failure occurs, stop the affected workflow.

Do not overwrite existing evidence.

Preserve all relevant evidence before corrective work begins, including controlled inputs, referenced evidence, release configuration evidence, backup package and manifest, integrity evidence, recovery receipts, recovery validation, runtime evidence, security evidence, operator recovery results, paid-assessment execution evidence, and the assessment database.

Use fresh output locations for new evaluations where the governed workflow requires fresh evidence.

---

## Step 2 — Review the Recovery Contract

Inspect `GovernanceReleaseOperatorRecoveryContractResult`.

Confirm `release_environment`, `backup_id`, `disposition`, `passed`, `checks`, and `failure_reasons`.

If `passed = false`, the release remains blocked.

Proceed to the deterministic action matrix.

---

## Step 3 — Review the Action Matrix

Inspect `GovernanceReleaseOperatorRecoveryActionMatrixResult`.

Confirm `recovery_verified`, `primary_action`, `actions`, and `failure_reasons`.

The first action for a blocked recovery must remain `stop_and_preserve`.

---

## Step 4 — Resolve Governed Blockers

### Environment Mismatch

If the action list contains `resolve_environment_mismatch`, verify the release-environment configuration.

Do not silently fall back to development configuration, storage, or security defaults.

### Backup / Recovery Failure

If the action list contains `inspect_backup_recovery`, review package integrity, manifest lineage, restore destination, recovered inventory, SQLite integrity, recovery validation, and backup-recovery gate failure reasons.

Do not modify the source backup to make validation pass.

### Runtime Failure

If the action list contains `inspect_runtime_readiness`, review release runtime configuration, clean-start evidence, health evidence, version evidence, storage-status evidence, restart evidence, restart-persistence evidence, runtime failure evidence, and runtime gate failure reasons.

A failed paid-trial start must not fall back to development mode.

### Security Failure

If the action list contains `inspect_security_readiness`, review secret-reference configuration, secret availability, CORS configuration, identity headers, tenant binding, redaction proof, invalid-configuration proof, and security gate failure reasons.

Do not print secret material or create/rotate credentials as part of this runbook.

---

## Step 5 — Rerun Applicable Readiness Checks

After a governed blocker is corrected, rerun the authoritative check that produced the stale or failed evidence.

Do not edit a prior result to indicate success. Create fresh evidence.

Then rebuild `GovernanceReleaseOperatorRecoveryContractResult`, `GovernanceReleaseOperatorRecoveryActionMatrixResult`, and `GovernanceReleaseOperatorRecoveryRunbook` from the new evidence.

---

## Step 6 — Interpret Recovery Verified Correctly

If the final runbook projection reports `stage = recovery_verified` and `recovery_verified = true`, the operator may conclude only that the evaluated paid-trial recovery, runtime, and security evidence passed the deterministic operator recovery verification contract.

Do not interpret this as resume authority, trial authorization, deployment authorization, delivery authorization, production authorization, or intervention authorization.

---

## Paid-Assessment Recovery Boundary

Existing paid-assessment execution recovery supports `executed`, `resumed`, and `reconciled`.

Execution recovery is not second execution authority.

Artifact reuse is not a new artifact. Completion is not a customer outcome.

Execution authority remains with the existing governed paid-assessment authorization path.

This release recovery runbook does not invoke that path.

---

## Failure Stop Conditions

Stop immediately if the recovery contract is blocked, any release gate fails, environments disagree, required evidence is missing or stale, integrity cannot be proven, runtime falls back to development, secret material appears in public evidence, identity/tenant validation fails, a deterministic gate is bypassed, or recovery verification is treated as resume authority.

Preserve evidence before further corrective work.

---

## Evidence Freshness Rule

Evidence must be regenerated when authoritative inputs change, including the release environment, data root, CORS origins, signing configuration, backup package, recovery destination, recovered database, or runtime process configuration.

Previously passing evidence does not remain authoritative after a material input change.

---

## No Silent Repair Rule

Do not:

- edit a failed JSON result into a passing result
- modify backup content to satisfy integrity checks
- modify manifest hashes
- replace evidence without preserving the previous artifact
- suppress failure reasons
- remove failed checks from a result
- substitute development configuration for paid-trial configuration

Correct the governed source condition and rerun the authoritative evaluation.

---

## Secret Handling Rule

Never include raw secret material in screenshots, runbook notes, Git commits, test fixtures, public API responses, support messages, or recovery artifacts.

Secret references and redacted metadata may be used where supported by the security contracts.

---

## Operator Record

For each recovery event, preserve at minimum: `release_environment`, `backup_id`, `failure_observed`, `initial_failure_reasons`, `initial_primary_action`, `corrective_domain`, `fresh_evidence_generated`, `final_recovery_contract_passed`, `final_runbook_stage`, and `operator_timestamp`.

This record documents operator activity. It does not create execution authority.

---

## Successful Recovery Criteria

A recovery verification cycle is successful only when the backup-recovery, runtime, security, operator recovery contract, action matrix, and runbook checks all report success for the same `paid_trial` environment.

Even then, the operator must stop before resume authority.

---

## Relationship to 04K Release Hardening

This runbook consumes evidence produced by:

- 04K-01 — Release Configuration Isolation
- 04K-02 — Durable Storage / Backup / Recovery Proof
- 04K-03 — Deployment + Process Restart Proof
- 04K-04 — Security / Secret / Environment Preflight
- 04K-05 — Operator Runbook + Failure Recovery

04K-05 does not replace the earlier authorities. It binds them into an operator-verifiable recovery workflow.

---

## Relationship to Future Release Gates

Successful 04K-05 recovery verification does not complete the paid-trial release.

Later release work remains separate, including:

- 04K-06 — Full Paid-Trial Release Acceptance Suite
- 04K-07 — Release Manifest / Trial Authorization Gate

04K-07 remains the later trial-authorization boundary. 04K-05 must not preempt it.

---

## Constitutional Summary

The recovery model is:

`failure → stop → preserve evidence → classify → resolve governed blocker → regenerate affected evidence → verify recovery → stop before resume authority`

Not:

`failure → retry → continue automatically`

The central rule is:

> Recovery verification proves recovery evidence. It does not grant authority to resume governed work.
