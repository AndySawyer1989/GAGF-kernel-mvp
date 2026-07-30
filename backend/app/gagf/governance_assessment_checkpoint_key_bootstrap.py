from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

from backend.app.gagf.governance_assessment_checkpoint_durable_key_service import (
    AssessmentCheckpointDurableKeyService,
)
from backend.app.gagf.governance_assessment_checkpoint_environment_secret_resolver import (
    EnvironmentAssessmentCheckpointSecretResolver,
)
from backend.app.gagf.governance_assessment_checkpoint_key_store import (
    AssessmentCheckpointSigningKeyMetadataStore,
)


ASSESSMENT_CHECKPOINT_KEY_BOOTSTRAP_VERSION = "1.0.0"


@dataclass(frozen=True)
class AssessmentCheckpointKeyBootstrapConfig:
    metadata_database_path: Path
    tenant_id: str | None = None
    key_id: str | None = None
    secret_reference: str | None = None
    make_active: bool = True


@dataclass(frozen=True)
class AssessmentCheckpointKeyBootstrapResult:
    service: AssessmentCheckpointDurableKeyService
    metadata_store: AssessmentCheckpointSigningKeyMetadataStore
    bootstrapped: bool
    tenant_id: str | None
    key_id: str | None


def build_assessment_checkpoint_key_service(
    *,
    config: AssessmentCheckpointKeyBootstrapConfig,
    environment: Mapping[str, str] | None = None,
) -> AssessmentCheckpointKeyBootstrapResult:
    metadata_store = AssessmentCheckpointSigningKeyMetadataStore(
        config.metadata_database_path
    )
    resolver = EnvironmentAssessmentCheckpointSecretResolver(
        environment=(
            environment
            if environment is not None
            else os.environ
        )
    )
    service = AssessmentCheckpointDurableKeyService(
        metadata_store=metadata_store,
        secret_resolver=resolver,
    )

    bootstrap_values = (
        config.tenant_id,
        config.key_id,
        config.secret_reference,
    )

    if all(value is None for value in bootstrap_values):
        return AssessmentCheckpointKeyBootstrapResult(
            service=service,
            metadata_store=metadata_store,
            bootstrapped=False,
            tenant_id=None,
            key_id=None,
        )

    if any(value is None for value in bootstrap_values):
        raise ValueError(
            "tenant_id, key_id, and secret_reference must "
            "all be provided for checkpoint key bootstrap"
        )

    assert config.tenant_id is not None
    assert config.key_id is not None
    assert config.secret_reference is not None

    try:
        existing = metadata_store.get_key(
            tenant_id=config.tenant_id,
            key_id=config.key_id,
        )
    except KeyError:
        service.register_key(
            tenant_id=config.tenant_id,
            key_id=config.key_id,
            secret_reference=config.secret_reference,
            make_active=config.make_active,
        )
        bootstrapped = True
    else:
        if existing.secret_reference != config.secret_reference:
            raise ValueError(
                "existing checkpoint key secret reference "
                "does not match bootstrap configuration"
            )

        if config.make_active and not existing.active:
            service.activate_key(
                tenant_id=config.tenant_id,
                key_id=config.key_id,
            )

        bootstrapped = False

    return AssessmentCheckpointKeyBootstrapResult(
        service=service,
        metadata_store=metadata_store,
        bootstrapped=bootstrapped,
        tenant_id=config.tenant_id,
        key_id=config.key_id,
    )
