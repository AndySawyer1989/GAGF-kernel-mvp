from __future__ import annotations

import hashlib
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.app.gagf.governance_assessment_api import (
    AssessmentExecutionApiRequest,
)
from backend.app.gagf.governance_commercial_paid_assessment_api import (
    create_governance_commercial_paid_assessment_router,
)
from backend.app.gagf.governance_commercial_paid_assessment_execution import (
    GovernanceCommercialPaidAssessmentExecutionService,
)
from backend.app.gagf.governance_commercial_paid_assessment_execution_input_binding import (
    GovernanceCommercialPaidAssessmentExecutionInputBindingService,
)


CSV_TEXT = (
    "event_id,event_type,occurred_at,work_item_id\n"
    "event-001,APPROVAL_DELAYED,"
    "2026-08-15T12:00:00+00:00,TICKET-001\n"
)


def build_assessment_execution_payload(
    *,
    tenant_id: str = "tenant-001",
    client_id: str = "client-001",
    engagement_id: str = "engagement-001",
    assessment_id: str = "assessment-001",
) -> dict:
    return {
        "tenant_id": tenant_id,
        "client_id": client_id,
        "engagement_id": engagement_id,
        "assessment_id": assessment_id,
        "assessment_name": (
            "Governance Health Assessment"
        ),
        "workflow_names": [
            "Change Management",
        ],
        "organizational_units": [
            "Operations",
        ],
        "period_start": (
            "2026-08-01"
        ),
        "period_end": (
            "2026-08-29"
        ),
        "objectives": [
            "Evaluate governance friction",
        ],
        "expected_outcomes": [
            "Produce deterministic findings",
        ],
        "evidence_requirements": [
            {
                "requirement_id": (
                    "evidence-001"
                ),
                "source_kind": "csv",
                "description": (
                    "Governance workflow telemetry"
                ),
                "required": True,
                "minimum_record_count": 1,
            }
        ],
        "evidence_inputs": [
            {
                "source": {
                    "source_id": (
                        "evidence-001"
                    ),
                    "kind": "csv",
                    "display_name": (
                        "Governance workflow telemetry"
                    ),
                    "source_location": (
                        "operator-upload"
                    ),
                },
                "csv_text": CSV_TEXT,
            }
        ],
        "client_display_name": (
            "Client Organization"
        ),
        "prepared_by": (
            "FIP Operator"
        ),
        "maximum_priorities": 3,
    }


