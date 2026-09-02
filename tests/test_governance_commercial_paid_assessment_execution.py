from __future__ import annotations

import hashlib
from datetime import date
from pathlib import Path

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
from backend.app.gagf.governance_assessment_isolation import (
    CommercialHierarchyContext,
)
from backend.app.gagf.governance_assessment_scope_configuration import (
    EvidenceRequirement,
)
from backend.app.gagf.governance_commercial_paid_assessment_adapter import (
    CommercialContractExecutionEventInput,
    CommercialEvidenceDeclarationInput,
    CommercialExecutionEvidenceApprovalInput,
    CommercialPaidAssessmentIntakeInput,
    CommercialPaidWorkAuthorizationInput,
    CommercialStorageDeclarationInput,
)
from backend.app.gagf.governance_commercial_paid_assessment_execution import (
    CommercialPaidAssessmentExecutionError,
    CommercialPaidAssessmentExecutionInput,
    GovernanceCommercialPaidAssessmentExecutionService,
)


CSV_TEXT = (
    "event_id,event_type,occurred_at,"
    "constraint_type,duration_minutes,workflow_name,"
    "organizational_unit\n"
    "event-001,APPROVAL_DELAYED,2026-08-15T12:00:00+00:00,"
    "APPROVAL_DELAYED,120,Change Management,Operations\n"
)


def build_request() -> AssessmentExecutionRequest:
    context = CommercialHierarchyContext(
        tenant_id="tenant-001",
        client_id="client-001",
        engagement_id="engagement-001",
        assessment_id="assessment-001",
    )

    return AssessmentExecutionRequest(
        context=context,
        assessment_name="Governance Health Assessment",
        workflow_names=("Change Management",),
        organizational_units=("Operations",),
        period_start=date(2026, 8, 1),
        period_end=date(2026, 8, 29),
        objectives=("Evaluate governance friction",),
        expected_outcomes=("Produce deterministic findings",),
        evidence_requirements=(
            EvidenceRequirement(
                requirement_id="evidence-001",
                source_kind=EvidenceSourceKind.CSV,
                description="Governance workflow telemetry",
                required=True,
                minimum_record_count=1,
            ),
        ),
        evidence_inputs=(
            DemonstrationEvidenceInput(
                source=EvidenceSourceReference(
                    source_id="evidence-001",
                    kind=EvidenceSourceKind.CSV,
                    display_name="Governance workflow telemetry",
                    source_location="operator-upload",
                ),
                csv_text=CSV_TEXT,
            ),
        ),
        client_display_name="Client Organization",
        prepared_by="FIP Operator",
        exclusions=(),
        maximum_priorities=3,
    )


def build_execution_input(
    database_path: Path,
) -> CommercialPaidAssessmentExecutionInput:
    digest = hashlib.sha256(
        CSV_TEXT.encode("utf-8")
    ).hexdigest()

    intake = CommercialPaidAssessmentIntakeInput(
        tenant_id="tenant-001",
        client_id="client-001",
        engagement_id="engagement-001",
        assessment_id="assessment-001",
        client_display_name="Client Organization",
        assessment_name="Governance Health Assessment",
        operator_name="FIP Operator",
        client_contact_name="Client Contact",
        assessment_scope_confirmed=True,
        evidence_scope_confirmed=True,
        client_data_use_confirmed=True,
        operator_readiness_confirmed=True,
        evidence=(
            CommercialEvidenceDeclarationInput(
                evidence_id="evidence-001",
                source_kind="csv",
                description="Governance workflow telemetry",
                classification="non_sensitive",
                client_authorized_for_assessment=True,
                minimization_review_completed=True,
                direct_identifiers_removed=True,
            ),
        ),
        storage=CommercialStorageDeclarationInput(
            repository_path=str(database_path),
            operator_controlled_location=True,
            access_restricted=True,
            storage_protection_confirmed=True,
            backup_plan_recorded=True,
            retention_period_recorded=True,
            deletion_plan_recorded=True,
        ),
    )

    contract_event = CommercialContractExecutionEventInput(
        contract_execution_event_id="contract-event-001",
        contract_executed=True,
        contract_execution_review_ready=True,
        contract_execution_confirmed=True,
        executed_contract_reference_recorded=True,
        executed_at_recorded=True,
        all_required_signatures_recorded=True,
        human_operator_confirmed_execution=True,
        requires_final_paid_work_authorization=True,
        human_boundary_required=True,
        gagf_kernel_authoritative=True,
        ai_override_allowed=False,
    )

    authorization = CommercialPaidWorkAuthorizationInput(
        authorization_id="authorization-001",
        tenant_id="tenant-001",
        client_id="client-001",
        engagement_id="engagement-001",
        assessment_id="assessment-001",
        contract_execution_event_id="contract-event-001",
        authorized_by="Authorized Operator",
        authorized_at="2026-08-29T18:00:00+00:00",
        paid_assessment_authorized=True,
    )

    approval = CommercialExecutionEvidenceApprovalInput(
        evidence_id="evidence-001",
        approved_content_sha256=digest,
        approved_by="Evidence Approver",
        approved_at="2026-08-29T18:01:00+00:00",
        execution_evidence_approved=True,
    )

    return CommercialPaidAssessmentExecutionInput(
        intake=intake,
        contract_execution_event=contract_event,
        paid_work_authorization=authorization,
        execution_evidence_approvals=(approval,),
        assessment_execution_request=build_request(),
    )


