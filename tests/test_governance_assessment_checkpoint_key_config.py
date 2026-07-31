import pytest

from backend.app.gagf.governance_assessment_checkpoint_key_config import (
    load_assessment_checkpoint_production_key_config,
)


def complete_environment():
    return {
        "GAGF_ASSESSMENT_CHECKPOINT_TENANT_ID": (
            "tenant-alpha"
        ),
        "GAGF_ASSESSMENT_CHECKPOINT_KEY_ID": "key-001",
        "GAGF_ASSESSMENT_CHECKPOINT_SECRET_REFERENCE": (
            "env://GAGF_ASSESSMENT_CHECKPOINT_SIGNING_SECRET"
        ),
    }


def test_complete_configuration_is_enabled(tmp_path):
    config = load_assessment_checkpoint_production_key_config(
        assessment_database_path=(
            tmp_path / "assessment.sqlite3"
        ),
        environment=complete_environment(),
    )

    assert config.enabled is True
    assert config.tenant_id == "tenant-alpha"
    assert config.key_id == "key-001"
    assert config.secret_reference == (
        "env://GAGF_ASSESSMENT_CHECKPOINT_SIGNING_SECRET"
    )


def test_metadata_database_is_sibling_of_assessment_database(
    tmp_path,
):
    config = load_assessment_checkpoint_production_key_config(
        assessment_database_path=(
            tmp_path / "assessment.sqlite3"
        ),
        environment=complete_environment(),
    )

    assert config.metadata_database_path == (
        tmp_path
        / "governance_assessment_checkpoint_keys.sqlite3"
    )


def test_absent_configuration_disables_signing(tmp_path):
    config = load_assessment_checkpoint_production_key_config(
        assessment_database_path=(
            tmp_path / "assessment.sqlite3"
        ),
        environment={},
    )

    assert config.enabled is False
    assert config.tenant_id is None
    assert config.key_id is None
    assert config.secret_reference is None


@pytest.mark.parametrize(
    "missing_name",
    [
        "GAGF_ASSESSMENT_CHECKPOINT_TENANT_ID",
        "GAGF_ASSESSMENT_CHECKPOINT_KEY_ID",
        "GAGF_ASSESSMENT_CHECKPOINT_SECRET_REFERENCE",
    ],
)
def test_partial_configuration_is_rejected(
    tmp_path,
    missing_name,
):
    environment = complete_environment()
    del environment[missing_name]

    with pytest.raises(
        ValueError,
        match="requires tenant ID, key ID, and secret reference",
    ):
        load_assessment_checkpoint_production_key_config(
            assessment_database_path=(
                tmp_path / "assessment.sqlite3"
            ),
            environment=environment,
        )


@pytest.mark.parametrize(
    ("name", "message"),
    [
        (
            "GAGF_ASSESSMENT_CHECKPOINT_TENANT_ID",
            "tenant ID cannot be empty",
        ),
        (
            "GAGF_ASSESSMENT_CHECKPOINT_KEY_ID",
            "key ID cannot be empty",
        ),
        (
            "GAGF_ASSESSMENT_CHECKPOINT_SECRET_REFERENCE",
            "secret reference cannot be empty",
        ),
    ],
)
def test_empty_configuration_value_is_rejected(
    tmp_path,
    name,
    message,
):
    environment = complete_environment()
    environment[name] = "   "

    with pytest.raises(ValueError, match=message):
        load_assessment_checkpoint_production_key_config(
            assessment_database_path=(
                tmp_path / "assessment.sqlite3"
            ),
            environment=environment,
        )


def test_configuration_values_are_trimmed(tmp_path):
    environment = complete_environment()
    environment[
        "GAGF_ASSESSMENT_CHECKPOINT_TENANT_ID"
    ] = "  tenant-alpha  "
    environment[
        "GAGF_ASSESSMENT_CHECKPOINT_KEY_ID"
    ] = "  key-001  "

    config = load_assessment_checkpoint_production_key_config(
        assessment_database_path=(
            tmp_path / "assessment.sqlite3"
        ),
        environment=environment,
    )

    assert config.tenant_id == "tenant-alpha"
    assert config.key_id == "key-001"
