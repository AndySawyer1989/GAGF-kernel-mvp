from datetime import datetime, timezone

import pytest

from backend.app.gagf.governance_assessment_isolation import (
    CommercialHierarchyContext,
)
from backend.app.gagf.governance_assessment_repository import (
    GovernanceAssessmentRepository,
)
from backend.app.gagf.governance_paid_assessment_client_acknowledgment import (
    GovernedPaidAssessmentClientAcknowledgment,
)
from backend.app.gagf.governance_paid_assessment_client_response import (
    GovernedPaidAssessmentClientResponse,
)
from backend.app.gagf.governance_paid_assessment_delivery_event import (
    GovernedPaidAssessmentDeliveryEvent,
)
from backend.app.gagf.governance_paid_assessment_lifecycle_persistence import (
    ACKNOWLEDGMENT_ARTIFACT_TYPE,
    CLIENT_RESPONSE_ARTIFACT_TYPE,
    DELIVERY_ARTIFACT_TYPE,
    GovernancePaidAssessmentLifecyclePersistenceService,
    PaidAssessmentLifecyclePersistenceError,
)


SERVICE = GovernancePaidAssessmentLifecyclePersistenceService()

HEX_A = "a" * 64
HEX_B = "b" * 64
HEX_C = "c" * 64
HEX_D = "d" * 64
HEX_E = "e" * 64
HEX_F = "f" * 64


def build_context():
    return CommercialHierarchyContext(
        tenant_id="tenant-alpha",
        client_id="client-acme",
        engagement_id="engagement-001",
        assessment_id="assessment-001",
    )


@pytest.fixture
def repository(tmp_path):
    repo = GovernanceAssessmentRepository(
        tmp_path / "paid-assessment.sqlite"
    )
    repo.create_assessment(
        context=build_context(),
        assessment_name="Paid Governance Assessment",
        status="completed",
    )
    return repo


def build_delivery_event(**overrides):
    values = {
        "tenant_id": "tenant-alpha",
        "client_id": "client-acme",
        "engagement_id": "engagement-001",
        "assessment_id": "assessment-001",
        "report_id": "report-001",
        "delivery_envelope_hash": HEX_A,
        "delivery_approval_hash": HEX_B,
        "human_delivery_confirmation_hash": HEX_C,
        "delivery_event_id": "delivery-event-001",
        "delivered_by": "FIP Operator",
        "delivered_at": "2026-08-18T19:15:00+00:00",
        "delivery_method": "email",
        "delivery_reference": "mail-message-001",
        "delivery_status": "delivered",
        "delivery_event_hash": HEX_D,
    }
    values.update(overrides)
    return GovernedPaidAssessmentDeliveryEvent(**values)


def build_acknowledgment(delivery_event=None, **overrides):
    delivery_event = delivery_event or build_delivery_event()

    values = {
        "tenant_id": delivery_event.tenant_id,
        "client_id": delivery_event.client_id,
        "engagement_id": delivery_event.engagement_id,
        "assessment_id": delivery_event.assessment_id,
        "report_id": delivery_event.report_id,
        "delivery_event_id": delivery_event.delivery_event_id,
        "delivery_event_hash": delivery_event.delivery_event_hash,
        "acknowledgment_id": "client-ack-001",
        "acknowledgment_evidence_hash": HEX_E,
        "acknowledged_by": "ACME Client Representative",
        "acknowledged_at": "2026-08-18T19:30:00+00:00",
        "acknowledgment_method": "email_reply",
        "acknowledgment_reference": "mail-reply-001",
        "acknowledgment_status": "client_receipt_acknowledged",
        "acknowledgment_hash": HEX_F,
    }
    values.update(overrides)

    return GovernedPaidAssessmentClientAcknowledgment(**values)