def build_payload(
    *,
    tenant_id: str = "tenant-001",
    client_id: str = "client-001",
    engagement_id: str = "engagement-001",
    assessment_id: str = "assessment-001",
) -> dict:
    digest = hashlib.sha256(
        CSV_TEXT.encode(
            "utf-8"
        )
    ).hexdigest()

    return {
        "intake": {
            "tenant_id": tenant_id,
            "client_id": client_id,
            "engagement_id": engagement_id,
            "assessment_id": assessment_id,
            "client_display_name": (
                "Client Organization"
            ),
            "assessment_name": (
                "Governance Health Assessment"
            ),
            "operator_name": (
                "FIP Operator"
            ),
            "client_contact_name": (
                "Client Contact"
            ),
            "assessment_scope_confirmed": True,
            "evidence_scope_confirmed": True,
            "client_data_use_confirmed": True,
            "operator_readiness_confirmed": True,
            "evidence": [
                {
                    "evidence_id": (
                        "evidence-001"
                    ),
                    "source_kind": (
                        "csv"
                    ),
                    "description": (
                        "Governance workflow telemetry"
                    ),
                    "classification": (
                        "non_sensitive"
                    ),
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
            "authorized_by": (
                "Authorized Operator"
            ),
            "authorized_at": (
                "2026-08-29T18:00:00+00:00"
            ),
            "paid_assessment_authorized": True,
        },
        "execution_evidence_approvals": [
            {
                "evidence_id": (
                    "evidence-001"
                ),
                "approved_content_sha256": (
                    digest
                ),
                "approved_by": (
                    "Evidence Approver"
                ),
                "approved_at": (
                    "2026-08-29T18:01:00+00:00"
                ),
                "execution_evidence_approved": True,
            }
        ],
    }


def build_client(
    tmp_path: Path,
) -> tuple[
    TestClient,
    GovernanceCommercialPaidAssessmentExecutionService,
    GovernanceCommercialPaidAssessmentExecutionInputBindingService,
]:
    execution_directory = (
        tmp_path
        / "paid-assessments"
    )

    binding_directory = (
        tmp_path
        / "execution-input-bindings"
    )

    service = (
        GovernanceCommercialPaidAssessmentExecutionService(
            execution_directory=(
                execution_directory
            )
        )
    )

    binding_service = (
        GovernanceCommercialPaidAssessmentExecutionInputBindingService(
            binding_directory=(
                binding_directory
            )
        )
    )

    app = FastAPI()

    app.include_router(
        create_governance_commercial_paid_assessment_router(
            service=service,
            execution_input_binding_service=(
                binding_service
            ),
        )
    )

    return (
        TestClient(app),
        service,
        binding_service,
    )


def bind_execution_input(
    *,
    binding_service: (
        GovernanceCommercialPaidAssessmentExecutionInputBindingService
    ),
    tenant_id: str = "tenant-001",
    client_id: str = "client-001",
    engagement_id: str = "engagement-001",
    assessment_id: str = "assessment-001",
) -> None:
    api_request = (
        AssessmentExecutionApiRequest(
            **build_assessment_execution_payload(
                tenant_id=tenant_id,
                client_id=client_id,
                engagement_id=engagement_id,
                assessment_id=assessment_id,
            )
        )
    )

    binding_service.bind(
        request=(
            api_request.to_application_request()
        )
    )


def test_get_execution_input_binding_returns_safe_metadata(
    tmp_path: Path,
) -> None:
    client, _, binding_service = (
        build_client(
            tmp_path
        )
    )

    bind_execution_input(
        binding_service=(
            binding_service
        )
    )

    response = client.get(
        (
            "/api/v1/governance-paid-assessments/"
            "tenant-001/client-001/"
            "engagement-001/assessment-001/"
            "execution-input-binding"
        )
    )

    assert response.status_code == 200

    body = response.json()

    assert (
        body[
            "hierarchy_key"
        ]
        == (
            "tenant-001/client-001/"
            "engagement-001/assessment-001"
        )
    )

    assert (
        body[
            "assessment_name"
        ]
        == "Governance Health Assessment"
    )

    assert (
        body[
            "client_display_name"
        ]
        == "Client Organization"
    )

    assert (
        isinstance(
            body[
                "assessment_execution_request_hash"
            ],
            str,
        )
    )

    assert (
        isinstance(
            body[
                "execution_input_hash"
            ],
            str,
        )
    )

    assert (
        isinstance(
            body[
                "binding_hash"
            ],
            str,
        )
    )

    assert len(
        body[
            "evidence"
        ]
    ) == 1

    evidence = (
        body[
            "evidence"
        ][0]
    )

    assert (
        evidence[
            "evidence_id"
        ]
        == "evidence-001"
    )

    assert (
        evidence[
            "source_id"
        ]
        == "evidence-001"
    )

    assert (
        evidence[
            "source_kind"
        ]
        == "csv"
    )

    assert (
        evidence[
            "content_sha256"
        ]
        == hashlib.sha256(
            CSV_TEXT.encode(
                "utf-8"
            )
        ).hexdigest()
    )

    assert (
        body[
            "boundaries"
        ][
            "raw_evidence_not_exposed"
        ]
        is True
    )

    assert (
        body[
            "boundaries"
        ][
            "binding_metadata_is_not_execution_authority"
        ]
        is True
    )

    assert (
        body[
            "boundaries"
        ][
            "binding_metadata_is_not_evidence_approval"
        ]
        is True
    )


def test_get_execution_input_binding_does_not_expose_raw_evidence(
    tmp_path: Path,
) -> None:
    client, _, binding_service = (
        build_client(
            tmp_path
        )
    )

    bind_execution_input(
        binding_service=(
            binding_service
        )
    )

    response = client.get(
        (
            "/api/v1/governance-paid-assessments/"
            "tenant-001/client-001/"
            "engagement-001/assessment-001/"
            "execution-input-binding"
        )
    )

    assert response.status_code == 200

    body_text = response.text

    assert CSV_TEXT not in body_text

    assert (
        "csv_text"
        not in body_text
    )

    assert (
        "assessment_execution_request_payload"
        not in body_text
    )

    assert (
        "assessment_execution_request_material"
        not in body_text
    )


def test_get_execution_input_binding_rejects_missing_binding(
    tmp_path: Path,
) -> None:
    client, _, _ = (
        build_client(
            tmp_path
        )
    )

    response = client.get(
        (
            "/api/v1/governance-paid-assessments/"
            "tenant-001/client-001/"
            "engagement-001/assessment-001/"
            "execution-input-binding"
        )
    )

    assert response.status_code == 409

    assert (
        response.json()[
            "detail"
        ][
            "code"
        ]
        == (
            "COMMERCIAL_PAID_ASSESSMENT_"
            "EXECUTION_INPUT_BINDING_ERROR"
        )
    )


def test_execute_paid_assessment_returns_created(
    tmp_path: Path,
) -> None:
    client, service, binding_service = (
        build_client(
            tmp_path
        )
    )

    bind_execution_input(
        binding_service=(
            binding_service
        )
    )

    payload = (
        build_payload()
    )

    expected_database_path = (
        service.database_path_for_hierarchy(
            tenant_id="tenant-001",
            client_id="client-001",
            engagement_id="engagement-001",
            assessment_id="assessment-001",
        )
    )

    assert (
        expected_database_path.exists()
        is False
    )

    response = client.post(
        "/api/v1/governance-paid-assessments/execute",
        json=payload,
    )

    assert response.status_code == 201

    body = response.json()

    assert (
        expected_database_path.exists()
        is True
    )

    assert (
        body[
            "operator_run_passed"
        ]
        is True
    )

    assert (
        body[
            "result"
        ][
            "disposition"
        ]
        == "executed"
    )

    assert (
        body[
            "result"
        ][
            "artifact_count_after"
        ]
        == 10
    )

    assert (
        body[
            "result"
        ][
            "hierarchy_key"
        ]
        == (
            "tenant-001/client-001/"
            "engagement-001/assessment-001"
        )
    )

    assert (
        body[
            "execution_input_binding"
        ][
            "hierarchy_key"
        ]
        == (
            "tenant-001/client-001/"
            "engagement-001/assessment-001"
        )
    )

    assert (
        body[
            "execution_input_binding"
        ][
            "binding_hash"
        ]
    )

    assert (
        body[
            "boundaries"
        ][
            "assessment_execution_request_is_server_bound"
        ]
        is True
    )

    assert (
        body[
            "boundaries"
        ][
            "raw_execution_evidence_is_not_browser_resubmitted"
        ]
        is True
    )


def test_execute_paid_assessment_reconciles_repeat(
    tmp_path: Path,
) -> None:
    client, _, binding_service = (
        build_client(
            tmp_path
        )
    )

    bind_execution_input(
        binding_service=(
            binding_service
        )
    )

    payload = (
        build_payload()
    )

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

    assert (
        first.json()[
            "result"
        ][
            "disposition"
        ]
        == "executed"
    )

    assert (
        second.json()[
            "result"
        ][
            "disposition"
        ]
        == "reconciled"
    )

    assert (
        first.json()[
            "result"
        ][
            "attempt_hash"
        ]
        == second.json()[
            "result"
        ][
            "attempt_hash"
        ]
    )


def test_two_hierarchies_use_distinct_server_databases(
    tmp_path: Path,
) -> None:
    client, service, binding_service = (
        build_client(
            tmp_path
        )
    )

    bind_execution_input(
        binding_service=(
            binding_service
        ),
        assessment_id=(
            "assessment-001"
        ),
    )

    bind_execution_input(
        binding_service=(
            binding_service
        ),
        assessment_id=(
            "assessment-002"
        ),
    )

    first_payload = build_payload(
        assessment_id=(
            "assessment-001"
        )
    )

    second_payload = build_payload(
        assessment_id=(
            "assessment-002"
        )
    )

    first_database = (
        service.database_path_for_hierarchy(
            tenant_id="tenant-001",
            client_id="client-001",
            engagement_id="engagement-001",
            assessment_id="assessment-001",
        )
    )

    second_database = (
        service.database_path_for_hierarchy(
            tenant_id="tenant-001",
            client_id="client-001",
            engagement_id="engagement-001",
            assessment_id="assessment-002",
        )
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

    assert (
        first.json()[
            "result"
        ][
            "disposition"
        ]
        == "executed"
    )

    assert (
        second.json()[
            "result"
        ][
            "disposition"
        ]
        == "executed"
    )

    assert first_database.exists() is True
    assert second_database.exists() is True


def test_repository_path_is_not_browser_input(
    tmp_path: Path,
) -> None:
    client, service, binding_service = (
        build_client(
            tmp_path
        )
    )

    bind_execution_input(
        binding_service=(
            binding_service
        )
    )

    payload = (
        build_payload()
    )

    payload[
        "intake"
    ][
        "storage"
    ][
        "repository_path"
    ] = (
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

    assert (
        expected_database_path.exists()
        is True
    )

    assert (
        Path(
            "C:/arbitrary/browser/path.sqlite3"
        ).exists()
        is False
    )

    assert (
        response.json()[
            "boundaries"
        ][
            "repository_path_is_server_assigned"
        ]
        is True
    )


def test_execute_rejects_missing_execution_input_binding(
    tmp_path: Path,
) -> None:
    client, _, _ = (
        build_client(
            tmp_path
        )
    )

    response = client.post(
        "/api/v1/governance-paid-assessments/execute",
        json=(
            build_payload()
        ),
    )

    assert response.status_code == 409

    assert (
        response.json()[
            "detail"
        ][
            "code"
        ]
        == (
            "COMMERCIAL_PAID_ASSESSMENT_"
            "EXECUTION_INPUT_BINDING_ERROR"
        )
    )


def test_execute_rejects_intake_name_mismatch(
    tmp_path: Path,
) -> None:
    client, _, binding_service = (
        build_client(
            tmp_path
        )
    )

    bind_execution_input(
        binding_service=(
            binding_service
        )
    )

    payload = (
        build_payload()
    )

    payload[
        "intake"
    ][
        "assessment_name"
    ] = (
        "Browser-Replaced Assessment Name"
    )

    response = client.post(
        "/api/v1/governance-paid-assessments/execute",
        json=payload,
    )

    assert response.status_code == 409

    assert (
        response.json()[
            "detail"
        ][
            "code"
        ]
        == (
            "COMMERCIAL_PAID_ASSESSMENT_"
            "EXECUTION_INPUT_BINDING_ERROR"
        )
    )


def test_execute_rejects_false_paid_work_authorization(
    tmp_path: Path,
) -> None:
    client, _, binding_service = (
        build_client(
            tmp_path
        )
    )

    bind_execution_input(
        binding_service=(
            binding_service
        )
    )

    payload = (
        build_payload()
    )

    payload[
        "paid_work_authorization"
    ][
        "paid_assessment_authorized"
    ] = False

    response = client.post(
        "/api/v1/governance-paid-assessments/execute",
        json=payload,
    )

    assert response.status_code == 422

    assert (
        response.json()[
            "detail"
        ][
            "code"
        ]
        == (
            "COMMERCIAL_PAID_ASSESSMENT_EXECUTION_ERROR"
        )
    )


def test_execute_rejects_wrong_evidence_hash(
    tmp_path: Path,
) -> None:
    client, _, binding_service = (
        build_client(
            tmp_path
        )
    )

    bind_execution_input(
        binding_service=(
            binding_service
        )
    )

    payload = (
        build_payload()
    )

    payload[
        "execution_evidence_approvals"
    ][0][
        "approved_content_sha256"
    ] = (
        "0" * 64
    )

    response = client.post(
        "/api/v1/governance-paid-assessments/execute",
        json=payload,
    )

    assert response.status_code == 422

    assert (
        response.json()[
            "detail"
        ][
            "code"
        ]
        == (
            "COMMERCIAL_PAID_ASSESSMENT_EXECUTION_ERROR"
        )
    )


def test_browser_cannot_supply_assessment_execution_request(
    tmp_path: Path,
) -> None:
    client, _, binding_service = (
        build_client(
            tmp_path
        )
    )

    bind_execution_input(
        binding_service=(
            binding_service
        )
    )

    payload = (
        build_payload()
    )

    payload[
        "assessment_execution_request"
    ] = {
        "tenant_id": "attacker-tenant",
        "client_id": "attacker-client",
        "engagement_id": "attacker-engagement",
        "assessment_id": "attacker-assessment",
    }

    response = client.post(
        "/api/v1/governance-paid-assessments/execute",
        json=payload,
    )

    assert response.status_code == 422

    detail = (
        response.json()[
            "detail"
        ]
    )

    assert any(
        item[
            "type"
        ]
        == "extra_forbidden"
        and item[
            "loc"
        ][-1]
        == "assessment_execution_request"
        for item in detail
    )