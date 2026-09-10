from pathlib import Path

import pytest

from backend.app.gagf.governance_assessment_isolation import (
    CommercialHierarchyContext,
)
from backend.app.gagf.governance_assessment_repository import (
    GovernanceAssessmentRepository,
)
from backend.app.gagf.governance_commercial_paid_assessment_execution import (
    GovernanceCommercialPaidAssessmentExecutionService,
)
from backend.app.gagf.governance_commercial_paid_assessment_lifecycle_status import (
    CommercialPaidAssessmentLifecycleStatusError,
    GovernanceCommercialPaidAssessmentLifecycleStatusService,
)
from backend.app.gagf.governance_paid_assessment_lifecycle_persistence import (
    ACKNOWLEDGMENT_ARTIFACT_TYPE,
    CLIENT_RESPONSE_ARTIFACT_TYPE,
    DELIVERY_ARTIFACT_TYPE,
)
from backend.app.gagf.governance_paid_assessment_lifecycle_query import (
    LIFECYCLE_STAGE_CLIENT_RESPONSE_RECORDED,
    LIFECYCLE_STAGE_DELIVERED,
    LIFECYCLE_STAGE_NOT_STARTED,
    LIFECYCLE_STAGE_RECEIPT_ACKNOWLEDGED,
    NEXT_STEP_NONE,
    NEXT_STEP_RECORD_ACKNOWLEDGMENT,
    NEXT_STEP_RECORD_DELIVERY,
    NEXT_STEP_RECORD_RESPONSE,
)


HIERARCHY = {
    "tenant_id": "tenant-alpha",
    "client_id": "client-acme",
    "engagement_id": "engagement-001",
    "assessment_id": "assessment-001",
}


def build_context() -> CommercialHierarchyContext:
    return CommercialHierarchyContext(**HIERARCHY)


def build_execution_service(
    tmp_path: Path,
) -> GovernanceCommercialPaidAssessmentExecutionService:
    return GovernanceCommercialPaidAssessmentExecutionService(
        execution_directory=tmp_path / "paid-assessments"
    )


def build_repository(
    execution_service: GovernanceCommercialPaidAssessmentExecutionService,
) -> GovernanceAssessmentRepository:
    database_path = (
        execution_service.database_path_for_hierarchy(
            **HIERARCHY
        )
    )

    database_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    repository = GovernanceAssessmentRepository(
        database_path
    )

    repository.create_assessment(
        context=build_context(),
        assessment_name="Paid Governance Assessment",
        status="complete",
    )

    return repository


def build_service(
    execution_service: GovernanceCommercialPaidAssessmentExecutionService,
) -> GovernanceCommercialPaidAssessmentLifecycleStatusService:
    return GovernanceCommercialPaidAssessmentLifecycleStatusService(
        execution_service=execution_service
    )


def delivery_payload() -> dict[str, object]:
    return {
        "tenant_id": HIERARCHY["tenant_id"],
        "client_id": HIERARCHY["client_id"],
        "engagement_id": HIERARCHY["engagement_id"],
        "assessment_id": HIERARCHY["assessment_id"],
        "report_id": "report-001",
        "delivery_event_id": "delivery-event-001",
        "delivery_event_hash": "a" * 64,
        "delivery_status": "delivered",
    }


def acknowledgment_payload() -> dict[str, object]:
    return {
        "tenant_id": HIERARCHY["tenant_id"],
        "client_id": HIERARCHY["client_id"],
        "engagement_id": HIERARCHY["engagement_id"],
        "assessment_id": HIERARCHY["assessment_id"],
        "report_id": "report-001",
        "delivery_event_id": "delivery-event-001",
        "delivery_event_hash": "a" * 64,
        "acknowledgment_id": "client-ack-001",
        "acknowledgment_hash": "b" * 64,
        "acknowledgment_status": (
            "client_receipt_acknowledged"
        ),
    }