def build_response(acknowledgment=None, **overrides):
    acknowledgment = acknowledgment or build_acknowledgment()

    values = {
        "tenant_id": acknowledgment.tenant_id,
        "client_id": acknowledgment.client_id,
        "engagement_id": acknowledgment.engagement_id,
        "assessment_id": acknowledgment.assessment_id,
        "report_id": acknowledgment.report_id,
        "acknowledgment_id": acknowledgment.acknowledgment_id,
        "acknowledgment_hash": acknowledgment.acknowledgment_hash,
        "response_id": "client-response-001",
        "response_evidence_hash": HEX_A,
        "responded_by": "ACME Client Representative",
        "responded_at": "2026-08-18T20:00:00+00:00",
        "response_method": "email_reply",
        "response_reference": "assessment-response-001",
        "findings_disposition": "acknowledged",
        "recommendations_disposition": "accepted",
        "response_note": "Accepted for planning review.",
        "response_status": "client_response_recorded",
        "response_hash": HEX_B,
    }
    values.update(overrides)

    return GovernedPaidAssessmentClientResponse(**values)


def test_persists_post_assessment_lifecycle(repository):
    delivery = build_delivery_event()
    acknowledgment = build_acknowledgment(delivery)
    response = build_response(acknowledgment)

    receipt = SERVICE.persist_lifecycle(
        repository=repository,
        delivery_event=delivery,
        client_acknowledgment=acknowledgment,
        client_response=response,
        created_at=datetime(
            2026, 8, 18, 20, 5, tzinfo=timezone.utc
        ),
    )

    artifacts = repository.list_artifacts(
        context=build_context()
    )

    assert len(artifacts) == 3
    assert [item.artifact_type for item in artifacts] == [
        DELIVERY_ARTIFACT_TYPE,
        ACKNOWLEDGMENT_ARTIFACT_TYPE,
        CLIENT_RESPONSE_ARTIFACT_TYPE,
    ]
    assert [item.sequence_number for item in artifacts] == [1, 2, 3]

    assert artifacts[0].payload == delivery.to_dict()
    assert artifacts[1].payload == acknowledgment.to_dict()
    assert artifacts[2].payload == response.to_dict()

    assert receipt.first_sequence_number == 1
    assert receipt.last_sequence_number == 3
    assert receipt.repository_chain_valid is True
    assert repository.verify_chain(context=build_context()) is True


def test_appends_after_existing_assessment_artifacts(repository):
    repository.append_artifact(
        context=build_context(),
        artifact_type="existing-assessment-artifact",
        payload={"existing": True},
    )

    delivery = build_delivery_event()
    acknowledgment = build_acknowledgment(delivery)
    response = build_response(acknowledgment)

    receipt = SERVICE.persist_lifecycle(
        repository=repository,
        delivery_event=delivery,
        client_acknowledgment=acknowledgment,
        client_response=response,
    )

    assert receipt.first_sequence_number == 2
    assert receipt.last_sequence_number == 4
    assert repository.verify_chain(context=build_context()) is True


def test_requires_existing_assessment(tmp_path):
    repository = GovernanceAssessmentRepository(
        tmp_path / "empty.sqlite"
    )

    delivery = build_delivery_event()
    acknowledgment = build_acknowledgment(delivery)
    response = build_response(acknowledgment)

    with pytest.raises(Exception, match="assessment not found"):
        SERVICE.persist_lifecycle(
            repository=repository,
            delivery_event=delivery,
            client_acknowledgment=acknowledgment,
            client_response=response,
        )


def test_rejects_non_delivered_event(repository):
    delivery = build_delivery_event(
        delivery_status="pending"
    )

    with pytest.raises(
        PaidAssessmentLifecyclePersistenceError,
        match="delivery_status=delivered",
    ):
        SERVICE.persist_lifecycle(
            repository=repository,
            delivery_event=delivery,
            client_acknowledgment=build_acknowledgment(delivery),
            client_response=build_response(
                build_acknowledgment(delivery)
            ),
        )


def test_rejects_acknowledgment_lineage_mismatch(repository):
    delivery = build_delivery_event()

    acknowledgment = build_acknowledgment(
        delivery,
        client_id="client-other",
    )
    response = build_response(acknowledgment)

    with pytest.raises(
        PaidAssessmentLifecyclePersistenceError,
        match="acknowledgment lineage",
    ):
        SERVICE.persist_lifecycle(
            repository=repository,
            delivery_event=delivery,
            client_acknowledgment=acknowledgment,
            client_response=response,
        )


def test_rejects_response_lineage_mismatch(repository):
    delivery = build_delivery_event()
    acknowledgment = build_acknowledgment(delivery)

    response = build_response(
        acknowledgment,
        acknowledgment_id="ack-other",
    )

    with pytest.raises(
        PaidAssessmentLifecyclePersistenceError,
        match="response lineage",
    ):
        SERVICE.persist_lifecycle(
            repository=repository,
            delivery_event=delivery,
            client_acknowledgment=acknowledgment,
            client_response=response,
        )


