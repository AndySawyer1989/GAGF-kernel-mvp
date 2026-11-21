from __future__ import annotations

from datetime import datetime, timezone

import pytest

from backend.app.gagf.governance_assessment_auth import (
    AssessmentActorContext,
)
from backend.app.gagf.governance_paid_work_authorization_issuance_service import (
    GovernancePaidWorkAuthorizationIssuanceService,
)
from backend.app.gagf.governance_paid_work_authorization_record_store import (
    GovernancePaidWorkAuthorizationRecordStore,
)
from backend.app.gagf.governance_paid_work_prerequisite_record import (
    AUTHORIZATION_PACKAGE_KIND,
    CONTRACT_EXECUTION_EVENT_KIND,
    PAYMENT_CONFIRMATION_EVENT_KIND,
    build_paid_work_prerequisite_record,
)
from backend.app.gagf.governance_paid_work_prerequisite_record_store import (
    GovernancePaidWorkPrerequisiteRecordStore,
    GovernancePaidWorkPrerequisiteRecordStoreIntegrityError,
    GovernancePaidWorkPrerequisiteRecordStoreNotFoundError,
)
from backend.app.gagf.governance_paid_work_prerequisite_resolver import (
    GovernancePaidWorkPrerequisiteResolver,
)


HIERARCHY = {
    "tenant_id": "tenant-alpha",
    "client_id": "client-acme",
    "engagement_id": "engagement-001",
    "assessment_id": "assessment-001",
}


def actor() -> AssessmentActorContext:
    return AssessmentActorContext(
        tenant_id="tenant-alpha",
        actor_id="operator-admin-001",
        roles=("assessment:admin",),
    )