def response_payload() -> dict[str, object]:
    return {
        "tenant_id": HIERARCHY["tenant_id"],
        "client_id": HIERARCHY["client_id"],
        "engagement_id": HIERARCHY["engagement_id"],
        "assessment_id": HIERARCHY["assessment_id"],
        "report_id": "report-001",
        "acknowledgment_id": "client-ack-001",
        "acknowledgment_hash": "b" * 64,
        "response_status": "client_response_recorded",
        "findings_disposition": "acknowledged",
        "recommendations_disposition": "accepted",
    }


def append_delivery(
    repository: GovernanceAssessmentRepository,
):
    return repository.append_artifact(
        context=build_context(),
        artifact_type=DELIVERY_ARTIFACT_TYPE,
        payload=delivery_payload(),
    )


def append_acknowledgment(
    repository: GovernanceAssessmentRepository,
):
    return repository.append_artifact(
        context=build_context(),
        artifact_type=ACKNOWLEDGMENT_ARTIFACT_TYPE,
        payload=acknowledgment_payload(),
    )


def append_response(
    repository: GovernanceAssessmentRepository,
):
    return repository.append_artifact(
        context=build_context(),
        artifact_type=CLIENT_RESPONSE_ARTIFACT_TYPE,
        payload=response_payload(),
    )


def test_projects_not_started_lifecycle(
    tmp_path: Path,
) -> None:
    execution_service = build_execution_service(
        tmp_path
    )
    build_repository(execution_service)

    result = build_service(
        execution_service
    ).get_status(
        **HIERARCHY
    )

    assert (
        result.current_stage
        == LIFECYCLE_STAGE_NOT_STARTED
    )
    assert (
        result.pending_next_step
        == NEXT_STEP_RECORD_DELIVERY
    )
    assert result.delivery_recorded is False
    assert result.receipt_acknowledged is False
    assert result.client_response_recorded is False
    assert result.report_id is None
    assert result.lifecycle_artifact_count == 0
    assert result.repository_chain_valid is True


def test_projects_delivered_lifecycle(
    tmp_path: Path,
) -> None:
    execution_service = build_execution_service(
        tmp_path
    )
    repository = build_repository(
        execution_service
    )

    append_delivery(repository)

    result = build_service(
        execution_service
    ).get_status(
        **HIERARCHY
    )

    assert result.current_stage == LIFECYCLE_STAGE_DELIVERED
    assert (
        result.pending_next_step
        == NEXT_STEP_RECORD_ACKNOWLEDGMENT
    )
    assert result.delivery_recorded is True
    assert result.receipt_acknowledged is False
    assert result.client_response_recorded is False
    assert result.report_id == "report-001"
    assert result.lifecycle_artifact_count == 1
    assert result.repository_chain_valid is True


def test_projects_receipt_acknowledged_lifecycle(
    tmp_path: Path,
) -> None:
    execution_service = build_execution_service(
        tmp_path
    )
    repository = build_repository(
        execution_service
    )

    append_delivery(repository)
    append_acknowledgment(repository)

    result = build_service(
        execution_service
    ).get_status(
        **HIERARCHY
    )

    assert (
        result.current_stage
        == LIFECYCLE_STAGE_RECEIPT_ACKNOWLEDGED
    )
    assert (
        result.pending_next_step
        == NEXT_STEP_RECORD_RESPONSE
    )
    assert result.delivery_recorded is True
    assert result.receipt_acknowledged is True
    assert result.client_response_recorded is False
    assert result.report_id == "report-001"
    assert result.lifecycle_artifact_count == 2
    assert result.repository_chain_valid is True


