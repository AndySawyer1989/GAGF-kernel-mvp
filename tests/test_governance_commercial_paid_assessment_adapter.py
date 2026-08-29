from __future__ import annotations

import pytest

from backend.app.gagf.governance_commercial_paid_assessment_adapter import (
    CommercialContractExecutionEventInput,
    CommercialEvidenceDeclarationInput,
    CommercialExecutionEvidenceApprovalInput,
    CommercialPaidAssessmentAdapterError,
    CommercialPaidAssessmentIntakeInput,
    CommercialPaidWorkAuthorizationInput,
    CommercialStorageDeclarationInput,
    GovernanceCommercialPaidAssessmentAdapter,
)
from backend.app.gagf.governance_paid_assessment_execution_handoff import (
    GovernancePaidAssessmentExecutionHandoffService,
    PaidAssessmentWorkAuthorization,
)
from backend.app.gagf.governance_real_paid_assessment_execution_evidence import (
    RealAssessmentExecutionEvidenceApproval,
)
from backend.app.gagf.governance_real_paid_assessment_readiness import (
    EvidenceDataClassification,
    RealPaidAssessmentIntake,
)


SERVICE = GovernanceCommercialPaidAssessmentAdapter()
HANDOFF_SERVICE = GovernancePaidAssessmentExecutionHandoffService()


def build_payload(
    *,
    classification: str = "sanitized",
) -> CommercialPaidAssessmentIntakeInput:
    return CommercialPaidAssessmentIntakeInput(
        tenant_id="tenant-alpha",
        client_id="client-acme",
        engagement_id="engagement-001",
        assessment_id="assessment-001",
        client_display_name="Acme Corporation",
        assessment_name="Governance Friction Assessment",
        operator_name="FIP Operator",
        client_contact_name="Client Sponsor",
        assessment_scope_confirmed=True,
        evidence_scope_confirmed=True,
        client_data_use_confirmed=True,
        operator_readiness_confirmed=True,
        evidence=(
            CommercialEvidenceDeclarationInput(
                evidence_id="evidence-001",
                source_kind="csv",
                description="Sanitized workflow event export",
                classification=classification,
                client_authorized_for_assessment=True,
                minimization_review_completed=True,
                direct_identifiers_removed=True,
            ),
        ),
        storage=CommercialStorageDeclarationInput(
            repository_path="assessment.sqlite3",
            operator_controlled_location=True,
            access_restricted=True,
            storage_protection_confirmed=True,
            backup_plan_recorded=True,
            retention_period_recorded=True,
            deletion_plan_recorded=True,
        ),
    )


def build_authorization_payload(
    *,
    paid_assessment_authorized: bool = True,
    authorized_at: str = "2026-08-29T14:30:00+00:00",
) -> CommercialPaidWorkAuthorizationInput:
    return CommercialPaidWorkAuthorizationInput(
        authorization_id="authorization-001",
        tenant_id="tenant-alpha",
        client_id="client-acme",
        engagement_id="engagement-001",
        assessment_id="assessment-001",
        contract_execution_event_id="contract-event-001",
        authorized_by="Commercial Approver",
        authorized_at=authorized_at,
        paid_assessment_authorized=(
            paid_assessment_authorized
        ),
    )


def build_contract_event_payload(
    *,
    contract_executed: bool = True,
    requires_final_paid_work_authorization: bool = True,
    human_boundary_required: bool = True,
    gagf_kernel_authoritative: bool = True,
    ai_override_allowed: bool = False,
) -> CommercialContractExecutionEventInput:
    return CommercialContractExecutionEventInput(
        contract_execution_event_id="contract-event-001",
        contract_executed=contract_executed,
        contract_execution_review_ready=True,
        contract_execution_confirmed=True,
        executed_contract_reference_recorded=True,
        executed_at_recorded=True,
        all_required_signatures_recorded=True,
        human_operator_confirmed_execution=True,
        requires_final_paid_work_authorization=(
            requires_final_paid_work_authorization
        ),
        human_boundary_required=human_boundary_required,
        gagf_kernel_authoritative=(
            gagf_kernel_authoritative
        ),
        ai_override_allowed=ai_override_allowed,
    )


def build_execution_evidence_approval_payload(
    *,
    digest: str = "a" * 64,
    approved_at: str = "2026-08-29T15:00:00+00:00",
    approved: bool = True,
) -> CommercialExecutionEvidenceApprovalInput:
    return CommercialExecutionEvidenceApprovalInput(
        evidence_id="evidence-001",
        approved_content_sha256=digest,
        approved_by="Evidence Approver",
        approved_at=approved_at,
        execution_evidence_approved=approved,
    )


