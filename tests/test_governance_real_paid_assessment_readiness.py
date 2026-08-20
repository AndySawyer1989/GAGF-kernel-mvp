import pytest

from backend.app.gagf.governance_real_paid_assessment_readiness import (
    ACTION_REQUEST_PAID_WORK_AUTHORIZATION,
    ACTION_RESOLVE_READINESS_BLOCKERS,
    READINESS_STATUS_BLOCKED,
    READINESS_STATUS_READY,
    EvidenceDataClassification,
    GovernanceRealPaidAssessmentReadinessService,
    RealAssessmentEvidenceDeclaration,
    RealAssessmentStorageDeclaration,
    RealPaidAssessmentIntake,
    RealPaidAssessmentReadinessError,
)


def build_storage(**overrides):
    values = {
        "repository_path": (
            r"C:\FIP\pilot-data\client-acme\assessment-001.sqlite3"
        ),
        "operator_controlled_location": True,
        "access_restricted": True,
        "storage_protection_confirmed": True,
        "backup_plan_recorded": True,
        "retention_period_recorded": True,
        "deletion_plan_recorded": True,
    }
    values.update(overrides)
    return RealAssessmentStorageDeclaration(**values)


def build_evidence(
    *,
    classification=EvidenceDataClassification.REDACTED,
    **overrides,
):
    values = {
        "evidence_id": "workflow-export-001",
        "source_kind": "csv",
        "description": "Redacted workflow export",
        "classification": classification,
        "client_authorized_for_assessment": True,
        "minimization_review_completed": True,
        "direct_identifiers_removed": True,
    }
    values.update(overrides)
    return RealAssessmentEvidenceDeclaration(**values)


def build_intake(**overrides):
    values = {
        "tenant_id": "tenant-acme",
        "client_id": "client-acme",
        "engagement_id": "engagement-001",
        "assessment_id": "assessment-001",
        "client_display_name": "ACME Corporation",
        "assessment_name": "Governance Runway Assessment",
        "operator_name": "FIP Operator",
        "client_contact_name": "Client Representative",
        "assessment_scope_confirmed": True,
        "evidence_scope_confirmed": True,
        "client_data_use_confirmed": True,
        "operator_readiness_confirmed": True,
        "evidence": (build_evidence(),),
        "storage": build_storage(),
    }
    values.update(overrides)
    return RealPaidAssessmentIntake(**values)


def test_redacted_real_client_intake_can_be_ready():
    result = GovernanceRealPaidAssessmentReadinessService().evaluate(
        intake=build_intake()
    )

    assert result.readiness_status == READINESS_STATUS_READY
    assert result.ready_for_paid_work_authorization is True
    assert (
        result.required_operator_action
        == ACTION_REQUEST_PAID_WORK_AUTHORIZATION
    )

    assert (
        result.hierarchy_key
        == "tenant-acme/client-acme/engagement-001/assessment-001"
    )

    assert result.evidence_count == 1
    assert result.permitted_evidence_count == 1
    assert result.blocked_evidence_count == 0
    assert result.blockers == ()

    assert result.storage_location_declared is True
    assert result.storage_controls_declared is True


@pytest.mark.parametrize(
    "classification",
    (
        EvidenceDataClassification.PII,
        EvidenceDataClassification.REGULATED,
        EvidenceDataClassification.FEDERAL,
        EvidenceDataClassification.SECRET,
    ),
)
def test_sensitive_classifications_are_blocked(
    classification,
):
    intake = build_intake(
        evidence=(
            build_evidence(
                classification=classification
            ),
        )
    )

    result = GovernanceRealPaidAssessmentReadinessService().evaluate(
        intake=intake
    )

    assert result.readiness_status == READINESS_STATUS_BLOCKED
    assert result.ready_for_paid_work_authorization is False
    assert (
        result.required_operator_action
        == ACTION_RESOLVE_READINESS_BLOCKERS
    )
    assert result.blocked_evidence_count == 1

    assert any(
        classification.value in blocker
        for blocker in result.blockers
    )


def test_redacted_evidence_requires_identifiers_removed():
    intake = build_intake(
        evidence=(
            build_evidence(
                direct_identifiers_removed=False
            ),
        )
    )

    result = GovernanceRealPaidAssessmentReadinessService().evaluate(
        intake=intake
    )

    assert result.ready_for_paid_work_authorization is False
    assert (
        "direct_identifiers_not_removed:workflow-export-001"
        in result.blockers
    )