def authorization_package() -> dict:
    return {
        "status": "ok",
        "event_type": (
            "assessment_factory_lite_paid_assessment_authorization_package"
        ),
        "package_status": "ready_for_paid_assessment_authorization",
        "authorization_id": "package-001",
        "prepared_at": "2026-10-14T18:00:00+00:00",
        "package_blockers": [],
        "human_authorization": {
            "human_operator_authorized_package": True,
            "paid_assessment_authorized": False,
        },
        "commercial_boundary": {
            "authorization_package_ready": True,
            "paid_assessment_authorized": False,
            "requires_separate_contract": True,
            "requires_separate_invoice": True,
            "requires_separate_payment_confirmation": True,
        },
        "governance_boundary": {
            "gagf_kernel_authoritative": True,
            "human_boundary_required": True,
            "ai_override_allowed": False,
            "authorization_is_package_readiness_only": True,
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
        "event_blockers": [],
        "execution_evidence": {
            "contract_executed": True,
        },
        "commercial_boundary": {
            "contract_executed": True,
            "paid_assessment_authorized": False,
            "requires_final_paid_work_authorization": True,
        },
        "governance_boundary": {
            "gagf_kernel_authoritative": True,
            "human_boundary_required": True,
            "ai_override_allowed": False,
            "contract_execution_event_is_not_paid_work_authorization": True,
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
        "event_blockers": [],
        "payment_confirmation_record": {
            "payment_confirmed": True,
        },
        "reconciliation_record": {
            "reconciliation_recorded": True,
        },
        "operator_confirmation": {
            "human_operator_confirmed_payment": True,
            "paid_assessment_authorized": False,
        },
        "commercial_boundary": {
            "payment_confirmed": True,
            "paid_assessment_authorized": False,
            "requires_final_paid_work_authorization": True,
        },
        "governance_boundary": {
            "gagf_kernel_authoritative": True,
            "human_boundary_required": True,
            "ai_override_allowed": False,
            "payment_confirmation_event_is_not_paid_work_authorization": True,
        },
    }


def build_resolver(tmp_path):
    prerequisite_store = GovernancePaidWorkPrerequisiteRecordStore(
        database_path=(
            tmp_path
            / "paid-work-prerequisites.sqlite3"
        )
    )

    authorization_store = GovernancePaidWorkAuthorizationRecordStore(
        database_path=(
            tmp_path
            / "paid-work-authorizations.sqlite3"
        )
    )

    issuance_service = GovernancePaidWorkAuthorizationIssuanceService(
        record_store=authorization_store,
        clock=lambda: datetime(
            2026,
            10,
            14,
            19,
            0,
            0,
            tzinfo=timezone.utc,
        ),
    )

    resolver = GovernancePaidWorkPrerequisiteResolver(
        prerequisite_store=prerequisite_store,
        issuance_service=issuance_service,
    )

    return (
        resolver,
        prerequisite_store,
        authorization_store,
    )


def seed_prerequisites(store):
    artifacts = (
        (
            AUTHORIZATION_PACKAGE_KIND,
            authorization_package(),
        ),
        (
            CONTRACT_EXECUTION_EVENT_KIND,
            contract_event(),
        ),
        (
            PAYMENT_CONFIRMATION_EVENT_KIND,
            payment_event(),
        ),
    )

    for kind, artifact in artifacts:
        record = build_paid_work_prerequisite_record(
            prerequisite_kind=kind,
            artifact=artifact,
            **HIERARCHY,
        )
        store.save(
            record=record
        )


def test_resolve_returns_exact_server_records(tmp_path):
    resolver, prerequisite_store, _ = build_resolver(
        tmp_path
    )
    seed_prerequisites(
        prerequisite_store
    )

    resolution = resolver.resolve(
        authorization_package_id="package-001",
        contract_execution_event_id="contract-event-001",
        payment_confirmation_event_id="payment-event-001",
        **HIERARCHY,
    )

    assert (
        resolution.authorization_package.artifact_id
        == "package-001"
    )
    assert (
        resolution.contract_execution_event.artifact_id
        == "contract-event-001"
    )
    assert (
        resolution.payment_confirmation_event.artifact_id
        == "payment-event-001"
    )


def test_issue_from_ids_creates_pa001_from_resolved_artifacts(tmp_path):
    resolver, prerequisite_store, authorization_store = (
        build_resolver(
            tmp_path
        )
    )
    seed_prerequisites(
        prerequisite_store
    )

    result = resolver.issue_from_ids(
        authorization_package_id="package-001",
        contract_execution_event_id="contract-event-001",
        payment_confirmation_event_id="payment-event-001",
        actor=actor(),
        **HIERARCHY,
    )

    assert result.issuance.authorization.authorization_id.startswith(
        "pa-001-"
    )
    assert (
        result.issuance.authorization.authorized_by
        == "operator-admin-001"
    )
    assert (
        result.issuance.authorization.contract_execution_event_id
        == "contract-event-001"
    )

    stored = authorization_store.get(
        authorization_id=(
            result.issuance.authorization.authorization_id
        )
    )

    assert stored.record_hash == result.issuance.record.record_hash


def test_missing_authorization_package_is_blocked(tmp_path):
    resolver, prerequisite_store, _ = build_resolver(
        tmp_path
    )
    seed_prerequisites(
        prerequisite_store
    )

    with pytest.raises(
        GovernancePaidWorkPrerequisiteRecordStoreNotFoundError,
        match="not found",
    ):
        resolver.resolve(
            authorization_package_id="missing-package",
            contract_execution_event_id="contract-event-001",
            payment_confirmation_event_id="payment-event-001",
            **HIERARCHY,
        )


def test_missing_contract_event_is_blocked(tmp_path):
    resolver, prerequisite_store, _ = build_resolver(
        tmp_path
    )
    seed_prerequisites(
        prerequisite_store
    )

    with pytest.raises(
        GovernancePaidWorkPrerequisiteRecordStoreNotFoundError,
        match="not found",
    ):
        resolver.resolve(
            authorization_package_id="package-001",
            contract_execution_event_id="missing-contract",
            payment_confirmation_event_id="payment-event-001",
            **HIERARCHY,
        )


def test_missing_payment_event_is_blocked(tmp_path):
    resolver, prerequisite_store, _ = build_resolver(
        tmp_path
    )
    seed_prerequisites(
        prerequisite_store
    )

    with pytest.raises(
        GovernancePaidWorkPrerequisiteRecordStoreNotFoundError,
        match="not found",
    ):
        resolver.resolve(
            authorization_package_id="package-001",
            contract_execution_event_id="contract-event-001",
            payment_confirmation_event_id="missing-payment",
            **HIERARCHY,
        )


def test_cross_assessment_resolution_is_blocked(tmp_path):
    resolver, prerequisite_store, _ = build_resolver(
        tmp_path
    )
    seed_prerequisites(
        prerequisite_store
    )

    wrong = dict(HIERARCHY)
    wrong["assessment_id"] = "assessment-other"

    with pytest.raises(
        GovernancePaidWorkPrerequisiteRecordStoreIntegrityError,
        match="hierarchy",
    ):
        resolver.resolve(
            authorization_package_id="package-001",
            contract_execution_event_id="contract-event-001",
            payment_confirmation_event_id="payment-event-001",
            **wrong,
        )


def test_cross_tenant_resolution_is_blocked(tmp_path):
    resolver, prerequisite_store, _ = build_resolver(
        tmp_path
    )
    seed_prerequisites(
        prerequisite_store
    )

    wrong = dict(HIERARCHY)
    wrong["tenant_id"] = "tenant-other"

    with pytest.raises(
        GovernancePaidWorkPrerequisiteRecordStoreIntegrityError,
        match="hierarchy",
    ):
        resolver.resolve(
            authorization_package_id="package-001",
            contract_execution_event_id="contract-event-001",
            payment_confirmation_event_id="payment-event-001",
            **wrong,
        )


def test_issue_from_ids_is_idempotent(tmp_path):
    resolver, prerequisite_store, _ = build_resolver(
        tmp_path
    )
    seed_prerequisites(
        prerequisite_store
    )

    first = resolver.issue_from_ids(
        authorization_package_id="package-001",
        contract_execution_event_id="contract-event-001",
        payment_confirmation_event_id="payment-event-001",
        actor=actor(),
        **HIERARCHY,
    )

    second = resolver.issue_from_ids(
        authorization_package_id="package-001",
        contract_execution_event_id="contract-event-001",
        payment_confirmation_event_id="payment-event-001",
        actor=actor(),
        **HIERARCHY,
    )

    assert (
        first.issuance.authorization.authorization_id
        == second.issuance.authorization.authorization_id
    )
    assert (
        first.issuance.record.record_hash
        == second.issuance.record.record_hash
    )


def test_resolution_preserves_server_artifact_hashes(tmp_path):
    resolver, prerequisite_store, _ = build_resolver(
        tmp_path
    )
    seed_prerequisites(
        prerequisite_store
    )

    result = resolver.issue_from_ids(
        authorization_package_id="package-001",
        contract_execution_event_id="contract-event-001",
        payment_confirmation_event_id="payment-event-001",
        actor=actor(),
        **HIERARCHY,
    )

    assert (
        result.issuance.authorization_package_hash
        == result.resolution.authorization_package.artifact_hash
    )
    assert (
        result.issuance.contract_execution_event_hash
        == result.resolution.contract_execution_event.artifact_hash
    )
    assert (
        result.issuance.payment_confirmation_event_hash
        == result.resolution.payment_confirmation_event.artifact_hash
    )


def test_result_boundaries_identify_server_resolution(tmp_path):
    resolver, prerequisite_store, _ = build_resolver(
        tmp_path
    )
    seed_prerequisites(
        prerequisite_store
    )

    result = resolver.issue_from_ids(
        authorization_package_id="package-001",
        contract_execution_event_id="contract-event-001",
        payment_confirmation_event_id="payment-event-001",
        actor=actor(),
        **HIERARCHY,
    )

    boundaries = result.to_dict()["boundaries"]

    assert boundaries["prerequisites_resolved_server_side"] is True
    assert boundaries["browser_artifact_payloads_not_used"] is True
    assert boundaries["issuance_service_remains_authority_boundary"] is True
    assert boundaries["resolver_does_not_create_prerequisite_records"] is True
    assert boundaries["resolver_does_not_bypass_admin_issuance"] is True


def test_resolver_does_not_expose_prerequisite_creation_methods(
    tmp_path,
):
    resolver, _, _ = build_resolver(
        tmp_path
    )

    assert not hasattr(
        resolver,
        "save"
    )
    assert not hasattr(
        resolver,
        "record"
    )
    assert not hasattr(
        resolver,
        "create_prerequisite"
    )