def test_receipt_binds_persisted_artifacts(repository):
    delivery = build_delivery_event()
    acknowledgment = build_acknowledgment(delivery)
    response = build_response(acknowledgment)

    receipt = SERVICE.persist_lifecycle(
        repository=repository,
        delivery_event=delivery,
        client_acknowledgment=acknowledgment,
        client_response=response,
    )

    artifacts = repository.list_artifacts(
        context=build_context()
    )

    assert receipt.delivery_artifact_id == artifacts[0].artifact_id
    assert receipt.delivery_artifact_hash == artifacts[0].artifact_hash
    assert (
        receipt.acknowledgment_artifact_id
        == artifacts[1].artifact_id
    )
    assert (
        receipt.acknowledgment_artifact_hash
        == artifacts[1].artifact_hash
    )
    assert receipt.response_artifact_id == artifacts[2].artifact_id
    assert receipt.response_artifact_hash == artifacts[2].artifact_hash


def test_persistence_does_not_create_new_authority(repository):
    delivery = build_delivery_event()
    acknowledgment = build_acknowledgment(delivery)
    response = build_response(acknowledgment)

    receipt = SERVICE.persist_lifecycle(
        repository=repository,
        delivery_event=delivery,
        client_acknowledgment=acknowledgment,
        client_response=response,
    )

    payload = receipt.to_dict()

    assert "intervention_requested" not in payload
    assert "intervention_authorized" not in payload
    assert "intervention_executed" not in payload
    assert "causal_success" not in payload
    assert "roi_verified" not in payload
    assert "remediation_success" not in payload
    assert "customer_outcome_verified" not in payload

def test_event_by_event_delivery_is_immediately_durable(repository):
    delivery = build_delivery_event()

    receipt = SERVICE.persist_delivery(
        repository=repository,
        delivery_event=delivery,
    )

    artifacts = repository.list_artifacts(
        context=build_context()
    )

    assert len(artifacts) == 1
    assert artifacts[0].artifact_type == DELIVERY_ARTIFACT_TYPE
    assert artifacts[0].payload == delivery.to_dict()

    assert receipt.artifact_type == DELIVERY_ARTIFACT_TYPE
    assert receipt.artifact_id == artifacts[0].artifact_id
    assert receipt.artifact_hash == artifacts[0].artifact_hash
    assert receipt.sequence_number == 1
    assert receipt.chain_hash == artifacts[0].chain_hash
    assert receipt.repository_chain_valid is True

    payload = receipt.to_dict()
    assert payload["boundaries"][
        "persistence_does_not_create_acknowledgment"
    ] is True
    assert payload["boundaries"][
        "persistence_does_not_create_client_response"
    ] is True


def test_event_by_event_acknowledgment_requires_durable_delivery(
    repository,
):
    acknowledgment = build_acknowledgment()

    with pytest.raises(
        PaidAssessmentLifecyclePersistenceError,
        match="before delivery",
    ):
        SERVICE.persist_acknowledgment(
            repository=repository,
            client_acknowledgment=acknowledgment,
        )

    assert repository.list_artifacts(
        context=build_context()
    ) == ()


def test_event_by_event_acknowledgment_becomes_second_artifact(
    repository,
):
    delivery = build_delivery_event()
    acknowledgment = build_acknowledgment(delivery)

    SERVICE.persist_delivery(
        repository=repository,
        delivery_event=delivery,
    )

    receipt = SERVICE.persist_acknowledgment(
        repository=repository,
        client_acknowledgment=acknowledgment,
    )

    artifacts = repository.list_artifacts(
        context=build_context()
    )

    assert [item.artifact_type for item in artifacts] == [
        DELIVERY_ARTIFACT_TYPE,
        ACKNOWLEDGMENT_ARTIFACT_TYPE,
    ]
    assert [item.sequence_number for item in artifacts] == [1, 2]
    assert artifacts[1].payload == acknowledgment.to_dict()
    assert receipt.sequence_number == 2
    assert receipt.repository_chain_valid is True


