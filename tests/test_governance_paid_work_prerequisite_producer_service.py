from __future__ import annotations

from datetime import datetime, timezone

import pytest

from backend.app.gagf.governance_assessment_auth import AssessmentActorContext
from backend.app.gagf.governance_paid_work_prerequisite_persistence_bridge import GovernancePaidWorkPrerequisitePersistenceBridge
from backend.app.gagf.governance_paid_work_prerequisite_producer_service import (
    GovernancePaidWorkPrerequisiteProducerError,
    GovernancePaidWorkPrerequisiteProducerService,
)
from backend.app.gagf.governance_paid_work_prerequisite_record import (
    AUTHORIZATION_PACKAGE_KIND,
    CONTRACT_EXECUTION_EVENT_KIND,
    PAYMENT_CONFIRMATION_EVENT_KIND,
)
from backend.app.gagf.governance_paid_work_prerequisite_record_store import GovernancePaidWorkPrerequisiteRecordStore

HIERARCHY = {
    "tenant_id": "tenant-alpha",
    "client_id": "client-acme",
    "engagement_id": "engagement-001",
    "assessment_id": "assessment-001",
}
FIXED_TIME = datetime(2026, 10, 14, 23, 45, 0, tzinfo=timezone.utc)


def actor(tenant_id: str = "tenant-alpha") -> AssessmentActorContext:
    return AssessmentActorContext(
        tenant_id=tenant_id,
        actor_id="operator-admin-001",
        roles=("assessment:admin",),
    )


class StubAuthorizationPackageService:
    def __init__(self): self.calls = []
    def build_package(self, **kwargs):
        self.calls.append(kwargs)
        c = kwargs["authorization_context"]
        return {
            "status": "ok",
            "event_type": "assessment_factory_lite_paid_assessment_authorization_package",
            "package_status": "ready_for_paid_assessment_authorization",
            "authorization_id": c["authorization_id"],
            "prepared_at": c["prepared_at"],
            "package_blockers": [],
            "human_authorization": {"human_operator_authorized_package": True, "paid_assessment_authorized": False},
            "commercial_boundary": {"authorization_package_ready": True, "paid_assessment_authorized": False},
            "governance_boundary": {"authorization_is_package_readiness_only": True, "gagf_kernel_authoritative": True, "human_boundary_required": True, "ai_override_allowed": False},
        }


class StubContractExecutionEventService:
    def __init__(self): self.calls = []
    def record_event(self, **kwargs):
        self.calls.append(kwargs)
        c = kwargs["contract_execution_context"]
        return {
            "status": "ok",
            "event_type": "assessment_factory_lite_contract_execution_event",
            "event_status": "contract_executed",
            "contract_execution_event_id": c["contract_execution_event_id"],
            "recorded_at": c["recorded_at"],
            "event_blockers": [],
            "execution_evidence": {"contract_executed": True},
            "commercial_boundary": {"contract_executed": True, "paid_assessment_authorized": False},
            "governance_boundary": {"contract_execution_event_is_not_paid_work_authorization": True, "gagf_kernel_authoritative": True, "human_boundary_required": True, "ai_override_allowed": False},
        }


class StubPaymentConfirmationEventService:
    def __init__(self): self.calls = []
    def record_event(self, **kwargs):
        self.calls.append(kwargs)
        c = kwargs["payment_confirmation_event_context"]
        return {
            "status": "ok",
            "event_type": "assessment_factory_lite_payment_confirmation_event",
            "event_status": "payment_confirmed",
            "payment_confirmation_event_id": c["payment_confirmation_event_id"],
            "recorded_at": c["recorded_at"],
            "event_blockers": [],
            "payment_confirmation_record": {"payment_confirmed": True},
            "reconciliation_record": {"reconciliation_recorded": True},
            "operator_confirmation": {"human_operator_confirmed_payment": True, "paid_assessment_authorized": False},
            "commercial_boundary": {"payment_confirmed": True, "paid_assessment_authorized": False},
            "governance_boundary": {"payment_confirmation_event_is_not_paid_work_authorization": True, "gagf_kernel_authoritative": True, "human_boundary_required": True, "ai_override_allowed": False},
        }


