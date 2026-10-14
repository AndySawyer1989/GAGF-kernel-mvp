from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone

import pytest

from backend.app.gagf.governance_assessment_auth import (
    ASSESSMENT_ADMIN_ROLE,
    ASSESSMENT_EXECUTOR_ROLE,
    AssessmentActorContext,
)
from backend.app.gagf.governance_paid_work_authorization_issuance_service import (
    GovernancePaidWorkAuthorizationIssuanceError,
    GovernancePaidWorkAuthorizationIssuanceService,
)
from backend.app.gagf.governance_paid_work_authorization_record_store import (
    GovernancePaidWorkAuthorizationRecordStore,
)


TENANT_ID = "tenant-alpha"
CLIENT_ID = "client-alpha"
ENGAGEMENT_ID = "engagement-001"
ASSESSMENT_ID = "assessment-001"

AUTHORIZED_AT = datetime(
    2026,
    10,
    14,
    17,
    0,
    0,
    tzinfo=timezone.utc,
)


def build_actor(
    *,
    tenant_id: str = TENANT_ID,
    actor_id: str = "operator-admin-001",
    roles: tuple[str, ...] = (
        ASSESSMENT_ADMIN_ROLE,
    ),
) -> AssessmentActorContext:
    return AssessmentActorContext(
        tenant_id=tenant_id,
        actor_id=actor_id,
        roles=roles,
    )