def test_execution_input_requires_governed_request(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "paid-assessment.sqlite3"
    execution_input = build_execution_input(database_path)

    with pytest.raises(
        CommercialPaidAssessmentExecutionError,
        match="assessment_execution_request",
    ):
        CommercialPaidAssessmentExecutionInput(
            intake=execution_input.intake,
            contract_execution_event=(
                execution_input.contract_execution_event
            ),
            paid_work_authorization=(
                execution_input.paid_work_authorization
            ),
            execution_evidence_approvals=(
                execution_input.execution_evidence_approvals
            ),
            assessment_execution_request=object(),  # type: ignore[arg-type]
        )


def test_execution_input_requires_evidence_approval(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "paid-assessment.sqlite3"
    execution_input = build_execution_input(database_path)

    with pytest.raises(
        CommercialPaidAssessmentExecutionError,
        match="at least one execution-evidence approval",
    ):
        CommercialPaidAssessmentExecutionInput(
            intake=execution_input.intake,
            contract_execution_event=(
                execution_input.contract_execution_event
            ),
            paid_work_authorization=(
                execution_input.paid_work_authorization
            ),
            execution_evidence_approvals=(),
            assessment_execution_request=(
                execution_input.assessment_execution_request
            ),
        )


def test_service_rejects_wrong_execution_input_type(
    tmp_path: Path,
) -> None:
    service = GovernanceCommercialPaidAssessmentExecutionService(
        execution_directory=tmp_path / "paid-assessments"
    )

    with pytest.raises(
        CommercialPaidAssessmentExecutionError,
        match="CommercialPaidAssessmentExecutionInput",
    ):
        service.execute(
            execution_input=object(),  # type: ignore[arg-type]
            execution_input_binding_hash="binding-hash-001",
        )


def test_service_executes_new_governed_paid_assessment(
    tmp_path: Path,
) -> None:
    execution_directory = tmp_path / "paid-assessments"

    service = GovernanceCommercialPaidAssessmentExecutionService(
        execution_directory=execution_directory
    )

    database_path = service.database_path_for_hierarchy(
        tenant_id="tenant-001",
        client_id="client-001",
        engagement_id="engagement-001",
        assessment_id="assessment-001",
    )

    assert database_path.exists() is False

    execution_input = build_execution_input(
        database_path
    )

    result = service.execute(
        execution_input=execution_input,
        execution_input_binding_hash="binding-hash-001",
    )

    payload = result.to_dict()

    assert database_path.exists() is True
    assert payload["disposition"] == "executed"
    assert payload["artifact_count_before"] == 0
    assert payload["artifact_count_after"] == 10
    assert (
        payload["hierarchy_key"]
        == "tenant-001/client-001/engagement-001/assessment-001"
    )
    assert (
        payload["boundaries"][
            "recovery_is_not_second_execution_authority"
        ]
        is True
    )


def test_service_reconciles_exact_repeat(
    tmp_path: Path,
) -> None:
    execution_directory = tmp_path / "paid-assessments"

    service = GovernanceCommercialPaidAssessmentExecutionService(
        execution_directory=execution_directory
    )

    database_path = service.database_path_for_hierarchy(
        tenant_id="tenant-001",
        client_id="client-001",
        engagement_id="engagement-001",
        assessment_id="assessment-001",
    )

    execution_input = build_execution_input(
        database_path
    )

    first = service.execute(
        execution_input=execution_input,
        execution_input_binding_hash="binding-hash-001",
    )
    second = service.execute(
        execution_input=execution_input,
        execution_input_binding_hash="binding-hash-001",
    )

    assert first.disposition == "executed"
    assert second.disposition == "reconciled"
    assert second.artifact_count_before == 10
    assert second.artifact_count_after == 10
    assert (
        first.attempt.attempt_hash
        == second.attempt.attempt_hash
    )


def test_service_requires_execution_input_binding_hash(
    tmp_path: Path,
) -> None:
    execution_directory = (
        tmp_path
        / "paid-assessments"
    )

    service = (
        GovernanceCommercialPaidAssessmentExecutionService(
            execution_directory=execution_directory
        )
    )

    database_path = (
        service.database_path_for_hierarchy(
            tenant_id="tenant-001",
            client_id="client-001",
            engagement_id="engagement-001",
            assessment_id="assessment-001",
        )
    )

    execution_input = build_execution_input(
        database_path
    )

    with pytest.raises(
        CommercialPaidAssessmentExecutionError,
        match="execution_input_binding_hash",
    ):
        service.execute(
            execution_input=execution_input,
            execution_input_binding_hash="",
        )


def test_successful_execution_records_durable_status(
    tmp_path: Path,
) -> None:
    execution_directory = (
        tmp_path
        / "paid-assessments"
    )

    service = (
        GovernanceCommercialPaidAssessmentExecutionService(
            execution_directory=execution_directory
        )
    )

    database_path = (
        service.database_path_for_hierarchy(
            tenant_id="tenant-001",
            client_id="client-001",
            engagement_id="engagement-001",
            assessment_id="assessment-001",
        )
    )

    execution_input = build_execution_input(
        database_path
    )

    result = service.execute(
        execution_input=execution_input,
        execution_input_binding_hash=(
            "binding-hash-001"
        ),
    )

    stored = service.status_store.get_status(
        tenant_id="tenant-001",
        client_id="client-001",
        engagement_id="engagement-001",
        assessment_id="assessment-001",
    )

    assert stored is not None

    assert stored.disposition == "executed"

    assert (
        stored.attempt_hash
        == result.attempt.attempt_hash
    )

    assert (
        stored.attempt_record_hash
        == result.attempt.record_hash
    )

    assert (
        stored.assessment_execution_request_hash
        == (
            result.attempt
            .assessment_execution_request_hash
        )
    )

    assert (
        stored.execution_input_binding_hash
        == "binding-hash-001"
    )

    assert stored.artifact_count_before == 0
    assert stored.artifact_count_after == 10


def test_exact_repeat_updates_status_to_reconciled(
    tmp_path: Path,
) -> None:
    execution_directory = (
        tmp_path
        / "paid-assessments"
    )

    service = (
        GovernanceCommercialPaidAssessmentExecutionService(
            execution_directory=execution_directory
        )
    )

    database_path = (
        service.database_path_for_hierarchy(
            tenant_id="tenant-001",
            client_id="client-001",
            engagement_id="engagement-001",
            assessment_id="assessment-001",
        )
    )

    execution_input = build_execution_input(
        database_path
    )

    service.execute(
        execution_input=execution_input,
        execution_input_binding_hash=(
            "binding-hash-001"
        ),
    )

    second = service.execute(
        execution_input=execution_input,
        execution_input_binding_hash=(
            "binding-hash-001"
        ),
    )

    stored = service.status_store.get_status(
        tenant_id="tenant-001",
        client_id="client-001",
        engagement_id="engagement-001",
        assessment_id="assessment-001",
    )

    assert stored is not None

    assert (
        second.disposition
        == "reconciled"
    )

    assert (
        stored.disposition
        == "reconciled"
    )

    assert (
        stored.artifact_count_before
        == 10
    )

    assert (
        stored.artifact_count_after
        == 10
    )


def test_changed_binding_hash_cannot_replace_existing_status(
    tmp_path: Path,
) -> None:
    execution_directory = (
        tmp_path
        / "paid-assessments"
    )

    service = (
        GovernanceCommercialPaidAssessmentExecutionService(
            execution_directory=execution_directory
        )
    )

    database_path = (
        service.database_path_for_hierarchy(
            tenant_id="tenant-001",
            client_id="client-001",
            engagement_id="engagement-001",
            assessment_id="assessment-001",
        )
    )

    execution_input = build_execution_input(
        database_path
    )

    service.execute(
        execution_input=execution_input,
        execution_input_binding_hash=(
            "binding-hash-001"
        ),
    )

    with pytest.raises(
        CommercialPaidAssessmentExecutionError,
        match="durable execution status failed",
    ):
        service.execute(
            execution_input=execution_input,
            execution_input_binding_hash=(
                "different-binding-hash"
            ),
        )
