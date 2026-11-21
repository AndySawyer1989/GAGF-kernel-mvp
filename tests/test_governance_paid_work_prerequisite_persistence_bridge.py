from __future__ import annotations

from backend.app.gagf.governance_paid_work_prerequisite_persistence_bridge import (
    GovernancePaidWorkPrerequisitePersistenceBridge,
)
from backend.app.gagf.governance_paid_work_prerequisite_record import (
    AUTHORIZATION_PACKAGE_KIND,
    CONTRACT_EXECUTION_EVENT_KIND,
    PAYMENT_CONFIRMATION_EVENT_KIND,
)
from backend.app.gagf.governance_paid_work_prerequisite_record_store import (
    GovernancePaidWorkPrerequisiteRecordStore,
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
        "authorization_id": "authorization-package-001",
        "prepared_at": "2026-10-14T20:00:00+00:00",
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
        "event_type": "assessment_factory_lite_contract_execution_event",
        "event_status": "contract_executed",
        "contract_execution_event_id": "contract-event-001",
        "recorded_at": "2026-10-14T20:10:00+00:00",
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
        "event_type": "assessment_factory_lite_payment_confirmation_event",
        "event_status": "payment_confirmed",
        "payment_confirmation_event_id": "payment-event-001",
        "recorded_at": "2026-10-14T20:20:00+00:00",
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


def build_bridge(tmp_path):
    store = GovernancePaidWorkPrerequisiteRecordStore(
        database_path=tmp_path / "paid-work-prerequisites.sqlite3"
    )
    return (
        GovernancePaidWorkPrerequisitePersistenceBridge(
            prerequisite_store=store
        ),
        store,
    )


def test_records_authorization_package(tmp_path):
    bridge, store = build_bridge(tmp_path)

    result = bridge.record_authorization_package(
        artifact=authorization_package(),
        **HIERARCHY,
    )

    assert result.prerequisite_kind == AUTHORIZATION_PACKAGE_KIND
    stored = store.get(
        prerequisite_kind=AUTHORIZATION_PACKAGE_KIND,
        artifact_id="authorization-package-001",
    )
    assert stored.record_hash == result.record.record_hash
    assert stored.tenant_id == HIERARCHY["tenant_id"]


def test_records_contract_execution_event(tmp_path):
    bridge, store = build_bridge(tmp_path)

    result = bridge.record_contract_execution_event(
        artifact=contract_event(),
        **HIERARCHY,
    )

    assert result.prerequisite_kind == CONTRACT_EXECUTION_EVENT_KIND
    stored = store.get(
        prerequisite_kind=CONTRACT_EXECUTION_EVENT_KIND,
        artifact_id="contract-event-001",
    )
    assert stored.record_hash == result.record.record_hash


def test_records_payment_confirmation_event(tmp_path):
    bridge, store = build_bridge(tmp_path)

    result = bridge.record_payment_confirmation_event(
        artifact=payment_event(),
        **HIERARCHY,
    )

    assert result.prerequisite_kind == PAYMENT_CONFIRMATION_EVENT_KIND
    stored = store.get(
        prerequisite_kind=PAYMENT_CONFIRMATION_EVENT_KIND,
        artifact_id="payment-event-001",
    )
    assert stored.record_hash == result.record.record_hash


def test_recording_is_idempotent(tmp_path):
    bridge, _ = build_bridge(tmp_path)

    first = bridge.record_contract_execution_event(
        artifact=contract_event(),
        **HIERARCHY,
    )
    second = bridge.record_contract_execution_event(
        artifact=contract_event(),
        **HIERARCHY,
    )

    assert first.record.record_hash == second.record.record_hash


def test_bridge_requires_explicit_hierarchy_binding(tmp_path):
    bridge, _ = build_bridge(tmp_path)

    result = bridge.record_payment_confirmation_event(
        tenant_id="tenant-alpha",
        client_id="client-acme",
        engagement_id="engagement-001",
        assessment_id="assessment-001",
        artifact=payment_event(),
    )

    assert result.record.hierarchy_key == (
        "tenant-alpha/client-acme/engagement-001/assessment-001"
    )


def test_bridge_preserves_exact_artifact(tmp_path):
    bridge, _ = build_bridge(tmp_path)
    artifact = authorization_package()

    result = bridge.record_authorization_package(
        artifact=artifact,
        **HIERARCHY,
    )

    assert result.record.artifact == artifact


def test_bridge_boundaries_do_not_create_authority(tmp_path):
    bridge, _ = build_bridge(tmp_path)

    result = bridge.record_payment_confirmation_event(
        artifact=payment_event(),
        **HIERARCHY,
    )

    boundaries = result.to_dict()["boundaries"]

    assert boundaries["artifact_persisted_as_prerequisite_evidence"] is True
    assert boundaries["persistence_does_not_create_paid_work_authority"] is True
    assert boundaries["prerequisite_record_is_not_pa001"] is True
    assert boundaries["authorization_package_readiness_is_not_pa001"] is True
    assert boundaries["contract_execution_is_not_pa001"] is True
    assert boundaries["payment_confirmation_is_not_pa001"] is True
    assert boundaries["persistence_does_not_authenticate_actor"] is True
    assert boundaries["persistence_does_not_authorize_execution"] is True
    assert boundaries["persistence_does_not_approve_delivery"] is True
    assert boundaries["persistence_does_not_grant_intervention_authority"] is True


def test_bridge_exposes_no_pa001_issuance_methods(tmp_path):
    bridge, _ = build_bridge(tmp_path)

    assert not hasattr(bridge, "issue")
    assert not hasattr(bridge, "authorize")
    assert not hasattr(bridge, "execute")
    assert not hasattr(bridge, "approve_delivery")
