from __future__ import annotations

import hashlib
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.app.gagf.governance_commercial_paid_assessment_api import (
    create_governance_commercial_paid_assessment_router,
)
from backend.app.gagf.governance_commercial_paid_assessment_execution import (
    GovernanceCommercialPaidAssessmentExecutionService,
)


CSV_TEXT = (
    "event_id,event_type,occurred_at,work_item_id\n"
    "event-001,APPROVAL_DELAYED,"
    "2026-08-15T12:00:00+00:00,TICKET-001\n"
)


def build_payload(
    *,
    tenant_id: str = "tenant-001",
    client_id: str = "client-001",
    engagement_id: str = "engagement-001",
    assessment_id: str = "assessment-001",
) -> dict:
    digest = hashlib.sha256(
        CSV_TEXT.encode("utf-8")
    ).hexdigest()

    return {
        "intake": {
            "tenant_id": tenant_id,
            "client_id": client_id,
            "engagement_id": engagement_id,
            "assessment_id": assessment_id,
            "client_display_name": "Client Organization",
            "assessment_name": "Governance Health Assessment",
            "operator_name": "FIP Operator",
            "client_contact_name": "Client Contact",
            "assessment_scope_confirmed": True,
            "evidence_scope_confirmed": True,
            "client_data_use_confirmed": True,
            "operator_readiness_confirmed": True,
            "evidence": [
                {
                    "evidence_id": "evidence-001",
                    "source_kind": "csv",
                    "description": "Governance workflow telemetry",
                    "classification": "non_sensitive",
                    "client_authorized_for_assessment": True,
                    "minimization_review_completed": True,
                    "direct_identifiers_removed": True,
                }
            ],
            "storage": {
                "operator_controlled_location": True,
                "access_restricted": True,
                "storage_protection_confirmed": True,
                "backup_plan_recorded": True,
                "retention_period_recorded": True,
                "deletion_plan_recorded": True,
            },
        },
        "contract_execution_event": {
            "contract_execution_event_id": (
                f"contract-event-{assessment_id}"
            ),
            "contract_executed": True,
            "contract_execution_review_ready": True,
            "contract_execution_confirmed": True,
            "executed_contract_reference_recorded": True,
            "executed_at_recorded": True,
            "all_required_signatures_recorded": True,
            "human_operator_confirmed_execution": True,
            "requires_final_paid_work_authorization": True,
            "human_boundary_required": True,
            "gagf_kernel_authoritative": True,
            "ai_override_allowed": False,
        },
        "paid_work_authorization": {
            "authorization_id": (
                f"authorization-{assessment_id}"
            ),
            "tenant_id": tenant_id,
            "client_id": client_id,
            "engagement_id": engagement_id,
            "assessment_id": assessment_id,
            "contract_execution_event_id": (
                f"contract-event-{assessment_id}"
            ),
            "authorized_by": "Authorized Operator",
            "authorized_at": "2026-08-29T18:00:00+00:00",
            "paid_assessment_authorized": True,
        },
        "execution_evidence_approvals": [
            {
                "evidence_id": "evidence-001",
                "approved_content_sha256": digest,
                "approved_by": "Evidence Approver",
                "approved_at": "2026-08-29T18:01:00+00:00",
                "execution_evidence_approved": True,
            }
        ],
        "assessment_execution_request": {
            "tenant_id": tenant_id,
            "client_id": client_id,
            "engagement_id": engagement_id,
            "assessment_id": assessment_id,
            "assessment_name": "Governance Health Assessment",
            "workflow_names": ["Change Management"],
            "organizational_units": ["Operations"],
            "period_start": "2026-08-01",
            "period_end": "2026-08-29",
            "objectives": [
                "Evaluate governance friction"
            ],
            "expected_outcomes": [
                "Produce deterministic findings"
            ],
            "evidence_requirements": [
                {
                    "requirement_id": "evidence-001",
                    "source_kind": "csv",
                    "description": "Governance workflow telemetry",
                    "required": True,
                    "minimum_record_count": 1,
                }
            ],
            "evidence_inputs": [
                {
                    "source": {
                        "source_id": "evidence-001",
                        "kind": "csv",
                        "display_name": (
                            "Governance workflow telemetry"
                        ),
                        "source_location": "operator-upload",
                    },
                    "csv_text": CSV_TEXT,
                }
            ],
            "client_display_name": "Client Organization",
            "prepared_by": "FIP Operator",
            "maximum_priorities": 3,
        },
    }


def build_client(
    execution_directory: Path,
) -> tuple[
    TestClient,
    GovernanceCommercialPaidAssessmentExecutionService,
]:
    service = GovernanceCommercialPaidAssessmentExecutionService(
        execution_directory=execution_directory
    )

    app = FastAPI()
    app.include_router(
        create_governance_commercial_paid_assessment_router(
            service=service
        )
    )

    return TestClient(app), service


