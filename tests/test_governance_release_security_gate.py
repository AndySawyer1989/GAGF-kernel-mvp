from dataclasses import FrozenInstanceError

import pytest

from backend.app.gagf.governance_assessment_auth import (
    ASSESSMENT_AUTH_VERSION,
)
from backend.app.gagf.governance_release_environment_security_preflight import (
    GovernanceReleaseEnvironmentSecurityPreflightResult,
)
from backend.app.gagf.governance_release_identity_tenant_boundary_preflight import (
    GovernanceReleaseIdentityTenantBoundaryPreflightResult,
)
from backend.app.gagf.governance_release_invalid_security_configuration_proof import (
    GovernanceReleaseInvalidSecurityConfigurationProofResult,
)
from backend.app.gagf.governance_release_secret_preflight import (
    GovernanceReleaseSecretPreflightResult,
)
from backend.app.gagf.governance_release_secret_redaction_proof import (
    GovernanceReleaseSecretRedactionProofResult,
)
from backend.app.gagf.governance_release_security_gate import (
    GOVERNANCE_RELEASE_SECURITY_GATE_TYPE,
    GOVERNANCE_RELEASE_SECURITY_GATE_VERSION,
    GovernanceReleaseSecurityGateResult,
    evaluate_governance_release_security_gate,
)


def build_secret_preflight(
    *,
    release_environment: str = "paid_trial",
    passed: bool = True,
) -> GovernanceReleaseSecretPreflightResult:
    return GovernanceReleaseSecretPreflightResult(
        release_environment=release_environment,
        signing_configuration_enabled=passed,
        tenant_configuration_present=passed,
        key_id_configuration_present=passed,
        secret_reference_present=passed,
        environment_secret_reference=passed,
        secret_resolved=passed,
        passed=passed,
        failure_reasons=(
            ()
            if passed
            else (
                "checkpoint_signing_secret_unavailable",
            )
        ),
    )


def build_environment_preflight(
    *,
    release_environment: str = "paid_trial",
    passed: bool = True,
) -> GovernanceReleaseEnvironmentSecurityPreflightResult:
    return GovernanceReleaseEnvironmentSecurityPreflightResult(
        release_environment=release_environment,
        explicit_origins=passed,
        wildcard_origin_absent=passed,
        credentialed_cors_enabled=passed,
        assessment_identity_headers_allowed=passed,
        origin_count=(
            1
            if passed
            else 0
        ),
        passed=passed,
        failure_reasons=(
            ()
            if passed
            else (
                "explicit_origins_required",
            )
        ),
    )


def build_identity_preflight(
    *,
    release_environment: str = "paid_trial",
    passed: bool = True,
) -> GovernanceReleaseIdentityTenantBoundaryPreflightResult:
    return GovernanceReleaseIdentityTenantBoundaryPreflightResult(
        release_environment=release_environment,
        assessment_auth_version=ASSESSMENT_AUTH_VERSION,
        tenant_identity_required=passed,
        actor_identity_required=passed,
        actor_roles_required=passed,
        missing_identity_fails_closed=passed,
        deterministic_role_parsing=passed,
        tenant_scope_binding_enforced=passed,
        insufficient_role_fails_closed=passed,
        valid_identity_accepted=passed,
        passed=passed,
        failure_reasons=(
            ()
            if passed
            else (
                "missing_identity_fails_closed",
            )
        ),
    )


def build_redaction_proof(
    *,
    release_environment: str = "paid_trial",
    passed: bool = True,
) -> GovernanceReleaseSecretRedactionProofResult:
    return GovernanceReleaseSecretRedactionProofResult(
        release_environment=release_environment,
        public_status_available=passed,
        secret_value_redacted=passed,
        secret_variable_name_redacted=passed,
        secret_reference_redacted=passed,
        tenant_identifier_redacted=passed,
        key_identifier_redacted=passed,
        redaction_verified=passed,
        passed=passed,
        failure_reasons=(
            ()
            if passed
            else (
                "redaction_verification_required",
            )
        ),
    )


def build_invalid_configuration_proof(
    *,
    release_environment: str = "paid_trial",
    passed: bool = True,
) -> GovernanceReleaseInvalidSecurityConfigurationProofResult:
    return GovernanceReleaseInvalidSecurityConfigurationProofResult(
        release_environment=release_environment,
        scenarios=(),
        scenario_count=(
            7
            if passed
            else 6
        ),
        rejected_scenario_count=(
            7
            if passed
            else 6
        ),
        all_invalid_configurations_rejected=passed,
        passed=passed,
        failure_reasons=(
            ()
            if passed
            else (
                "missing_signing_secret_not_rejected",
            )
        ),
    )


def build_gate_kwargs(
) -> dict[str, object]:
    return {
        "secret_preflight":
            build_secret_preflight(),

        "environment_preflight":
            build_environment_preflight(),

        "identity_preflight":
            build_identity_preflight(),

        "redaction_proof":
            build_redaction_proof(),

        "invalid_configuration_proof":
            build_invalid_configuration_proof(),
    }


def evaluate(
    **overrides: object,
) -> GovernanceReleaseSecurityGateResult:
    kwargs = build_gate_kwargs()
    kwargs.update(
        overrides
    )

    return evaluate_governance_release_security_gate(
        secret_preflight=kwargs[
            "secret_preflight"
        ],
        environment_preflight=kwargs[
            "environment_preflight"
        ],
        identity_preflight=kwargs[
            "identity_preflight"
        ],
        redaction_proof=kwargs[
            "redaction_proof"
        ],
        invalid_configuration_proof=kwargs[
            "invalid_configuration_proof"
        ],
    )


