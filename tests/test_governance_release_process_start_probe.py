from __future__ import annotations

import os
import socket
from pathlib import Path

from backend.app.gagf.governance_release_process_start_probe import (
    probe_governance_release_process_start,
)


def find_free_port() -> int:
    with socket.socket(
        socket.AF_INET,
        socket.SOCK_STREAM,
    ) as sock:
        sock.bind(
            (
                "127.0.0.1",
                0,
            )
        )

        return int(
            sock.getsockname()[
                1
            ]
        )


def build_paid_trial_environment(
    tmp_path: Path,
) -> dict[str, str]:
    environment = dict(
        os.environ
    )

    environment[
        "GAGF_RELEASE_ENVIRONMENT"
    ] = "paid_trial"

    environment[
        "GAGF_RELEASE_DATA_ROOT"
    ] = str(
        (
            tmp_path
            / "release-data"
        ).resolve()
    )

    return environment


def test_paid_trial_process_starts_and_exposes_health(
    tmp_path: Path,
) -> None:
    receipt = (
        probe_governance_release_process_start(
            repo_root=Path.cwd(),
            environment=(
                build_paid_trial_environment(
                    tmp_path
                )
            ),
            host="127.0.0.1",
            port=find_free_port(),
        )
    )

    assert (
        receipt.health_status_code
        == 200
    )


def test_paid_trial_process_exposes_version(
    tmp_path: Path,
) -> None:
    receipt = (
        probe_governance_release_process_start(
            repo_root=Path.cwd(),
            environment=(
                build_paid_trial_environment(
                    tmp_path
                )
            ),
            host="127.0.0.1",
            port=find_free_port(),
        )
    )

    assert (
        receipt.version_status_code
        == 200
    )


def test_paid_trial_process_uses_paid_trial_storage_configuration(
    tmp_path: Path,
) -> None:
    receipt = (
        probe_governance_release_process_start(
            repo_root=Path.cwd(),
            environment=(
                build_paid_trial_environment(
                    tmp_path
                )
            ),
            host="127.0.0.1",
            port=find_free_port(),
        )
    )

    assert (
        receipt.storage_status_code
        == 200
    )

    assert (
        receipt.release_environment
        == "paid_trial"
    )

    assert (
        receipt.storage_paths_exposed
        is False
    )


def test_process_start_receipt_preserves_authority_boundaries(
    tmp_path: Path,
) -> None:
    receipt = (
        probe_governance_release_process_start(
            repo_root=Path.cwd(),
            environment=(
                build_paid_trial_environment(
                    tmp_path
                )
            ),
            host="127.0.0.1",
            port=find_free_port(),
        )
    )

    boundaries = (
        receipt.to_dict()[
            "boundaries"
        ]
    )

    assert (
        boundaries[
            "process_start_is_not_deployment_authority"
        ]
        is True
    )

    assert (
        boundaries[
            "process_start_is_not_restart_proof"
        ]
        is True
    )

    assert (
        boundaries[
            "process_start_is_not_trial_authorization"
        ]
        is True
    )

    assert (
        boundaries[
            "process_start_is_not_production_activation"
        ]
        is True
    )

    assert (
        boundaries[
            "http_health_is_not_business_readiness"
        ]
        is True
    )