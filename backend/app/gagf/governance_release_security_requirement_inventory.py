from __future__ import annotations

from dataclasses import dataclass
from typing import Any


GOVERNANCE_RELEASE_SECURITY_REQUIREMENT_INVENTORY_TYPE = (
    "governance-release-security-requirement-inventory"
)

GOVERNANCE_RELEASE_SECURITY_REQUIREMENT_INVENTORY_VERSION = (
    "0.1.0"
)

SUPPORTED_RELEASE_ENVIRONMENTS = (
    "prelive",
    "paid_trial",
)


class GovernanceReleaseSecurityRequirementInventoryError(
    ValueError
):
    pass


@dataclass(
    frozen=True,
    slots=True,
)
class GovernanceReleaseSecurityRequirement:
    requirement_id: str
    category: str
    description: str
    verification_type: str

    required: bool = True
    secret_bearing: bool = False

    def to_dict(
        self,
    ) -> dict[str, Any]:
        return {
            "requirement_id":
                self.requirement_id,

            "category":
                self.category,

            "description":
                self.description,

            "verification_type":
                self.verification_type,

            "required":
                self.required,

            "secret_bearing":
                self.secret_bearing,
        }


@dataclass(
    frozen=True,
    slots=True,
)
class GovernanceReleaseSecurityRequirementInventory:
    release_environment: str
    requirements: tuple[
        GovernanceReleaseSecurityRequirement,
        ...,
    ]

    inventory_type: str = (
        GOVERNANCE_RELEASE_SECURITY_REQUIREMENT_INVENTORY_TYPE
    )

    version: str = (
        GOVERNANCE_RELEASE_SECURITY_REQUIREMENT_INVENTORY_VERSION
    )

    @property
    def requirement_count(
        self,
    ) -> int:
        return len(
            self.requirements
        )

    @property
    def required_count(
        self,
    ) -> int:
        return sum(
            1
            for requirement
            in self.requirements
            if requirement.required
        )

    @property
    def secret_bearing_requirement_count(
        self,
    ) -> int:
        return sum(
            1
            for requirement
            in self.requirements
            if requirement.secret_bearing
        )

    def to_public_dict(
        self,
    ) -> dict[str, Any]:
        return {
            "inventory_type":
                self.inventory_type,

            "version":
                self.version,

            "release_environment":
                self.release_environment,

            "requirement_count":
                self.requirement_count,

            "required_count":
                self.required_count,

            "secret_bearing_requirement_count":
                self.secret_bearing_requirement_count,

            "requirements": [
                requirement.to_dict()
                for requirement
                in self.requirements
            ],

            "boundaries": {
                "inventory_is_not_security_validation":
                    True,

                "inventory_is_not_secret_resolution":
                    True,

                "inventory_is_not_credential_validation":
                    True,

                "inventory_is_not_deployment_activation":
                    True,

                "inventory_is_not_trial_authorization":
                    True,

                "inventory_exposes_no_secret_material":
                    True,
            },
        }


def build_governance_release_security_requirement_inventory(
    *,
    release_environment: str,
) -> GovernanceReleaseSecurityRequirementInventory:
    normalized_environment = (
        _normalize_release_environment(
            release_environment
        )
    )

    requirements = (
        GovernanceReleaseSecurityRequirement(
            requirement_id="SEC-001",
            category="release_configuration",
            description=(
                "release environment must be "
                "explicitly selected"
            ),
            verification_type=(
                "environment_configuration"
            ),
        ),

        GovernanceReleaseSecurityRequirement(
            requirement_id="SEC-002",
            category="release_configuration",
            description=(
                "release data root must be explicit "
                "and environment isolated"
            ),
            verification_type=(
                "storage_configuration"
            ),
        ),

        GovernanceReleaseSecurityRequirement(
            requirement_id="SEC-003",
            category="request_identity",
            description=(
                "assessment requests must provide "
                "tenant identity"
            ),
            verification_type="http_header",
        ),

        GovernanceReleaseSecurityRequirement(
            requirement_id="SEC-004",
            category="request_identity",
            description=(
                "assessment requests must provide "
                "actor identity"
            ),
            verification_type="http_header",
        ),

        GovernanceReleaseSecurityRequirement(
            requirement_id="SEC-005",
            category="request_identity",
            description=(
                "assessment requests must provide "
                "actor role evidence"
            ),
            verification_type="http_header",
        ),

        GovernanceReleaseSecurityRequirement(
            requirement_id="SEC-006",
            category="tenant_isolation",
            description=(
                "request tenant identity must remain "
                "bound to the requested tenant scope"
            ),
            verification_type=(
                "tenant_boundary_validation"
            ),
        ),

        GovernanceReleaseSecurityRequirement(
            requirement_id="SEC-007",
            category="authentication_failure",
            description=(
                "missing required assessment identity "
                "must fail closed"
            ),
            verification_type=(
                "negative_http_probe"
            ),
        ),

        GovernanceReleaseSecurityRequirement(
            requirement_id="SEC-008",
            category="secret_management",
            description=(
                "required signing or credential "
                "material must resolve through an "
                "approved runtime secret source"
            ),
            verification_type=(
                "secret_resolution"
            ),
            secret_bearing=True,
        ),

        GovernanceReleaseSecurityRequirement(
            requirement_id="SEC-009",
            category="secret_management",
            description=(
                "secret material must never appear "
                "in public release status output"
            ),
            verification_type=(
                "redaction_validation"
            ),
            secret_bearing=True,
        ),

        GovernanceReleaseSecurityRequirement(
            requirement_id="SEC-010",
            category="cors",
            description=(
                "browser origins must be explicitly "
                "constrained for the release runtime"
            ),
            verification_type=(
                "cors_configuration"
            ),
        ),

        GovernanceReleaseSecurityRequirement(
            requirement_id="SEC-011",
            category="cors",
            description=(
                "assessment identity headers must be "
                "explicitly permitted when browser "
                "access is enabled"
            ),
            verification_type=(
                "cors_configuration"
            ),
        ),

        GovernanceReleaseSecurityRequirement(
            requirement_id="SEC-012",
            category="environment_safety",
            description=(
                "release runtime must reject unsafe "
                "or incomplete security configuration"
            ),
            verification_type=(
                "negative_runtime_probe"
            ),
        ),
    )

    return (
        GovernanceReleaseSecurityRequirementInventory(
            release_environment=(
                normalized_environment
            ),
            requirements=requirements,
        )
    )


def _normalize_release_environment(
    value: object,
) -> str:
    if not isinstance(
        value,
        str,
    ):
        raise (
            GovernanceReleaseSecurityRequirementInventoryError(
                "release_environment must be a string"
            )
        )

    normalized = (
        value
        .strip()
        .lower()
    )

    if not normalized:
        raise (
            GovernanceReleaseSecurityRequirementInventoryError(
                "release_environment must not be empty"
            )
        )

    if (
        normalized
        not in SUPPORTED_RELEASE_ENVIRONMENTS
    ):
        raise (
            GovernanceReleaseSecurityRequirementInventoryError(
                "security requirement inventory "
                "supports only prelive and paid_trial"
            )
        )

    return normalized