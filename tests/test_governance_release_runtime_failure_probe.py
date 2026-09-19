from __future__ import annotations

import os
import socket
from pathlib import Path

from backend.app.gagf.governance_release_runtime_failure_probe import (
    probe_governance_release_runtime_failure,
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


def base_environment() -> dict[str, str]:
    environment = dict(
        os.environ
    )

    environment.pop(
        "GAGF_RELEASE_ENVIRONMENT",
        None,
    )

    environment.pop(
        "GAGF_RELEASE_DATA_ROOT",
        None,
    )

    return environment


def test_paid_trial_without_data_root_fails_process_start(
    tmp_path: Path,
) -> None:
    environment = (
        base_environment()
    )

    environment[
        "GAGF_RELEASE_ENVIRONMENT"
    ] = "paid_trial"

    receipt = (
        probe_governance_release_runtime_failure(
            repo_root=Path.cwd(),
            environment=environment,
            host="127.0.0.1",
            port=find_free_port(),
        )
    )

    assert (
        receipt.process_exited
        is True
    )

    assert (
        receipt.health_reached
        is False
    )

    assert (
        receipt.failure_proven
        is True
    )

    assert (
        receipt.exit_code
        is not None
    )

    assert (
        receipt.exit_code
        != 0
    )


def test_prelive_without_data_root_fails_process_start(
    tmp_path: Path,
) -> None:
    environment = (
        base_environment()
    )

    environment[
        "GAGF_RELEASE_ENVIRONMENT"
    ] = "prelive"

    receipt = (
        probe_governance_release_runtime_failure(
            repo_root=Path.cwd(),
            environment=environment,
            host="127.0.0.1",
            port=find_free_port(),
        )
    )

    assert (
        receipt.process_exited
        is True
    )

    assert (
        receipt.health_reached
        is False
    )

    assert (
        receipt.failure_proven
        is True
    )


def test_unsupported_release_environment_fails_process_start(
    tmp_path: Path,
) -> None:
    environment = (
        base_environment()
    )

    environment[
        "GAGF_RELEASE_ENVIRONMENT"
    ] = "production-ish"

    environment[
        "GAGF_RELEASE_DATA_ROOT"
    ] = str(
        (
            tmp_path
            / "release-data"
        ).resolve()
    )

    receipt = (
        probe_governance_release_runtime_failure(
            repo_root=Path.cwd(),
            environment=environment,
            host="127.0.0.1",
            port=find_free_port(),
        )
    )

    assert (
        receipt.process_exited
        is True
    )

    assert (
        receipt.health_reached
        is False
    )

    assert (
        receipt.failure_proven
        is True
    )


def test_failure_receipt_preserves_authority_boundaries(
    tmp_path: Path,
) -> None:
    environment = (
        base_environment()
    )

    environment[
        "GAGF_RELEASE_ENVIRONMENT"
    ] = "paid_trial"

    receipt = (
        probe_governance_release_runtime_failure(
            repo_root=Path.cwd(),
            environment=environment,
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
            "failure_probe_is_not_deployment_authority"
        ]
        is True
    )

    assert (
        boundaries[
            "failure_probe_is_not_trial_authorization"
        ]
        is True
    )

    assert (
        boundaries[
            "configuration_rejection_is_not_runtime_health"
        ]
        is True
    )

    assert (
        boundaries[
            "failed_start_must_not_fallback_to_development"
        ]
        is True
    )

    assert (
        boundaries[
            "failure_probe_does_not_mutate_release_storage"
        ]
        is True
    )