import sqlite3

import pytest

from backend.app.gagf.governance_assessment_isolation import (
    CommercialHierarchyContext,
)
from backend.app.gagf.governance_assessment_repository import (
    GovernanceAssessmentRepository,
)
from backend.app.gagf.governance_paid_assessment_lifecycle_persistence import (
    ACKNOWLEDGMENT_ARTIFACT_TYPE,
    CLIENT_RESPONSE_ARTIFACT_TYPE,
    DELIVERY_ARTIFACT_TYPE,
)
from backend.app.gagf.governance_paid_assessment_lifecycle_query import (
    GovernancePaidAssessmentLifecycleQueryService,
    LIFECYCLE_STAGE_CLIENT_RESPONSE_RECORDED,
    LIFECYCLE_STAGE_DELIVERED,
    LIFECYCLE_STAGE_NOT_STARTED,
    LIFECYCLE_STAGE_RECEIPT_ACKNOWLEDGED,
    NEXT_STEP_NONE,
    NEXT_STEP_RECORD_ACKNOWLEDGMENT,
    NEXT_STEP_RECORD_DELIVERY,
    NEXT_STEP_RECORD_RESPONSE,
    PaidAssessmentLifecycleQueryError,
)


def build_context(**overrides):
    values = {
        "tenant_id": "tenant-alpha",
        "client_id": "client-acme",
        "engagement_id": "engagement-001",
        "assessment_id": "assessment-001",
    }
    values.update(overrides)
    return CommercialHierarchyContext(**values)


@pytest.fixture
def repository(tmp_path):
    repo = GovernanceAssessmentRepository(
        tmp_path / "paid-assessment-query.sqlite3"
    )
    repo.create_assessment(
        context=build_context(),
        assessment_name="Paid Governance Assessment",
        status="complete",
    )
    return repo


def delivery_payload(**overrides):
    values = {
        "tenant_id": "tenant-alpha",
        "client_id": "client-acme",
        "engagement_id": "engagement-001",
        "assessment_id": "assessment-001",
        "report_id": "report-001",
        "delivery_event_id": "delivery-event-001",
        "delivery_event_hash": "a" * 64,
        "delivery_status": "delivered",
    }
    values.update(overrides)
    return values


def acknowledgment_payload(**overrides):
    values = {
        "tenant_id": "tenant-alpha",
        "client_id": "client-acme",
        "engagement_id": "engagement-001",
        "assessment_id": "assessment-001",
        "report_id": "report-001",
        "delivery_event_id": "delivery-event-001",
        "delivery_event_hash": "a" * 64,
        "acknowledgment_id": "client-ack-001",
        "acknowledgment_hash": "b" * 64,
        "acknowledgment_status": "client_receipt_acknowledged",
    }
    values.update(overrides)
    return values


def response_payload(**overrides):
    values = {
        "tenant_id": "tenant-alpha",
        "client_id": "client-acme",
        "engagement_id": "engagement-001",
        "assessment_id": "assessment-001",
        "report_id": "report-001",
        "acknowledgment_id": "client-ack-001",
        "acknowledgment_hash": "b" * 64,
        "response_status": "client_response_recorded",
        "findings_disposition": "acknowledged",
        "recommendations_disposition": "accepted",
    }
    values.update(overrides)
    return values


def service(repository):
    return GovernancePaidAssessmentLifecycleQueryService(
        repository=repository
    )


def append_delivery(repository):
    return repository.append_artifact(
        context=build_context(),
        artifact_type=DELIVERY_ARTIFACT_TYPE,
        payload=delivery_payload(),
    )


def append_acknowledgment(repository):
    return repository.append_artifact(
        context=build_context(),
        artifact_type=ACKNOWLEDGMENT_ARTIFACT_TYPE,
        payload=acknowledgment_payload(),
    )


def append_response(repository):
    return repository.append_artifact(
        context=build_context(),
        artifact_type=CLIENT_RESPONSE_ARTIFACT_TYPE,
        payload=response_payload(),
    )


def test_state_before_post_assessment_lifecycle(repository):
    state = service(repository).get_state(
        context=build_context()
    )

    assert state.current_stage == LIFECYCLE_STAGE_NOT_STARTED
    assert state.pending_next_step == NEXT_STEP_RECORD_DELIVERY
    assert state.delivery_recorded is False
    assert state.receipt_acknowledged is False
    assert state.client_response_recorded is False
    assert state.report_id is None
    assert state.findings_disposition is None
    assert state.recommendations_disposition is None
    assert state.lifecycle_artifact_count == 0
    assert state.repository_artifact_count == 0
    assert state.repository_chain_valid is True
    assert state.latest_lifecycle_artifact is None


