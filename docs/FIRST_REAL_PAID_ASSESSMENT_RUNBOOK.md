# First Real Paid Assessment Controlled Execution Runbook

## Purpose

This runbook defines the controlled operator sequence for the first real paid assessment.

The governed path is PILOT-004 preflight -> PILOT-005 execution package -> PILOT-012 controlled-execution readiness -> PILOT-013 launch manifest -> separate human launch review -> PA015 execution -> PA014 recovery/reconciliation -> post-execution verification.

This runbook does not grant paid-work authorization, execution authority, human launch approval, recovery authority, delivery approval, or customer acceptance.

## Constitutional Boundary

PILOT-004 READY
!= PILOT-005 package prepared
!= PILOT-012 READY
!= PILOT-013 ready_for_human_launch_review
!= human launch GO
!= paid-work authorization
!= PA015 invocation
!= governed execution
!= successful assessment completion
!= delivery approval
!= customer outcome

Payment confirmation
!= paid-work authorization

PILOT-012 READY
!= human launch approval

PILOT-013 ready_for_human_launch_review
!= execution authority

Human launch GO
!= deterministic execution

PA015 completion
!= delivery approval

A prepared package, readiness result, or launch manifest is evidence about intended execution and governance state. None of those artifacts alone grants permission to execute.

## Required Inputs

- intake JSON
- paid-work authorization JSON
- contract execution event JSON
- payment confirmation event JSON
- assessment request JSON
- evidence approvals JSON
- referenced evidence files
- intended SQLite database path
- fresh PILOT-004 preflight JSON path
- fresh PILOT-005 execution-package JSON path
- fresh PILOT-012 execution-readiness JSON path
- fresh PILOT-013 launch-manifest JSON path
- fresh PA015 execution-output JSON path

PILOT-005 records paths, byte counts, and SHA-256 commitments rather than duplicating client evidence.

The payment-confirmation event records commercial payment evidence only. It does not create paid-work authorization.

## Phase 1 - Confirm Fresh Targets

The database, preflight output, execution package, execution-readiness output, launch-manifest output, and PA015 output must all be fresh for a first execution.

Existing-database handling belongs to the governed PA014/PA015 recovery path and causes PILOT-012 to report a governed execution-readiness blocker.

## Phase 2 - Run PILOT-004 Preflight

Use module mode from the repository root:

& $Python -m scripts.run_real_paid_assessment_preflight --database $Database --intake-json $IntakeJson --authorization-json $AuthorizationJson --contract-event-json $ContractEventJson --request-json $RequestJson --evidence-approvals-json $EvidenceApprovalsJson --output-json $PreflightJson

Exit 0 means operationally READY. Exit 1 means malformed or governed-input failure. Exit 2 means governed but BLOCKED.

PILOT-004 READY is not execution authority.

## Phase 3 - Prepare PILOT-005 Execution Package

Use module mode:

& $Python -m scripts.prepare_real_paid_assessment_execution_package --database $Database --intake-json $IntakeJson --authorization-json $AuthorizationJson --contract-event-json $ContractEventJson --request-json $RequestJson --evidence-approvals-json $EvidenceApprovalsJson --preflight-json $PreflightJson --execution-output-json $ExecutionOutputJson --output-json $ExecutionPackageJson

The package binds controlled inputs and evidence with SHA-256 commitments and records the PA015 argv.

Package preparation does not execute the assessment.

## Phase 4 - Review the PILOT-005 Package

Confirm these required values:

pilot004_preflight.ready_for_operator_execution = true
execution.human_go_no_go_required = true
execution.automatically_execute = false
boundaries.package_is_not_execution = true
boundaries.package_is_not_paid_work_authorization = true

The recorded PA015 argv must contain -m followed by scripts.run_real_paid_assessment.

Do not execute it yet.

## Phase 5 - Run PILOT-012 Controlled-Execution Readiness

