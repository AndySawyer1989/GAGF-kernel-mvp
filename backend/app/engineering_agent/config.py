from __future__ import annotations

import math
import os
from dataclasses import dataclass
from pathlib import Path


class EngineeringAgentConfigurationError(ValueError):
    """Raised when Engineering Agent configuration is invalid."""


@dataclass(frozen=True, slots=True)
class EngineeringAgentSettings:
    repository_path: Path
    workspace_root: Path
    data_root: Path
    database_timeout_seconds: float = 10.0
    application_name: str = "Engineering Agent"
    api_version: str = "1"

    def __post_init__(self) -> None:
        repository = Path(self.repository_path).expanduser().resolve()
        workspace = Path(self.workspace_root).expanduser().resolve()
        data = Path(self.data_root).expanduser().resolve()

        if not repository.is_dir():
            raise EngineeringAgentConfigurationError(
                "repository_path must identify an existing directory"
            )

        if self._overlaps(workspace, repository):
            raise EngineeringAgentConfigurationError(
                "workspace_root must not overlap the repository"
            )

        if self._overlaps(data, repository):
            raise EngineeringAgentConfigurationError(
                "data_root must not overlap the repository"
            )

        if self._overlaps(data, workspace):
            raise EngineeringAgentConfigurationError(
                "data_root and workspace_root must not overlap"
            )

        timeout = self.database_timeout_seconds

        if (
            isinstance(timeout, bool)
            or not isinstance(timeout, (int, float))
            or not math.isfinite(timeout)
            or timeout <= 0
        ):
            raise EngineeringAgentConfigurationError(
                "database_timeout_seconds must be a finite positive number"
            )

        if not isinstance(self.application_name, str) or not self.application_name.strip():
            raise EngineeringAgentConfigurationError(
                "application_name must be a non-empty string"
            )

        if not isinstance(self.api_version, str) or not self.api_version.strip():
            raise EngineeringAgentConfigurationError(
                "api_version must be a non-empty string"
            )

        object.__setattr__(self, "repository_path", repository)
        object.__setattr__(self, "workspace_root", workspace)
        object.__setattr__(self, "data_root", data)
        object.__setattr__(
            self,
            "database_timeout_seconds",
            float(timeout),
        )

    @staticmethod
    def _overlaps(first: Path, second: Path) -> bool:
        return (
            first == second
            or first in second.parents
            or second in first.parents
        )

    @property
    def workflow_database_path(self) -> Path:
        return self.data_root / "agent_workflows.db"

    @property
    def approval_database_path(self) -> Path:
        return self.data_root / "agent_approvals.db"

    @classmethod
    def from_environment(cls) -> EngineeringAgentSettings:
        required = {
            "ENGINEERING_AGENT_REPOSITORY_PATH":
                os.environ.get("ENGINEERING_AGENT_REPOSITORY_PATH"),
            "ENGINEERING_AGENT_WORKSPACE_ROOT":
                os.environ.get("ENGINEERING_AGENT_WORKSPACE_ROOT"),
            "ENGINEERING_AGENT_DATA_ROOT":
                os.environ.get("ENGINEERING_AGENT_DATA_ROOT"),
        }

        missing = [
            name
            for name, value in required.items()
            if not value or not value.strip()
        ]

        if missing:
            raise EngineeringAgentConfigurationError(
                "Missing required environment variables: "
                + ", ".join(missing)
            )

        return cls(
            repository_path=Path(
                required["ENGINEERING_AGENT_REPOSITORY_PATH"]
            ),
            workspace_root=Path(
                required["ENGINEERING_AGENT_WORKSPACE_ROOT"]
            ),
            data_root=Path(
                required["ENGINEERING_AGENT_DATA_ROOT"]
            ),
        )