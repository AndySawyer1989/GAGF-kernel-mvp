from __future__ import annotations

import hashlib
import sqlite3
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
    CommercialPaidAssessmentExecutionInput,
    GovernanceCommercialPaidAssessmentExecutionService,
)
from backend.app.gagf.governance_commercial_paid_assessment_results_read_model import (
    CommercialPaidAssessmentResultsReadModelError,
    GovernanceCommercialPaidAssessmentResultsReadModelService,
    SAFE_RESULT_ARTIFACT_TYPES,
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


def build_executed_service(
    tmp_path: Path,
) -> GovernanceCommercialPaidAssessmentExecutionService:
    service = GovernanceCommercialPaidAssessmentExecutionService(
        execution_directory=tmp_path / "paid-assessments"
    )

    database_path = service.database_path_for_hierarchy(
        tenant_id="tenant-001",
        client_id="client-001",
        engagement_id="engagement-001",
        assessment_id="assessment-001",
    )

    service.execute(
        execution_input=build_execution_input(database_path),
        execution_input_binding_hash="binding-hash-001",
    )

    return service


def test_read_model_requires_execution_service() -> None:
    with pytest.raises(
        CommercialPaidAssessmentResultsReadModelError,
        match="execution_service",
    ):
        GovernanceCommercialPaidAssessmentResultsReadModelService(
            execution_service=object(),  # type: ignore[arg-type]
        )


def test_read_model_requires_durable_execution_status(
    tmp_path: Path,
) -> None:
    service = GovernanceCommercialPaidAssessmentExecutionService(
        execution_directory=tmp_path / "paid-assessments"
    )

    read_service = (
        GovernanceCommercialPaidAssessmentResultsReadModelService(
            execution_service=service
        )
    )

    with pytest.raises(
        CommercialPaidAssessmentResultsReadModelError,
        match="durable paid execution status",
    ):
        read_service.read(
            tenant_id="tenant-001",
            client_id="client-001",
            engagement_id="engagement-001",
            assessment_id="assessment-001",
        )


def test_read_model_projects_canonical_paid_results(
    tmp_path: Path,
) -> None:
    service = build_executed_service(tmp_path)

    result = (
        GovernanceCommercialPaidAssessmentResultsReadModelService(
            execution_service=service
        )
        .read(
            tenant_id="tenant-001",
            client_id="client-001",
            engagement_id="engagement-001",
            assessment_id="assessment-001",
        )
    )

    payload = result.to_dict()

    assert payload["hierarchy_key"] == (
        "tenant-001/client-001/"
        "engagement-001/assessment-001"
    )
    assert payload["execution_disposition"] == "executed"
    assert payload["artifact_count"] == 10
    assert payload["repository_chain_valid"] is True
    assert len(payload["artifact_inventory"]) == 10

    result_types = tuple(
        artifact["artifact_type"]
        for artifact in payload["result_artifacts"]
    )

    assert result_types == SAFE_RESULT_ARTIFACT_TYPES


def test_read_model_does_not_expose_raw_evidence_payload(
    tmp_path: Path,
) -> None:
    service = build_executed_service(tmp_path)

    result = (
        GovernanceCommercialPaidAssessmentResultsReadModelService(
            execution_service=service
        )
        .read(
            tenant_id="tenant-001",
            client_id="client-001",
            engagement_id="engagement-001",
            assessment_id="assessment-001",
        )
        .to_dict()
    )

    result_types = {
        artifact["artifact_type"]
        for artifact in result["result_artifacts"]
    }

    assert "evidence-intake-batch" not in result_types
    assert "scope-configuration" not in result_types
    assert CSV_TEXT not in repr(result["result_artifacts"])

    assert (
        result["boundaries"][
            "raw_evidence_payloads_not_exposed"
        ]
        is True
    )


def test_read_model_inventory_preserves_full_canonical_chain(
    tmp_path: Path,
) -> None:
    service = build_executed_service(tmp_path)

    result = (
        GovernanceCommercialPaidAssessmentResultsReadModelService(
            execution_service=service
        )
        .read(
            tenant_id="tenant-001",
            client_id="client-001",
            engagement_id="engagement-001",
            assessment_id="assessment-001",
        )
        .to_dict()
    )

    inventory_types = tuple(
        item["artifact_type"]
        for item in result["artifact_inventory"]
    )

    assert inventory_types == (
        "scope-configuration",
        "evidence-intake-batch",
        "evidence-quality",
        "friction-summary",
        "governance-debt-score",
        "intervention-plan",
        "assessment-roadmap",
        "executive-projection",
        "client-report-package",
        "demonstration-manifest",
    )


def test_read_model_restores_reconciled_disposition(
    tmp_path: Path,
) -> None:
    service = build_executed_service(tmp_path)

    database_path = service.database_path_for_hierarchy(
        tenant_id="tenant-001",
        client_id="client-001",
        engagement_id="engagement-001",
        assessment_id="assessment-001",
    )

    second = service.execute(
        execution_input=build_execution_input(database_path),
        execution_input_binding_hash="binding-hash-001",
    )

    assert second.disposition == "reconciled"

    result = (
        GovernanceCommercialPaidAssessmentResultsReadModelService(
            execution_service=service
        )
        .read(
            tenant_id="tenant-001",
            client_id="client-001",
            engagement_id="engagement-001",
            assessment_id="assessment-001",
        )
    )

    assert result.execution_disposition == "reconciled"


def test_read_model_rejects_tampered_paid_artifact(
    tmp_path: Path,
) -> None:
    service = build_executed_service(tmp_path)

    database_path = service.database_path_for_hierarchy(
        tenant_id="tenant-001",
        client_id="client-001",
        engagement_id="engagement-001",
        assessment_id="assessment-001",
    )

    with sqlite3.connect(database_path) as connection:
        connection.execute(
            """
            UPDATE governance_assessment_artifacts
            SET payload_json = ?
            WHERE artifact_type = ?
            """,
            (
                '{"tampered":true}',
                "friction-summary",
            ),
        )

    read_service = (
        GovernanceCommercialPaidAssessmentResultsReadModelService(
            execution_service=service
        )
    )

    with pytest.raises(
        Exception,
        match="payload hash",
    ):
        read_service.read(
            tenant_id="tenant-001",
            client_id="client-001",
            engagement_id="engagement-001",
            assessment_id="assessment-001",
        )


def test_read_model_is_read_only(
    tmp_path: Path,
) -> None:
    service = build_executed_service(tmp_path)

    database_path = service.database_path_for_hierarchy(
        tenant_id="tenant-001",
        client_id="client-001",
        engagement_id="engagement-001",
        assessment_id="assessment-001",
    )

    before_bytes = database_path.read_bytes()

    result = (
        GovernanceCommercialPaidAssessmentResultsReadModelService(
            execution_service=service
        )
        .read(
            tenant_id="tenant-001",
            client_id="client-001",
            engagement_id="engagement-001",
            assessment_id="assessment-001",
        )
    )

    after_bytes = database_path.read_bytes()

    assert result.repository_chain_valid is True
    assert after_bytes == before_bytes