def test_client_authorization_is_required_per_evidence_item():
    intake = build_intake(
        evidence=(
            build_evidence(
                client_authorized_for_assessment=False
            ),
        )
    )

    result = GovernanceRealPaidAssessmentReadinessService().evaluate(
        intake=intake
    )

    assert result.ready_for_paid_work_authorization is False
    assert (
        "evidence_not_client_authorized:workflow-export-001"
        in result.blockers
    )


def test_minimization_review_is_required():
    intake = build_intake(
        evidence=(
            build_evidence(
                minimization_review_completed=False
            ),
        )
    )

    result = GovernanceRealPaidAssessmentReadinessService().evaluate(
        intake=intake
    )

    assert result.ready_for_paid_work_authorization is False
    assert (
        "evidence_minimization_not_completed:workflow-export-001"
        in result.blockers
    )


@pytest.mark.parametrize(
    ("field_name", "expected_blocker"),
    (
        (
            "assessment_scope_confirmed",
            "assessment_scope_not_confirmed",
        ),
        (
            "evidence_scope_confirmed",
            "evidence_scope_not_confirmed",
        ),
        (
            "client_data_use_confirmed",
            "client_data_use_not_confirmed",
        ),
        (
            "operator_readiness_confirmed",
            "operator_readiness_not_confirmed",
        ),
    ),
)
def test_required_intake_confirmations_fail_closed(
    field_name,
    expected_blocker,
):
    intake = build_intake(
        **{field_name: False}
    )

    result = GovernanceRealPaidAssessmentReadinessService().evaluate(
        intake=intake
    )

    assert result.ready_for_paid_work_authorization is False
    assert expected_blocker in result.blockers


@pytest.mark.parametrize(
    ("field_name", "expected_blocker"),
    (
        (
            "operator_controlled_location",
            "storage_not_operator_controlled",
        ),
        (
            "access_restricted",
            "storage_access_not_restricted",
        ),
        (
            "storage_protection_confirmed",
            "storage_protection_not_confirmed",
        ),
        (
            "backup_plan_recorded",
            "backup_plan_not_recorded",
        ),
        (
            "retention_period_recorded",
            "retention_period_not_recorded",
        ),
        (
            "deletion_plan_recorded",
            "deletion_plan_not_recorded",
        ),
    ),
)
def test_storage_controls_fail_closed(
    field_name,
    expected_blocker,
):
    intake = build_intake(
        storage=build_storage(
            **{field_name: False}
        )
    )

    result = GovernanceRealPaidAssessmentReadinessService().evaluate(
        intake=intake
    )

    assert result.ready_for_paid_work_authorization is False
    assert expected_blocker in result.blockers


def test_readiness_does_not_manufacture_authority():
    result = GovernanceRealPaidAssessmentReadinessService().evaluate(
        intake=build_intake()
    )

    payload = result.to_dict()

    assert payload["ready_for_paid_work_authorization"] is True

    boundaries = payload["boundaries"]

    assert boundaries[
        "intake_is_not_paid_work_authorization"
    ] is True
    assert boundaries[
        "readiness_is_not_paid_work_authorization"
    ] is True
    assert boundaries[
        "readiness_is_not_assessment_execution"
    ] is True
    assert boundaries[
        "readiness_is_not_production_onboarding"
    ] is True
    assert boundaries[
        "storage_declaration_is_not_technical_verification"
    ] is True
    assert boundaries[
        "ready_does_not_authorize_sensitive_data"
    ] is True
    assert boundaries[
        "ready_does_not_certify_compliance"
    ] is True

    assert "paid_assessment_authorized" not in payload
    assert "assessment_executed" not in payload
    assert "production_onboarding_authorized" not in payload
    assert "compliance_certified" not in payload


def test_intake_requires_evidence():
    with pytest.raises(
        RealPaidAssessmentReadinessError,
        match="at least one evidence declaration",
    ):
        build_intake(evidence=())


def test_context_uses_existing_four_part_commercial_hierarchy():
    intake = build_intake()

    assert intake.context.tenant_id == "tenant-acme"
    assert intake.context.client_id == "client-acme"
    assert intake.context.engagement_id == "engagement-001"
    assert intake.context.assessment_id == "assessment-001"