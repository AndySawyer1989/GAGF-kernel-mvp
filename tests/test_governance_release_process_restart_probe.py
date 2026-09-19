from __future__ import annotations

import os
import socket
from pathlib import Path

from backend.app.gagf.governance_release_process_restart_probe import (
    probe_governance_release_process_restart,
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


def test_paid_trial_process_restarts_successfully(
    tmp_path: Path,
) -> None:
    receipt = (
        probe_governance_release_process_restart(
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
        receipt.restart_succeeded
        is True
    )


def test_restart_uses_same_network_binding(
    tmp_path: Path,
) -> None:
    port = find_free_port()

    receipt = (
        probe_governance_release_process_restart(
            repo_root=Path.cwd(),
            environment=(
                build_paid_trial_environment(
                    tmp_path
                )
            ),
            host="127.0.0.1",
            port=port,
        )
    )

    assert (
        receipt.same_network_binding
        is True
    )

    assert (
        receipt.first_start.port
        == port
    )

    assert (
        receipt.second_start.port
        == port
    )


def test_restart_preserves_paid_trial_environment(
    tmp_path: Path,
) -> None:
    receipt = (
        probe_governance_release_process_restart(
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
        receipt.same_release_environment
        is True
    )

    assert (
        receipt.first_start.release_environment
        == "paid_trial"
    )

    assert (
        receipt.second_start.release_environment
        == "paid_trial"
    )

    assert (
        receipt.first_start.storage_paths_exposed
        is False
    )

    assert (
        receipt.second_start.storage_paths_exposed
        is False
    )


def test_restart_receipt_preserves_authority_boundaries(
    tmp_path: Path,
) -> None:
    receipt = (
        probe_governance_release_process_restart(
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
            "restart_is_not_state_persistence_proof"
        ]
        is True
    )

    assert (
        boundaries[
            "restart_is_not_deployment_authority"
        ]
        is True
    )

    assert (
        boundaries[
            "restart_is_not_trial_authorization"
        ]
        is True
    )

    assert (
        boundaries[
            "restart_is_not_production_activation"
        ]
        is True
    )

    assert (
        boundaries[
            "restart_does_not_grant_business_readiness"
        ]
        is True
    )