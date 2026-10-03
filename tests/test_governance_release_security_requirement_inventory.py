import json

import pytest

from backend.app.gagf.governance_release_security_requirement_inventory import (
    GovernanceReleaseSecurityRequirementInventoryError,
    build_governance_release_security_requirement_inventory,
)


def test_paid_trial_inventory_is_complete() -> None:
    inventory = (
        build_governance_release_security_requirement_inventory(
            release_environment="paid_trial"
        )
    )

    assert (
        inventory.release_environment
        == "paid_trial"
    )

    assert (
        inventory.requirement_count
        == 12
    )

    assert (
        inventory.required_count
        == 12
    )

    assert (
        inventory.secret_bearing_requirement_count
        == 2
    )


def test_prelive_inventory_uses_same_security_baseline() -> None:
    prelive = (
        build_governance_release_security_requirement_inventory(
            release_environment="prelive"
        )
    )

    paid_trial = (
        build_governance_release_security_requirement_inventory(
            release_environment="paid_trial"
        )
    )

    assert (
        tuple(
            requirement.requirement_id
            for requirement
            in prelive.requirements
        )
        ==
        tuple(
            requirement.requirement_id
            for requirement
            in paid_trial.requirements
        )
    )


def test_inventory_covers_required_security_categories() -> None:
    inventory = (
        build_governance_release_security_requirement_inventory(
            release_environment="paid_trial"
        )
    )

    categories = {
        requirement.category
        for requirement
        in inventory.requirements
    }

    assert categories == {
        "release_configuration",
        "request_identity",
        "tenant_isolation",
        "authentication_failure",
        "secret_management",
        "cors",
        "environment_safety",
    }


def test_inventory_is_deterministic() -> None:
    first = (
        build_governance_release_security_requirement_inventory(
            release_environment="paid_trial"
        )
    )

    second = (
        build_governance_release_security_requirement_inventory(
            release_environment="paid_trial"
        )
    )

    assert (
        first
        == second
    )

    assert (
        first.to_public_dict()
        == second.to_public_dict()
    )


def test_public_inventory_contains_no_secret_values() -> None:
    inventory = (
        build_governance_release_security_requirement_inventory(
            release_environment="paid_trial"
        )
    )

    payload = json.dumps(
        inventory.to_public_dict(),
        sort_keys=True,
    )

    assert (
        "secret_value"
        not in payload
    )

    assert (
        "private_key_value"
        not in payload
    )

    assert (
        "credential_value"
        not in payload
    )


def test_inventory_preserves_authority_boundaries() -> None:
    inventory = (
        build_governance_release_security_requirement_inventory(
            release_environment="paid_trial"
        )
    )

    boundaries = (
        inventory.to_public_dict()[
            "boundaries"
        ]
    )

    assert (
        boundaries[
            "inventory_is_not_security_validation"
        ]
        is True
    )

    assert (
        boundaries[
            "inventory_is_not_secret_resolution"
        ]
        is True
    )

    assert (
        boundaries[
            "inventory_is_not_credential_validation"
        ]
        is True
    )

    assert (
        boundaries[
            "inventory_is_not_deployment_activation"
        ]
        is True
    )

    assert (
        boundaries[
            "inventory_is_not_trial_authorization"
        ]
        is True
    )

    assert (
        boundaries[
            "inventory_exposes_no_secret_material"
        ]
        is True
    )


@pytest.mark.parametrize(
    "release_environment",
    (
        "",
        "development",
        "test",
        "production-ish",
    ),
)
def test_inventory_rejects_non_release_environment(
    release_environment: str,
) -> None:
    with pytest.raises(
        GovernanceReleaseSecurityRequirementInventoryError,
    ):
        build_governance_release_security_requirement_inventory(
            release_environment=(
                release_environment
            )
        )