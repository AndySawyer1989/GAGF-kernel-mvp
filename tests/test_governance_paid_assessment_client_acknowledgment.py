from dataclasses import FrozenInstanceError

import pytest

from backend.app.gagf.governance_paid_assessment_client_acknowledgment import (
    ClientAssessmentReceiptAcknowledgment,
    GovernancePaidAssessmentClientAcknowledgmentService,
    PaidAssessmentClientAcknowledgmentError,
)
from backend.app.gagf.governance_paid_assessment_delivery_event import (
    GovernedPaidAssessmentDeliveryEvent,
    canonical_json,
    sha256_text,
)


SERVICE = GovernancePaidAssessmentClientAcknowledgmentService()

HEX_A = "a" * 64
HEX_B = "b" * 64
HEX_C = "c" * 64


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
    }
    values.update(overrides)

    payload = {
        "event_type": "governance-paid-assessment-delivery-event",
        "version": "0.1.0",
        "schema_version": "1.0.0",
        **values,
    }

    return GovernedPaidAssessmentDeliveryEvent(
        **values,
        delivery_event_hash=sha256_text(
            canonical_json(payload)
        ),
    )


def build_acknowledgment(
    delivery_event=None,
    **overrides,
):
    delivery_event = delivery_event or build_delivery_event()

    values = {
        "acknowledgment_id": "client-ack-001",
        "tenant_id": delivery_event.tenant_id,
        "client_id": delivery_event.client_id,
        "engagement_id": delivery_event.engagement_id,
        "assessment_id": delivery_event.assessment_id,
        "report_id": delivery_event.report_id,
        "delivery_event_id": delivery_event.delivery_event_id,
        "delivery_event_hash": delivery_event.delivery_event_hash,
        "acknowledged_by": "ACME Client Representative",
        "acknowledged_at": "2026-08-18T19:30:00+00:00",
        "acknowledgment_method": "email_reply",
        "acknowledgment_reference": "mail-reply-001",
        "client_acknowledged_receipt": True,
    }
    values.update(overrides)

    return ClientAssessmentReceiptAcknowledgment(**values)


def test_records_client_receipt_acknowledgment():
    delivery_event = build_delivery_event()
    acknowledgment = build_acknowledgment(delivery_event)

    result = SERVICE.record_acknowledgment(
        delivery_event=delivery_event,
        acknowledgment=acknowledgment,
    )

    assert (
        result.acknowledgment_status
        == "client_receipt_acknowledged"
    )
    assert result.hierarchy_key == (
        "tenant-alpha/client-acme/engagement-001/assessment-001"
    )
    assert result.report_id == delivery_event.report_id
    assert (
        result.delivery_event_id
        == delivery_event.delivery_event_id
    )
    assert (
        result.delivery_event_hash
        == delivery_event.delivery_event_hash
    )
    assert (
        result.acknowledgment_evidence_hash
        == acknowledgment.acknowledgment_evidence_hash
    )


def test_requires_delivered_event():
    delivery_event = build_delivery_event(
        delivery_status="pending"
    )

    with pytest.raises(
        PaidAssessmentClientAcknowledgmentError,
        match="delivery_status=delivered",
    ):
        SERVICE.record_acknowledgment(
            delivery_event=delivery_event,
            acknowledgment=build_acknowledgment(
                delivery_event
            ),
        )


def test_rejects_tampered_delivery_event_hash():
    delivery_event = build_delivery_event()

    tampered = GovernedPaidAssessmentDeliveryEvent(
        tenant_id=delivery_event.tenant_id,
        client_id=delivery_event.client_id,
        engagement_id=delivery_event.engagement_id,
        assessment_id=delivery_event.assessment_id,
        report_id=delivery_event.report_id,
        delivery_envelope_hash=(
            delivery_event.delivery_envelope_hash
        ),
        delivery_approval_hash=(
            delivery_event.delivery_approval_hash
        ),
        human_delivery_confirmation_hash=(
            delivery_event.human_delivery_confirmation_hash
        ),
        delivery_event_id=delivery_event.delivery_event_id,
        delivered_by=delivery_event.delivered_by,
        delivered_at=delivery_event.delivered_at,
        delivery_method=delivery_event.delivery_method,
        delivery_reference="tampered-reference",
        delivery_status=delivery_event.delivery_status,
        delivery_event_hash=delivery_event.delivery_event_hash,
    )

    with pytest.raises(
        PaidAssessmentClientAcknowledgmentError,
        match="hash verification",
    ):
        SERVICE.record_acknowledgment(
            delivery_event=tampered,
            acknowledgment=build_acknowledgment(tampered),
        )


