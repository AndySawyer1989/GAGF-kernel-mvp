from __future__ import annotations

import sqlite3
from dataclasses import replace
from pathlib import Path

from backend.app.gagf.governance_release_backup_integrity import (
    create_governance_release_backup_integrity_manifest,
)
from backend.app.gagf.governance_release_backup_package import (
    create_governance_release_backup_package,
)
from backend.app.gagf.governance_release_backup_recovery import (
    recover_governance_release_backup,
)
from backend.app.gagf.governance_release_backup_recovery_gate import (
    evaluate_governance_release_backup_recovery_gate,
)
from backend.app.gagf.governance_release_durable_storage_inventory import (
    build_governance_release_durable_storage_inventory,
)
from backend.app.gagf.governance_release_recovery_validation import (
    validate_governance_release_recovery,
)
from backend.app.gagf.governance_release_storage_configuration import (
    GAGF_RELEASE_DATA_ROOT_ENV,
    GAGF_RELEASE_ENVIRONMENT_ENV,
    RELEASE_ENVIRONMENT_PAID_TRIAL,
    load_governance_release_storage_configuration,
)


def build_gate_evidence(
    tmp_path: Path,
):
    configuration = (
        load_governance_release_storage_configuration(
            application_data_root=(
                tmp_path
                / "development"
            ),
            environment={
                GAGF_RELEASE_ENVIRONMENT_ENV:
                    RELEASE_ENVIRONMENT_PAID_TRIAL,

                GAGF_RELEASE_DATA_ROOT_ENV:
                    str(
                        (
                            tmp_path
                            / "release-data"
                        ).resolve()
                    ),
            },
        )
    )

    inventory = (
        build_governance_release_durable_storage_inventory(
            configuration=configuration
        )
    )

    for item in inventory.required_items:
        if item.storage_kind == "sqlite":
            item.path.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            connection = sqlite3.connect(
                item.path
            )

            try:
                connection.execute(
                    """
                    CREATE TABLE evidence (
                        value TEXT NOT NULL
                    )
                    """
                )

                connection.execute(
                    """
                    INSERT INTO evidence (
                        value
                    )
                    VALUES (?)
                    """,
                    (
                        item.name,
                    ),
                )

                connection.commit()

            finally:
                connection.close()

        elif item.storage_kind == "directory":
            item.path.mkdir(
                parents=True,
                exist_ok=True,
            )

            (
                item.path
                / "evidence.txt"
            ).write_text(
                item.name,
                encoding="utf-8",
            )

    backup_receipt = (
        create_governance_release_backup_package(
            inventory=inventory,
            backup_parent=(
                tmp_path
                / "backups"
            ),
            backup_id="backup-001",
        )
    )

    manifest = (
        create_governance_release_backup_integrity_manifest(
            backup_receipt=backup_receipt
        )
    )

    recovery_receipt = (
        recover_governance_release_backup(
            backup_root=(
                backup_receipt.backup_root
            ),
            restore_root=(
                tmp_path
                / "restore"
            ),
        )
    )

    validation_receipt = (
        validate_governance_release_recovery(
            restore_root=(
                recovery_receipt.restore_root
            ),
            manifest=manifest,
        )
    )

    return (
        inventory,
        backup_receipt,
        manifest,
        recovery_receipt,
        validation_receipt,
    )


def evaluate(
    evidence,
):
    (
        inventory,
        backup_receipt,
        manifest,
        recovery_receipt,
        validation_receipt,
    ) = evidence

    return (
        evaluate_governance_release_backup_recovery_gate(
            inventory=inventory,
            backup_receipt=backup_receipt,
            manifest=manifest,
            recovery_receipt=recovery_receipt,
            validation_receipt=validation_receipt,
        )
    )


def test_complete_backup_recovery_evidence_passes_gate(
    tmp_path: Path,
) -> None:
    result = evaluate(
        build_gate_evidence(
            tmp_path
        )
    )

    assert result.passed is True
    assert result.failure_reasons == ()

    assert all(
        result.checks.values()
    )


def test_environment_mismatch_fails_gate(
    tmp_path: Path,
) -> None:
    evidence = list(
        build_gate_evidence(
            tmp_path
        )
    )

    evidence[2] = replace(
        evidence[2],
        release_environment="prelive",
    )

    result = evaluate(
        tuple(
            evidence
        )
    )

    assert result.passed is False

    assert (
        "single_release_environment"
        in result.failure_reasons
    )


def test_backup_identity_mismatch_fails_gate(
    tmp_path: Path,
) -> None:
    evidence = list(
        build_gate_evidence(
            tmp_path
        )
    )

    evidence[2] = replace(
        evidence[2],
        backup_id="different-backup",
    )

    result = evaluate(
        tuple(
            evidence
        )
    )

    assert result.passed is False

    assert (
        "single_backup_identity"
        in result.failure_reasons
    )


def test_recovery_hash_mismatch_fails_gate(
    tmp_path: Path,
) -> None:
    evidence = list(
        build_gate_evidence(
            tmp_path
        )
    )

    evidence[3] = replace(
        evidence[3],
        verified_package_sha256=(
            "0" * 64
        ),
    )

    result = evaluate(
        tuple(
            evidence
        )
    )

    assert result.passed is False

    assert (
        "recovery_hash_matches_manifest"
        in result.failure_reasons
    )


def test_validation_hash_mismatch_fails_gate(
    tmp_path: Path,
) -> None:
    evidence = list(
        build_gate_evidence(
            tmp_path
        )
    )

    evidence[4] = replace(
        evidence[4],
        source_package_sha256=(
            "f" * 64
        ),
    )

    result = evaluate(
        tuple(
            evidence
        )
    )

    assert result.passed is False

    assert (
        "validation_hash_matches_manifest"
        in result.failure_reasons
    )


def test_recovery_file_count_mismatch_fails_gate(
    tmp_path: Path,
) -> None:
    evidence = list(
        build_gate_evidence(
            tmp_path
        )
    )

    evidence[3] = replace(
        evidence[3],
        recovered_file_count=0,
    )

    result = evaluate(
        tuple(
            evidence
        )
    )

    assert result.passed is False

    assert (
        "recovery_file_count_matches_manifest"
        in result.failure_reasons
    )


def test_gate_preserves_authority_boundaries(
    tmp_path: Path,
) -> None:
    result = evaluate(
        build_gate_evidence(
            tmp_path
        )
    )

    boundaries = (
        result.to_dict()[
            "boundaries"
        ]
    )

    assert (
        boundaries[
            "gate_is_not_deployment_authority"
        ]
        is True
    )

    assert (
        boundaries[
            "gate_is_not_trial_authorization"
        ]
        is True
    )

    assert (
        boundaries[
            "gate_is_not_production_activation"
        ]
        is True
    )

    assert (
        boundaries[
            "gate_is_not_restore_execution"
        ]
        is True
    )

    assert (
        boundaries[
            "gate_is_not_backup_execution"
        ]
        is True
    )

    assert (
        boundaries[
            "gate_only_evaluates_existing_evidence"
        ]
        is True
    )