from __future__ import annotations

from copy import deepcopy

import pytest

from backend.app.gagf.governance_paid_work_prerequisite_record import (
    AUTHORIZATION_PACKAGE_KIND,
    CONTRACT_EXECUTION_EVENT_KIND,
    PAYMENT_CONFIRMATION_EVENT_KIND,
    GovernancePaidWorkPrerequisiteRecordError,
    build_paid_work_prerequisite_record,
    paid_work_prerequisite_record_from_dict,
)


HIERARCHY = {
    "tenant_id": "tenant-alpha",
    "client_id": "client-acme",
    "engagement_id": "engagement-001",
    "assessment_id": "assessment-001",
}


def authorization_package() -> dict:
    return {
        "status": "ok",
        "event_type": (
            "assessment_factory_lite_paid_assessment_authorization_package"
        ),
        "package_status": "ready_for_paid_assessment_authorization",
        "authorization_id": "package-001",
        "prepared_at": "2026-10-14T18:00:00+00:00",
        "human_authorization": {
            "human_operator_authorized_package": True,
            "paid_assessment_authorized": False,
        },
        "commercial_boundary": {
            "authorization_package_ready": True,
            "paid_assessment_authorized": False,
        },
    }


def contract_event() -> dict:
    return {
        "status": "ok",
        "event_type": (
            "assessment_factory_lite_contract_execution_event"
        ),
        "event_status": "contract_executed",
        "contract_execution_event_id": "contract-event-001",
        "recorded_at": "2026-10-14T18:10:00+00:00",
        "execution_evidence": {
            "contract_executed": True,
        },
        "commercial_boundary": {
            "contract_executed": True,
            "paid_assessment_authorized": False,
        },
    }


def payment_event() -> dict:
    return {
        "status": "ok",
        "event_type": (
            "assessment_factory_lite_payment_confirmation_event"
        ),
        "event_status": "payment_confirmed",
        "payment_confirmation_event_id": "payment-event-001",
        "recorded_at": "2026-10-14T18:20:00+00:00",
        "payment_confirmation_record": {
            "payment_confirmed": True,
        },
        "commercial_boundary": {
            "payment_confirmed": True,
            "paid_assessment_authorized": False,
        },
    }


@pytest.mark.parametrize(
    ("kind", "factory", "expected_id", "expected_status"),
    [
        (
            AUTHORIZATION_PACKAGE_KIND,
            authorization_package,
            "package-001",
            "ready_for_paid_assessment_authorization",
        ),
        (
            CONTRACT_EXECUTION_EVENT_KIND,
            contract_event,
            "contract-event-001",
            "contract_executed",
        ),
        (
            PAYMENT_CONFIRMATION_EVENT_KIND,
            payment_event,
            "payment-event-001",
            "payment_confirmed",
        ),
    ],
)
def test_builds_hierarchy_bound_immutable_prerequisite_record(
    kind,
    factory,
    expected_id,
    expected_status,
):
    record = build_paid_work_prerequisite_record(
        prerequisite_kind=kind,
        artifact=factory(),
        **HIERARCHY,
    )

    assert record.prerequisite_kind == kind
    assert record.artifact_id == expected_id
    assert record.source_status == expected_status
    assert (
        record.hierarchy_key
        == "tenant-alpha/client-acme/engagement-001/assessment-001"
    )
    assert len(record.artifact_hash) == 64
    assert len(record.record_hash) == 64

    record.verify()


def test_record_preserves_exact_canonical_artifact():
    source = authorization_package()

    record = build_paid_work_prerequisite_record(
        prerequisite_kind=AUTHORIZATION_PACKAGE_KIND,
        artifact=source,
        **HIERARCHY,
    )

    assert record.artifact == source

    source["authorization_id"] = "mutated-browser-copy"

    assert record.artifact["authorization_id"] == "package-001"


def test_record_round_trip_reverifies_integrity():
    record = build_paid_work_prerequisite_record(
        prerequisite_kind=CONTRACT_EXECUTION_EVENT_KIND,
        artifact=contract_event(),
        **HIERARCHY,
    )

    reconstructed = (
        paid_work_prerequisite_record_from_dict(
            record.to_dict()
        )
    )

    assert reconstructed == record
    reconstructed.verify()