Re-evaluate the governed execution inputs immediately before launch review:

& $Python -m scripts.verify_first_real_paid_assessment_execution_readiness --database $Database --intake-json $IntakeJson --authorization-json $AuthorizationJson --contract-event-json $ContractEventJson --request-json $RequestJson --evidence-approvals-json $EvidenceApprovalsJson --output-json $ExecutionReadinessJson

PILOT-012 uses the same governed execution inputs as PA015 and evaluates fresh execution readiness without executing the assessment.

Required READY values:

status = ready_for_controlled_execution
ready_for_controlled_execution = true
required_operator_action = begin_controlled_real_paid_assessment_execution
blockers = []

PILOT-012 exit 0 means the readiness evaluation completed successfully. Inspect the governed result because exit 0 may represent READY or BLOCKED.

PILOT-012 READY does not create paid-work authorization, execution authority, human launch approval, delivery approval, customer acceptance, remediation-success evidence, ROI evidence, or customer-outcome evidence.

If PILOT-012 is BLOCKED, stop.

## Phase 6 - Run PILOT-013 Launch Manifest

PILOT-013 converges the independently governed payment-confirmation evidence, paid-work authorization, authorization bridge, contract execution evidence, and fresh PILOT-012 execution-readiness result.

Use module mode:

& $Python -m scripts.verify_first_real_paid_assessment_launch_manifest --database $Database --intake-json $IntakeJson --authorization-json $AuthorizationJson --contract-event-json $ContractEventJson --request-json $RequestJson --evidence-approvals-json $EvidenceApprovalsJson --payment-confirmation-json $PaymentConfirmationJson --output-json $LaunchManifestJson

Required READY values:

status = ready_for_human_launch_review
ready_for_human_launch_review = true
required_operator_action = perform_human_controlled_launch_review
blockers = []

PILOT-013 exit 0 means the governed manifest evaluation completed successfully. Inspect the governed result because exit 0 may represent READY or BLOCKED.

PILOT-013 is read-only.

It does not create a contract event, invoice, payment request, payment confirmation, paid-work authorization, execution authority, human launch approval, PA015 execution, delivery approval, or customer outcome.

Payment confirmation remains separate from paid-work authorization.

If PILOT-013 is BLOCKED, stop.

## Phase 7 - Human Launch Review / Go-No-Go

A human operator must make a separate GO/NO-GO launch decision after reviewing the PILOT-005 package, fresh PILOT-012 readiness result, and PILOT-013 launch manifest.

Confirm:

human_go_no_go_required = true
automatically_execute = false
PILOT-012 status = ready_for_controlled_execution
PILOT-013 status = ready_for_human_launch_review

Human review must confirm that the hierarchy, contract event, payment confirmation evidence, paid-work authorization, evidence approvals, intended database target, and recorded PA015 argv correspond to the intended client assessment.

If the decision is NO-GO, stop. Do not invoke PA015.

A human GO does not replace deterministic PA015 validation.

## Phase 8 - Execute the Exact PA015 argv

After a separate human GO decision, execute the exact argv stored in the PILOT-005 package.

$ExecutionProgram = [string]$Package.execution.argv[0]
$ExecutionArguments = @($Package.execution.argv | Select-Object -Skip 1)
& $ExecutionProgram @ExecutionArguments

Do not manually reconstruct the command.

PA015 remains the operator execution entry point. PA014 remains the governed recovery/reconciliation path.

PILOT-013 does not invoke PA015.

## Phase 9 - Preserve PA015 Evidence

Preserve the PA015 execution output exactly.

Never overwrite it or delete state simply to force a fresh retry.

Preserve the PILOT-012 and PILOT-013 artifacts used for the human launch decision alongside the execution evidence.

## Phase 10 - Verify PA015 Result

Inspect:

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

The result hierarchy must match the execution-package hierarchy and the hierarchy reviewed by PILOT-012 and PILOT-013.

