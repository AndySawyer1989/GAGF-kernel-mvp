import inspect
import sqlite3
from dataclasses import replace
from datetime import date, datetime, timezone

import pytest

from backend.app.gagf.governance_assessment_application import (
    AssessmentExecutionRequest,
)
from backend.app.gagf.governance_assessment_demonstration import (
    DemonstrationEvidenceInput,
)
from backend.app.gagf.governance_assessment_domain import (
    EvidenceSourceKind,
    EvidenceSourceReference,
)
from backend.app.gagf.governance_assessment_demonstration_persistence import (
    DemonstrationPersistenceError,
)
from backend.app.gagf.governance_assessment_repository import (
    ArtifactIntegrityError,
    GovernanceAssessmentRepository,
)
from backend.app.gagf.governance_assessment_scope_configuration import (
    EvidenceRequirement,
)
from backend.app.gagf.governance_paid_assessment_execution_handoff import (
    GovernancePaidAssessmentExecutionHandoffService,
    PaidAssessmentWorkAuthorization,
)
from backend.app.gagf.governance_real_paid_assessment_authorization_bridge import (
    GovernanceRealPaidAssessmentAuthorizationBridgeService,
)
from backend.app.gagf.governance_real_paid_assessment_execution_evidence import (
    GovernanceRealPaidAssessmentExecutionEvidenceService,
    RealAssessmentExecutionEvidenceApproval,
)
from backend.app.gagf.governance_real_paid_assessment_execution_recovery import (
    EXECUTION_ATTEMPT_TABLE,
    RECOVERY_DISPOSITION_EXECUTED,
    RECOVERY_DISPOSITION_RECONCILED,
    RECOVERY_DISPOSITION_RESUMED,
    GovernanceRealPaidAssessmentExecutionAttemptStore,
    GovernanceRealPaidAssessmentExecutionRecoveryService,
    RealPaidAssessmentExecutionAttemptConflictError,
    RealPaidAssessmentExecutionRecoveryError,
)
from backend.app.gagf.governance_real_paid_assessment_readiness import (
    EvidenceDataClassification,
    GovernanceRealPaidAssessmentReadinessService,
    RealAssessmentEvidenceDeclaration,
    RealAssessmentStorageDeclaration,
    RealPaidAssessmentIntake,
)


CSV_TEXT = (
    "event_id,event_type,occurred_at,work_item_id\n"
    "event-001,APPROVAL_DELAYED,"
    "2026-01-01T12:00:00Z,TICKET-1\n"
    "event-002,APPROVAL_DELAYED,"
    "2026-01-01T13:00:00Z,TICKET-2\n"
    "event-003,WORK_BLOCKED,"
    "2026-01-02T12:00:00Z,TICKET-3\n"
    "event-004,ESCALATION,"
    "2026-01-03T12:00:00Z,TICKET-4\n"
)


def build_contract_event():
    return {
        "status": "ok",
        "event_type": (
            "assessment_factory_lite_contract_execution_event"
        ),
        "package_name": "assessment_factory_lite",
        "release": (
            "assessment-factory-lite-scope-call-conversion"
        ),
        "version": "2.3.0",
        "event_stage": "contract_execution",
        "event_status": "contract_executed",
        "contract_execution_event_id": "contract-event-real-001",
        "recorded_at": "2026-08-20T18:30:00+00:00",
        "execution_evidence": {
            "executed_contract_reference": (
                "contract-ref-real-001"
            ),
            "executed_at": "2026-08-20T18:25:00+00:00",
            "executed_contract_reference_recorded": True,
            "executed_at_recorded": True,
            "contract_execution_confirmed": True,
            "contract_executed": True,
        },
        "event_checklist": {
            "contract_execution_review_ready": True,
            "contract_execution_confirmed": True,
            "executed_contract_reference_recorded": True,
            "executed_at_recorded": True,
            "execution_method_recorded": True,
            "all_required_signatures_recorded": True,
            "human_operator_confirmed_execution": True,
            "signature_record_is_not_invoice": True,
            "signature_record_is_not_payment": True,
            "invoice_not_created": True,
            "payment_not_requested": True,
            "paid_assessment_not_authorized": True,
            "production_onboarding_not_started": True,
        },
        "event_blockers": [],
        "commercial_boundary": {
            "contract_execution_recorded": True,
            "contract_executed": True,
            "invoice_created": False,
            "payment_requested": False,
            "paid_assessment_authorized": False,
            "production_onboarding_authorized": False,
            "requires_separate_invoice": True,
            "requires_separate_payment_confirmation": True,
            "requires_final_paid_work_authorization": True,
            "requires_separate_production_onboarding": True,
        },
        "governance_boundary": {
            "deterministic_status_required": True,
            "gagf_kernel_authoritative": True,
            "ai_override_allowed": False,
            "human_boundary_required": True,
            "release_marker_preserved": True,
            "contract_execution_event_is_not_invoice": True,
            "contract_execution_event_is_not_payment": True,
            "contract_execution_event_is_not_paid_work_authorization": True,
        },
    }