def test_state_after_delivery(repository):
    delivery = append_delivery(repository)

    state = service(repository).get_state(
        context=build_context()
    )

    assert state.current_stage == LIFECYCLE_STAGE_DELIVERED
    assert (
        state.pending_next_step
        == NEXT_STEP_RECORD_ACKNOWLEDGMENT
    )
    assert state.delivery_recorded is True
    assert state.receipt_acknowledged is False
    assert state.client_response_recorded is False
    assert state.report_id == "report-001"
    assert state.lifecycle_artifact_count == 1
    assert state.latest_lifecycle_artifact is not None
    assert (
        state.latest_lifecycle_artifact.artifact_id
        == delivery.artifact_id
    )


def test_state_after_receipt_acknowledgment(repository):
    append_delivery(repository)
    acknowledgment = append_acknowledgment(repository)

    state = service(repository).get_state(
        context=build_context()
    )

    assert (
        state.current_stage
        == LIFECYCLE_STAGE_RECEIPT_ACKNOWLEDGED
    )
    assert state.pending_next_step == NEXT_STEP_RECORD_RESPONSE
    assert state.delivery_recorded is True
    assert state.receipt_acknowledged is True
    assert state.client_response_recorded is False
    assert state.report_id == "report-001"
    assert state.lifecycle_artifact_count == 2
    assert (
        state.latest_lifecycle_artifact.artifact_id
        == acknowledgment.artifact_id
    )


def test_state_after_client_response(repository):
    append_delivery(repository)
    append_acknowledgment(repository)
    response = append_response(repository)

    state = service(repository).get_state(
        context=build_context()
    )

    assert (
        state.current_stage
        == LIFECYCLE_STAGE_CLIENT_RESPONSE_RECORDED
    )
    assert state.pending_next_step == NEXT_STEP_NONE
    assert state.delivery_recorded is True
    assert state.receipt_acknowledged is True
    assert state.client_response_recorded is True
    assert state.report_id == "report-001"
    assert state.findings_disposition == "acknowledged"
    assert state.recommendations_disposition == "accepted"
    assert state.lifecycle_artifact_count == 3
    assert (
        state.latest_lifecycle_artifact.artifact_id
        == response.artifact_id
    )


def test_query_preserves_repository_sequence(repository):
    repository.append_artifact(
        context=build_context(),
        artifact_type="existing-assessment-artifact",
        payload={"value": 1},
    )
    delivery = append_delivery(repository)
    acknowledgment = append_acknowledgment(repository)
    response = append_response(repository)

    state = service(repository).get_state(
        context=build_context()
    )

    assert state.repository_artifact_count == 4
    assert state.lifecycle_artifact_count == 3
    assert [
        item.sequence_number
        for item in state.lifecycle_artifacts
    ] == [
        delivery.sequence_number,
        acknowledgment.sequence_number,
        response.sequence_number,
    ]
    assert [
        item.sequence_number
        for item in state.lifecycle_artifacts
    ] == [2, 3, 4]


def test_query_is_read_only(repository):
    append_delivery(repository)
    append_acknowledgment(repository)
    append_response(repository)

    before = repository.list_artifacts(
        context=build_context()
    )

    first = service(repository).get_state(
        context=build_context()
    )
    second = service(repository).get_state(
        context=build_context()
    )

    after = repository.list_artifacts(
        context=build_context()
    )

    assert before == after
    assert first == second
    assert len(after) == 3


def test_query_is_hierarchy_scoped(repository):
    append_delivery(repository)

    foreign_context = build_context(
        tenant_id="tenant-other"
    )

    with pytest.raises(Exception, match="assessment not found"):
        service(repository).get_state(
            context=foreign_context
        )


def test_rejects_acknowledgment_without_delivery(repository):
    repository.append_artifact(
        context=build_context(),
        artifact_type=ACKNOWLEDGMENT_ARTIFACT_TYPE,
        payload=acknowledgment_payload(),
    )

    with pytest.raises(
        PaidAssessmentLifecycleQueryError,
        match="acknowledgment exists without delivery",
    ):
        service(repository).get_state(
            context=build_context()
        )


def test_rejects_response_without_acknowledgment(repository):
    append_delivery(repository)

    repository.append_artifact(
        context=build_context(),
        artifact_type=CLIENT_RESPONSE_ARTIFACT_TYPE,
        payload=response_payload(),
    )

    with pytest.raises(
        PaidAssessmentLifecycleQueryError,
        match="response exists without receipt acknowledgment",
    ):
        service(repository).get_state(
            context=build_context()
        )


