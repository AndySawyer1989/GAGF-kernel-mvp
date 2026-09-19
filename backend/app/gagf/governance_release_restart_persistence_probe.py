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

from backend.app.gagf.governance_assessment_isolation import (
    CommercialHierarchyContext,
)
from backend.app.gagf.governance_assessment_repository import (
    GovernanceAssessmentRepository,
)
from backend.app.gagf.governance_commercial_paid_assessment_execution import (
    GovernanceCommercialPaidAssessmentExecutionService,
)
from backend.app.gagf.governance_paid_assessment_lifecycle_persistence import (
    ACKNOWLEDGMENT_ARTIFACT_TYPE,
    CLIENT_RESPONSE_ARTIFACT_TYPE,
    DELIVERY_ARTIFACT_TYPE,
)
from backend.app.gagf.governance_release_storage_configuration import (
    GovernanceReleaseStorageConfiguration,
)


GOVERNANCE_RELEASE_RESTART_PERSISTENCE_PROBE_TYPE = (
    "governance-release-restart-persistence-probe"
)

GOVERNANCE_RELEASE_RESTART_PERSISTENCE_PROBE_VERSION = (
    "0.1.0"
)


class GovernanceReleaseRestartPersistenceError(
    RuntimeError
):
    pass


@dataclass(
    frozen=True,
    slots=True,
)
class GovernanceReleaseRestartPersistenceReceipt:
    tenant_id: str
    client_id: str
    engagement_id: str
    assessment_id: str

    current_stage: str
    pending_next_step: str

    lifecycle_artifact_count: int
    repository_chain_valid: bool

    first_runtime_healthy: bool
    second_runtime_healthy: bool

    persistence_proven: bool

    probe_type: str = (
        GOVERNANCE_RELEASE_RESTART_PERSISTENCE_PROBE_TYPE
    )

    version: str = (
        GOVERNANCE_RELEASE_RESTART_PERSISTENCE_PROBE_VERSION
    )

    @property
    def hierarchy_key(
        self,
    ) -> str:
        return "/".join(
            (
                self.tenant_id,
                self.client_id,
                self.engagement_id,
                self.assessment_id,
            )
        )

    def to_dict(
        self,
    ) -> dict[str, object]:
        return {
            "probe_type":
                self.probe_type,

            "version":
                self.version,

            "tenant_id":
                self.tenant_id,

            "client_id":
                self.client_id,

            "engagement_id":
                self.engagement_id,

            "assessment_id":
                self.assessment_id,

            "hierarchy_key":
                self.hierarchy_key,

            "current_stage":
                self.current_stage,

            "pending_next_step":
                self.pending_next_step,

            "lifecycle_artifact_count":
                self.lifecycle_artifact_count,

            "repository_chain_valid":
                self.repository_chain_valid,

            "first_runtime_healthy":
                self.first_runtime_healthy,

            "second_runtime_healthy":
                self.second_runtime_healthy,

            "persistence_proven":
                self.persistence_proven,

            "boundaries": {
                "persistence_is_not_lifecycle_transition_authority":
                    True,

                "persistence_is_not_deployment_authority":
                    True,

                "persistence_is_not_trial_authorization":
                    True,

                "persistence_is_not_production_activation":
                    True,

                "persistence_is_not_intervention_authority":
                    True,

                "probe_uses_normal_authenticated_http_boundary":
                    True,
            },
        }