def test_event_by_event_response_requires_durable_acknowledgment(
    repository,
):
    delivery = build_delivery_event()
    acknowledgment = build_acknowledgment(delivery)
    response = build_response(acknowledgment)

    SERVICE.persist_delivery(
        repository=repository,
        delivery_event=delivery,
    )

    with pytest.raises(
        PaidAssessmentLifecyclePersistenceError,
        match="before receipt acknowledgment",
    ):
        SERVICE.persist_client_response(
            repository=repository,
            client_response=response,
        )

    artifacts = repository.list_artifacts(
        context=build_context()
    )

    assert len(artifacts) == 1
    assert artifacts[0].artifact_type == DELIVERY_ARTIFACT_TYPE


def test_event_by_event_response_becomes_third_artifact(repository):
    delivery = build_delivery_event()
    acknowledgment = build_acknowledgment(delivery)
    response = build_response(acknowledgment)

    SERVICE.persist_delivery(
        repository=repository,
        delivery_event=delivery,
    )
    SERVICE.persist_acknowledgment(
        repository=repository,
        client_acknowledgment=acknowledgment,
    )

    receipt = SERVICE.persist_client_response(
        repository=repository,
        client_response=response,
    )

    artifacts = repository.list_artifacts(
        context=build_context()
    )

    assert [item.artifact_type for item in artifacts] == [
        DELIVERY_ARTIFACT_TYPE,
        ACKNOWLEDGMENT_ARTIFACT_TYPE,
        CLIENT_RESPONSE_ARTIFACT_TYPE,
    ]
    assert [item.sequence_number for item in artifacts] == [1, 2, 3]

    assert artifacts[0].payload == delivery.to_dict()
    assert artifacts[1].payload == acknowledgment.to_dict()
    assert artifacts[2].payload == response.to_dict()

    assert receipt.sequence_number == 3
    assert receipt.repository_chain_valid is True
    assert repository.verify_chain(
        context=build_context()
    ) is True


def test_event_by_event_rejects_duplicate_delivery_before_append(
    repository,
):
    delivery = build_delivery_event()

    SERVICE.persist_delivery(
        repository=repository,
        delivery_event=delivery,
    )

    before = repository.list_artifacts(
        context=build_context()
    )

    with pytest.raises(
        PaidAssessmentLifecyclePersistenceError,
        match="delivery lifecycle artifact already exists",
    ):
        SERVICE.persist_delivery(
            repository=repository,
            delivery_event=delivery,
        )

    after = repository.list_artifacts(
        context=build_context()
    )

    assert after == before


def test_event_by_event_rejects_acknowledgment_lineage_substitution(
    repository,
):
    delivery = build_delivery_event()

    SERVICE.persist_delivery(
        repository=repository,
        delivery_event=delivery,
    )

    acknowledgment = build_acknowledgment(
        delivery,
        report_id="report-substituted",
    )

    with pytest.raises(
        PaidAssessmentLifecyclePersistenceError,
        match="persisted delivery field report_id",
    ):
        SERVICE.persist_acknowledgment(
            repository=repository,
            client_acknowledgment=acknowledgment,
        )

    artifacts = repository.list_artifacts(
        context=build_context()
    )

    assert len(artifacts) == 1
    assert artifacts[0].artifact_type == DELIVERY_ARTIFACT_TYPE


def test_event_by_event_rejects_response_lineage_substitution(
    repository,
):
    delivery = build_delivery_event()
    acknowledgment = build_acknowledgment(delivery)

    SERVICE.persist_delivery(
        repository=repository,
        delivery_event=delivery,
    )
    SERVICE.persist_acknowledgment(
        repository=repository,
        client_acknowledgment=acknowledgment,
    )

    response = build_response(
        acknowledgment,
        acknowledgment_id="ack-substituted",
    )

    with pytest.raises(
        PaidAssessmentLifecyclePersistenceError,
        match="persisted acknowledgment field acknowledgment_id",
    ):
        SERVICE.persist_client_response(
            repository=repository,
            client_response=response,
        )

    artifacts = repository.list_artifacts(
        context=build_context()
    )

    assert len(artifacts) == 2
    assert [
        item.artifact_type for item in artifacts
    ] == [
        DELIVERY_ARTIFACT_TYPE,
        ACKNOWLEDGMENT_ARTIFACT_TYPE,
    ]