def test_build_intake_creates_governed_real_paid_assessment_intake():
    result = SERVICE.build_intake(
        payload=build_payload()
    )

    assert isinstance(
        result,
        RealPaidAssessmentIntake,
    )

    assert result.hierarchy_key == (
        "tenant-alpha/client-acme/"
        "engagement-001/assessment-001"
    )

    assert result.client_display_name == "Acme Corporation"
    assert result.assessment_name == (
        "Governance Friction Assessment"
    )

    assert len(result.evidence) == 1

    evidence = result.evidence[0]

    assert evidence.evidence_id == "evidence-001"
    assert evidence.classification is (
        EvidenceDataClassification.SANITIZED
    )

    assert result.storage.repository_path == (
        "assessment.sqlite3"
    )


@pytest.mark.parametrize(
    "classification",
    [
        "non_sensitive",
        "sanitized",
        "redacted",
    ],
)
def test_build_intake_accepts_current_pilot_classifications(
    classification,
):
    result = SERVICE.build_intake(
        payload=build_payload(
            classification=classification
        )
    )

    assert result.evidence[0].classification.value == (
        classification
    )


@pytest.mark.parametrize(
    "classification",
    [
        "pii",
        "regulated",
        "federal",
        "secret",
    ],
)
def test_build_intake_rejects_blocked_pilot_classifications(
    classification,
):
    with pytest.raises(
        CommercialPaidAssessmentAdapterError,
        match="not permitted for the current paid-assessment pilot",
    ):
        SERVICE.build_intake(
            payload=build_payload(
                classification=classification
            )
        )


def test_build_intake_rejects_unknown_classification():
    with pytest.raises(
        CommercialPaidAssessmentAdapterError,
        match="classification is not recognized",
    ):
        SERVICE.build_intake(
            payload=build_payload(
                classification="unknown"
            )
        )


def test_commercial_intake_requires_evidence():
    with pytest.raises(
        CommercialPaidAssessmentAdapterError,
        match="at least one evidence declaration is required",
    ):
        CommercialPaidAssessmentIntakeInput(
            tenant_id="tenant-alpha",
            client_id="client-acme",
            engagement_id="engagement-001",
            assessment_id="assessment-001",
            client_display_name="Acme Corporation",
            assessment_name="Governance Friction Assessment",
            operator_name="FIP Operator",
            client_contact_name="Client Sponsor",
            assessment_scope_confirmed=True,
            evidence_scope_confirmed=True,
            client_data_use_confirmed=True,
            operator_readiness_confirmed=True,
            evidence=(),
            storage=CommercialStorageDeclarationInput(
                repository_path="assessment.sqlite3",
                operator_controlled_location=True,
                access_restricted=True,
                storage_protection_confirmed=True,
                backup_plan_recorded=True,
                retention_period_recorded=True,
                deletion_plan_recorded=True,
            ),
        )


def test_commercial_intake_requires_boolean_confirmations():
    with pytest.raises(
        CommercialPaidAssessmentAdapterError,
        match="assessment_scope_confirmed must be a boolean",
    ):
        CommercialPaidAssessmentIntakeInput(
            tenant_id="tenant-alpha",
            client_id="client-acme",
            engagement_id="engagement-001",
            assessment_id="assessment-001",
            client_display_name="Acme Corporation",
            assessment_name="Governance Friction Assessment",
            operator_name="FIP Operator",
            client_contact_name="Client Sponsor",
            assessment_scope_confirmed="yes",
            evidence_scope_confirmed=True,
            client_data_use_confirmed=True,
            operator_readiness_confirmed=True,
            evidence=build_payload().evidence,
            storage=build_payload().storage,
        )


def test_adapter_rejects_wrong_intake_payload_type():
    with pytest.raises(
        CommercialPaidAssessmentAdapterError,
        match=(
            "payload must be a "
            "CommercialPaidAssessmentIntakeInput"
        ),
    ):
        SERVICE.build_intake(
            payload={},
        )


def test_build_paid_work_authorization_creates_governed_authorization():
    result = SERVICE.build_paid_work_authorization(
        payload=build_authorization_payload()
    )

    assert isinstance(
        result,
        PaidAssessmentWorkAuthorization,
    )

    assert result.authorization_id == (
        "authorization-001"
    )

    assert result.tenant_id == "tenant-alpha"
    assert result.client_id == "client-acme"
    assert result.engagement_id == "engagement-001"
    assert result.assessment_id == "assessment-001"

    assert result.contract_execution_event_id == (
        "contract-event-001"
    )

    assert result.authorized_by == (
        "Commercial Approver"
    )

    assert result.paid_assessment_authorized is True

    assert len(result.authorization_hash) == 64