def test_projects_client_response_lifecycle(
    tmp_path: Path,
) -> None:
    execution_service = build_execution_service(
        tmp_path
    )
    repository = build_repository(
        execution_service
    )

    append_delivery(repository)
    append_acknowledgment(repository)
    append_response(repository)

    result = build_service(
        execution_service
    ).get_status(
        **HIERARCHY
    )

    assert (
        result.current_stage
        == LIFECYCLE_STAGE_CLIENT_RESPONSE_RECORDED
    )
    assert result.pending_next_step == NEXT_STEP_NONE
    assert result.delivery_recorded is True
    assert result.receipt_acknowledged is True
    assert result.client_response_recorded is True
    assert result.report_id == "report-001"
    assert (
        result.findings_disposition
        == "acknowledged"
    )
    assert (
        result.recommendations_disposition
        == "accepted"
    )
    assert result.lifecycle_artifact_count == 3
    assert result.repository_chain_valid is True

    payload = result.to_dict()

    assert payload["boundaries"][
        "lifecycle_status_is_read_only_projection"
    ] is True
    assert payload["boundaries"][
        "delivery_is_not_receipt"
    ] is True
    assert payload["boundaries"][
        "receipt_is_not_response"
    ] is True
    assert payload["boundaries"][
        "response_is_not_intervention_authority"
    ] is True


def test_status_query_is_read_only(
    tmp_path: Path,
) -> None:
    execution_service = build_execution_service(
        tmp_path
    )
    repository = build_repository(
        execution_service
    )

    append_delivery(repository)
    append_acknowledgment(repository)
    append_response(repository)

    before = repository.list_artifacts(
        context=build_context()
    )

    service = build_service(
        execution_service
    )

    first = service.get_status(
        **HIERARCHY
    )
    second = service.get_status(
        **HIERARCHY
    )

    after = repository.list_artifacts(
        context=build_context()
    )

    assert first == second
    assert before == after
    assert len(after) == 3


def test_rejects_invalid_lifecycle_order(
    tmp_path: Path,
) -> None:
    execution_service = build_execution_service(
        tmp_path
    )
    repository = build_repository(
        execution_service
    )

    repository.append_artifact(
        context=build_context(),
        artifact_type=ACKNOWLEDGMENT_ARTIFACT_TYPE,
        payload=acknowledgment_payload(),
    )

    with pytest.raises(
        CommercialPaidAssessmentLifecycleStatusError,
        match="acknowledgment exists without delivery",
    ):
        build_service(
            execution_service
        ).get_status(
            **HIERARCHY
        )


def test_repository_chain_tamper_fails_closed(
    tmp_path: Path,
) -> None:
    execution_service = build_execution_service(
        tmp_path
    )
    repository = build_repository(
        execution_service
    )

    delivery = append_delivery(repository)

    with repository._connect() as connection:
        connection.execute(
            "UPDATE governance_assessment_artifacts "
            "SET chain_hash = ? WHERE artifact_id = ?",
            (
                "f" * 64,
                delivery.artifact_id,
            ),
        )

    with pytest.raises(
        Exception,
        match="chain verification failed",
    ):
        build_service(
            execution_service
        ).get_status(
            **HIERARCHY
        )


def test_missing_hierarchy_database_projects_not_started(
    tmp_path: Path,
) -> None:
    execution_service = build_execution_service(
        tmp_path
    )

    result = build_service(
        execution_service
    ).get_status(
        **HIERARCHY
    )

    assert (
        result.current_stage
        == LIFECYCLE_STAGE_NOT_STARTED
    )
    assert (
        result.pending_next_step
        == NEXT_STEP_RECORD_DELIVERY
    )
    assert result.delivery_recorded is False
    assert result.receipt_acknowledged is False
    assert result.client_response_recorded is False
    assert result.report_id is None
    assert result.findings_disposition is None
    assert result.recommendations_disposition is None
    assert result.lifecycle_artifact_count == 0
    assert result.repository_chain_valid is True


def test_rejects_blank_hierarchy_component(
    tmp_path: Path,
) -> None:
    execution_service = build_execution_service(
        tmp_path
    )

    service = build_service(
        execution_service
    )

    with pytest.raises(
        CommercialPaidAssessmentLifecycleStatusError,
        match="tenant_id must not be empty",
    ):
        service.get_status(
            tenant_id=" ",
            client_id="client-acme",
            engagement_id="engagement-001",
            assessment_id="assessment-001",
        )
