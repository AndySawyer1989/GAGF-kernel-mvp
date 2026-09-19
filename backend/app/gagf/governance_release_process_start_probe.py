from __future__ import annotations

import json
import subprocess
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping


GOVERNANCE_RELEASE_PROCESS_START_PROBE_TYPE = (
    "governance-release-process-start-probe"
)

GOVERNANCE_RELEASE_PROCESS_START_PROBE_VERSION = "0.1.0"


class GovernanceReleaseProcessStartError(RuntimeError):
    pass


@dataclass(
    frozen=True,
    slots=True,
)
class GovernanceReleaseProcessStartReceipt:
    host: str
    port: int
    health_status_code: int
    version_status_code: int
    storage_status_code: int
    release_environment: str
    storage_paths_exposed: bool

    probe_type: str = (
        GOVERNANCE_RELEASE_PROCESS_START_PROBE_TYPE
    )

    version: str = (
        GOVERNANCE_RELEASE_PROCESS_START_PROBE_VERSION
    )

    def to_dict(
        self,
    ) -> dict[str, object]:
        return {
            "probe_type":
                self.probe_type,

            "version":
                self.version,

            "host":
                self.host,

            "port":
                self.port,

            "health_status_code":
                self.health_status_code,

            "version_status_code":
                self.version_status_code,

            "storage_status_code":
                self.storage_status_code,

            "release_environment":
                self.release_environment,

            "storage_paths_exposed":
                self.storage_paths_exposed,

            "boundaries": {
                "process_start_is_not_deployment_authority":
                    True,

                "process_start_is_not_restart_proof":
                    True,

                "process_start_is_not_trial_authorization":
                    True,

                "process_start_is_not_production_activation":
                    True,

                "http_health_is_not_business_readiness":
                    True,
            },
        }


def probe_governance_release_process_start(
    *,
    repo_root: Path,
    environment: Mapping[str, str],
    host: str,
    port: int,
    startup_timeout_seconds: float = 15.0,
) -> GovernanceReleaseProcessStartReceipt:
    resolved_repo_root = (
        Path(
            repo_root
        )
        .resolve()
    )

    if not resolved_repo_root.is_dir():
        raise GovernanceReleaseProcessStartError(
            "repo root does not exist"
        )

    if not host.strip():
        raise GovernanceReleaseProcessStartError(
            "host must not be empty"
        )

    if (
        not isinstance(
            port,
            int,
        )
        or port < 1
        or port > 65535
    ):
        raise GovernanceReleaseProcessStartError(
            "port must be between 1 and 65535"
        )

    if startup_timeout_seconds <= 0:
        raise GovernanceReleaseProcessStartError(
            "startup timeout must be positive"
        )

    process_environment = dict(
        environment
    )

    command = [
        sys.executable,
        "-m",
        "uvicorn",
        "backend.app.main:app",
        "--host",
        host,
        "--port",
        str(
            port
        ),
        "--log-level",
        "warning",
    ]

    process = subprocess.Popen(
        command,
        cwd=resolved_repo_root,
        env=process_environment,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    try:
        _wait_for_health(
            process=process,
            host=host,
            port=port,
            timeout_seconds=(
                startup_timeout_seconds
            ),
        )

        health_status_code, _ = (
            _get_json(
                host=host,
                port=port,
                path="/health",
            )
        )

        version_status_code, _ = (
            _get_json(
                host=host,
                port=port,
                path="/version",
            )
        )

        (
            storage_status_code,
            storage_payload,
        ) = _get_json(
            host=host,
            port=port,
            path=(
                "/api/v1/governance-release/"
                "storage-status"
            ),
        )

        release_storage = (
            storage_payload[
                "release_storage"
            ]
        )

        return (
            GovernanceReleaseProcessStartReceipt(
                host=host,
                port=port,
                health_status_code=(
                    health_status_code
                ),
                version_status_code=(
                    version_status_code
                ),
                storage_status_code=(
                    storage_status_code
                ),
                release_environment=str(
                    release_storage[
                        "release_environment"
                    ]
                ),
                storage_paths_exposed=bool(
                    release_storage[
                        "storage_paths_exposed"
                    ]
                ),
            )
        )

    finally:
        _terminate_process(
            process
        )


def _wait_for_health(
    *,
    process: subprocess.Popen[bytes],
    host: str,
    port: int,
    timeout_seconds: float,
) -> None:
    deadline = (
        time.monotonic()
        + timeout_seconds
    )

    last_error: Exception | None = None

    while time.monotonic() < deadline:
        exit_code = process.poll()

        if exit_code is not None:
            raise GovernanceReleaseProcessStartError(
                "governance release process exited "
                f"before health check; exit_code="
                f"{exit_code}"
            )

        try:
            status_code, _ = _get_json(
                host=host,
                port=port,
                path="/health",
            )

            if status_code == 200:
                return

        except (
            urllib.error.URLError,
            ConnectionError,
            TimeoutError,
            json.JSONDecodeError,
        ) as exc:
            last_error = exc

        time.sleep(
            0.1
        )

    raise GovernanceReleaseProcessStartError(
        "governance release process did not "
        "become healthy before timeout"
    ) from last_error


def _get_json(
    *,
    host: str,
    port: int,
    path: str,
) -> tuple[
    int,
    dict[str, object],
]:
    url = (
        f"http://{host}:{port}{path}"
    )

    with urllib.request.urlopen(
        url,
        timeout=2.0,
    ) as response:
        payload = json.loads(
            response.read().decode(
                "utf-8"
            )
        )

        if not isinstance(
            payload,
            dict,
        ):
            raise GovernanceReleaseProcessStartError(
                "expected JSON object response: "
                f"{path}"
            )

        return (
            response.status,
            payload,
        )


def _terminate_process(
    process: subprocess.Popen[bytes],
) -> None:
    if process.poll() is not None:
        return

    process.terminate()

    try:
        process.wait(
            timeout=5.0
        )

    except subprocess.TimeoutExpired:
        process.kill()

        process.wait(
            timeout=5.0
        )