def probe_governance_release_restart_persistence(
    *,
    repo_root: Path,
    configuration:
        GovernanceReleaseStorageConfiguration,
    environment: Mapping[str, str],
    host: str,
    port: int,
    tenant_id: str = "restart-tenant",
    client_id: str = "restart-client",
    engagement_id: str = "restart-engagement",
    assessment_id: str = "restart-assessment",
    startup_timeout_seconds: float = 15.0,
) -> GovernanceReleaseRestartPersistenceReceipt:
    resolved_repo_root = (
        Path(
            repo_root
        )
        .resolve()
    )

    if not resolved_repo_root.is_dir():
        raise GovernanceReleaseRestartPersistenceError(
            "repo root does not exist"
        )

    if not host.strip():
        raise GovernanceReleaseRestartPersistenceError(
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
        raise GovernanceReleaseRestartPersistenceError(
            "port must be between 1 and 65535"
        )

    if startup_timeout_seconds <= 0:
        raise GovernanceReleaseRestartPersistenceError(
            "startup timeout must be positive"
        )

    hierarchy = {
        "tenant_id":
            _require_text(
                tenant_id,
                "tenant_id",
            ),

        "client_id":
            _require_text(
                client_id,
                "client_id",
            ),

        "engagement_id":
            _require_text(
                engagement_id,
                "engagement_id",
            ),

        "assessment_id":
            _require_text(
                assessment_id,
                "assessment_id",
            ),
    }

    context = CommercialHierarchyContext(
        **hierarchy
    )

    execution_directory = (
        configuration.effective_data_root
        / "governance_paid_assessment_executions"
    )

    execution_service = (
        GovernanceCommercialPaidAssessmentExecutionService(
            execution_directory=execution_directory
        )
    )

    database_path = Path(
        execution_service.database_path_for_hierarchy(
            **hierarchy
        )
    )

    database_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    repository = GovernanceAssessmentRepository(
        database_path
    )

    repository.create_assessment(
        context=context,
        assessment_name=(
            "Restart Persistence Assessment"
        ),
        status="complete",
    )

    repository.append_artifact(
        context=context,
        artifact_type=(
            DELIVERY_ARTIFACT_TYPE
        ),
        payload={
            **hierarchy,

            "report_id":
                "restart-report-001",

            "delivery_event_id":
                "restart-delivery-001",

            "delivery_event_hash":
                "a" * 64,

            "delivery_status":
                "delivered",
        },
    )

    repository.append_artifact(
        context=context,
        artifact_type=(
            ACKNOWLEDGMENT_ARTIFACT_TYPE
        ),
        payload={
            **hierarchy,

            "report_id":
                "restart-report-001",

            "delivery_event_id":
                "restart-delivery-001",

            "delivery_event_hash":
                "a" * 64,

            "acknowledgment_id":
                "restart-ack-001",

            "acknowledgment_hash":
                "b" * 64,

            "acknowledgment_status":
                "client_receipt_acknowledged",
        },
    )

    repository.append_artifact(
        context=context,
        artifact_type=(
            CLIENT_RESPONSE_ARTIFACT_TYPE
        ),
        payload={
            **hierarchy,

            "report_id":
                "restart-report-001",

            "acknowledgment_id":
                "restart-ack-001",

            "acknowledgment_hash":
                "b" * 64,

            "response_status":
                "client_response_recorded",

            "findings_disposition":
                "acknowledged",

            "recommendations_disposition":
                "accepted",
        },
    )

    first_runtime_healthy = (
        _run_runtime_and_probe_health(
            repo_root=resolved_repo_root,
            environment=environment,
            host=host,
            port=port,
            startup_timeout_seconds=(
                startup_timeout_seconds
            ),
        )
    )

    lifecycle_payload = (
        _run_runtime_and_get_lifecycle(
            repo_root=resolved_repo_root,
            environment=environment,
            host=host,
            port=port,
            hierarchy=hierarchy,
            startup_timeout_seconds=(
                startup_timeout_seconds
            ),
        )
    )

    second_runtime_healthy = True

    current_stage = str(
        lifecycle_payload[
            "current_stage"
        ]
    )

    pending_next_step = str(
        lifecycle_payload[
            "pending_next_step"
        ]
    )

    lifecycle_artifact_count = int(
        lifecycle_payload[
            "lifecycle_artifact_count"
        ]
    )

    repository_chain_valid = bool(
        lifecycle_payload[
            "repository_chain_valid"
        ]
    )

    persistence_proven = (
        first_runtime_healthy
        and second_runtime_healthy
        and current_stage
        == "client_response_recorded"
        and pending_next_step
        == "none"
        and lifecycle_artifact_count
        == 3
        and repository_chain_valid
        is True
    )

    if not persistence_proven:
        raise GovernanceReleaseRestartPersistenceError(
            "post-restart PA-012 lifecycle "
            "persistence proof failed"
        )

    return (
        GovernanceReleaseRestartPersistenceReceipt(
            tenant_id=hierarchy[
                "tenant_id"
            ],
            client_id=hierarchy[
                "client_id"
            ],
            engagement_id=hierarchy[
                "engagement_id"
            ],
            assessment_id=hierarchy[
                "assessment_id"
            ],
            current_stage=current_stage,
            pending_next_step=(
                pending_next_step
            ),
            lifecycle_artifact_count=(
                lifecycle_artifact_count
            ),
            repository_chain_valid=(
                repository_chain_valid
            ),
            first_runtime_healthy=(
                first_runtime_healthy
            ),
            second_runtime_healthy=(
                second_runtime_healthy
            ),
            persistence_proven=True,
        )
    )


def _run_runtime_and_probe_health(
    *,
    repo_root: Path,
    environment: Mapping[str, str],
    host: str,
    port: int,
    startup_timeout_seconds: float,
) -> bool:
    process = _start_process(
        repo_root=repo_root,
        environment=environment,
        host=host,
        port=port,
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

        status, _ = _get_json(
            host=host,
            port=port,
            path="/health",
        )

        return status == 200

    finally:
        _terminate_process(
            process
        )


def _run_runtime_and_get_lifecycle(
    *,
    repo_root: Path,
    environment: Mapping[str, str],
    host: str,
    port: int,
    hierarchy: Mapping[str, str],
    startup_timeout_seconds: float,
) -> dict[str, object]:
    process = _start_process(
        repo_root=repo_root,
        environment=environment,
        host=host,
        port=port,
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

        path = (
            "/api/v1/governance-paid-assessments/"
            f"{hierarchy['tenant_id']}/"
            f"{hierarchy['client_id']}/"
            f"{hierarchy['engagement_id']}/"
            f"{hierarchy['assessment_id']}/"
            "lifecycle-status"
        )

        status, payload = _get_json(
            host=host,
            port=port,
            path=path,
            headers={
                "X-Tenant-ID":
                    hierarchy[
                        "tenant_id"
                    ],

                "X-Actor-ID":
                    "release-restart-probe",

                "X-Actor-Roles":
                    "assessment:admin",
            },
        )

        if status != 200:
            raise GovernanceReleaseRestartPersistenceError(
                "post-restart lifecycle status "
                f"returned HTTP {status}"
            )

        return payload

    finally:
        _terminate_process(
            process
        )


def _start_process(
    *,
    repo_root: Path,
    environment: Mapping[str, str],
    host: str,
    port: int,
) -> subprocess.Popen[bytes]:
    return subprocess.Popen(
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
        cwd=Path(
            repo_root
        ).resolve(),
        env=dict(
            environment
        ),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
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
            raise GovernanceReleaseRestartPersistenceError(
                "runtime exited before becoming "
                f"healthy; exit_code={exit_code}"
            )

        try:
            status, _ = _get_json(
                host=host,
                port=port,
                path="/health",
            )

            if status == 200:
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

    raise GovernanceReleaseRestartPersistenceError(
        "runtime did not become healthy "
        "before timeout"
    ) from last_error


def _get_json(
    *,
    host: str,
    port: int,
    path: str,
    headers: Mapping[str, str] | None = None,
) -> tuple[
    int,
    dict[str, object],
]:
    url = (
        f"http://{host}:{port}{path}"
    )

    request = urllib.request.Request(
        url=url,
        method="GET",
        headers=dict(
            headers
            or {}
        ),
    )

    with urllib.request.urlopen(
        request,
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
            raise GovernanceReleaseRestartPersistenceError(
                "expected JSON object response"
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


def _require_text(
    value: object,
    field_name: str,
) -> str:
    if not isinstance(
        value,
        str,
    ):
        raise GovernanceReleaseRestartPersistenceError(
            f"{field_name} must be a string"
        )

    normalized = value.strip()

    if not normalized:
        raise GovernanceReleaseRestartPersistenceError(
            f"{field_name} must not be empty"
        )

    return normalized