def build_inputs(database_path):
    intake = RealPaidAssessmentIntake(
        tenant_id="tenant-alpha",
        client_id="client-acme",
        engagement_id="engagement-001",
        assessment_id="assessment-001",
        client_display_name="ACME Corporation",
        assessment_name="Governance Runway Assessment",
        operator_name="FIP Operator",
        client_contact_name="Client Representative",
        assessment_scope_confirmed=True,
        evidence_scope_confirmed=True,
        client_data_use_confirmed=True,
        operator_readiness_confirmed=True,
        evidence=(
            RealAssessmentEvidenceDeclaration(
                evidence_id="source-001",
                source_kind="csv",
                description="Redacted workflow export",
                classification=(
                    EvidenceDataClassification.REDACTED
                ),
                client_authorized_for_assessment=True,
                minimization_review_completed=True,
                direct_identifiers_removed=True,
            ),
        ),
        storage=RealAssessmentStorageDeclaration(
            repository_path=str(database_path),
            operator_controlled_location=True,
            access_restricted=True,
            storage_protection_confirmed=True,
            backup_plan_recorded=True,
            retention_period_recorded=True,
            deletion_plan_recorded=True,
        ),
    )

    readiness = (
        GovernanceRealPaidAssessmentReadinessService()
        .evaluate(
            intake=intake
        )
    )

    authorization = PaidAssessmentWorkAuthorization(
        authorization_id="paid-work-auth-real-001",
        tenant_id=intake.tenant_id,
        client_id=intake.client_id,
        engagement_id=intake.engagement_id,
        assessment_id=intake.assessment_id,
        contract_execution_event_id="contract-event-real-001",
        authorized_by="FIP Operator",
        authorized_at="2026-08-20T18:35:00+00:00",
        paid_assessment_authorized=True,
    )

    bridge = (
        GovernanceRealPaidAssessmentAuthorizationBridgeService()
        .bind(
            intake=intake,
            readiness=readiness,
            paid_work_authorization=authorization,
        )
    )

    request = AssessmentExecutionRequest(
        context=intake.context,
        assessment_name=intake.assessment_name,
        workflow_names=("Incident Management",),
        organizational_units=("IT Operations",),
        period_start=date(2026, 1, 1),
        period_end=date(2026, 6, 30),
        objectives=("Reduce governance friction",),
        expected_outcomes=("Faster completion",),
        evidence_requirements=(
            EvidenceRequirement(
                requirement_id="required-csv",
                source_kind=EvidenceSourceKind.CSV,
                description="Workflow evidence",
                required=True,
                minimum_record_count=4,
            ),
        ),
        evidence_inputs=(
            DemonstrationEvidenceInput(
                source=EvidenceSourceReference(
                    source_id="source-001",
                    kind=EvidenceSourceKind.CSV,
                    display_name="Redacted Workflow Export",
                ),
                csv_text=CSV_TEXT,
            ),
        ),
        client_display_name=intake.client_display_name,
        prepared_by=intake.operator_name,
    )

    evidence_binding = (
        GovernanceRealPaidAssessmentExecutionEvidenceService()
        .bind(
            intake=intake,
            request=request,
            approvals=(
                RealAssessmentExecutionEvidenceApproval(
                    evidence_id="source-001",
                    approved_content_sha256=(
                        __import__("hashlib")
                        .sha256(CSV_TEXT.encode("utf-8"))
                        .hexdigest()
                    ),
                    approved_by="FIP Operator",
                    approved_at="2026-08-20T18:40:00+00:00",
                    execution_evidence_approved=True,
                ),
            ),
        )
    )

    handoff = (
        GovernancePaidAssessmentExecutionHandoffService()
        .build_handoff(
            contract_execution_event=build_contract_event(),
            paid_work_authorization=authorization,
            assessment_execution_request=request,
        )
    )

    return {
        "intake": intake,
        "authorization": authorization,
        "bridge": bridge,
        "request": request,
        "evidence_binding": evidence_binding,
        "handoff": handoff,
    }


