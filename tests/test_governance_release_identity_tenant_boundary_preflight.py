from __future__ import annotations

import asyncio

import pytest

from backend.app.gagf.governance_assessment_auth import (
    ASSESSMENT_AUTH_VERSION,
)
from backend.app.gagf.governance_release_identity_tenant_boundary_preflight import (
    GOVERNANCE_RELEASE_IDENTITY_TENANT_BOUNDARY_PREFLIGHT_TYPE,
    GOVERNANCE_RELEASE_IDENTITY_TENANT_BOUNDARY_PREFLIGHT_VERSION,
    evaluate_governance_release_identity_tenant_boundary_preflight,
)


def evaluate(
    release_environment: str,
):
    return asyncio.run(
        evaluate_governance_release_identity_tenant_boundary_preflight(
            release_environment=release_environment,
        )
    )


@pytest.mark.parametrize(
    "release_environment",
    (
        "paid_trial",
        "prelive",
    ),
)
def test_identity_preflight_fails_closed_without_provider_evidence(
    release_environment: str,
) -> None:
    result = evaluate(
        release_environment
    )

    assert result.release_environment == release_environment
    assert result.assessment_auth_version == ASSESSMENT_AUTH_VERSION

    assert result.identity_provider_configured is False
    assert result.deployment_identity_evidence_present is False
    assert result.provider_claim_mapping_verified is False
    assert result.tenant_boundary_evidence_verified is False
    assert result.role_mapping_evidence_verified is False

    assert result.passed is False

    assert result.failure_reasons == (
        "production_identity_provider_not_configured",
        "deployment_identity_evidence_unavailable",
        "provider_claim_mapping_unverified",
        "tenant_boundary_evidence_unverified",
        "role_mapping_evidence_unverified",
    )


@pytest.mark.parametrize(
    "release_environment",
    (
        "",
        "development",
        "test",
        "production",
        "production-ish",
    ),
)
def test_non_release_environment_is_rejected(
    release_environment: str,
) -> None:
    with pytest.raises(
        ValueError,
        match=(
            "identity/tenant boundary preflight requires "
            "release environment prelive or paid_trial"
        ),
    ):
        evaluate(
            release_environment
        )


def test_release_environment_is_normalized(
) -> None:
    result = evaluate(
        "  PAID_TRIAL  "
    )

    assert result.release_environment == "paid_trial"
    assert result.passed is False


def test_public_result_reports_unverified_identity_evidence(
) -> None:
    result = evaluate(
        "paid_trial"
    )

    public = result.to_public_dict()

    assert (
        public["preflight_type"]
        == GOVERNANCE_RELEASE_IDENTITY_TENANT_BOUNDARY_PREFLIGHT_TYPE
    )

    assert (
        public["version"]
        == GOVERNANCE_RELEASE_IDENTITY_TENANT_BOUNDARY_PREFLIGHT_VERSION
    )

    assert public["assessment_auth_version"] == ASSESSMENT_AUTH_VERSION

    assert public["identity_provider_configured"] is False
    assert public["deployment_identity_evidence_present"] is False
    assert public["provider_claim_mapping_verified"] is False
    assert public["tenant_boundary_evidence_verified"] is False
    assert public["role_mapping_evidence_verified"] is False

    assert public["passed"] is False
    assert public["failure_reasons"] == list(result.failure_reasons)


def test_public_result_preserves_authority_boundaries(
) -> None:
    boundaries = evaluate(
        "paid_trial"
    ).to_public_dict()["boundaries"]

    assert isinstance(boundaries, dict)

    assert all(
        value is True
        for value in boundaries.values()
    )

    assert (
        boundaries[
            "preflight_does_not_verify_identity_by_simulation"
        ]
        is True
    )

    assert (
        boundaries[
            "unverified_identity_evidence_fails_closed"
        ]
        is True
    )


def test_public_result_contains_no_synthetic_identity_values(
) -> None:
    public_text = repr(
        evaluate(
            "paid_trial"
        ).to_public_dict()
    )

    assert "tenant-alpha" not in public_text
    assert "tenant-beta" not in public_text
    assert "release-preflight-actor" not in public_text


def test_preflight_has_no_synthetic_request_or_identity_helpers(
) -> None:
    from backend.app.gagf import (
        governance_release_identity_tenant_boundary_preflight as module,
    )

    forbidden_helpers = (
        "_build_request",
        "_missing_header_fails_closed",
        "_prove_deterministic_role_parsing",
        "_tenant_mismatch_is_denied",
        "_insufficient_role_is_denied",
        "_valid_identity_is_accepted",
    )

    for helper_name in forbidden_helpers:
        assert not hasattr(
            module,
            helper_name,
        )