## Phase 11 - Interpret Recovery Correctly

executed means a fresh governed attempt executed the assessment.

resumed means a valid exact-prefix partial attempt was resumed and missing canonical artifacts were appended.

reconciled means an already-complete exact attempt was reconciled without duplicate canonical artifacts.

Recovery is not second execution authority.

Artifact reuse is not a new artifact.

Completion is not customer outcome.

## Phase 12 - Stop Before Delivery

Successful PA015 completion is not delivery approval.

operator_run_passed = true and artifact_count_after = 10 do not authorize delivery.

The governed delivery lifecycle remains separate from assessment execution.

## Failure Handling

If PILOT-004 exits 1 or 2: stop.

If PILOT-005 exits 1: stop.

If PILOT-012 exits 1: stop because the readiness evaluation failed structurally.

If PILOT-012 returns status = blocked: stop and resolve the listed governed blockers.

If PILOT-013 exits 1: stop because the launch-manifest evaluation failed structurally.

If PILOT-013 returns status = blocked: stop and resolve the listed governed blockers.

If the database appears after PILOT-004 READY or PILOT-005 preparation: treat earlier fresh-target evidence as stale and rerun the applicable readiness checks through the governed path.

If PILOT-005 output already exists: preserve it.

If PILOT-012 output already exists: preserve it and use a fresh output path for a new evaluation.

If PILOT-013 output already exists: preserve it and use a fresh output path for a new evaluation.

If PA015 output already exists: preserve it.

If PA015 fails: preserve all controlled inputs, outputs, database state, preflight evidence, package evidence, readiness evidence, launch-manifest evidence, and commercial evidence.

Use the governed PA014/PA015 recovery path.

## Evidence Preservation Rule

Preserve:

- controlled input files
- referenced evidence files
- contract execution event JSON
- payment confirmation event JSON
- paid-work authorization JSON
- PILOT-004 preflight JSON
- PILOT-005 execution package JSON
- PILOT-012 execution-readiness JSON
- PILOT-013 launch-manifest JSON
- PA015 execution JSON
- assessment database

The PILOT-005 package binds intended inputs with SHA-256 commitments. It does not replace source files.

PILOT-012 is a fresh read-only readiness evaluation.

PILOT-013 is a read-only convergence manifest.

Neither replaces its source evidence.

## First Real Client Safety Rule

Before execution confirm hierarchy, authorization, exact contract-event identity, payment-confirmation evidence, evidence approvals, PILOT-004 READY, successful PILOT-005 preparation, correct commitments, PILOT-012 ready_for_controlled_execution, PILOT-013 ready_for_human_launch_review, fresh targets, the exact module-mode PA015 argv, and a separate human GO.

Do not infer paid-work authorization from payment confirmation.

Do not infer human launch approval from PILOT-012 or PILOT-013.

Do not infer execution from readiness or launch-manifest status.

## Non-Claims

This runbook does not claim package preparation is paid-work authorization or execution authority.

Payment confirmation is not paid-work authorization.

PILOT-004 READY is not execution.

PILOT-005 package preparation is not execution.

PILOT-012 READY is not human launch approval or execution authority.

PILOT-013 ready_for_human_launch_review is not human launch approval or execution authority.

Human GO is not deterministic execution.

PA015 is not recovery authority.

Recovery is not a second business event.

Assessment completion is not customer outcome.

Execution completion is not delivery approval.

No distributed exactly-once or additional concurrency guarantee is claimed.

## Safe Operational Claim

The first-real-assessment launch sequence provides a reproducible, evidence-bound operator path from preflight through execution-package preparation, fresh controlled-execution readiness, commercial/execution convergence validation, separate human launch review, and the existing PA015 governed execution path.

PILOT-012 remains the execution-readiness authority.

PILOT-013 verifies launch-manifest convergence only.

It preserves a separate human launch decision and does not itself execute the assessment.