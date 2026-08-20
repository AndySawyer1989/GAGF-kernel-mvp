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
from backend.app.gagf.governance_paid_assessment_closeout import (
    CLOSEOUT_BASIS_CLIENT_RESPONSE,
    PAID_ASSESSMENT_CLOSEOUT_ARTIFACT_TYPE,
    PAID_ASSESSMENT_CLOSEOUT_STATUS,
    GovernancePaidAssessmentCloseoutService,
    PaidAssessmentCloseoutError,
    PaidAssessmentCloseoutRequest,
)
from backend.app.gagf.governance_paid_assessment_delivery_event import (
    GovernedPaidAssessmentDeliveryEvent,
)
from backend.app.gagf.governance_paid_assessment_lifecycle_persistence import (
    ACKNOWLEDGMENT_ARTIFACT_TYPE,
    CLIENT_RESPONSE_ARTIFACT_TYPE,
    DELIVERY_ARTIFACT_TYPE,
    GovernancePaidAssessmentLifecyclePersistenceService,
)


HEX_A = "a" * 64
HEX_B = "b" * 64
HEX_C = "c" * 64
HEX_D = "d" * 64
HEX_E = "e" * 64
HEX_F = "f" * 64

FIXED_CLOSEOUT_TIME = datetime(
    2026,
    8,
    18,
    20,
    30,
    tzinfo=timezone.utc,
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


def create_repository(path):
    repository = GovernanceAssessmentRepository(path)

    repository.create_assessment(
        context=build_context(),
        assessment_name="Paid Governance Assessment",
        status="completed",
    )

    return repository


@pytest.fixture
def repository(tmp_path):
    return create_repository(
        tmp_path / "paid-assessment-closeout.sqlite"
    )


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


def build_acknowledgment(
    delivery_event=None,
    **overrides,
):
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


def build_response(
    acknowledgment=None,
    **overrides,
):
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


def establish_completed_lifecycle(repository):
    delivery = build_delivery_event()
    acknowledgment = build_acknowledgment(delivery)
    response = build_response(acknowledgment)

    persistence = (
        GovernancePaidAssessmentLifecyclePersistenceService()
    )

    persistence.persist_lifecycle(
        repository=repository,
        delivery_event=delivery,
        client_acknowledgment=acknowledgment,
        client_response=response,
        created_at=datetime(
            2026,
            8,
            18,
            20,
            5,
            tzinfo=timezone.utc,
        ),
    )

    return delivery, acknowledgment, response


def build_closeout_request(**overrides):
    values = {
        "context": build_context(),
        "report_id": "report-001",
        "closed_by": "FIP Operator",
        "closeout_reason": (
            "Assessment delivery, receipt, and client response recorded."
        ),
        "administrative_closeout_confirmed": True,
    }
    values.update(overrides)

    return PaidAssessmentCloseoutRequest(**values)


def closeout_service(repository):
    return GovernancePaidAssessmentCloseoutService(
        repository=repository
    )


def test_closes_completed_paid_assessment(repository):
    establish_completed_lifecycle(repository)

    result = closeout_service(repository).close_assessment(
        request=build_closeout_request(),
        created_at=FIXED_CLOSEOUT_TIME,
    )

    assert result.closeout_status == PAID_ASSESSMENT_CLOSEOUT_STATUS
    assert result.closeout_status == "assessment_closed"
    assert result.closeout_basis == CLOSEOUT_BASIS_CLIENT_RESPONSE
    assert result.report_id == "report-001"
    assert result.closed_by == "FIP Operator"
    assert result.repository_chain_valid is True

    artifacts = repository.list_artifacts(
        context=build_context()
    )

    assert len(artifacts) == 4
    assert [artifact.artifact_type for artifact in artifacts] == [
        DELIVERY_ARTIFACT_TYPE,
        ACKNOWLEDGMENT_ARTIFACT_TYPE,
        CLIENT_RESPONSE_ARTIFACT_TYPE,
        PAID_ASSESSMENT_CLOSEOUT_ARTIFACT_TYPE,
    ]

    assert [artifact.sequence_number for artifact in artifacts] == [
        1,
        2,
        3,
        4,
    ]


def test_closeout_preserves_client_response_lineage(repository):
    establish_completed_lifecycle(repository)

    response_artifact = repository.list_artifacts(
        context=build_context(),
        artifact_type=CLIENT_RESPONSE_ARTIFACT_TYPE,
    )[0]

    result = closeout_service(repository).close_assessment(
        request=build_closeout_request(),
        created_at=FIXED_CLOSEOUT_TIME,
    )

    assert (
        result.client_response_artifact_id
        == response_artifact.artifact_id
    )
    assert (
        result.client_response_artifact_hash
        == response_artifact.artifact_hash
    )
    assert result.findings_disposition == "acknowledged"
    assert result.recommendations_disposition == "accepted"

    closeout_artifact = repository.list_artifacts(
        context=build_context(),
        artifact_type=PAID_ASSESSMENT_CLOSEOUT_ARTIFACT_TYPE,
    )[0]

    assert (
        closeout_artifact.payload["client_response_artifact_id"]
        == response_artifact.artifact_id
    )
    assert (
        closeout_artifact.payload["client_response_artifact_hash"]
        == response_artifact.artifact_hash
    )


def test_closeout_preserves_hierarchy(repository):
    establish_completed_lifecycle(repository)

    result = closeout_service(repository).close_assessment(
        request=build_closeout_request(),
        created_at=FIXED_CLOSEOUT_TIME,
    )

    assert result.tenant_id == "tenant-alpha"
    assert result.client_id == "client-acme"
    assert result.engagement_id == "engagement-001"
    assert result.assessment_id == "assessment-001"

    assert result.hierarchy_key == (
        "tenant-alpha/"
        "client-acme/"
        "engagement-001/"
        "assessment-001"
    )


def test_closeout_keeps_repository_chain_valid(repository):
    establish_completed_lifecycle(repository)

    result = closeout_service(repository).close_assessment(
        request=build_closeout_request(),
        created_at=FIXED_CLOSEOUT_TIME,
    )

    assert result.sequence_number == 4
    assert result.repository_chain_valid is True
    assert repository.verify_chain(
        context=build_context()
    ) is True


def test_rejects_second_closeout(repository):
    establish_completed_lifecycle(repository)

    service = closeout_service(repository)

    service.close_assessment(
        request=build_closeout_request(),
        created_at=FIXED_CLOSEOUT_TIME,
    )

    with pytest.raises(
        PaidAssessmentCloseoutError,
        match="already has a closeout artifact",
    ):
        service.close_assessment(
            request=build_closeout_request(),
            created_at=datetime(
                2026,
                8,
                18,
                20,
                31,
                tzinfo=timezone.utc,
            ),
        )


def test_rejects_closeout_before_client_response(repository):
    with pytest.raises(
        PaidAssessmentCloseoutError,
        match="current_stage=client_response_recorded",
    ):
        closeout_service(repository).close_assessment(
            request=build_closeout_request(),
            created_at=FIXED_CLOSEOUT_TIME,
        )

    assert repository.list_artifacts(
        context=build_context()
    ) == ()


def test_rejects_report_id_mismatch(repository):
    establish_completed_lifecycle(repository)

    with pytest.raises(
        PaidAssessmentCloseoutError,
        match="report_id does not match",
    ):
        closeout_service(repository).close_assessment(
            request=build_closeout_request(
                report_id="report-other"
            ),
            created_at=FIXED_CLOSEOUT_TIME,
        )


def test_requires_explicit_administrative_confirmation():
    with pytest.raises(
        PaidAssessmentCloseoutError,
        match="administrative_closeout_confirmed must be true",
    ):
        build_closeout_request(
            administrative_closeout_confirmed=False
        )


def test_rejects_naive_closeout_timestamp(repository):
    establish_completed_lifecycle(repository)

    with pytest.raises(
        PaidAssessmentCloseoutError,
        match="created_at must be timezone-aware",
    ):
        closeout_service(repository).close_assessment(
            request=build_closeout_request(),
            created_at=datetime(
                2026,
                8,
                18,
                20,
                30,
            ),
        )


def test_closeout_does_not_mutate_assessment_record(repository):
    establish_completed_lifecycle(repository)

    before = repository.get_assessment(
        context=build_context()
    )

    closeout_service(repository).close_assessment(
        request=build_closeout_request(),
        created_at=FIXED_CLOSEOUT_TIME,
    )

    after = repository.get_assessment(
        context=build_context()
    )

    assert after == before
    assert after.status == "completed"


def test_closeout_does_not_create_downstream_authority(repository):
    establish_completed_lifecycle(repository)

    payload = closeout_service(
        repository
    ).close_assessment(
        request=build_closeout_request(),
        created_at=FIXED_CLOSEOUT_TIME,
    ).to_dict()

    assert payload["closeout_status"] == "assessment_closed"
    assert payload["recommendations_disposition"] == "accepted"

    assert "recommendations_implemented" not in payload
    assert "intervention_requested" not in payload
    assert "intervention_authorized" not in payload
    assert "intervention_executed" not in payload
    assert "causal_success" not in payload
    assert "roi_verified" not in payload
    assert "remediation_success" not in payload
    assert "customer_outcome_verified" not in payload


def test_closeout_serialization_contains_immutable_evidence(repository):
    establish_completed_lifecycle(repository)

    result = closeout_service(repository).close_assessment(
        request=build_closeout_request(),
        created_at=FIXED_CLOSEOUT_TIME,
    )

    payload = result.to_dict()

    assert payload["hierarchy_key"] == (
        "tenant-alpha/client-acme/engagement-001/assessment-001"
    )
    assert payload["report_id"] == "report-001"
    assert payload["closeout_status"] == "assessment_closed"
    assert payload["closeout_basis"] == "client_response_recorded"
    assert payload["repository_chain_valid"] is True

    assert payload["client_response_artifact_id"]
    assert payload["client_response_artifact_hash"]
    assert payload["artifact_id"]
    assert payload["artifact_hash"]
    assert payload["chain_hash"]
    assert payload["closeout_id"]
    assert payload["closeout_hash"]


def test_closeout_hash_is_deterministic_for_fixed_inputs(tmp_path):
    repository_a = create_repository(
        tmp_path / "closeout-a.sqlite"
    )
    repository_b = create_repository(
        tmp_path / "closeout-b.sqlite"
    )

    establish_completed_lifecycle(repository_a)
    establish_completed_lifecycle(repository_b)

    result_a = closeout_service(
        repository_a
    ).close_assessment(
        request=build_closeout_request(),
        created_at=FIXED_CLOSEOUT_TIME,
    )

    result_b = closeout_service(
        repository_b
    ).close_assessment(
        request=build_closeout_request(),
        created_at=FIXED_CLOSEOUT_TIME,
    )

    assert result_a.closeout_id == result_b.closeout_id
    assert result_a.closeout_hash == result_b.closeout_hash


def test_repository_tampering_fails_closed(repository):
    establish_completed_lifecycle(repository)

    response_artifact = repository.list_artifacts(
        context=build_context(),
        artifact_type=CLIENT_RESPONSE_ARTIFACT_TYPE,
    )[0]

    with repository._connect() as connection:
        connection.execute(
            "UPDATE governance_assessment_artifacts "
            "SET chain_hash = ? WHERE artifact_id = ?",
            ("0" * 64, response_artifact.artifact_id),
        )

    with pytest.raises(Exception, match="chain"):
        closeout_service(repository).close_assessment(
            request=build_closeout_request(),
            created_at=FIXED_CLOSEOUT_TIME,
        )

    closeouts = repository.list_artifacts(
        context=build_context(),
        artifact_type=PAID_ASSESSMENT_CLOSEOUT_ARTIFACT_TYPE,
    )

    assert closeouts == ()