def build_attempt(
    *,
    database_path,
    recorded_at,
):
    values = build_inputs(database_path)

    store = GovernanceRealPaidAssessmentExecutionAttemptStore(
        database_path
    )

    attempt = store.build_attempt(
        authorization_bridge=values["bridge"],
        evidence_binding=values["evidence_binding"],
        paid_work_authorization=values["authorization"],
        handoff=values["handoff"],
        request=values["request"],
        recorded_at=recorded_at,
    )

    return store, attempt, values


def test_same_logical_attempt_has_stable_identity_across_timestamps(
    tmp_path,
):
    database_path = tmp_path / "attempt.sqlite3"

    _, first, _ = build_attempt(
        database_path=database_path,
        recorded_at=datetime(
            2026,
            8,
            20,
            18,
            45,
            tzinfo=timezone.utc,
        ),
    )

    _, second, _ = build_attempt(
        database_path=database_path,
        recorded_at=datetime(
            2026,
            8,
            20,
            19,
            45,
            tzinfo=timezone.utc,
        ),
    )

    assert first.attempt_hash == second.attempt_hash
    assert first.record_hash != second.record_hash


def test_exact_retry_reuses_existing_durable_attempt(
    tmp_path,
):
    database_path = tmp_path / "attempt.sqlite3"

    store, first, _ = build_attempt(
        database_path=database_path,
        recorded_at=datetime(
            2026,
            8,
            20,
            18,
            45,
            tzinfo=timezone.utc,
        ),
    )

    persisted = store.record_attempt(
        attempt=first
    )

    _, retry, _ = build_attempt(
        database_path=database_path,
        recorded_at=datetime(
            2026,
            8,
            20,
            19,
            45,
            tzinfo=timezone.utc,
        ),
    )

    reconciled = store.record_attempt(
        attempt=retry
    )

    assert reconciled.attempt_hash == persisted.attempt_hash
    assert reconciled.record_hash == persisted.record_hash
    assert reconciled.recorded_at == persisted.recorded_at

    with sqlite3.connect(database_path) as connection:
        count = connection.execute(
            f"SELECT COUNT(*) FROM {EXECUTION_ATTEMPT_TABLE}"
        ).fetchone()[0]

    assert count == 1


def test_changed_governed_request_conflicts_with_existing_attempt(
    tmp_path,
):
    database_path = tmp_path / "attempt.sqlite3"

    store, original, values = build_attempt(
        database_path=database_path,
        recorded_at=datetime(
            2026,
            8,
            20,
            18,
            45,
            tzinfo=timezone.utc,
        ),
    )

    store.record_attempt(
        attempt=original
    )

    changed_request = replace(
        values["request"],
        objectives=("Different governed objective",),
    )

    changed_handoff = (
        GovernancePaidAssessmentExecutionHandoffService()
        .build_handoff(
            contract_execution_event=build_contract_event(),
            paid_work_authorization=values["authorization"],
            assessment_execution_request=changed_request,
        )
    )

    changed_evidence = (
        GovernanceRealPaidAssessmentExecutionEvidenceService()
        .bind(
            intake=values["intake"],
            request=changed_request,
            approvals=(
                RealAssessmentExecutionEvidenceApproval(
                    evidence_id="source-001",
                    approved_content_sha256=(
                        __import__("hashlib")
                        .sha256(CSV_TEXT.encode("utf-8"))
                        .hexdigest()
                    ),
                    approved_by="FIP Operator",
                    approved_at="2026-08-20T18:40:00+00:00",
                    execution_evidence_approved=True,
                ),
            ),
        )
    )

    conflicting = store.build_attempt(
        authorization_bridge=values["bridge"],
        evidence_binding=changed_evidence,
        paid_work_authorization=values["authorization"],
        handoff=changed_handoff,
        request=changed_request,
        recorded_at=datetime(
            2026,
            8,
            20,
            19,
            45,
            tzinfo=timezone.utc,
        ),
    )

    assert conflicting.attempt_hash != original.attempt_hash

    with pytest.raises(
        RealPaidAssessmentExecutionAttemptConflictError,
        match="existing execution attempt does not match",
    ):
        store.record_attempt(
            attempt=conflicting
        )


