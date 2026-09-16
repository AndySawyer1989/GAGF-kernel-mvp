from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.app.gagf.governance_release_storage_configuration import (
    load_governance_release_storage_configuration,
)
from backend.app.gagf.governance_release_storage_status_api import (
    create_governance_release_storage_status_router,
)


REPO_ROOT = (
    Path(__file__).resolve().parents[1]
)


def test_status_api_is_read_only_and_redacted(
    tmp_path: Path,
) -> None:
    configuration = (
        load_governance_release_storage_configuration(
            application_data_root=(
                tmp_path
                / "development"
            ),
            environment={},
        )
    )

    app = FastAPI()

    app.include_router(
        create_governance_release_storage_status_router(
            configuration=configuration
        )
    )

    client = TestClient(
        app
    )

    response = client.get(
        "/api/v1/governance-release/storage-status"
    )

    assert response.status_code == 200

    payload = response.json()

    assert (
        payload["authority"]
        == "READ_ONLY"
    )

    release_storage = (
        payload["release_storage"]
    )

    assert (
        release_storage[
            "release_environment"
        ]
        == "development"
    )

    assert (
        release_storage[
            "storage_paths_exposed"
        ]
        is False
    )

    serialized = str(
        payload
    )

    assert (
        str(
            configuration.data_root
        )
        not in serialized
    )

    assert (
        "assessment_database_path"
        not in serialized
    )

    assert (
        "controlled_trial_root"
        not in serialized
    )


def test_status_router_is_get_only(
    tmp_path: Path,
) -> None:
    configuration = (
        load_governance_release_storage_configuration(
            application_data_root=(
                tmp_path
                / "development"
            ),
            environment={},
        )
    )

    app = FastAPI()

    app.include_router(
        create_governance_release_storage_status_router(
            configuration=configuration
        )
    )

    paths = (
        TestClient(app)
        .get(
            "/openapi.json"
        )
        .json()[
            "paths"
        ]
    )

    route = (
        "/api/v1/governance-release/storage-status"
    )

    assert route in paths

    assert set(
        paths[route].keys()
    ) == {
        "get"
    }


def test_public_status_preserves_authority_boundaries(
    tmp_path: Path,
) -> None:
    configuration = (
        load_governance_release_storage_configuration(
            application_data_root=(
                tmp_path
                / "development"
            ),
            environment={},
        )
    )

    status = (
        configuration
        .to_public_status_dict()
    )

    boundaries = (
        status[
            "boundaries"
        ]
    )

    assert (
        boundaries[
            "status_is_observability_only"
        ]
        is True
    )

    assert (
        boundaries[
            "status_is_not_trial_authorization"
        ]
        is True
    )

    assert (
        boundaries[
            "status_is_not_execution_authority"
        ]
        is True
    )

    assert (
        boundaries[
            "status_does_not_expose_filesystem_paths"
        ]
        is True
    )


def test_main_exposes_paid_trial_redacted_status(
    tmp_path: Path,
) -> None:
    root = (
        tmp_path
        / "release-data"
    ).resolve()

    environment = os.environ.copy()

    environment[
        "GAGF_RELEASE_ENVIRONMENT"
    ] = "paid_trial"

    environment[
        "GAGF_RELEASE_DATA_ROOT"
    ] = str(
        root
    )

    code = r'''
from fastapi.testclient import TestClient
from backend.app.main import app

response = TestClient(app).get(
    "/api/v1/governance-release/storage-status"
)

print(response.status_code)
print(response.json())
'''

    result = subprocess.run(
        [
            sys.executable,
            "-c",
            code,
        ],
        cwd=REPO_ROOT,
        env=environment,
        text=True,
        capture_output=True,
        check=False,
    )

    assert (
        result.returncode
        == 0
    ), result.stderr

    lines = (
        result.stdout
        .strip()
        .splitlines()
    )

    assert "200" in lines

    output = (
        result.stdout
    )

    assert (
        "'release_environment': 'paid_trial'"
        in output
    )

    assert (
        "'explicit_data_root': True"
        in output
    )

    assert (
        "'environment_namespaced': True"
        in output
    )

    assert (
        str(root)
        not in output
    )