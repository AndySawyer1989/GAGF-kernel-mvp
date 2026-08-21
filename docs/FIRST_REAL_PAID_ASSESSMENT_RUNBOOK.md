# First Real Paid Assessment Controlled Execution Runbook

## Purpose

This runbook defines the controlled operator sequence for the first real paid assessment.

The governed path is PILOT-004 preflight -> PILOT-005 execution package -> human go/no-go -> PA015 execution -> PA014 recovery/reconciliation -> post-execution verification.

This runbook does not grant paid-work authorization, execution authority, recovery authority, delivery approval, or customer acceptance.

## Constitutional Boundary

PILOT-004 READY
!= PILOT-005 package prepared
!= human go/no-go
!= paid-work authorization
!= PA015 invocation
!= governed execution
!= successful assessment completion
!= delivery approval
!= customer outcome

A prepared package is evidence about intended execution inputs. It is not permission to execute.

## Required Inputs

- intake JSON
- paid-work authorization JSON
- contract execution event JSON
- assessment request JSON
- evidence approvals JSON
- referenced evidence files
- intended SQLite database path
- fresh PILOT-004 preflight JSON path
- fresh PILOT-005 execution-package JSON path
- fresh PA015 execution-output JSON path

PILOT-005 records paths, byte counts, and SHA-256 commitments rather than duplicating client evidence.

## Phase 1 — Confirm Fresh Targets

The database, preflight output, execution package, and PA015 output must all be fresh for a first execution.

Existing-database handling belongs to the governed PA014/PA015 recovery path.

## Phase 2 — Run PILOT-004 Preflight

Use module mode from the repository root:

& $Python -m scripts.run_real_paid_assessment_preflight --database $Database --intake-json $IntakeJson --authorization-json $AuthorizationJson --contract-event-json $ContractEventJson --request-json $RequestJson --evidence-approvals-json $EvidenceApprovalsJson --output-json $PreflightJson

Exit 0 means operationally READY. Exit 1 means malformed or governed-input failure. Exit 2 means governed but BLOCKED.

PILOT-004 READY is not execution authority.

## Phase 3 — Prepare PILOT-005 Execution Package

Use module mode:

& $Python -m scripts.prepare_real_paid_assessment_execution_package --database $Database --intake-json $IntakeJson --authorization-json $AuthorizationJson --contract-event-json $ContractEventJson --request-json $RequestJson --evidence-approvals-json $EvidenceApprovalsJson --preflight-json $PreflightJson --execution-output-json $ExecutionOutputJson --output-json $ExecutionPackageJson

The package binds controlled inputs and evidence with SHA-256 commitments and records the PA015 argv.

Package preparation does not execute the assessment.

## Phase 4 — Review the Package

Confirm these required values:

pilot004_preflight.ready_for_operator_execution = true
execution.human_go_no_go_required = true
execution.automatically_execute = false
boundaries.package_is_not_execution = true
boundaries.package_is_not_paid_work_authorization = true

The recorded PA015 argv must contain -m followed by scripts.run_real_paid_assessment.

## Phase 5 — Human Go/No-Go

A human operator must make a separate GO/NO-GO decision.

human_go_no_go_required = true
automatically_execute = false

If the decision is NO-GO, stop. Do not invoke PA015.

## Phase 6 — Execute the Exact PA015 argv

After a separate human GO decision, execute the exact argv stored in the package.

$ExecutionProgram = [string]$Package.execution.argv[0]
$ExecutionArguments = @($Package.execution.argv | Select-Object -Skip 1)
& $ExecutionProgram @ExecutionArguments

Do not manually reconstruct the command.

PA015 remains the operator execution entry point. PA014 remains the governed recovery/reconciliation path.

## Phase 7 — Preserve PA015 Evidence

Preserve the PA015 execution output exactly. Never overwrite it or delete state simply to force a fresh retry.

## Phase 8 — Verify PA015 Result

$ExecutionEvidence.operator_run_passed
$ExecutionEvidence.result

Expected recovery fields:

- attempt_hash
- record_hash
- hierarchy_key
- disposition
- artifact_count_before
- artifact_count_after
- execution_result

Allowed dispositions are executed, resumed, and reconciled.

artifact_count_after = 10

The result hierarchy must match the execution-package hierarchy.

## Phase 9 — Interpret Recovery Correctly

executed means a fresh governed attempt executed the assessment.

resumed means a valid exact-prefix partial attempt was resumed and missing canonical artifacts were appended.

reconciled means an already-complete exact attempt was reconciled without duplicate canonical artifacts.

Recovery is not second execution authority. Artifact reuse is not a new artifact. Completion is not customer outcome.

## Phase 10 — Stop Before Delivery

Successful PA015 completion is not delivery approval.

operator_run_passed = true and artifact_count_after = 10 do not authorize delivery.

## Failure Handling

If PILOT-004 exits 1 or 2: stop.
If PILOT-005 exits 1: stop.
If the database appears after PILOT-004 READY: treat the preflight as stale.
If PILOT-005 output already exists: preserve it.
If PA015 output already exists: preserve it.
If PA015 fails: preserve all controlled inputs, outputs, database state, preflight evidence, and package evidence.
Use the governed PA014/PA015 recovery path.

## Evidence Preservation Rule

Preserve controlled input files, referenced evidence files, PILOT-004 preflight JSON, PILOT-005 execution package JSON, PA015 execution JSON, and the assessment database.

The PILOT-005 package binds intended inputs with SHA-256 commitments. It does not replace source files.

## First Real Client Safety Rule

Before execution confirm hierarchy, authorization, contract-event identity, evidence approvals, PILOT-004 READY, fresh targets, successful PILOT-005 preparation, correct commitments, module-mode PA015 argv, and a separate human GO.

## Non-Claims

This runbook does not claim package preparation is paid-work authorization or execution authority.
PILOT-004 READY is not execution.
Human GO is not deterministic execution authority.
PA015 is not recovery authority.
Recovery is not a second business event.
Assessment completion is not customer outcome.
Execution completion is not delivery approval.
No distributed exactly-once or additional concurrency guarantee is claimed.

## Safe Operational Claim

PILOT-005 provides a reproducible, evidence-bound operator handoff between successful PILOT-004 preflight and the existing PA015 governed execution path.

It preserves a separate human go/no-go checkpoint and does not itself execute the assessment.