def test_tampered_attempt_record_fails_closed(
    tmp_path,
):
    database_path = tmp_path / "attempt.sqlite3"

    store, attempt, _ = build_attempt(
        database_path=database_path,
        recorded_at=datetime(
            2026,
            8,
            20,
            18,
            45,
            tzinfo=timezone.utc,
        ),
    )

    store.record_attempt(
        attempt=attempt
    )

    with sqlite3.connect(database_path) as connection:
        connection.execute(
            f"""
            UPDATE {EXECUTION_ATTEMPT_TABLE}
            SET handoff_hash = ?
            """,
            ("tampered-handoff-hash",),
        )

    with pytest.raises(
        RealPaidAssessmentExecutionRecoveryError,
        match="identity hash verification failed",
    ):
        store.get_attempt_for_hierarchy(
            tenant_id=attempt.tenant_id,
            client_id=attempt.client_id,
            engagement_id=attempt.engagement_id,
            assessment_id=attempt.assessment_id,
        )


def test_attempt_record_is_not_core_assessment_artifact(
    tmp_path,
):
    database_path = tmp_path / "attempt.sqlite3"

    store, attempt, _ = build_attempt(
        database_path=database_path,
        recorded_at=datetime(
            2026,
            8,
            20,
            18,
            45,
            tzinfo=timezone.utc,
        ),
    )

    store.record_attempt(
        attempt=attempt
    )

    repository = GovernanceAssessmentRepository(
        database_path
    )

    artifacts = repository.list_artifacts(
        context=build_inputs(
            database_path
        )["request"].context
    )

    assert artifacts == ()

def test_normal_real_execution_still_rejects_existing_database(
    tmp_path,
):
    database_path = tmp_path / "existing.sqlite3"

    values = build_inputs(database_path)

    store = GovernanceRealPaidAssessmentExecutionAttemptStore(
        database_path
    )

    attempt = store.build_attempt(
        authorization_bridge=values["bridge"],
        evidence_binding=values["evidence_binding"],
        paid_work_authorization=values["authorization"],
        handoff=values["handoff"],
        request=values["request"],
        recorded_at=datetime(
            2026,
            8,
            20,
            18,
            45,
            tzinfo=timezone.utc,
        ),
    )

    store.record_attempt(
        attempt=attempt
    )

    from backend.app.gagf.governance_real_paid_assessment_execution import (
        GovernanceRealPaidAssessmentExecutionService,
        RealPaidAssessmentExecutionError,
    )

    with pytest.raises(
        RealPaidAssessmentExecutionError,
        match="database already exists",
    ):
        GovernanceRealPaidAssessmentExecutionService().execute(
            database_path=database_path,
            intake=values["intake"],
            authorization_bridge=values["bridge"],
            evidence_binding=values["evidence_binding"],
            contract_execution_event=build_contract_event(),
            paid_work_authorization=values["authorization"],
            request=values["request"],
        )

def test_public_execution_api_has_no_existing_database_bypass():
    from backend.app.gagf.governance_real_paid_assessment_execution import (
        GovernanceRealPaidAssessmentExecutionService,
    )

    parameters = inspect.signature(
        GovernanceRealPaidAssessmentExecutionService.execute
    ).parameters

    assert "allow_existing_database" not in parameters
    assert "require_fresh_database" not in parameters


def execute_recoverably(
    *,
    database_path,
    recorded_at=None,
    values=None,
):
    supplied = values or build_inputs(database_path)

    result = (
        GovernanceRealPaidAssessmentExecutionRecoveryService()
        .execute(
            database_path=database_path,
            intake=supplied["intake"],
            authorization_bridge=supplied["bridge"],
            evidence_binding=supplied["evidence_binding"],
            contract_execution_event=build_contract_event(),
            paid_work_authorization=supplied["authorization"],
            request=supplied["request"],
            recorded_at=recorded_at,
        )
    )

    return result, supplied