def test_execute_paid_assessment_returns_created(
    tmp_path: Path,
) -> None:
    execution_directory = tmp_path / "paid-assessments"
    client, service = build_client(execution_directory)

    payload = build_payload()

    expected_database_path = (
        service.database_path_for_hierarchy(
            tenant_id="tenant-001",
            client_id="client-001",
            engagement_id="engagement-001",
            assessment_id="assessment-001",
        )
    )

    assert expected_database_path.exists() is False

    response = client.post(
        "/api/v1/governance-paid-assessments/execute",
        json=payload,
    )

    assert response.status_code == 201

    body = response.json()

    assert expected_database_path.exists() is True
    assert body["operator_run_passed"] is True
    assert body["result"]["disposition"] == "executed"
    assert body["result"]["artifact_count_after"] == 10
    assert (
        body["result"]["hierarchy_key"]
        == "tenant-001/client-001/"
        "engagement-001/assessment-001"
    )
    assert (
        body["boundaries"][
            "execution_database_is_hierarchy_scoped"
        ]
        is True
    )


def test_execute_paid_assessment_reconciles_repeat(
    tmp_path: Path,
) -> None:
    execution_directory = tmp_path / "paid-assessments"
    client, _ = build_client(execution_directory)

    payload = build_payload()

    first = client.post(
        "/api/v1/governance-paid-assessments/execute",
        json=payload,
    )
    second = client.post(
        "/api/v1/governance-paid-assessments/execute",
        json=payload,
    )

    assert first.status_code == 201
    assert second.status_code == 201

    assert first.json()["result"]["disposition"] == "executed"
    assert second.json()["result"]["disposition"] == "reconciled"

    assert (
        first.json()["result"]["attempt_hash"]
        == second.json()["result"]["attempt_hash"]
    )


def test_two_hierarchies_use_distinct_server_databases(
    tmp_path: Path,
) -> None:
    execution_directory = tmp_path / "paid-assessments"
    client, service = build_client(execution_directory)

    first_payload = build_payload(
        assessment_id="assessment-001"
    )
    second_payload = build_payload(
        assessment_id="assessment-002"
    )

    first_database = service.database_path_for_hierarchy(
        tenant_id="tenant-001",
        client_id="client-001",
        engagement_id="engagement-001",
        assessment_id="assessment-001",
    )
    second_database = service.database_path_for_hierarchy(
        tenant_id="tenant-001",
        client_id="client-001",
        engagement_id="engagement-001",
        assessment_id="assessment-002",
    )

    assert first_database != second_database

    first = client.post(
        "/api/v1/governance-paid-assessments/execute",
        json=first_payload,
    )
    second = client.post(
        "/api/v1/governance-paid-assessments/execute",
        json=second_payload,
    )

    assert first.status_code == 201
    assert second.status_code == 201

    assert first.json()["result"]["disposition"] == "executed"
    assert second.json()["result"]["disposition"] == "executed"

    assert first_database.exists() is True
    assert second_database.exists() is True


def test_repository_path_is_not_browser_input(
    tmp_path: Path,
) -> None:
    execution_directory = tmp_path / "paid-assessments"
    client, service = build_client(execution_directory)
    payload = build_payload()

    payload["intake"]["storage"]["repository_path"] = (
        "C:/arbitrary/browser/path.sqlite3"
    )

    expected_database_path = (
        service.database_path_for_hierarchy(
            tenant_id="tenant-001",
            client_id="client-001",
            engagement_id="engagement-001",
            assessment_id="assessment-001",
        )
    )

    response = client.post(
        "/api/v1/governance-paid-assessments/execute",
        json=payload,
    )

    assert response.status_code == 201
    assert expected_database_path.exists() is True
    assert (
        Path(
            "C:/arbitrary/browser/path.sqlite3"
        ).exists()
        is False
    )
    assert (
        response.json()["boundaries"][
            "repository_path_is_server_assigned"
        ]
        is True
    )


def test_execute_rejects_false_paid_work_authorization(
    tmp_path: Path,
) -> None:
    client, _ = build_client(
        tmp_path / "paid-assessments"
    )
    payload = build_payload()

    payload["paid_work_authorization"][
        "paid_assessment_authorized"
    ] = False

    response = client.post(
        "/api/v1/governance-paid-assessments/execute",
        json=payload,
    )

    assert response.status_code == 422
    assert (
        response.json()["detail"]["code"]
        == "COMMERCIAL_PAID_ASSESSMENT_EXECUTION_ERROR"
    )


def test_execute_rejects_wrong_evidence_hash(
    tmp_path: Path,
) -> None:
    client, _ = build_client(
        tmp_path / "paid-assessments"
    )
    payload = build_payload()

    payload["execution_evidence_approvals"][0][
        "approved_content_sha256"
    ] = "0" * 64

    response = client.post(
        "/api/v1/governance-paid-assessments/execute",
        json=payload,
    )

    assert response.status_code == 422
    assert (
        response.json()["detail"]["code"]
        == "COMMERCIAL_PAID_ASSESSMENT_EXECUTION_ERROR"
    )