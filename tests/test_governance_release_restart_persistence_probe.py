from __future__ import annotations

import os
import socket
from pathlib import Path

from backend.app.gagf.governance_release_restart_persistence_probe import (
    probe_governance_release_restart_persistence,
)
from backend.app.gagf.governance_release_storage_configuration import (
    GAGF_RELEASE_DATA_ROOT_ENV,
    GAGF_RELEASE_ENVIRONMENT_ENV,
    load_governance_release_storage_configuration,
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


def build_environment(
    tmp_path: Path,
) -> dict[str, str]:
    environment = dict(
        os.environ
    )

    environment[
        GAGF_RELEASE_ENVIRONMENT_ENV
    ] = "paid_trial"

    environment[
        GAGF_RELEASE_DATA_ROOT_ENV
    ] = str(
        (
            tmp_path
            / "release-data"
        ).resolve()
    )

    return environment


def build_configuration(
    tmp_path: Path,
    environment: dict[str, str],
):
    return (
        load_governance_release_storage_configuration(
            application_data_root=(
                tmp_path
                / "development"
            ),
            environment=environment,
        )
    )


def test_pa012_lifecycle_survives_real_process_restart(
    tmp_path: Path,
) -> None:
    environment = build_environment(
        tmp_path
    )

    configuration = (
        build_configuration(
            tmp_path,
            environment,
        )
    )

    receipt = (
        probe_governance_release_restart_persistence(
            repo_root=Path.cwd(),
            configuration=configuration,
            environment=environment,
            host="127.0.0.1",
            port=find_free_port(),
        )
    )

    assert (
        receipt.persistence_proven
        is True
    )

    assert (
        receipt.first_runtime_healthy
        is True
    )

    assert (
        receipt.second_runtime_healthy
        is True
    )


def test_post_restart_projects_client_response_state(
    tmp_path: Path,
) -> None:
    environment = build_environment(
        tmp_path
    )

    configuration = (
        build_configuration(
            tmp_path,
            environment,
        )
    )

    receipt = (
        probe_governance_release_restart_persistence(
            repo_root=Path.cwd(),
            configuration=configuration,
            environment=environment,
            host="127.0.0.1",
            port=find_free_port(),
        )
    )

    assert (
        receipt.current_stage
        == "client_response_recorded"
    )

    assert (
        receipt.pending_next_step
        == "none"
    )

    assert (
        receipt.lifecycle_artifact_count
        == 3
    )

    assert (
        receipt.repository_chain_valid
        is True
    )


def test_restart_persistence_preserves_hierarchy_identity(
    tmp_path: Path,
) -> None:
    environment = build_environment(
        tmp_path
    )

    configuration = (
        build_configuration(
            tmp_path,
            environment,
        )
    )

    receipt = (
        probe_governance_release_restart_persistence(
            repo_root=Path.cwd(),
            configuration=configuration,
            environment=environment,
            host="127.0.0.1",
            port=find_free_port(),
            tenant_id="restart-tenant",
            client_id="restart-client",
            engagement_id="restart-engagement",
            assessment_id="restart-assessment",
        )
    )

    assert (
        receipt.hierarchy_key
        == (
            "restart-tenant/"
            "restart-client/"
            "restart-engagement/"
            "restart-assessment"
        )
    )


def test_restart_persistence_receipt_preserves_boundaries(
    tmp_path: Path,
) -> None:
    environment = build_environment(
        tmp_path
    )

    configuration = (
        build_configuration(
            tmp_path,
            environment,
        )
    )

    receipt = (
        probe_governance_release_restart_persistence(
            repo_root=Path.cwd(),
            configuration=configuration,
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
            "persistence_is_not_lifecycle_transition_authority"
        ]
        is True
    )

    assert (
        boundaries[
            "persistence_is_not_deployment_authority"
        ]
        is True
    )

    assert (
        boundaries[
            "persistence_is_not_trial_authorization"
        ]
        is True
    )

    assert (
        boundaries[
            "persistence_is_not_production_activation"
        ]
        is True
    )

    assert (
        boundaries[
            "persistence_is_not_intervention_authority"
        ]
        is True
    )