def test_paid_work_authorization_preserves_exact_hierarchy():
    result = SERVICE.build_paid_work_authorization(
        payload=CommercialPaidWorkAuthorizationInput(
            authorization_id="authorization-002",
            tenant_id="tenant-specific",
            client_id="client-specific",
            engagement_id="engagement-specific",
            assessment_id="assessment-specific",
            contract_execution_event_id="contract-specific",
            authorized_by="Approver Two",
            authorized_at="2026-08-29T15:00:00Z",
            paid_assessment_authorized=True,
        )
    )

    assert (
        result.tenant_id,
        result.client_id,
        result.engagement_id,
        result.assessment_id,
    ) == (
        "tenant-specific",
        "client-specific",
        "engagement-specific",
        "assessment-specific",
    )

    assert result.contract_execution_event_id == (
        "contract-specific"
    )


def test_paid_work_authorization_requires_affirmative_authority():
    with pytest.raises(
        CommercialPaidAssessmentAdapterError,
        match="paid_assessment_authorized must be true",
    ):
        build_authorization_payload(
            paid_assessment_authorized=False
        )


def test_paid_work_authorization_requires_boolean_authority():
    with pytest.raises(
        CommercialPaidAssessmentAdapterError,
        match="paid_assessment_authorized must be a boolean",
    ):
        CommercialPaidWorkAuthorizationInput(
            authorization_id="authorization-001",
            tenant_id="tenant-alpha",
            client_id="client-acme",
            engagement_id="engagement-001",
            assessment_id="assessment-001",
            contract_execution_event_id="contract-event-001",
            authorized_by="Commercial Approver",
            authorized_at="2026-08-29T14:30:00+00:00",
            paid_assessment_authorized="yes",
        )


def test_paid_work_authorization_rejects_invalid_timestamp():
    with pytest.raises(
        CommercialPaidAssessmentAdapterError,
        match="paid-work authorization is invalid",
    ):
        SERVICE.build_paid_work_authorization(
            payload=build_authorization_payload(
                authorized_at="not-a-timestamp"
            )
        )


def test_adapter_rejects_wrong_authorization_payload_type():
    with pytest.raises(
        CommercialPaidAssessmentAdapterError,
        match=(
            "payload must be a "
            "CommercialPaidWorkAuthorizationInput"
        ),
    ):
        SERVICE.build_paid_work_authorization(
            payload={},
        )


def test_build_contract_execution_event_creates_expected_contract():
    result = SERVICE.build_contract_execution_event(
        payload=build_contract_event_payload()
    )

    assert result["status"] == "ok"

    assert result["event_type"] == (
        "assessment_factory_lite_contract_execution_event"
    )

    assert result["event_status"] == "contract_executed"

    assert result["contract_execution_event_id"] == (
        "contract-event-001"
    )

    assert result["execution_evidence"][
        "contract_executed"
    ] is True

    assert result["commercial_boundary"][
        "contract_executed"
    ] is True

    assert result["commercial_boundary"][
        "paid_assessment_authorized"
    ] is False

    assert result["commercial_boundary"][
        "requires_final_paid_work_authorization"
    ] is True

    assert result["governance_boundary"][
        "human_boundary_required"
    ] is True

    assert result["governance_boundary"][
        "gagf_kernel_authoritative"
    ] is True

    assert result["governance_boundary"][
        "ai_override_allowed"
    ] is False

    assert result["governance_boundary"][
        "contract_execution_event_is_not_paid_work_authorization"
    ] is True

    assert result["event_blockers"] == []


def test_contract_execution_event_passes_existing_handoff_validator():
    event = SERVICE.build_contract_execution_event(
        payload=build_contract_event_payload()
    )

    HANDOFF_SERVICE._validate_contract_execution_event(
        event
    )


def test_contract_event_does_not_create_paid_work_authority():
    result = SERVICE.build_contract_execution_event(
        payload=build_contract_event_payload()
    )

    assert result["commercial_boundary"][
        "paid_assessment_authorized"
    ] is False

    assert result["commercial_boundary"][
        "requires_final_paid_work_authorization"
    ] is True


def test_contract_event_requires_confirmed_contract_execution():
    with pytest.raises(
        CommercialPaidAssessmentAdapterError,
        match="contract_executed must be true",
    ):
        build_contract_event_payload(
            contract_executed=False
        )


def test_contract_event_requires_final_paid_work_authorization_boundary():
    with pytest.raises(
        CommercialPaidAssessmentAdapterError,
        match=(
            "requires_final_paid_work_authorization "
            "must be true"
        ),
    ):
        build_contract_event_payload(
            requires_final_paid_work_authorization=False
        )