def test_record_hash_binds_hierarchy():
    first = build_paid_work_prerequisite_record(
        prerequisite_kind=PAYMENT_CONFIRMATION_EVENT_KIND,
        artifact=payment_event(),
        **HIERARCHY,
    )

    other_hierarchy = dict(HIERARCHY)
    other_hierarchy["assessment_id"] = "assessment-002"

    second = build_paid_work_prerequisite_record(
        prerequisite_kind=PAYMENT_CONFIRMATION_EVENT_KIND,
        artifact=payment_event(),
        **other_hierarchy,
    )

    assert first.artifact_hash == second.artifact_hash
    assert first.record_hash != second.record_hash


def test_rejects_wrong_event_type_for_kind():
    source = contract_event()
    source["event_type"] = (
        "assessment_factory_lite_payment_confirmation_event"
    )

    with pytest.raises(
        GovernancePaidWorkPrerequisiteRecordError,
        match="event_type",
    ):
        build_paid_work_prerequisite_record(
            prerequisite_kind=CONTRACT_EXECUTION_EVENT_KIND,
            artifact=source,
            **HIERARCHY,
        )


@pytest.mark.parametrize(
    ("kind", "factory", "status_field", "bad_status"),
    [
        (
            AUTHORIZATION_PACKAGE_KIND,
            authorization_package,
            "package_status",
            "pending_authorization_review",
        ),
        (
            CONTRACT_EXECUTION_EVENT_KIND,
            contract_event,
            "event_status",
            "pending_contract_execution_confirmation",
        ),
        (
            PAYMENT_CONFIRMATION_EVENT_KIND,
            payment_event,
            "event_status",
            "pending_payment_confirmation",
        ),
    ],
)
def test_rejects_nonterminal_prerequisite(
    kind,
    factory,
    status_field,
    bad_status,
):
    source = factory()
    source[status_field] = bad_status

    with pytest.raises(
        GovernancePaidWorkPrerequisiteRecordError,
        match="required terminal status",
    ):
        build_paid_work_prerequisite_record(
            prerequisite_kind=kind,
            artifact=source,
            **HIERARCHY,
        )


def test_rejects_missing_recorded_timestamp():
    source = payment_event()
    source["recorded_at"] = "not_recorded"

    with pytest.raises(
        GovernancePaidWorkPrerequisiteRecordError,
        match="timestamp",
    ):
        build_paid_work_prerequisite_record(
            prerequisite_kind=PAYMENT_CONFIRMATION_EVENT_KIND,
            artifact=source,
            **HIERARCHY,
        )


def test_tampered_artifact_is_rejected_on_reconstruction():
    record = build_paid_work_prerequisite_record(
        prerequisite_kind=AUTHORIZATION_PACKAGE_KIND,
        artifact=authorization_package(),
        **HIERARCHY,
    )

    payload = deepcopy(
        record.to_dict()
    )
    payload["artifact"]["authorization_id"] = "tampered"

    with pytest.raises(
        GovernancePaidWorkPrerequisiteRecordError,
        match="canonical_artifact_json",
    ):
        paid_work_prerequisite_record_from_dict(
            payload
        )


def test_tampered_record_hash_is_rejected():
    record = build_paid_work_prerequisite_record(
        prerequisite_kind=CONTRACT_EXECUTION_EVENT_KIND,
        artifact=contract_event(),
        **HIERARCHY,
    )

    payload = record.to_dict()
    payload["record_hash"] = "0" * 64

    with pytest.raises(
        GovernancePaidWorkPrerequisiteRecordError,
        match="record_hash",
    ):
        paid_work_prerequisite_record_from_dict(
            payload
        )


def test_record_boundaries_do_not_create_authority():
    record = build_paid_work_prerequisite_record(
        prerequisite_kind=PAYMENT_CONFIRMATION_EVENT_KIND,
        artifact=payment_event(),
        **HIERARCHY,
    )

    boundaries = record.to_dict()["boundaries"]

    assert (
        boundaries[
            "recording_does_not_create_paid_work_authority"
        ]
        is True
    )
    assert (
        boundaries[
            "package_readiness_is_not_paid_work_authority"
        ]
        is True
    )
    assert (
        boundaries[
            "contract_execution_is_not_paid_work_authority"
        ]
        is True
    )
    assert (
        boundaries[
            "payment_confirmation_is_not_paid_work_authority"
        ]
        is True
    )
    assert (
        boundaries[
            "record_integrity_is_not_actor_authentication"
        ]
        is True
    )
    assert (
        boundaries[
            "record_integrity_is_not_intervention_authority"
        ]
        is True
    )
