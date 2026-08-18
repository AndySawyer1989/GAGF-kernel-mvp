from dataclasses import FrozenInstanceError

import pytest

from backend.app.gagf.governance_paid_assessment_delivery_envelope import (
    GovernedPaidAssessmentDeliveryEnvelope,
)
from backend.app.gagf.governance_paid_assessment_delivery_event import (
    GovernancePaidAssessmentDeliveryEventService,
    HumanAssessmentDeliveryConfirmation,
    PaidAssessmentDeliveryEventError,
)


SERVICE = GovernancePaidAssessmentDeliveryEventService()

HEX_A = "a" * 64
HEX_B = "b" * 64
HEX_C = "c" * 64
HEX_D = "d" * 64
HEX_E = "e" * 64


def build_envelope(**overrides):
    values = {
        "tenant_id": "tenant-alpha",
        "client_id": "client-acme",
        "engagement_id": "engagement-001",
        "assessment_id": "assessment-001",
        "report_id": "report-001",
        "execution_result_hash": HEX_A,
        "application_hash": HEX_B,
        "report_package_hash": HEX_C,
        "report_markdown_hash": HEX_D,
        "delivery_approval_id": "delivery-approval-001",
        "delivery_approval_hash": HEX_E,
        "delivery_status": "approved_for_human_delivery",
        "envelope_hash": HEX_A,
    }
    values.update(overrides)
    return GovernedPaidAssessmentDeliveryEnvelope(**values)


def build_confirmation(**overrides):
    values = {
        "delivery_event_id": "delivery-event-001",
        "tenant_id": "tenant-alpha",
        "client_id": "client-acme",
        "engagement_id": "engagement-001",
        "assessment_id": "assessment-001",
        "report_id": "report-001",
        "delivered_by": "Andy Sawyer",
        "delivered_at": "2026-08-18T19:15:00+00:00",
        "delivery_method": "email",
        "delivery_reference": "mail-message-001",
        "delivery_completed": True,
    }
    values.update(overrides)
    return HumanAssessmentDeliveryConfirmation(**values)


def test_records_completed_human_delivery_event():
    envelope = build_envelope()
    confirmation = build_confirmation()

    result = SERVICE.record_delivery(
        delivery_envelope=envelope,
        human_confirmation=confirmation,
    )

    assert result.delivery_status == "delivered"
    assert result.hierarchy_key == (
        "tenant-alpha/client-acme/engagement-001/assessment-001"
    )
    assert result.report_id == envelope.report_id
    assert result.delivery_envelope_hash == envelope.envelope_hash
    assert (
        result.delivery_approval_hash
        == envelope.delivery_approval_hash
    )
    assert (
        result.human_delivery_confirmation_hash
        == confirmation.confirmation_hash
    )
    assert result.delivery_event_id == "delivery-event-001"
    assert result.delivered_by == "Andy Sawyer"
    assert result.delivered_at == "2026-08-18T19:15:00+00:00"
    assert result.delivery_method == "email"
    assert result.delivery_reference == "mail-message-001"


def test_rejects_envelope_not_approved_for_human_delivery():
    envelope = build_envelope(
        delivery_status="review_ready"
    )

    with pytest.raises(
        PaidAssessmentDeliveryEventError,
        match="approved_for_human_delivery",
    ):
        SERVICE.record_delivery(
            delivery_envelope=envelope,
            human_confirmation=build_confirmation(),
        )


def test_confirmation_requires_completed_delivery():
    with pytest.raises(
        PaidAssessmentDeliveryEventError,
        match="delivery_completed must be true",
    ):
        build_confirmation(delivery_completed=False)


@pytest.mark.parametrize(
    ("field_name", "value"),
    (
        ("tenant_id", "tenant-other"),
        ("client_id", "client-other"),
        ("engagement_id", "engagement-other"),
        ("assessment_id", "assessment-other"),
        ("report_id", "report-other"),
    ),
)
def test_rejects_cross_identity_confirmation(
    field_name,
    value,
):
    confirmation = build_confirmation(
        **{field_name: value}
    )

    with pytest.raises(
        PaidAssessmentDeliveryEventError,
        match="identity does not match",
    ):
        SERVICE.record_delivery(
            delivery_envelope=build_envelope(),
            human_confirmation=confirmation,
        )


def test_confirmation_hash_is_deterministic():
    first = build_confirmation()
    second = build_confirmation()

    assert first.confirmation_hash == second.confirmation_hash


def test_delivery_event_hash_is_deterministic():
    first = SERVICE.record_delivery(
        delivery_envelope=build_envelope(),
        human_confirmation=build_confirmation(),
    )
    second = SERVICE.record_delivery(
        delivery_envelope=build_envelope(),
        human_confirmation=build_confirmation(),
    )

    assert first.delivery_event_hash == second.delivery_event_hash


def test_delivery_event_hash_changes_with_delivery_reference():
    first = SERVICE.record_delivery(
        delivery_envelope=build_envelope(),
        human_confirmation=build_confirmation(),
    )
    second = SERVICE.record_delivery(
        delivery_envelope=build_envelope(),
        human_confirmation=build_confirmation(
            delivery_reference="mail-message-002"
        ),
    )

    assert first.delivery_event_hash != second.delivery_event_hash


def test_delivery_event_is_immutable():
    result = SERVICE.record_delivery(
        delivery_envelope=build_envelope(),
        human_confirmation=build_confirmation(),
    )

    with pytest.raises(FrozenInstanceError):
        result.delivery_status = "changed"


def test_delivery_confirmation_is_immutable():
    confirmation = build_confirmation()

    with pytest.raises(FrozenInstanceError):
        confirmation.delivery_completed = False


def test_serialization_does_not_overclaim_downstream_state():
    result = SERVICE.record_delivery(
        delivery_envelope=build_envelope(),
        human_confirmation=build_confirmation(),
    )

    serialized = result.to_dict()

    assert serialized["delivery_status"] == "delivered"
    assert "client_received" not in serialized
    assert "client_acknowledged" not in serialized
    assert "client_accepted" not in serialized
    assert "recommendations_accepted" not in serialized
    assert "intervention_authorized" not in serialized
    assert "customer_outcome_verified" not in serialized
    assert "causal_success" not in serialized
    assert "roi_verified" not in serialized


def test_invalid_delivered_at_is_rejected():
    with pytest.raises(
        PaidAssessmentDeliveryEventError,
        match="ISO-8601",
    ):
        build_confirmation(
            delivered_at="not-a-date"
        )


def test_empty_delivery_reference_is_rejected():
    with pytest.raises(
        PaidAssessmentDeliveryEventError,
        match="delivery_reference must not be empty",
    ):
        build_confirmation(
            delivery_reference=" "
        )