def test_receipt_acknowledgment_must_be_explicit():
    delivery_event = build_delivery_event()

    with pytest.raises(
        PaidAssessmentClientAcknowledgmentError,
        match="client_acknowledged_receipt must be true",
    ):
        build_acknowledgment(
            delivery_event,
            client_acknowledged_receipt=False,
        )


@pytest.mark.parametrize(
    ("field_name", "value"),
    (
        ("tenant_id", "tenant-other"),
        ("client_id", "client-other"),
        ("engagement_id", "engagement-other"),
        ("assessment_id", "assessment-other"),
        ("report_id", "report-other"),
        ("delivery_event_id", "delivery-event-other"),
        ("delivery_event_hash", "f" * 64),
    ),
)
def test_rejects_cross_lineage_acknowledgment(
    field_name,
    value,
):
    delivery_event = build_delivery_event()
    acknowledgment = build_acknowledgment(
        delivery_event,
        **{field_name: value},
    )

    with pytest.raises(
        PaidAssessmentClientAcknowledgmentError,
        match="lineage does not match",
    ):
        SERVICE.record_acknowledgment(
            delivery_event=delivery_event,
            acknowledgment=acknowledgment,
        )


def test_rejects_acknowledgment_before_delivery():
    delivery_event = build_delivery_event()

    acknowledgment = build_acknowledgment(
        delivery_event,
        acknowledged_at="2026-08-18T19:14:59+00:00",
    )

    with pytest.raises(
        PaidAssessmentClientAcknowledgmentError,
        match="must not occur before delivered_at",
    ):
        SERVICE.record_acknowledgment(
            delivery_event=delivery_event,
            acknowledgment=acknowledgment,
        )


def test_acknowledgment_hash_is_deterministic():
    delivery_event = build_delivery_event()

    first = SERVICE.record_acknowledgment(
        delivery_event=delivery_event,
        acknowledgment=build_acknowledgment(delivery_event),
    )

    second = SERVICE.record_acknowledgment(
        delivery_event=delivery_event,
        acknowledgment=build_acknowledgment(delivery_event),
    )

    assert first.acknowledgment_hash == second.acknowledgment_hash


def test_acknowledgment_hash_changes_with_reference():
    delivery_event = build_delivery_event()

    first = SERVICE.record_acknowledgment(
        delivery_event=delivery_event,
        acknowledgment=build_acknowledgment(delivery_event),
    )

    second = SERVICE.record_acknowledgment(
        delivery_event=delivery_event,
        acknowledgment=build_acknowledgment(
            delivery_event,
            acknowledgment_reference="mail-reply-002",
        ),
    )

    assert first.acknowledgment_hash != second.acknowledgment_hash


def test_acknowledgment_artifact_is_immutable():
    delivery_event = build_delivery_event()

    result = SERVICE.record_acknowledgment(
        delivery_event=delivery_event,
        acknowledgment=build_acknowledgment(delivery_event),
    )

    with pytest.raises(FrozenInstanceError):
        result.acknowledgment_status = "changed"


def test_acknowledgment_evidence_is_immutable():
    delivery_event = build_delivery_event()
    acknowledgment = build_acknowledgment(delivery_event)

    with pytest.raises(FrozenInstanceError):
        acknowledgment.client_acknowledged_receipt = False


def test_serialization_does_not_overclaim_acceptance_or_outcome():
    delivery_event = build_delivery_event()

    result = SERVICE.record_acknowledgment(
        delivery_event=delivery_event,
        acknowledgment=build_acknowledgment(delivery_event),
    )

    serialized = result.to_dict()

    assert (
        serialized["acknowledgment_status"]
        == "client_receipt_acknowledged"
    )

    assert "findings_accepted" not in serialized
    assert "recommendations_accepted" not in serialized
    assert "client_satisfied" not in serialized
    assert "intervention_authorized" not in serialized
    assert "causal_success" not in serialized
    assert "roi_verified" not in serialized
    assert "remediation_success" not in serialized
    assert "customer_outcome_verified" not in serialized


def test_acknowledged_at_requires_timezone():
    delivery_event = build_delivery_event()

    with pytest.raises(
        PaidAssessmentClientAcknowledgmentError,
        match="must include a timezone",
    ):
        build_acknowledgment(
            delivery_event,
            acknowledged_at="2026-08-18T19:30:00",
        )


def test_empty_acknowledgment_reference_is_rejected():
    delivery_event = build_delivery_event()

    with pytest.raises(
        PaidAssessmentClientAcknowledgmentError,
        match="acknowledgment_reference must not be empty",
    ):
        build_acknowledgment(
            delivery_event,
            acknowledgment_reference=" ",
        )