def test_fresh_recovery_execution_records_attempt_and_executes(
    tmp_path,
):
    database_path = tmp_path / "fresh-recovery.sqlite3"

    result, values = execute_recoverably(
        database_path=database_path,
        recorded_at=datetime(
            2026,
            8,
            20,
            18,
            45,
            tzinfo=timezone.utc,
        ),
    )

    assert result.disposition == RECOVERY_DISPOSITION_EXECUTED
    assert result.artifact_count_before == 0
    assert result.artifact_count_after == 10
    assert result.execution_result.application_completed is True
    assert result.execution_result.repository_chain_valid is True

    store = GovernanceRealPaidAssessmentExecutionAttemptStore(
        database_path
    )

    durable = store.get_attempt_for_hierarchy(
        tenant_id=values["request"].context.tenant_id,
        client_id=values["request"].context.client_id,
        engagement_id=values["request"].context.engagement_id,
        assessment_id=values["request"].context.assessment_id,
    )

    assert durable is not None
    assert durable.attempt_hash == result.attempt.attempt_hash


def test_completed_matching_execution_reconciles_without_new_artifacts(
    tmp_path,
):
    database_path = tmp_path / "completed-recovery.sqlite3"

    first, values = execute_recoverably(
        database_path=database_path,
        recorded_at=datetime(
            2026,
            8,
            20,
            18,
            45,
            tzinfo=timezone.utc,
        ),
    )

    repository = GovernanceAssessmentRepository(
        database_path
    )

    before = repository.list_artifacts(
        context=values["request"].context
    )

    before_identity = tuple(
        (
            artifact.artifact_id,
            artifact.artifact_hash,
            artifact.sequence_number,
            artifact.chain_hash,
        )
        for artifact in before
    )

    second, _ = execute_recoverably(
        database_path=database_path,
        recorded_at=datetime(
            2026,
            8,
            20,
            19,
            45,
            tzinfo=timezone.utc,
        ),
        values=values,
    )

    after = repository.list_artifacts(
        context=values["request"].context
    )

    after_identity = tuple(
        (
            artifact.artifact_id,
            artifact.artifact_hash,
            artifact.sequence_number,
            artifact.chain_hash,
        )
        for artifact in after
    )

    assert first.disposition == RECOVERY_DISPOSITION_EXECUTED
    assert second.disposition == RECOVERY_DISPOSITION_RECONCILED
    assert second.artifact_count_before == 10
    assert second.artifact_count_after == 10
    assert before_identity == after_identity
    assert second.attempt.record_hash == first.attempt.record_hash


def test_partial_matching_execution_resumes_and_preserves_prefix(
    tmp_path,
):
    database_path = tmp_path / "partial-recovery.sqlite3"

    first, values = execute_recoverably(
        database_path=database_path,
        recorded_at=datetime(
            2026,
            8,
            20,
            18,
            45,
            tzinfo=timezone.utc,
        ),
    )

    assert first.artifact_count_after == 10

    repository = GovernanceAssessmentRepository(
        database_path
    )

    complete = repository.list_artifacts(
        context=values["request"].context
    )

    preserved_before = tuple(
        (
            artifact.artifact_id,
            artifact.artifact_type,
            artifact.artifact_hash,
            artifact.sequence_number,
            artifact.chain_hash,
        )
        for artifact in complete[:4]
    )

    with sqlite3.connect(database_path) as connection:
        connection.execute(
            """
            DELETE FROM governance_assessment_artifacts
            WHERE tenant_id = ?
              AND client_id = ?
              AND engagement_id = ?
              AND assessment_id = ?
              AND sequence_number > 4
            """,
            (
                values["request"].context.tenant_id,
                values["request"].context.client_id,
                values["request"].context.engagement_id,
                values["request"].context.assessment_id,
            ),
        )

    partial = repository.list_artifacts(
        context=values["request"].context
    )

    assert len(partial) == 4
    assert repository.verify_chain(
        context=values["request"].context
    ) is True

    resumed, _ = execute_recoverably(
        database_path=database_path,
        recorded_at=datetime(
            2026,
            8,
            20,
            19,
            45,
            tzinfo=timezone.utc,
        ),
        values=values,
    )

    recovered = repository.list_artifacts(
        context=values["request"].context
    )

    preserved_after = tuple(
        (
            artifact.artifact_id,
            artifact.artifact_type,
            artifact.artifact_hash,
            artifact.sequence_number,
            artifact.chain_hash,
        )
        for artifact in recovered[:4]
    )

    assert resumed.disposition == RECOVERY_DISPOSITION_RESUMED
    assert resumed.artifact_count_before == 4
    assert resumed.artifact_count_after == 10
    assert len(recovered) == 10
    assert preserved_before == preserved_after
    assert repository.verify_chain(
        context=values["request"].context
    ) is True