def test_contract_event_requires_human_boundary():
    with pytest.raises(
        CommercialPaidAssessmentAdapterError,
        match="human_boundary_required must be true",
    ):
        build_contract_event_payload(
            human_boundary_required=False
        )


def test_contract_event_requires_gagf_kernel_authority():
    with pytest.raises(
        CommercialPaidAssessmentAdapterError,
        match="gagf_kernel_authoritative must be true",
    ):
        build_contract_event_payload(
            gagf_kernel_authoritative=False
        )


def test_contract_event_prohibits_ai_override():
    with pytest.raises(
        CommercialPaidAssessmentAdapterError,
        match="ai_override_allowed must be false",
    ):
        build_contract_event_payload(
            ai_override_allowed=True
        )


def test_contract_event_requires_boolean_values():
    with pytest.raises(
        CommercialPaidAssessmentAdapterError,
        match="contract_executed must be a boolean",
    ):
        CommercialContractExecutionEventInput(
            contract_execution_event_id="contract-event-001",
            contract_executed="yes",
            contract_execution_review_ready=True,
            contract_execution_confirmed=True,
            executed_contract_reference_recorded=True,
            executed_at_recorded=True,
            all_required_signatures_recorded=True,
            human_operator_confirmed_execution=True,
            requires_final_paid_work_authorization=True,
            human_boundary_required=True,
            gagf_kernel_authoritative=True,
            ai_override_allowed=False,
        )


def test_adapter_rejects_wrong_contract_event_payload_type():
    with pytest.raises(
        CommercialPaidAssessmentAdapterError,
        match=(
            "payload must be a "
            "CommercialContractExecutionEventInput"
        ),
    ):
        SERVICE.build_contract_execution_event(
            payload={},
        )


def test_build_execution_evidence_approval_creates_governed_approval():
    result = SERVICE.build_execution_evidence_approval(
        payload=build_execution_evidence_approval_payload()
    )

    assert isinstance(
        result,
        RealAssessmentExecutionEvidenceApproval,
    )

    assert result.evidence_id == "evidence-001"
    assert result.approved_content_sha256 == "a" * 64
    assert result.approved_by == "Evidence Approver"
    assert result.execution_evidence_approved is True


def test_execution_evidence_approval_preserves_exact_digest():
    digest = (
        "0123456789abcdef"
        "0123456789abcdef"
        "0123456789abcdef"
        "0123456789abcdef"
    )

    result = SERVICE.build_execution_evidence_approval(
        payload=build_execution_evidence_approval_payload(
            digest=digest
        )
    )

    assert result.approved_content_sha256 == digest


def test_execution_evidence_approval_requires_affirmative_approval():
    with pytest.raises(
        CommercialPaidAssessmentAdapterError,
        match="execution_evidence_approved must be true",
    ):
        build_execution_evidence_approval_payload(
            approved=False
        )


def test_execution_evidence_approval_requires_boolean_approval():
    with pytest.raises(
        CommercialPaidAssessmentAdapterError,
        match=(
            "execution_evidence_approved "
            "must be a boolean"
        ),
    ):
        CommercialExecutionEvidenceApprovalInput(
            evidence_id="evidence-001",
            approved_content_sha256="a" * 64,
            approved_by="Evidence Approver",
            approved_at="2026-08-29T15:00:00Z",
            execution_evidence_approved="yes",
        )


def test_execution_evidence_approval_rejects_short_digest():
    with pytest.raises(
        CommercialPaidAssessmentAdapterError,
        match="execution-evidence approval is invalid",
    ):
        SERVICE.build_execution_evidence_approval(
            payload=build_execution_evidence_approval_payload(
                digest="a" * 63
            )
        )


def test_execution_evidence_approval_rejects_non_hex_digest():
    with pytest.raises(
        CommercialPaidAssessmentAdapterError,
        match="execution-evidence approval is invalid",
    ):
        SERVICE.build_execution_evidence_approval(
            payload=build_execution_evidence_approval_payload(
                digest="z" * 64
            )
        )


def test_execution_evidence_approval_rejects_invalid_timestamp():
    with pytest.raises(
        CommercialPaidAssessmentAdapterError,
        match="execution-evidence approval is invalid",
    ):
        SERVICE.build_execution_evidence_approval(
            payload=build_execution_evidence_approval_payload(
                approved_at="not-a-timestamp"
            )
        )


def test_adapter_rejects_wrong_execution_evidence_payload_type():
    with pytest.raises(
        CommercialPaidAssessmentAdapterError,
        match=(
            "payload must be a "
            "CommercialExecutionEvidenceApprovalInput"
        ),
    ):
        SERVICE.build_execution_evidence_approval(
            payload={},
        )