def test_rejects_duplicate_lifecycle_artifact_type(repository):
    append_delivery(repository)

    repository.append_artifact(
        context=build_context(),
        artifact_type=DELIVERY_ARTIFACT_TYPE,
        payload=delivery_payload(
            delivery_event_id="delivery-event-002",
            delivery_event_hash="c" * 64,
        ),
    )

    with pytest.raises(
        PaidAssessmentLifecycleQueryError,
        match="duplicate paid-assessment lifecycle artifact type",
    ):
        service(repository).get_state(
            context=build_context()
        )


@pytest.mark.parametrize(
    ("artifact_type", "payload"),
    [
        (
            DELIVERY_ARTIFACT_TYPE,
            delivery_payload(client_id="client-other"),
        ),
        (
            ACKNOWLEDGMENT_ARTIFACT_TYPE,
            acknowledgment_payload(
                client_id="client-other"
            ),
        ),
        (
            CLIENT_RESPONSE_ARTIFACT_TYPE,
            response_payload(client_id="client-other"),
        ),
    ],
)
def test_rejects_lifecycle_hierarchy_mismatch(
    repository,
    artifact_type,
    payload,
):
    if artifact_type != DELIVERY_ARTIFACT_TYPE:
        append_delivery(repository)

    if artifact_type == CLIENT_RESPONSE_ARTIFACT_TYPE:
        append_acknowledgment(repository)

    repository.append_artifact(
        context=build_context(),
        artifact_type=artifact_type,
        payload=payload,
    )

    with pytest.raises(
        PaidAssessmentLifecycleQueryError,
        match="hierarchy mismatch",
    ):
        service(repository).get_state(
            context=build_context()
        )


def test_rejects_acknowledgment_delivery_lineage_mismatch(repository):
    append_delivery(repository)

    repository.append_artifact(
        context=build_context(),
        artifact_type=ACKNOWLEDGMENT_ARTIFACT_TYPE,
        payload=acknowledgment_payload(
            delivery_event_id="delivery-other"
        ),
    )

    with pytest.raises(
        PaidAssessmentLifecycleQueryError,
        match="acknowledgment lineage",
    ):
        service(repository).get_state(
            context=build_context()
        )


def test_rejects_response_acknowledgment_lineage_mismatch(repository):
    append_delivery(repository)
    append_acknowledgment(repository)

    repository.append_artifact(
        context=build_context(),
        artifact_type=CLIENT_RESPONSE_ARTIFACT_TYPE,
        payload=response_payload(
            acknowledgment_id="ack-other"
        ),
    )

    with pytest.raises(
        PaidAssessmentLifecycleQueryError,
        match="response lineage",
    ):
        service(repository).get_state(
            context=build_context()
        )


def test_repository_chain_tamper_is_rejected(repository):
    delivery = append_delivery(repository)

    with repository._connect() as connection:
        connection.execute(
            "UPDATE governance_assessment_artifacts "
            "SET chain_hash = ? WHERE artifact_id = ?",
            ("f" * 64, delivery.artifact_id),
        )

    with pytest.raises(
        Exception,
        match="chain verification failed",
    ):
        service(repository).get_state(
            context=build_context()
        )


def test_projection_does_not_create_downstream_authority(repository):
    append_delivery(repository)
    append_acknowledgment(repository)
    append_response(repository)

    payload = service(repository).get_state(
        context=build_context()
    ).to_dict()

    assert payload["recommendations_disposition"] == "accepted"

    assert "intervention_requested" not in payload
    assert "intervention_authorized" not in payload
    assert "intervention_executed" not in payload
    assert "causal_success" not in payload
    assert "roi_verified" not in payload
    assert "remediation_success" not in payload
    assert "customer_outcome_verified" not in payload


def test_state_serialization_contains_evidence_references(repository):
    delivery = append_delivery(repository)
    acknowledgment = append_acknowledgment(repository)
    response = append_response(repository)

    payload = service(repository).get_state(
        context=build_context()
    ).to_dict()

    assert payload["hierarchy_key"] == (
        "tenant-alpha/client-acme/engagement-001/assessment-001"
    )
    assert payload["repository_chain_valid"] is True
    assert payload["lifecycle_artifact_count"] == 3
    assert payload["repository_artifact_count"] == 3

    assert [
        item["artifact_id"]
        for item in payload["lifecycle_artifacts"]
    ] == [
        delivery.artifact_id,
        acknowledgment.artifact_id,
        response.artifact_id,
    ]