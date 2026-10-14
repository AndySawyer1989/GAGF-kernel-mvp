from __future__ import annotations

import copy

import pytest

from backend.app.gagf.governance_paid_assessment_execution_handoff import (
    PaidAssessmentWorkAuthorization,
)
from backend.app.gagf.governance_paid_work_authorization_record import (
    GOVERNANCE_PAID_WORK_AUTHORIZATION_RECORD_SCHEMA_VERSION,
    GOVERNANCE_PAID_WORK_AUTHORIZATION_RECORD_TYPE,
    GOVERNANCE_PAID_WORK_AUTHORIZATION_RECORD_VERSION,
    GovernancePaidWorkAuthorizationRecordError,
    GovernancePaidWorkAuthorizationRecordIntegrityError,
    build_paid_work_authorization_record,
    paid_work_authorization_record_from_dict,
    verify_paid_work_authorization_record,
)


def build_authorization() -> PaidAssessmentWorkAuthorization:
    return PaidAssessmentWorkAuthorization(
        authorization_id="pa-001-auth-001",
        tenant_id="tenant-001",
        client_id="client-001",
        engagement_id="engagement-001",
        assessment_id="assessment-001",
        contract_execution_event_id="contract-event-001",
        authorized_by="operator-001",
        authorized_at="2026-10-13T19:00:00+00:00",
        paid_assessment_authorized=True,
    )


def test_build_record_binds_existing_pa001_without_creating_new_authority():
    authorization = build_authorization()

    record = build_paid_work_authorization_record(
        authorization=authorization
    )

    assert record.authorization_id == authorization.authorization_id
    assert record.authorization_hash == authorization.authorization_hash

    assert record.record_type == (
        GOVERNANCE_PAID_WORK_AUTHORIZATION_RECORD_TYPE
    )
    assert record.version == (
        GOVERNANCE_PAID_WORK_AUTHORIZATION_RECORD_VERSION
    )
    assert record.schema_version == (
        GOVERNANCE_PAID_WORK_AUTHORIZATION_RECORD_SCHEMA_VERSION
    )

    assert record.hierarchy_key == (
        "tenant-001/client-001/engagement-001/assessment-001"
    )

    assert record.paid_assessment_authorized is True

    boundaries = record.to_dict()["boundaries"]

    assert boundaries["recording_does_not_create_authority"] is True
    assert (
        boundaries["record_integrity_is_not_actor_authentication"]
        is True
    )
    assert (
        boundaries["paid_work_authorization_is_not_trial_authorization"]
        is True
    )
    assert (
        boundaries["paid_work_authorization_is_not_execution"]
        is True
    )
    assert (
        boundaries["paid_work_authorization_is_not_delivery"]
        is True
    )
    assert (
        boundaries[
            "paid_work_authorization_is_not_intervention_authority"
        ]
        is True
    )


def test_record_round_trip_reconstructs_same_pa001():
    authorization = build_authorization()

    record = build_paid_work_authorization_record(
        authorization=authorization
    )

    reconstructed_record = (
        paid_work_authorization_record_from_dict(
            record.to_dict()
        )
    )

    reconstructed_authorization = (
        verify_paid_work_authorization_record(
            reconstructed_record
        )
    )

    assert (
        reconstructed_authorization.to_dict()
        == authorization.to_dict()
    )
    assert (
        reconstructed_authorization.authorization_hash
        == authorization.authorization_hash
    )


def test_record_hash_is_deterministic():
    authorization = build_authorization()

    first = build_paid_work_authorization_record(
        authorization=authorization
    )
    second = build_paid_work_authorization_record(
        authorization=authorization
    )

    assert first.record_hash == second.record_hash
    assert first.to_dict() == second.to_dict()


def test_record_rejects_non_pa001_input():
    with pytest.raises(
        GovernancePaidWorkAuthorizationRecordError,
        match=(
            "authorization must be a "
            "PaidAssessmentWorkAuthorization"
        ),
    ):
        build_paid_work_authorization_record(
            authorization=object()
        )


def test_record_rejects_tampered_authorized_by():
    authorization = build_authorization()

    record = build_paid_work_authorization_record(
        authorization=authorization
    )

    payload = copy.deepcopy(
        record.to_dict()
    )
    payload["authorized_by"] = "tampered-operator"

    with pytest.raises(
        GovernancePaidWorkAuthorizationRecordIntegrityError,
        match="record hash mismatch",
    ):
        paid_work_authorization_record_from_dict(
            payload
        )


def test_record_rejects_tampered_contract_event():
    authorization = build_authorization()

    record = build_paid_work_authorization_record(
        authorization=authorization
    )

    payload = copy.deepcopy(
        record.to_dict()
    )
    payload["contract_execution_event_id"] = "other-contract"

    with pytest.raises(
        GovernancePaidWorkAuthorizationRecordIntegrityError,
        match="record hash mismatch",
    ):
        paid_work_authorization_record_from_dict(
            payload
        )


def test_record_rejects_tampered_hierarchy_key():
    authorization = build_authorization()

    record = build_paid_work_authorization_record(
        authorization=authorization
    )

    payload = copy.deepcopy(
        record.to_dict()
    )
    payload["hierarchy_key"] = (
        "tenant-999/client-001/engagement-001/assessment-001"
    )

    with pytest.raises(
        GovernancePaidWorkAuthorizationRecordIntegrityError,
        match="hierarchy mismatch",
    ):
        paid_work_authorization_record_from_dict(
            payload
        )


def test_record_rejects_boundary_tampering():
    authorization = build_authorization()

    record = build_paid_work_authorization_record(
        authorization=authorization
    )

    payload = copy.deepcopy(
        record.to_dict()
    )
    payload["boundaries"][
        "recording_does_not_create_authority"
    ] = False

    with pytest.raises(
        GovernancePaidWorkAuthorizationRecordIntegrityError,
        match="boundaries mismatch",
    ):
        paid_work_authorization_record_from_dict(
            payload
        )


def test_record_rejects_authorization_hash_tampering():
    authorization = build_authorization()

    record = build_paid_work_authorization_record(
        authorization=authorization
    )

    payload = copy.deepcopy(
        record.to_dict()
    )
    payload["authorization_hash"] = "a" * 64

    with pytest.raises(
        GovernancePaidWorkAuthorizationRecordIntegrityError,
    ):
        paid_work_authorization_record_from_dict(
            payload
        )


def test_record_rejects_record_hash_tampering():
    authorization = build_authorization()

    record = build_paid_work_authorization_record(
        authorization=authorization
    )

    payload = copy.deepcopy(
        record.to_dict()
    )
    payload["record_hash"] = "b" * 64

    with pytest.raises(
        GovernancePaidWorkAuthorizationRecordIntegrityError,
        match="record hash mismatch",
    ):
        paid_work_authorization_record_from_dict(
            payload
        )


def test_record_rejects_missing_required_field():
    authorization = build_authorization()

    record = build_paid_work_authorization_record(
        authorization=authorization
    )

    payload = copy.deepcopy(
        record.to_dict()
    )
    del payload["authorized_at"]

    with pytest.raises(
        GovernancePaidWorkAuthorizationRecordError,
        match="missing paid-work authorization record field",
    ):
        paid_work_authorization_record_from_dict(
            payload
        )