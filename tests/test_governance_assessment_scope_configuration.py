from dataclasses import FrozenInstanceError
from datetime import date

import pytest

from backend.app.gagf.governance_assessment_domain import (
    EvidenceSourceKind,
)
from backend.app.gagf.governance_assessment_isolation import (
    CommercialHierarchyContext,
)
from backend.app.gagf.governance_assessment_scope_configuration import (
    AssessmentScopeConfiguration,
    EvidenceRequirement,
    GovernanceAssessmentScopeConfigurationService,
    ScopeConfigurationError,
    ScopeConfigurationStatus,
)


SERVICE = GovernanceAssessmentScopeConfigurationService()


def build_context():
    return CommercialHierarchyContext(
        tenant_id="tenant-alpha",
        client_id="client-acme",
        engagement_id="engagement-001",
        assessment_id="assessment-001",
    )


def build_requirement(
    requirement_id="requirement-001",
):
    return EvidenceRequirement(
        requirement_id=requirement_id,
        source_kind=EvidenceSourceKind.CSV,
        description="Ticket workflow export",
        required=True,
        minimum_record_count=10,
    )


def build_configuration(**overrides):
    values = {
        "context": build_context(),
        "assessment_name": "Governance Runway Assessment",
        "workflow_names": ("Incident Management",),
        "organizational_units": ("IT Operations",),
        "period_start": date(2026, 1, 1),
        "period_end": date(2026, 6, 30),
        "objectives": ("Reduce approval delay",),
        "expected_outcomes": (
            "Shorter incident resolution time",
        ),
        "exclusions": ("Vendor-managed incidents",),
        "evidence_requirements": (
            build_requirement(),
        ),
        "status": ScopeConfigurationStatus.VALIDATED,
    }
    values.update(overrides)
    return SERVICE.configure(**values)


def test_scope_status_values_are_stable():
    assert ScopeConfigurationStatus.DRAFT.value == "draft"
    assert ScopeConfigurationStatus.LOCKED.value == "locked"


def test_evidence_requirement_serializes():
    serialized = build_requirement().to_dict()

    assert serialized["requirement_id"] == "requirement-001"
    assert serialized["source_kind"] == "csv"
    assert serialized["minimum_record_count"] == 10


def test_required_evidence_requires_positive_minimum():
    with pytest.raises(
        ScopeConfigurationError,
        match="minimum count",
    ):
        EvidenceRequirement(
            requirement_id="requirement-001",
            source_kind=EvidenceSourceKind.CSV,
            description="Ticket export",
            required=True,
            minimum_record_count=0,
        )


def test_configuration_is_bound_to_full_hierarchy():
    configuration = build_configuration()

    assert configuration.hierarchy_key == (
        "tenant-alpha/client-acme/"
        "engagement-001/assessment-001"
    )


def test_configuration_normalizes_text_values():
    configuration = build_configuration(
        assessment_name=" Assessment ",
        workflow_names=(" Incident Management ",),
        organizational_units=(" IT Operations ",),
        objectives=(" Reduce delay ",),
        expected_outcomes=(" Faster work ",),
        exclusions=(" External vendors ",),
    )

    assert configuration.assessment_name == "Assessment"
    assert configuration.workflow_names == (
        "Incident Management",
    )
    assert configuration.objectives == ("Reduce delay",)


def test_configuration_rejects_duplicate_workflows():
    with pytest.raises(
        ScopeConfigurationError,
        match="duplicate",
    ):
        build_configuration(
            workflow_names=(
                "Incident Management",
                "Incident Management",
            )
        )


def test_configuration_rejects_empty_objectives():
    with pytest.raises(
        ScopeConfigurationError,
        match="objectives",
    ):
        build_configuration(objectives=())


def test_configuration_rejects_reversed_period():
    with pytest.raises(
        ScopeConfigurationError,
        match="period_end",
    ):
        build_configuration(
            period_start=date(2026, 7, 1),
            period_end=date(2026, 6, 1),
        )


def test_configuration_rejects_duplicate_requirements():
    requirement = build_requirement()

    with pytest.raises(
        ScopeConfigurationError,
        match="duplicate identifiers",
    ):
        build_configuration(
            evidence_requirements=(
                requirement,
                requirement,
            )
        )


def test_configuration_hash_is_deterministic():
    first = build_configuration()
    second = build_configuration()

    assert first.configuration_hash == (
        second.configuration_hash
    )


def test_configuration_hash_changes_by_tenant():
    alpha = build_configuration()
    beta = build_configuration(
        context=CommercialHierarchyContext(
            tenant_id="tenant-beta",
            client_id="client-acme",
            engagement_id="engagement-001",
            assessment_id="assessment-001",
        )
    )

    assert alpha.configuration_hash != (
        beta.configuration_hash
    )


def test_configuration_converts_to_domain_scope():
    configuration = build_configuration()
    scope = configuration.to_scope()

    assert scope.workflow_names == (
        "Incident Management",
    )
    assert scope.organizational_units == (
        "IT Operations",
    )
    assert scope.period_start == date(2026, 1, 1)
    assert scope.exclusions == (
        "Vendor-managed incidents",
    )


def test_validated_scope_is_ready_for_evidence():
    configuration = build_configuration()

    assert SERVICE.validate_ready_for_evidence(
        configuration
    ) is configuration


def test_draft_scope_is_not_ready_for_evidence():
    configuration = build_configuration(
        status=ScopeConfigurationStatus.DRAFT
    )

    with pytest.raises(
        ScopeConfigurationError,
        match="validated or locked",
    ):
        SERVICE.validate_ready_for_evidence(
            configuration
        )


def test_scope_requires_evidence_requirements_before_intake():
    configuration = build_configuration(
        evidence_requirements=()
    )

    with pytest.raises(
        ScopeConfigurationError,
        match="at least one evidence requirement",
    ):
        SERVICE.validate_ready_for_evidence(
            configuration
        )


def test_lock_returns_locked_configuration():
    configuration = build_configuration()
    locked = SERVICE.lock(configuration)

    assert locked.status is ScopeConfigurationStatus.LOCKED
    assert locked.hierarchy_key == configuration.hierarchy_key
    assert locked.configuration_hash != (
        configuration.configuration_hash
    )


def test_lock_is_idempotent():
    locked = SERVICE.lock(build_configuration())

    assert SERVICE.lock(locked) is locked


def test_configuration_serializes_public_contract():
    serialized = build_configuration().to_dict()

    assert serialized["status"] == "validated"
    assert serialized["period_start"] == "2026-01-01"
    assert serialized["period_end"] == "2026-06-30"
    assert serialized["evidence_requirements"][0][
        "source_kind"
    ] == "csv"


def test_configuration_is_immutable():
    configuration = build_configuration()

    with pytest.raises(FrozenInstanceError):
        configuration.assessment_name = "Changed"


def test_scope_configuration_type_is_stable():
    configuration = build_configuration()

    assert isinstance(
        configuration,
        AssessmentScopeConfiguration,
    )