def build_service(tmp_path):
    store = GovernancePaidWorkPrerequisiteRecordStore(database_path=tmp_path / "paid-work-prerequisites.sqlite3")
    bridge = GovernancePaidWorkPrerequisitePersistenceBridge(prerequisite_store=store)
    a = StubAuthorizationPackageService(); c = StubContractExecutionEventService(); p = StubPaymentConfirmationEventService()
    ids = iter([f"instance-{i:03d}" for i in range(1, 50)])
    producer = GovernancePaidWorkPrerequisiteProducerService(
        persistence_bridge=bridge, authorization_package_service=a,
        contract_execution_event_service=c, payment_confirmation_event_service=p,
        clock=lambda: FIXED_TIME, instance_id_factory=lambda: next(ids),
    )
    return producer, store, a, c, p


def test_authorization_package_binds_server_identity_time_and_actor(tmp_path):
    producer, store, a, _, _ = build_service(tmp_path)
    result = producer.produce_authorization_package(
        source={"authorization_context": {"authorization_id": "browser-id", "prepared_at": "1900", "pricing_reviewed": True}},
        actor=actor(), **HIERARCHY,
    )
    call = a.calls[0]["authorization_context"]
    assert call["authorization_id"] != "browser-id"
    assert call["prepared_at"] == FIXED_TIME.isoformat()
    provenance = result.record.artifact["governance_provenance"]
    assert provenance["producer_actor_id"] == "operator-admin-001"
    assert provenance["producer_tenant_id"] == "tenant-alpha"
    assert provenance["evidence_instance_id"] == "instance-001"
    assert provenance["actor_context_bound"] is True
    assert store.get(prerequisite_kind=AUTHORIZATION_PACKAGE_KIND, artifact_id=result.record.artifact_id).record_hash == result.record.record_hash


def test_contract_event_gets_new_append_only_instance(tmp_path):
    producer, _, _, _, _ = build_service(tmp_path)
    first = producer.produce_contract_execution_event(source={}, actor=actor(), **HIERARCHY)
    second = producer.produce_contract_execution_event(source={}, actor=actor(), **HIERARCHY)
    assert first.record.artifact_id != second.record.artifact_id
    assert first.record.artifact["governance_provenance"]["evidence_instance_id"] != second.record.artifact["governance_provenance"]["evidence_instance_id"]
    assert first.created is True and second.created is True


def test_payment_event_is_hierarchy_bound(tmp_path):
    producer, _, _, _, _ = build_service(tmp_path)
    result = producer.produce_payment_confirmation_event(source={}, actor=actor(), **HIERARCHY)
    assert result.record.hierarchy_key == "tenant-alpha/client-acme/engagement-001/assessment-001"
    assert result.record.artifact_id.startswith("payment-confirmation-event-")


def test_actor_tenant_must_match_prerequisite_tenant(tmp_path):
    producer, _, _, _, _ = build_service(tmp_path)
    with pytest.raises(GovernancePaidWorkPrerequisiteProducerError, match="actor tenant"):
        producer.produce_authorization_package(source={}, actor=actor("tenant-other"), **HIERARCHY)


def test_trusted_business_evidence_is_forwarded_but_identity_is_server_owned(tmp_path):
    producer, _, a, _, _ = build_service(tmp_path)
    producer.produce_authorization_package(
        source={
            "operator_approval": {"paid_assessment_authorization_approved": True},
            "authorization_context": {"authorization_id": "untrusted-id", "prepared_at": "untrusted-time", "pricing_reviewed": True},
        },
        actor=actor(), **HIERARCHY,
    )
    call = a.calls[0]
    assert call["operator_approval"]["paid_assessment_authorization_approved"] is True
    assert call["authorization_context"]["pricing_reviewed"] is True
    assert call["authorization_context"]["authorization_id"] != "untrusted-id"
    assert call["authorization_context"]["prepared_at"] != "untrusted-time"


def test_production_boundaries_capture_actor_and_instance_rules(tmp_path):
    producer, _, _, _, _ = build_service(tmp_path)
    result = producer.produce_contract_execution_event(source={}, actor=actor(), **HIERARCHY)
    boundaries = result.to_dict()["boundaries"]
    assert boundaries["producer_actor_context_is_bound"] is True
    assert boundaries["evidence_instances_are_append_only"] is True
    assert boundaries["production_requires_pre_authenticated_actor_context"] is True
    assert boundaries["production_is_not_paid_work_authority"] is True


def test_producer_exposes_no_pa001_authority_methods(tmp_path):
    producer, _, _, _, _ = build_service(tmp_path)
    assert not hasattr(producer, "issue")
    assert not hasattr(producer, "authorize")
    assert not hasattr(producer, "execute")
