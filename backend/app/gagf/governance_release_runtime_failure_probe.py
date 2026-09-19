from __future__ import annotations

import subprocess
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping


GOVERNANCE_RELEASE_RUNTIME_FAILURE_PROBE_TYPE = (
    "governance-release-runtime-failure-probe"
)

GOVERNANCE_RELEASE_RUNTIME_FAILURE_PROBE_VERSION = (
    "0.1.0"
)


class GovernanceReleaseRuntimeFailureProbeError(
    RuntimeError
):
    pass


@dataclass(
    frozen=True,
    slots=True,
)
class GovernanceReleaseRuntimeFailureReceipt:
    host: str
    port: int

    process_exited: bool
    health_reached: bool
    exit_code: int | None

    failure_proven: bool

    probe_type: str = (
        GOVERNANCE_RELEASE_RUNTIME_FAILURE_PROBE_TYPE
    )

    version: str = (
        GOVERNANCE_RELEASE_RUNTIME_FAILURE_PROBE_VERSION
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

            "process_exited":
                self.process_exited,

            "health_reached":
                self.health_reached,

            "exit_code":
                self.exit_code,

            "failure_proven":
                self.failure_proven,

            "boundaries": {
                "failure_probe_is_not_deployment_authority":
                    True,

                "failure_probe_is_not_trial_authorization":
                    True,

                "configuration_rejection_is_not_runtime_health":
                    True,

                "failed_start_must_not_fallback_to_development":
                    True,

                "failure_probe_does_not_mutate_release_storage":
                    True,
            },
        }


def probe_governance_release_runtime_failure(
    *,
    repo_root: Path,
    environment: Mapping[str, str],
    host: str,
    port: int,
    timeout_seconds: float = 8.0,
) -> GovernanceReleaseRuntimeFailureReceipt:
    resolved_repo_root = (
        Path(
            repo_root
        )
        .resolve()
    )

    if not resolved_repo_root.is_dir():
        raise GovernanceReleaseRuntimeFailureProbeError(
            "repo root does not exist"
        )

    if not host.strip():
        raise GovernanceReleaseRuntimeFailureProbeError(
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
        raise GovernanceReleaseRuntimeFailureProbeError(
            "port must be between 1 and 65535"
        )

    if timeout_seconds <= 0:
        raise GovernanceReleaseRuntimeFailureProbeError(
            "timeout must be positive"
        )

    process = subprocess.Popen(
        [
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
        ],
        cwd=resolved_repo_root,
        env=dict(
            environment
        ),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    try:
        deadline = (
            time.monotonic()
            + timeout_seconds
        )

        health_reached = False

        while time.monotonic() < deadline:
            exit_code = process.poll()

            if exit_code is not None:
                return (
                    GovernanceReleaseRuntimeFailureReceipt(
                        host=host,
                        port=port,
                        process_exited=True,
                        health_reached=False,
                        exit_code=exit_code,
                        failure_proven=True,
                    )
                )

            if _health_available(
                host=host,
                port=port,
            ):
                health_reached = True
                break

            time.sleep(
                0.1
            )

        if health_reached:
            raise GovernanceReleaseRuntimeFailureProbeError(
                "invalid release configuration "
                "unexpectedly reached health"
            )

        raise GovernanceReleaseRuntimeFailureProbeError(
            "runtime neither exited nor reached "
            "health before failure timeout"
        )

    finally:
        _terminate_process(
            process
        )


def _health_available(
    *,
    host: str,
    port: int,
) -> bool:
    try:
        with urllib.request.urlopen(
            f"http://{host}:{port}/health",
            timeout=0.5,
        ) as response:
            return (
                response.status
                == 200
            )

    except (
        urllib.error.URLError,
        ConnectionError,
        TimeoutError,
    ):
        return False


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