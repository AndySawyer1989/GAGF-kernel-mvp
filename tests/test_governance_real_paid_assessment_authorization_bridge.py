import pytest

from backend.app.gagf.governance_paid_assessment_execution_handoff import (
    PaidAssessmentWorkAuthorization,
)
from backend.app.gagf.governance_real_paid_assessment_authorization_bridge import (
    BRIDGE_STATUS_READY,
    GovernanceRealPaidAssessmentAuthorizationBridgeService,
    RealPaidAssessmentAuthorizationBridgeError,
)
from backend.app.gagf.governance_real_paid_assessment_readiness import (
    EvidenceDataClassification,
    GovernanceRealPaidAssessmentReadinessService,
    RealAssessmentEvidenceDeclaration,
    RealAssessmentStorageDeclaration,
    RealPaidAssessmentIntake,
)


def build_intake():
    return RealPaidAssessmentIntake(
        tenant_id="tenant-acme",
        client_id="client-acme",
        engagement_id="engagement-001",
        assessment_id="assessment-001",
        client_display_name="ACME Corporation",
        assessment_name="Governance Runway Assessment",
        operator_name="FIP Operator",
        client_contact_name="Client Representative",
        assessment_scope_confirmed=True,
        evidence_scope_confirmed=True,
        client_data_use_confirmed=True,
        operator_readiness_confirmed=True,
        evidence=(
            RealAssessmentEvidenceDeclaration(
                evidence_id="workflow-export-001",
                source_kind="csv",
                description="Redacted workflow export",
                classification=EvidenceDataClassification.REDACTED,
                client_authorized_for_assessment=True,
                minimization_review_completed=True,
                direct_identifiers_removed=True,
            ),
        ),
        storage=RealAssessmentStorageDeclaration(
            repository_path=(
                r"C:\FIP\pilot-data\client-acme\assessment-001.sqlite3"
            ),
            operator_controlled_location=True,
            access_restricted=True,
            storage_protection_confirmed=True,
            backup_plan_recorded=True,
            retention_period_recorded=True,
            deletion_plan_recorded=True,
        ),
    )


def build_authorization(**overrides):
    values = {
        "authorization_id": "paid-work-auth-real-001",
        "tenant_id": "tenant-acme",
        "client_id": "client-acme",
        "engagement_id": "engagement-001",
        "assessment_id": "assessment-001",
        "contract_execution_event_id": "contract-event-real-001",
        "authorized_by": "FIP Operator",
        "authorized_at": "2026-08-20T16:55:00+00:00",
        "paid_assessment_authorized": True,
    }
    values.update(overrides)
    return PaidAssessmentWorkAuthorization(**values)


def test_ready_intake_binds_independent_paid_work_authorization():
    intake = build_intake()

    readiness = GovernanceRealPaidAssessmentReadinessService().evaluate(
        intake=intake
    )

    bridge = (
        GovernanceRealPaidAssessmentAuthorizationBridgeService()
        .bind(
            intake=intake,
            readiness=readiness,
            paid_work_authorization=build_authorization(),
        )
    )

    assert bridge.bridge_status == BRIDGE_STATUS_READY
    assert bridge.paid_assessment_authorized is True
    assert bridge.authorization_id == "paid-work-auth-real-001"
    assert (
        bridge.hierarchy_key
        == "tenant-acme/client-acme/engagement-001/assessment-001"
    )


def test_bridge_rejects_hierarchy_mismatch():
    intake = build_intake()

    readiness = GovernanceRealPaidAssessmentReadinessService().evaluate(
        intake=intake
    )

    with pytest.raises(
        RealPaidAssessmentAuthorizationBridgeError,
        match="authorization hierarchy",
    ):
        (
            GovernanceRealPaidAssessmentAuthorizationBridgeService()
            .bind(
                intake=intake,
                readiness=readiness,
                paid_work_authorization=build_authorization(
                    client_id="wrong-client"
                ),
            )
        )


def test_bridge_rejects_blocked_readiness():
    base = build_intake()

    blocked_intake = RealPaidAssessmentIntake(
        tenant_id=base.tenant_id,
        client_id=base.client_id,
        engagement_id=base.engagement_id,
        assessment_id=base.assessment_id,
        client_display_name=base.client_display_name,
        assessment_name=base.assessment_name,
        operator_name=base.operator_name,
        client_contact_name=base.client_contact_name,
        assessment_scope_confirmed=base.assessment_scope_confirmed,
        evidence_scope_confirmed=base.evidence_scope_confirmed,
        client_data_use_confirmed=base.client_data_use_confirmed,
        operator_readiness_confirmed=False,
        evidence=base.evidence,
        storage=base.storage,
    )

    readiness = GovernanceRealPaidAssessmentReadinessService().evaluate(
        intake=blocked_intake
    )

    with pytest.raises(
        RealPaidAssessmentAuthorizationBridgeError,
        match="not READY",
    ):
        (
            GovernanceRealPaidAssessmentAuthorizationBridgeService()
            .bind(
                intake=blocked_intake,
                readiness=readiness,
                paid_work_authorization=build_authorization(),
            )
        )


def test_bridge_does_not_manufacture_execution_authority():
    intake = build_intake()

    readiness = GovernanceRealPaidAssessmentReadinessService().evaluate(
        intake=intake
    )

    bridge = (
        GovernanceRealPaidAssessmentAuthorizationBridgeService()
        .bind(
            intake=intake,
            readiness=readiness,
            paid_work_authorization=build_authorization(),
        )
    )

    payload = bridge.to_dict()

    assert payload["paid_assessment_authorized"] is True
    assert payload["boundaries"][
        "readiness_did_not_create_authorization"
    ] is True
    assert payload["boundaries"][
        "bridge_did_not_create_authorization"
    ] is True
    assert payload["boundaries"][
        "authorization_is_not_execution"
    ] is True

    assert "assessment_executed" not in payload
    assert "production_onboarding_authorized" not in payload
    assert "customer_outcome_verified" not in payload