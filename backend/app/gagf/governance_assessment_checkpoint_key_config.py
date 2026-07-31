from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path


ASSESSMENT_CHECKPOINT_KEY_CONFIG_VERSION = "1.0.0"

ASSESSMENT_CHECKPOINT_TENANT_ENV = (
    "GAGF_ASSESSMENT_CHECKPOINT_TENANT_ID"
)
ASSESSMENT_CHECKPOINT_KEY_ID_ENV = (
    "GAGF_ASSESSMENT_CHECKPOINT_KEY_ID"
)
ASSESSMENT_CHECKPOINT_SECRET_REFERENCE_ENV = (
    "GAGF_ASSESSMENT_CHECKPOINT_SECRET_REFERENCE"
)


@dataclass(frozen=True)
class AssessmentCheckpointProductionKeyConfig:
    enabled: bool
    metadata_database_path: Path
    tenant_id: str | None = None
    key_id: str | None = None
    secret_reference: str | None = None


def load_assessment_checkpoint_production_key_config(
    *,
    assessment_database_path: str | Path,
    environment: Mapping[str, str],
) -> AssessmentCheckpointProductionKeyConfig:
    metadata_database_path = Path(
        assessment_database_path
    ).with_name(
        "governance_assessment_checkpoint_keys.sqlite3"
    )

    tenant_id = environment.get(
        ASSESSMENT_CHECKPOINT_TENANT_ENV
    )
    key_id = environment.get(
        ASSESSMENT_CHECKPOINT_KEY_ID_ENV
    )
    secret_reference = environment.get(
        ASSESSMENT_CHECKPOINT_SECRET_REFERENCE_ENV
    )

    values = (tenant_id, key_id, secret_reference)

    if all(value is None for value in values):
        return AssessmentCheckpointProductionKeyConfig(
            enabled=False,
            metadata_database_path=metadata_database_path,
        )

    if any(value is None for value in values):
        raise ValueError(
            "checkpoint signing configuration requires "
            "tenant ID, key ID, and secret reference"
        )

    normalized_tenant_id = tenant_id.strip()
    normalized_key_id = key_id.strip()
    normalized_secret_reference = secret_reference.strip()

    if not normalized_tenant_id:
        raise ValueError(
            "checkpoint signing tenant ID cannot be empty"
        )

    if not normalized_key_id:
        raise ValueError(
            "checkpoint signing key ID cannot be empty"
        )

    if not normalized_secret_reference:
        raise ValueError(
            "checkpoint signing secret reference cannot be empty"
        )

    return AssessmentCheckpointProductionKeyConfig(
        enabled=True,
        metadata_database_path=metadata_database_path,
        tenant_id=normalized_tenant_id,
        key_id=normalized_key_id,
        secret_reference=normalized_secret_reference,
    )
