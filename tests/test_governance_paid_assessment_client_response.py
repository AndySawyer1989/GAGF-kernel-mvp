from dataclasses import FrozenInstanceError

import pytest

from backend.app.gagf.governance_paid_assessment_client_acknowledgment import (
    GovernedPaidAssessmentClientAcknowledgment,
    canonical_json as acknowledgment_canonical_json,
    sha256_text as acknowledgment_sha256_text,
)
from backend.app.gagf.governance_paid_assessment_client_response import (
    ClientAssessmentResponse,
    GovernancePaidAssessmentClientResponseService,
    PaidAssessmentClientResponseError,
)


SERVICE = GovernancePaidAssessmentClientResponseService()

HEX_A = "a" * 64
HEX_B = "b" * 64
HEX_C = "c" * 64


def build_client_acknowledgment(**overrides):
    values = {
        "tenant_id": "tenant-alpha",
        "client_id": "client-acme",
        "engagement_id": "engagement-001",
        "assessment_id": "assessment-001",
        "report_id": "report-001",
        "delivery_event_id": "delivery-event-001",
        "delivery_event_hash": HEX_A,
        "acknowledgment_id": "client-ack-001",
        "acknowledgment_evidence_hash": HEX_B,
        "acknowledged_by": "ACME Client Representative",
        "acknowledged_at": "2026-08-18T19:30:00+00:00",
        "acknowledgment_method": "email_reply",
        "acknowledgment_reference": "mail-reply-001",
        "acknowledgment_status": "client_receipt_acknowledged",
    }
    values.update(overrides)

    payload = {
        "acknowledgment_type": (
            "governance-paid-assessment-client-acknowledgment"
        ),
        "version": "0.1.0",
        "schema_version": "1.0.0",
        **values,
    }

    return GovernedPaidAssessmentClientAcknowledgment(
        **values,
        acknowledgment_hash=acknowledgment_sha256_text(
            acknowledgment_canonical_json(payload)
        ),
    )


def build_response(
    acknowledgment=None,
    **overrides,
):
    acknowledgment = (
        acknowledgment
        or build_client_acknowledgment()
    )

    values = {
        "response_id": "client-response-001",
        "tenant_id": acknowledgment.tenant_id,
        "client_id": acknowledgment.client_id,
        "engagement_id": acknowledgment.engagement_id,
        "assessment_id": acknowledgment.assessment_id,
        "report_id": acknowledgment.report_id,
        "acknowledgment_id": acknowledgment.acknowledgment_id,
        "acknowledgment_hash": acknowledgment.acknowledgment_hash,
        "responded_by": "ACME Client Representative",
        "responded_at": "2026-08-18T20:00:00+00:00",
        "response_method": "email_reply",
        "response_reference": "assessment-response-001",
        "findings_disposition": "acknowledged",
        "recommendations_disposition": "under_review",
        "response_note": "Client is reviewing recommendations.",
    }
    values.update(overrides)

    return ClientAssessmentResponse(**values)


def test_records_client_assessment_response():
    acknowledgment = build_client_acknowledgment()
    response = build_response(acknowledgment)

    result = SERVICE.record_response(
        client_acknowledgment=acknowledgment,
        response=response,
    )

    assert result.response_status == "client_response_recorded"
    assert result.hierarchy_key == (
        "tenant-alpha/client-acme/engagement-001/assessment-001"
    )
    assert result.report_id == acknowledgment.report_id
    assert (
        result.acknowledgment_id
        == acknowledgment.acknowledgment_id
    )
    assert (
        result.acknowledgment_hash
        == acknowledgment.acknowledgment_hash
    )
    assert result.findings_disposition == "acknowledged"
    assert (
        result.recommendations_disposition
        == "under_review"
    )
    assert (
        result.response_evidence_hash
        == response.response_evidence_hash
    )