def build_authorization_package():
    return {
        "status": "ok",
        "event_type": (
            "assessment_factory_lite_paid_assessment_authorization_package"
        ),
        "package_status": "ready_for_paid_assessment_authorization",
        "authorization_id": "authorization-package-001",
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


def build_contract_execution_event():
    return {
        "status": "ok",
        "event_type": (
            "assessment_factory_lite_contract_execution_event"
        ),
        "event_status": "contract_executed",
        "contract_execution_event_id": "contract-event-001",
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


def build_payment_confirmation_event():
    return {
        "status": "ok",
        "event_type": (
            "assessment_factory_lite_payment_confirmation_event"
        ),
        "event_status": "payment_confirmed",
        "payment_confirmation_event_id": "payment-confirmation-001",
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


def build_service(tmp_path):
    store = GovernancePaidWorkAuthorizationRecordStore(
        database_path=(
            tmp_path
            / "paid-work-authorizations.sqlite3"
        )
    )

    service = GovernancePaidWorkAuthorizationIssuanceService(
        record_store=store,
        clock=lambda: AUTHORIZED_AT,
    )

    return service, store


def issue_ready(service, **overrides):
    values = {
        "tenant_id": TENANT_ID,
        "client_id": CLIENT_ID,
        "engagement_id": ENGAGEMENT_ID,
        "assessment_id": ASSESSMENT_ID,
        "authorization_package": build_authorization_package(),
        "contract_execution_event": build_contract_execution_event(),
        "payment_confirmation_event": build_payment_confirmation_event(),
        "actor": build_actor(),
    }
    values.update(overrides)

    return service.issue(**values)


def test_admin_issues_and_persists_pa001(tmp_path):
    service, store = build_service(tmp_path)

    result = issue_ready(service)

    authorization = result.authorization
    record = result.record

    assert authorization.authorization_id.startswith("pa-001-")
    assert authorization.authorization_id != "authorization-package-001"

    assert authorization.tenant_id == TENANT_ID
    assert authorization.client_id == CLIENT_ID
    assert authorization.engagement_id == ENGAGEMENT_ID
    assert authorization.assessment_id == ASSESSMENT_ID

    assert (
        authorization.contract_execution_event_id
        == "contract-event-001"
    )
    assert authorization.authorized_by == "operator-admin-001"
    assert authorization.authorized_at == AUTHORIZED_AT.isoformat()
    assert authorization.paid_assessment_authorized is True

    assert record.authorization_id == authorization.authorization_id
    assert record.authorization_hash == authorization.authorization_hash
    assert len(record.record_hash) == 64

    stored = store.get(
        authorization_id=authorization.authorization_id
    )

    assert stored == record


def test_issuance_is_idempotent_for_same_governed_evidence(tmp_path):
    service, store = build_service(tmp_path)

    first = issue_ready(service)

    second_service = GovernancePaidWorkAuthorizationIssuanceService(
        record_store=store,
        clock=lambda: datetime(
            2026,
            10,
            15,
            17,
            0,
            0,
            tzinfo=timezone.utc,
        ),
    )

    second = issue_ready(second_service)

    assert (
        second.authorization.authorization_id
        == first.authorization.authorization_id
    )
    assert (
        second.authorization.authorized_at
        == first.authorization.authorized_at
    )
    assert second.record.record_hash == first.record.record_hash


def test_executor_role_cannot_issue_pa001(tmp_path):
    service, _ = build_service(tmp_path)

    with pytest.raises(
        GovernancePaidWorkAuthorizationIssuanceError,
        match="assessment:admin",
    ):
        issue_ready(
            service,
            actor=build_actor(
                roles=(
                    ASSESSMENT_EXECUTOR_ROLE,
                )
            ),
        )


def test_actor_tenant_mismatch_is_rejected(tmp_path):
    service, _ = build_service(tmp_path)

    with pytest.raises(
        GovernancePaidWorkAuthorizationIssuanceError,
        match="actor tenant",
    ):
        issue_ready(
            service,
            actor=build_actor(
                tenant_id="tenant-beta"
            ),
        )


def test_package_readiness_does_not_self_authorize(tmp_path):
    service, _ = build_service(tmp_path)

    package = build_authorization_package()
    package["package_status"] = "pending_authorization_review"

    with pytest.raises(
        GovernancePaidWorkAuthorizationIssuanceError,
        match="authorization package is not ready",
    ):
        issue_ready(
            service,
            authorization_package=package,
        )


def test_package_that_claims_paid_work_authority_is_rejected(tmp_path):
    service, _ = build_service(tmp_path)

    package = build_authorization_package()
    package["commercial_boundary"][
        "paid_assessment_authorized"
    ] = True

    with pytest.raises(
        GovernancePaidWorkAuthorizationIssuanceError,
        match="paid_assessment_authorized must be false",
    ):
        issue_ready(
            service,
            authorization_package=package,
        )


def test_unexecuted_contract_is_rejected(tmp_path):
    service, _ = build_service(tmp_path)

    contract = build_contract_execution_event()
    contract["event_status"] = "pending_contract_execution_confirmation"

    with pytest.raises(
        GovernancePaidWorkAuthorizationIssuanceError,
        match="must be contract_executed",
    ):
        issue_ready(
            service,
            contract_execution_event=contract,
        )


def test_contract_event_that_claims_authority_is_rejected(tmp_path):
    service, _ = build_service(tmp_path)

    contract = build_contract_execution_event()
    contract["commercial_boundary"][
        "paid_assessment_authorized"
    ] = True

    with pytest.raises(
        GovernancePaidWorkAuthorizationIssuanceError,
        match="paid_assessment_authorized must be false",
    ):
        issue_ready(
            service,
            contract_execution_event=contract,
        )


def test_unconfirmed_payment_is_rejected(tmp_path):
    service, _ = build_service(tmp_path)

    payment = build_payment_confirmation_event()
    payment["event_status"] = "pending_payment_confirmation"

    with pytest.raises(
        GovernancePaidWorkAuthorizationIssuanceError,
        match="must be payment_confirmed",
    ):
        issue_ready(
            service,
            payment_confirmation_event=payment,
        )


def test_payment_event_that_claims_authority_is_rejected(tmp_path):
    service, _ = build_service(tmp_path)

    payment = build_payment_confirmation_event()
    payment["commercial_boundary"][
        "paid_assessment_authorized"
    ] = True

    with pytest.raises(
        GovernancePaidWorkAuthorizationIssuanceError,
        match="paid_assessment_authorized must be false",
    ):
        issue_ready(
            service,
            payment_confirmation_event=payment,
        )


def test_payment_reconciliation_is_required(tmp_path):
    service, _ = build_service(tmp_path)

    payment = build_payment_confirmation_event()
    payment["reconciliation_record"][
        "reconciliation_recorded"
    ] = False

    with pytest.raises(
        GovernancePaidWorkAuthorizationIssuanceError,
        match="reconciliation_recorded must be true",
    ):
        issue_ready(
            service,
            payment_confirmation_event=payment,
        )


def test_ai_override_boundary_is_rejected(tmp_path):
    service, _ = build_service(tmp_path)

    package = build_authorization_package()
    package["governance_boundary"][
        "ai_override_allowed"
    ] = True

    with pytest.raises(
        GovernancePaidWorkAuthorizationIssuanceError,
        match="ai_override_allowed must be false",
    ):
        issue_ready(
            service,
            authorization_package=package,
        )


def test_pa001_is_consumable_by_existing_execution_store_gate(tmp_path):
    service, store = build_service(tmp_path)

    result = issue_ready(service)

    resolved = store.require_for_execution(
        authorization_id=(
            result.authorization.authorization_id
        ),
        tenant_id=TENANT_ID,
        client_id=CLIENT_ID,
        engagement_id=ENGAGEMENT_ID,
        assessment_id=ASSESSMENT_ID,
        contract_execution_event_id="contract-event-001",
    )

    assert resolved.record_hash == result.record.record_hash
    assert resolved.paid_assessment_authorized is True


def test_result_preserves_authority_boundaries(tmp_path):
    service, _ = build_service(tmp_path)

    payload = issue_ready(service).to_dict()

    boundaries = payload["boundaries"]

    assert boundaries["package_readiness_is_not_authority"] is True
    assert boundaries["contract_execution_is_not_authority"] is True
    assert boundaries["payment_confirmation_is_not_authority"] is True
    assert boundaries["admin_issuance_action_creates_pa001"] is True
    assert boundaries["pa001_is_not_execution"] is True
    assert boundaries["pa001_is_not_delivery"] is True
    assert boundaries["pa001_is_not_production_onboarding"] is True
    assert boundaries["pa001_is_not_intervention_authority"] is True
    assert boundaries["record_integrity_is_not_actor_authentication"] is True

    assert len(payload["authorization_package_hash"]) == 64
    assert len(payload["contract_execution_event_hash"]) == 64
    assert len(payload["payment_confirmation_event_hash"]) == 64
