from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from backend.app.gagf.governance_assessment_checkpoint_key_config import (
    ASSESSMENT_CHECKPOINT_KEY_ID_ENV,
    ASSESSMENT_CHECKPOINT_SECRET_REFERENCE_ENV,
    ASSESSMENT_CHECKPOINT_TENANT_ENV,
)
from backend.app.gagf.governance_release_secret_preflight import (
    evaluate_governance_release_secret_preflight,
)


GOVERNANCE_RELEASE_SECRET_REDACTION_PROOF_TYPE = (
    "governance-release-secret-redaction-proof"
)

GOVERNANCE_RELEASE_SECRET_REDACTION_PROOF_VERSION = (
    "0.1.0"
)


@dataclass(
    frozen=True,
    slots=True,
)
class GovernanceReleaseSecretRedactionProofResult:
    release_environment: str

    public_status_available: bool

    secret_value_redacted: bool
    secret_variable_name_redacted: bool
    secret_reference_redacted: bool
    tenant_identifier_redacted: bool
    key_identifier_redacted: bool

    redaction_verified: bool

    passed: bool
    failure_reasons: tuple[str, ...]

    proof_type: str = (
        GOVERNANCE_RELEASE_SECRET_REDACTION_PROOF_TYPE
    )

    version: str = (
        GOVERNANCE_RELEASE_SECRET_REDACTION_PROOF_VERSION
    )

    def to_public_dict(
        self,
    ) -> dict[str, Any]:
        return {
            "proof_type":
                self.proof_type,

            "version":
                self.version,

            "release_environment":
                self.release_environment,

            "public_status_available":
                self.public_status_available,

            "secret_value_redacted":
                self.secret_value_redacted,

            "secret_variable_name_redacted":
                self.secret_variable_name_redacted,

            "secret_reference_redacted":
                self.secret_reference_redacted,

            "tenant_identifier_redacted":
                self.tenant_identifier_redacted,

            "key_identifier_redacted":
                self.key_identifier_redacted,

            "redaction_verified":
                self.redaction_verified,

            "passed":
                self.passed,

            "failure_reasons":
                list(
                    self.failure_reasons
                ),

            "boundaries": {
                "proof_is_read_only":
                    True,

                "proof_uses_existing_secret_preflight":
                    True,

                "proof_does_not_return_secret_material":
                    True,

                "proof_does_not_return_secret_reference":
                    True,

                "proof_does_not_return_secret_variable_name":
                    True,

                "proof_does_not_return_signing_tenant_identifier":
                    True,

                "proof_does_not_return_signing_key_identifier":
                    True,

                "redaction_proof_is_not_credential_validity":
                    True,

                "redaction_proof_is_not_deployment_activation":
                    True,

                "redaction_proof_is_not_trial_authorization":
                    True,
            },
        }


def evaluate_governance_release_secret_redaction_proof(
    *,
    release_environment: str,
    assessment_database_path: str | Path,
    environment: Mapping[str, str],
) -> GovernanceReleaseSecretRedactionProofResult:
    preflight = (
        evaluate_governance_release_secret_preflight(
            release_environment=release_environment,
            assessment_database_path=assessment_database_path,
            environment=environment,
        )
    )

    public_status = (
        preflight.to_public_dict()
    )

    serialized_public_status = json.dumps(
        public_status,
        sort_keys=True,
    )

    tenant_identifier = _nonblank_value(
        environment,
        ASSESSMENT_CHECKPOINT_TENANT_ENV,
    )

    key_identifier = _nonblank_value(
        environment,
        ASSESSMENT_CHECKPOINT_KEY_ID_ENV,
    )

    secret_reference = _nonblank_value(
        environment,
        ASSESSMENT_CHECKPOINT_SECRET_REFERENCE_ENV,
    )

    secret_variable_name = (
        _secret_variable_name(
            secret_reference
        )
    )

    secret_value = (
        _nonblank_value(
            environment,
            secret_variable_name,
        )
        if secret_variable_name
        else None
    )

    public_status_available = (
        isinstance(
            public_status,
            dict,
        )
        and bool(
            public_status
        )
    )

    secret_value_redacted = (
        _value_is_absent(
            serialized_public_status,
            secret_value,
        )
    )

    secret_variable_name_redacted = (
        _value_is_absent(
            serialized_public_status,
            secret_variable_name,
        )
    )

    secret_reference_redacted = (
        _value_is_absent(
            serialized_public_status,
            secret_reference,
        )
    )

    tenant_identifier_redacted = (
        _value_is_absent(
            serialized_public_status,
            tenant_identifier,
        )
    )

    key_identifier_redacted = (
        _value_is_absent(
            serialized_public_status,
            key_identifier,
        )
    )

    redaction_verified = all(
        (
            public_status_available,
            secret_value_redacted,
            secret_variable_name_redacted,
            secret_reference_redacted,
            tenant_identifier_redacted,
            key_identifier_redacted,
        )
    )

    checks = {
        "public_status_required":
            public_status_available,

        "secret_value_redaction_required":
            secret_value_redacted,

        "secret_variable_name_redaction_required":
            secret_variable_name_redacted,

        "secret_reference_redaction_required":
            secret_reference_redacted,

        "tenant_identifier_redaction_required":
            tenant_identifier_redacted,

        "key_identifier_redaction_required":
            key_identifier_redacted,

        "redaction_verification_required":
            redaction_verified,
    }

    failure_reasons = tuple(
        name
        for name, passed
        in checks.items()
        if not passed
    )

    return GovernanceReleaseSecretRedactionProofResult(
        release_environment=(
            preflight.release_environment
        ),
        public_status_available=(
            public_status_available
        ),
        secret_value_redacted=(
            secret_value_redacted
        ),
        secret_variable_name_redacted=(
            secret_variable_name_redacted
        ),
        secret_reference_redacted=(
            secret_reference_redacted
        ),
        tenant_identifier_redacted=(
            tenant_identifier_redacted
        ),
        key_identifier_redacted=(
            key_identifier_redacted
        ),
        redaction_verified=(
            redaction_verified
        ),
        passed=(
            not failure_reasons
        ),
        failure_reasons=(
            failure_reasons
        ),
    )


def _nonblank_value(
    environment: Mapping[str, str],
    variable_name: str | None,
) -> str | None:
    if not variable_name:
        return None

    value = environment.get(
        variable_name
    )

    if not isinstance(
        value,
        str,
    ):
        return None

    normalized = (
        value.strip()
    )

    if not normalized:
        return None

    return normalized


def _secret_variable_name(
    secret_reference: str | None,
) -> str | None:
    if not secret_reference:
        return None

    prefix = "env://"

    if not secret_reference.startswith(
        prefix
    ):
        return None

    variable_name = (
        secret_reference[
            len(prefix):
        ]
        .strip()
    )

    if not variable_name:
        return None

    return variable_name


def _value_is_absent(
    serialized_public_status: str,
    sensitive_value: str | None,
) -> bool:
    if not sensitive_value:
        return True

    return (
        sensitive_value
        not in serialized_public_status
    )