@pytest.mark.parametrize(
    "disposition",
    (
        "acknowledged",
        "under_review",
        "disputed",
    ),
)
def test_accepts_allowed_findings_dispositions(
    disposition,
):
    acknowledgment = build_client_acknowledgment()

    response = build_response(
        acknowledgment,
        findings_disposition=disposition,
    )

    result = SERVICE.record_response(
        client_acknowledgment=acknowledgment,
        response=response,
    )

    assert result.findings_disposition == disposition


@pytest.mark.parametrize(
    "disposition",
    (
        "under_review",
        "accepted",
        "partially_accepted",
        "declined",
    ),
)
def test_accepts_allowed_recommendation_dispositions(
    disposition,
):
    acknowledgment = build_client_acknowledgment()

    response = build_response(
        acknowledgment,
        recommendations_disposition=disposition,
    )

    result = SERVICE.record_response(
        client_acknowledgment=acknowledgment,
        response=response,
    )

    assert result.recommendations_disposition == disposition


def test_rejects_invalid_findings_disposition():
    acknowledgment = build_client_acknowledgment()

    with pytest.raises(
        PaidAssessmentClientResponseError,
        match="findings_disposition must be one of",
    ):
        build_response(
            acknowledgment,
            findings_disposition="accepted",
        )


def test_rejects_invalid_recommendation_disposition():
    acknowledgment = build_client_acknowledgment()

    with pytest.raises(
        PaidAssessmentClientResponseError,
        match="recommendations_disposition must be one of",
    ):
        build_response(
            acknowledgment,
            recommendations_disposition="implemented",
        )


def test_requires_client_receipt_acknowledgment():
    acknowledgment = build_client_acknowledgment(
        acknowledgment_status="pending"
    )

    with pytest.raises(
        PaidAssessmentClientResponseError,
        match="client_receipt_acknowledged",
    ):
        SERVICE.record_response(
            client_acknowledgment=acknowledgment,
            response=build_response(acknowledgment),
        )


def test_rejects_tampered_acknowledgment():
    original = build_client_acknowledgment()

    tampered = GovernedPaidAssessmentClientAcknowledgment(
        tenant_id=original.tenant_id,
        client_id=original.client_id,
        engagement_id=original.engagement_id,
        assessment_id=original.assessment_id,
        report_id=original.report_id,
        delivery_event_id=original.delivery_event_id,
        delivery_event_hash=original.delivery_event_hash,
        acknowledgment_id=original.acknowledgment_id,
        acknowledgment_evidence_hash=(
            original.acknowledgment_evidence_hash
        ),
        acknowledged_by=original.acknowledged_by,
        acknowledged_at=original.acknowledged_at,
        acknowledgment_method=original.acknowledgment_method,
        acknowledgment_reference="tampered-reference",
        acknowledgment_status=original.acknowledgment_status,
        acknowledgment_hash=original.acknowledgment_hash,
    )

    with pytest.raises(
        PaidAssessmentClientResponseError,
        match="hash verification",
    ):
        SERVICE.record_response(
            client_acknowledgment=tampered,
            response=build_response(tampered),
        )


@pytest.mark.parametrize(
    ("field_name", "value"),
    (
        ("tenant_id", "tenant-other"),
        ("client_id", "client-other"),
        ("engagement_id", "engagement-other"),
        ("assessment_id", "assessment-other"),
        ("report_id", "report-other"),
        ("acknowledgment_id", "ack-other"),
        ("acknowledgment_hash", "f" * 64),
    ),
)
def test_rejects_cross_lineage_response(
    field_name,
    value,
):
    acknowledgment = build_client_acknowledgment()

    response = build_response(
        acknowledgment,
        **{field_name: value},
    )

    with pytest.raises(
        PaidAssessmentClientResponseError,
        match="lineage does not match",
    ):
        SERVICE.record_response(
            client_acknowledgment=acknowledgment,
            response=response,
        )


def test_rejects_response_before_acknowledgment():
    acknowledgment = build_client_acknowledgment()

    response = build_response(
        acknowledgment,
        responded_at="2026-08-18T19:29:59+00:00",
    )

    with pytest.raises(
        PaidAssessmentClientResponseError,
        match="must not occur before acknowledged_at",
    ):
        SERVICE.record_response(
            client_acknowledgment=acknowledgment,
            response=response,
        )


