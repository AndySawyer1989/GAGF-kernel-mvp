import pytest

from backend.app.gagf.governance_assessment_audit_checkpoint import (
    AssessmentAuditCheckpoint,
)
from backend.app.gagf.governance_assessment_checkpoint_key_bootstrap import (
    AssessmentCheckpointKeyBootstrapConfig,
    build_assessment_checkpoint_key_service,
)


def config(tmp_path, **overrides):
    values = {
        "metadata_database_path": tmp_path / "keys.sqlite3",
        "tenant_id": "tenant-alpha",
        "key_id": "key-001",
        "secret_reference": "env://GAGF_CHECKPOINT_KEY",
        "make_active": True,
    }
    values.update(overrides)
    return AssessmentCheckpointKeyBootstrapConfig(**values)


def checkpoint():
    return AssessmentAuditCheckpoint(
        checkpoint_id="checkpoint-001",
        tenant_id="tenant-alpha",
        chain_head_hash="a" * 64,
        checked_count=1,
        valid=True,
        reason_code=None,
        created_at="2026-07-30T00:00:00+00:00",
    )


def test_bootstrap_registers_active_environment_key(tmp_path):
    result = build_assessment_checkpoint_key_service(
        config=config(tmp_path),
        environment={
            "GAGF_CHECKPOINT_KEY": "private-secret"
        },
    )

    assert result.bootstrapped is True
    active = result.metadata_store.get_active_key(
        tenant_id="tenant-alpha"
    )
    assert active.key_id == "key-001"
    assert active.secret_reference == (
        "env://GAGF_CHECKPOINT_KEY"
    )


def test_bootstrapped_service_signs_checkpoint(tmp_path):
    result = build_assessment_checkpoint_key_service(
        config=config(tmp_path),
        environment={
            "GAGF_CHECKPOINT_KEY": "private-secret"
        },
    )

    signed = result.service.sign_checkpoint(
        checkpoint=checkpoint()
    )

    assert signed.key_id == "key-001"
    assert len(signed.signature) == 64


def test_bootstrap_is_idempotent_across_restart(tmp_path):
    environment = {
        "GAGF_CHECKPOINT_KEY": "private-secret"
    }

    first = build_assessment_checkpoint_key_service(
        config=config(tmp_path),
        environment=environment,
    )
    second = build_assessment_checkpoint_key_service(
        config=config(tmp_path),
        environment=environment,
    )

    assert first.bootstrapped is True
    assert second.bootstrapped is False
    assert len(second.metadata_store.list_keys(
        tenant_id="tenant-alpha"
    )) == 1


def test_restart_service_can_sign(tmp_path):
    environment = {
        "GAGF_CHECKPOINT_KEY": "private-secret"
    }

    build_assessment_checkpoint_key_service(
        config=config(tmp_path),
        environment=environment,
    )
    restarted = build_assessment_checkpoint_key_service(
        config=config(tmp_path),
        environment=environment,
    )

    signed = restarted.service.sign_checkpoint(
        checkpoint=checkpoint()
    )

    assert signed.key_id == "key-001"


def test_metadata_database_does_not_store_secret_value(tmp_path):
    result = build_assessment_checkpoint_key_service(
        config=config(tmp_path),
        environment={
            "GAGF_CHECKPOINT_KEY": "do-not-store-this"
        },
    )

    metadata = result.metadata_store.get_key(
        tenant_id="tenant-alpha",
        key_id="key-001",
    ).to_dict()

    assert "do-not-store-this" not in str(metadata)
    assert metadata["secret_reference"] == (
        "env://GAGF_CHECKPOINT_KEY"
    )


def test_bootstrap_rejects_missing_environment_secret(tmp_path):
    with pytest.raises(
        KeyError,
        match="signing secret was not found",
    ):
        build_assessment_checkpoint_key_service(
            config=config(tmp_path),
            environment={},
        )


def test_partial_bootstrap_configuration_is_rejected(tmp_path):
    with pytest.raises(
        ValueError,
        match="must all be provided",
    ):
        build_assessment_checkpoint_key_service(
            config=config(
                tmp_path,
                key_id=None,
            ),
            environment={
                "GAGF_CHECKPOINT_KEY": "private-secret"
            },
        )


def test_service_can_start_without_initial_key(tmp_path):
    result = build_assessment_checkpoint_key_service(
        config=AssessmentCheckpointKeyBootstrapConfig(
            metadata_database_path=tmp_path / "keys.sqlite3"
        ),
        environment={},
    )

    assert result.bootstrapped is False
    assert result.tenant_id is None
    assert result.key_id is None


def test_mismatched_existing_reference_is_rejected(tmp_path):
    environment = {
        "GAGF_CHECKPOINT_KEY": "private-secret",
        "GAGF_OTHER_KEY": "other-secret",
    }

    build_assessment_checkpoint_key_service(
        config=config(tmp_path),
        environment=environment,
    )

    with pytest.raises(
        ValueError,
        match="does not match bootstrap configuration",
    ):
        build_assessment_checkpoint_key_service(
            config=config(
                tmp_path,
                secret_reference="env://GAGF_OTHER_KEY",
            ),
            environment=environment,
        )
