from __future__ import annotations

import asyncio

import pytest

from backend.app.gagf.governance_release_identity_tenant_boundary_preflight import (
    GOVERNANCE_RELEASE_IDENTITY_TENANT_BOUNDARY_PREFLIGHT_TYPE,
    GOVERNANCE_RELEASE_IDENTITY_TENANT_BOUNDARY_PREFLIGHT_VERSION,
    REQUIRED_IDENTITY_HEADERS,
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


def test_paid_trial_identity_tenant_boundary_preflight_passes(
) -> None:
    result = evaluate(
        "paid_trial"
    )

    assert result.passed is True
    assert result.failure_reasons == ()

    assert (
        result.tenant_identity_required
        is True
    )

    assert (
        result.actor_identity_required
        is True
    )

    assert (
        result.actor_roles_required
        is True
    )

    assert (
        result.missing_identity_fails_closed
        is True
    )

    assert (
        result.deterministic_role_parsing
        is True
    )

    assert (
        result.tenant_scope_binding_enforced
        is True
    )

    assert (
        result.insufficient_role_fails_closed
        is True
    )

    assert (
        result.valid_identity_accepted
        is True
    )


def test_prelive_identity_tenant_boundary_preflight_passes(
) -> None:
    result = evaluate(
        "prelive"
    )

    assert result.passed is True

    assert (
        result.release_environment
        == "prelive"
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

    assert (
        result.release_environment
        == "paid_trial"
    )

    assert result.passed is True


def test_public_result_exposes_identity_metadata_only(
) -> None:
    result = evaluate(
        "paid_trial"
    )

    public = (
        result.to_public_dict()
    )

    assert (
        public[
            "preflight_type"
        ]
        == GOVERNANCE_RELEASE_IDENTITY_TENANT_BOUNDARY_PREFLIGHT_TYPE
    )

    assert (
        public[
            "version"
        ]
        == GOVERNANCE_RELEASE_IDENTITY_TENANT_BOUNDARY_PREFLIGHT_VERSION
    )

    assert (
        public[
            "required_identity_headers"
        ]
        == list(
            REQUIRED_IDENTITY_HEADERS
        )
    )

    assert (
        public[
            "assessment_auth_version"
        ]
        == result.assessment_auth_version
    )

    assert (
        public[
            "tenant_scope_binding_enforced"
        ]
        is True
    )

    assert (
        public[
            "missing_identity_fails_closed"
        ]
        is True
    )

    assert (
        public[
            "insufficient_role_fails_closed"
        ]
        is True
    )

    assert (
        public[
            "valid_identity_accepted"
        ]
        is True
    )


def test_public_result_preserves_authority_boundaries(
) -> None:
    result = evaluate(
        "paid_trial"
    )

    boundaries = (
        result.to_public_dict()[
            "boundaries"
        ]
    )

    assert (
        boundaries[
            "preflight_is_read_only"
        ]
        is True
    )

    assert (
        boundaries[
            "preflight_uses_existing_assessment_auth_authority"
        ]
        is True
    )

    assert (
        boundaries[
            "preflight_does_not_create_identity"
        ]
        is True
    )

    assert (
        boundaries[
            "preflight_does_not_grant_roles"
        ]
        is True
    )

    assert (
        boundaries[
            "preflight_does_not_grant_access"
        ]
        is True
    )

    assert (
        boundaries[
            "identity_preflight_is_not_authentication"
        ]
        is True
    )

    assert (
        boundaries[
            "identity_preflight_is_not_authorization"
        ]
        is True
    )

    assert (
        boundaries[
            "identity_preflight_is_not_deployment_activation"
        ]
        is True
    )

    assert (
        boundaries[
            "identity_preflight_is_not_trial_authorization"
        ]
        is True
    )


def test_public_result_does_not_expose_synthetic_identity_values(
) -> None:
    result = evaluate(
        "paid_trial"
    )

    public_text = repr(
        result.to_public_dict()
    )

    assert (
        "tenant-alpha"
        not in public_text
    )

    assert (
        "tenant-beta"
        not in public_text
    )

    assert (
        "release-preflight-actor"
        not in public_text
    )


def test_required_identity_header_contract_is_exact(
) -> None:
    assert (
        REQUIRED_IDENTITY_HEADERS
        == (
            "X-Tenant-ID",
            "X-Actor-ID",
            "X-Actor-Roles",
        )
    )