def test_response_hash_is_deterministic():
    acknowledgment = build_client_acknowledgment()

    first = SERVICE.record_response(
        client_acknowledgment=acknowledgment,
        response=build_response(acknowledgment),
    )

    second = SERVICE.record_response(
        client_acknowledgment=acknowledgment,
        response=build_response(acknowledgment),
    )

    assert first.response_hash == second.response_hash


def test_response_hash_changes_with_disposition():
    acknowledgment = build_client_acknowledgment()

    first = SERVICE.record_response(
        client_acknowledgment=acknowledgment,
        response=build_response(
            acknowledgment,
            recommendations_disposition="under_review",
        ),
    )

    second = SERVICE.record_response(
        client_acknowledgment=acknowledgment,
        response=build_response(
            acknowledgment,
            recommendations_disposition="accepted",
        ),
    )

    assert first.response_hash != second.response_hash


def test_response_hash_changes_with_note():
    acknowledgment = build_client_acknowledgment()

    first = SERVICE.record_response(
        client_acknowledgment=acknowledgment,
        response=build_response(
            acknowledgment,
            response_note="Reviewing.",
        ),
    )

    second = SERVICE.record_response(
        client_acknowledgment=acknowledgment,
        response=build_response(
            acknowledgment,
            response_note="Accepted for planning.",
        ),
    )

    assert first.response_hash != second.response_hash


def test_response_artifact_is_immutable():
    acknowledgment = build_client_acknowledgment()

    result = SERVICE.record_response(
        client_acknowledgment=acknowledgment,
        response=build_response(acknowledgment),
    )

    with pytest.raises(FrozenInstanceError):
        result.response_status = "changed"


def test_response_evidence_is_immutable():
    acknowledgment = build_client_acknowledgment()
    response = build_response(acknowledgment)

    with pytest.raises(FrozenInstanceError):
        response.findings_disposition = "disputed"


def test_response_note_may_be_empty():
    acknowledgment = build_client_acknowledgment()

    response = build_response(
        acknowledgment,
        response_note="",
    )

    result = SERVICE.record_response(
        client_acknowledgment=acknowledgment,
        response=response,
    )

    assert result.response_note == ""


def test_accepted_recommendations_do_not_authorize_intervention():
    acknowledgment = build_client_acknowledgment()

    result = SERVICE.record_response(
        client_acknowledgment=acknowledgment,
        response=build_response(
            acknowledgment,
            recommendations_disposition="accepted",
        ),
    )

    serialized = result.to_dict()

    assert serialized["recommendations_disposition"] == "accepted"
    assert "intervention_requested" not in serialized
    assert "intervention_authorized" not in serialized
    assert "intervention_executed" not in serialized
    assert "causal_success" not in serialized
    assert "roi_verified" not in serialized
    assert "remediation_success" not in serialized
    assert "customer_outcome_verified" not in serialized


def test_findings_acknowledged_does_not_mean_findings_validated():
    acknowledgment = build_client_acknowledgment()

    result = SERVICE.record_response(
        client_acknowledgment=acknowledgment,
        response=build_response(
            acknowledgment,
            findings_disposition="acknowledged",
        ),
    )

    serialized = result.to_dict()

    assert serialized["findings_disposition"] == "acknowledged"
    assert "findings_validated" not in serialized
    assert "findings_proven" not in serialized
    assert "causal_success" not in serialized


def test_responded_at_requires_timezone():
    acknowledgment = build_client_acknowledgment()

    with pytest.raises(
        PaidAssessmentClientResponseError,
        match="must include a timezone",
    ):
        build_response(
            acknowledgment,
            responded_at="2026-08-18T20:00:00",
        )


def test_empty_response_reference_is_rejected():
    acknowledgment = build_client_acknowledgment()

    with pytest.raises(
        PaidAssessmentClientResponseError,
        match="response_reference must not be empty",
    ):
        build_response(
            acknowledgment,
            response_reference=" ",
        )