def test_security_gate_passes_when_all_evidence_passes(
) -> None:
    result = evaluate()

    assert result.release_environment == "paid_trial"
    assert result.passed is True
    assert result.failure_reasons == ()

    assert all(
        result.checks.values()
    )


def test_security_gate_requires_paid_trial_environment(
) -> None:
    result = evaluate(
        secret_preflight=(
            build_secret_preflight(
                release_environment="prelive"
            )
        ),
        environment_preflight=(
            build_environment_preflight(
                release_environment="prelive"
            )
        ),
        identity_preflight=(
            build_identity_preflight(
                release_environment="prelive"
            )
        ),
        redaction_proof=(
            build_redaction_proof(
                release_environment="prelive"
            )
        ),
        invalid_configuration_proof=(
            build_invalid_configuration_proof(
                release_environment="prelive"
            )
        ),
    )

    assert result.passed is False
    assert result.failure_reasons == (
        "paid_trial_environment",
    )


@pytest.mark.parametrize(
    (
        "argument_name",
        "failed_value",
        "expected_failure",
    ),
    (
        (
            "secret_preflight",
            build_secret_preflight(
                passed=False
            ),
            "secret_preflight_passed",
        ),
        (
            "environment_preflight",
            build_environment_preflight(
                passed=False
            ),
            "environment_security_preflight_passed",
        ),
        (
            "identity_preflight",
            build_identity_preflight(
                passed=False
            ),
            "identity_tenant_boundary_preflight_passed",
        ),
        (
            "redaction_proof",
            build_redaction_proof(
                passed=False
            ),
            "secret_redaction_proof_passed",
        ),
        (
            "invalid_configuration_proof",
            build_invalid_configuration_proof(
                passed=False
            ),
            "invalid_security_configuration_proof_passed",
        ),
    ),
)
def test_security_gate_fails_when_component_evidence_fails(
    argument_name: str,
    failed_value: object,
    expected_failure: str,
) -> None:
    result = evaluate(
        **{
            argument_name:
                failed_value,
        }
    )

    assert result.passed is False

    assert (
        expected_failure
        in result.failure_reasons
    )


@pytest.mark.parametrize(
    (
        "argument_name",
        "mismatched_value",
        "expected_failure",
    ),
    (
        (
            "environment_preflight",
            build_environment_preflight(
                release_environment="prelive"
            ),
            "environment_preflight_matches_gate_environment",
        ),
        (
            "identity_preflight",
            build_identity_preflight(
                release_environment="prelive"
            ),
            "identity_preflight_matches_gate_environment",
        ),
        (
            "redaction_proof",
            build_redaction_proof(
                release_environment="prelive"
            ),
            "redaction_proof_matches_gate_environment",
        ),
        (
            "invalid_configuration_proof",
            build_invalid_configuration_proof(
                release_environment="prelive"
            ),
            "invalid_configuration_proof_matches_gate_environment",
        ),
    ),
)
def test_security_gate_rejects_environment_mismatch(
    argument_name: str,
    mismatched_value: object,
    expected_failure: str,
) -> None:
    result = evaluate(
        **{
            argument_name:
                mismatched_value,
        }
    )

    assert result.passed is False

    assert (
        expected_failure
        in result.failure_reasons
    )


def test_security_gate_public_projection_preserves_boundaries(
) -> None:
    payload = evaluate().to_dict()

    assert (
        payload["gate_type"]
        == GOVERNANCE_RELEASE_SECURITY_GATE_TYPE
    )

    assert (
        payload["version"]
        == GOVERNANCE_RELEASE_SECURITY_GATE_VERSION
    )

    assert payload[
        "release_environment"
    ] == "paid_trial"

    assert payload["passed"] is True
    assert payload["failure_reasons"] == []

    boundaries = payload[
        "boundaries"
    ]

    assert isinstance(
        boundaries,
        dict,
    )

    expected_boundaries = {
        "gate_is_read_only",
        "gate_evaluates_existing_evidence_only",
        "gate_does_not_resolve_secret_material",
        "gate_does_not_create_credentials",
        "gate_does_not_rotate_credentials",
        "gate_does_not_authenticate_actor",
        "gate_does_not_authorize_actor",
        "gate_is_not_deployment_activation",
        "gate_is_not_trial_authorization",
        "gate_is_not_production_activation",
        "gate_is_not_intervention_authority",
        "security_readiness_is_not_customer_trial_authority",
    }

    assert (
        set(
            boundaries
        )
        == expected_boundaries
    )

    assert all(
        value is True
        for value
        in boundaries.values()
    )


def test_security_gate_result_is_immutable(
) -> None:
    result = evaluate()

    with pytest.raises(
        FrozenInstanceError
    ):
        result.passed = False


@pytest.mark.parametrize(
    "argument_name",
    (
        "secret_preflight",
        "environment_preflight",
        "identity_preflight",
        "redaction_proof",
        "invalid_configuration_proof",
    ),
)
def test_security_gate_rejects_wrong_evidence_type(
    argument_name: str,
) -> None:
    kwargs = build_gate_kwargs()

    kwargs[
        argument_name
    ] = object()

    with pytest.raises(
        TypeError,
    ):
        evaluate_governance_release_security_gate(
            secret_preflight=kwargs[
                "secret_preflight"
            ],
            environment_preflight=kwargs[
                "environment_preflight"
            ],
            identity_preflight=kwargs[
                "identity_preflight"
            ],
            redaction_proof=kwargs[
                "redaction_proof"
            ],
            invalid_configuration_proof=kwargs[
                "invalid_configuration_proof"
            ],
        )