def test_unclaimed_existing_database_fails_without_claiming_it(
    tmp_path,
):
    database_path = tmp_path / "legacy-unclaimed.sqlite3"

    with sqlite3.connect(database_path) as connection:
        connection.execute(
            """
            CREATE TABLE legacy_marker (
                marker TEXT NOT NULL
            )
            """
        )
        connection.execute(
            "INSERT INTO legacy_marker (marker) VALUES (?)",
            ("pre-pa014",),
        )

    values = build_inputs(database_path)

    with pytest.raises(
        RealPaidAssessmentExecutionRecoveryError,
        match="no governed execution-attempt identity",
    ):
        execute_recoverably(
            database_path=database_path,
            values=values,
        )

    with sqlite3.connect(database_path) as connection:
        attempt_table = connection.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
              AND name = ?
            """,
            (EXECUTION_ATTEMPT_TABLE,),
        ).fetchone()

        marker = connection.execute(
            "SELECT marker FROM legacy_marker"
        ).fetchone()

    assert attempt_table is None
    assert marker[0] == "pre-pa014"


def test_different_attempt_conflicts_before_artifact_mutation(
    tmp_path,
):
    database_path = tmp_path / "attempt-conflict.sqlite3"

    _, values = execute_recoverably(
        database_path=database_path,
        recorded_at=datetime(
            2026,
            8,
            20,
            18,
            45,
            tzinfo=timezone.utc,
        ),
    )

    repository = GovernanceAssessmentRepository(
        database_path
    )

    before = repository.list_artifacts(
        context=values["request"].context
    )

    before_identity = tuple(
        (
            artifact.artifact_id,
            artifact.artifact_hash,
            artifact.sequence_number,
            artifact.chain_hash,
        )
        for artifact in before
    )

    changed_request = replace(
        values["request"],
        objectives=("Different governed objective",),
    )

    changed_evidence = (
        GovernanceRealPaidAssessmentExecutionEvidenceService()
        .bind(
            intake=values["intake"],
            request=changed_request,
            approvals=(
                RealAssessmentExecutionEvidenceApproval(
                    evidence_id="source-001",
                    approved_content_sha256=(
                        __import__("hashlib")
                        .sha256(CSV_TEXT.encode("utf-8"))
                        .hexdigest()
                    ),
                    approved_by="FIP Operator",
                    approved_at="2026-08-20T18:40:00+00:00",
                    execution_evidence_approved=True,
                ),
            ),
        )
    )

    conflicting_values = dict(values)
    conflicting_values["request"] = changed_request
    conflicting_values["evidence_binding"] = changed_evidence

    with pytest.raises(
        RealPaidAssessmentExecutionAttemptConflictError,
        match="existing execution attempt does not match",
    ):
        execute_recoverably(
            database_path=database_path,
            values=conflicting_values,
        )

    after = repository.list_artifacts(
        context=values["request"].context
    )

    after_identity = tuple(
        (
            artifact.artifact_id,
            artifact.artifact_hash,
            artifact.sequence_number,
            artifact.chain_hash,
        )
        for artifact in after
    )

    assert before_identity == after_identity


def test_corrupt_artifact_fails_before_recovery_replay(
    tmp_path,
):
    database_path = tmp_path / "corrupt-recovery.sqlite3"

    _, values = execute_recoverably(
        database_path=database_path,
        recorded_at=datetime(
            2026,
            8,
            20,
            18,
            45,
            tzinfo=timezone.utc,
        ),
    )

    with sqlite3.connect(database_path) as connection:
        connection.execute(
            """
            UPDATE governance_assessment_artifacts
            SET payload_json = ?
            WHERE tenant_id = ?
              AND client_id = ?
              AND engagement_id = ?
              AND assessment_id = ?
              AND sequence_number = 2
            """,
            (
                '{"tampered":true}',
                values["request"].context.tenant_id,
                values["request"].context.client_id,
                values["request"].context.engagement_id,
                values["request"].context.assessment_id,
            ),
        )

    with pytest.raises(
        ArtifactIntegrityError,
        match="payload hash verification failed",
    ):
        execute_recoverably(
            database_path=database_path,
            values=values,
        )

def test_chain_valid_wrong_artifact_order_fails_before_mutation(
    tmp_path,
):
    database_path = tmp_path / "wrong-order-recovery.sqlite3"

    _, values = execute_recoverably(
        database_path=database_path,
        recorded_at=datetime(
            2026,
            8,
            20,
            18,
            45,
            tzinfo=timezone.utc,
        ),
    )

    repository = GovernanceAssessmentRepository(
        database_path
    )

    with sqlite3.connect(database_path) as connection:
        connection.execute(
            """
            DELETE FROM governance_assessment_artifacts
            WHERE tenant_id = ?
              AND client_id = ?
              AND engagement_id = ?
              AND assessment_id = ?
            """,
            (
                values["request"].context.tenant_id,
                values["request"].context.client_id,
                values["request"].context.engagement_id,
                values["request"].context.assessment_id,
            ),
        )

    unexpected = repository.append_artifact(
        context=values["request"].context,
        artifact_type="unexpected-core-artifact",
        payload={
            "state": "integrity-valid-but-wrong-order",
        },
    )

    before = repository.list_artifacts(
        context=values["request"].context
    )

    assert len(before) == 1
    assert before[0].artifact_id == unexpected.artifact_id
    assert repository.verify_chain(
        context=values["request"].context
    ) is True

    with pytest.raises(
        RealPaidAssessmentExecutionRecoveryError,
        match="not an exact prefix",
    ):
        execute_recoverably(
            database_path=database_path,
            values=values,
        )

    after = repository.list_artifacts(
        context=values["request"].context
    )

    assert len(after) == 1
    assert after[0].artifact_id == unexpected.artifact_id
    assert after[0].artifact_hash == unexpected.artifact_hash
    assert repository.verify_chain(
        context=values["request"].context
    ) is True


def test_same_type_wrong_payload_fails_before_second_artifact_append(
    tmp_path,
):
    database_path = tmp_path / "wrong-payload-recovery.sqlite3"

    _, values = execute_recoverably(
        database_path=database_path,
        recorded_at=datetime(
            2026,
            8,
            20,
            18,
            45,
            tzinfo=timezone.utc,
        ),
    )

    repository = GovernanceAssessmentRepository(
        database_path
    )

    with sqlite3.connect(database_path) as connection:
        connection.execute(
            """
            DELETE FROM governance_assessment_artifacts
            WHERE tenant_id = ?
              AND client_id = ?
              AND engagement_id = ?
              AND assessment_id = ?
            """,
            (
                values["request"].context.tenant_id,
                values["request"].context.client_id,
                values["request"].context.engagement_id,
                values["request"].context.assessment_id,
            ),
        )

    conflicting = repository.append_artifact(
        context=values["request"].context,
        artifact_type="scope-configuration",
        payload={
            "state": "wrong-but-internally-valid-payload",
        },
    )

    before = repository.list_artifacts(
        context=values["request"].context
    )

    assert len(before) == 1
    assert before[0].artifact_type == "scope-configuration"
    assert before[0].artifact_id == conflicting.artifact_id
    assert repository.verify_chain(
        context=values["request"].context
    ) is True

    with pytest.raises(
        DemonstrationPersistenceError,
        match="conflicting artifact payload",
    ):
        execute_recoverably(
            database_path=database_path,
            values=values,
        )

    after = repository.list_artifacts(
        context=values["request"].context
    )

    assert len(after) == 1
    assert after[0].artifact_id == conflicting.artifact_id
    assert after[0].artifact_hash == conflicting.artifact_hash
    assert repository.verify_chain(
        context=values["request"].context
    ) is True