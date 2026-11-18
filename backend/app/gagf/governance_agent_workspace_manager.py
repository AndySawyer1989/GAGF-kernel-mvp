from __future__ import annotations

import hashlib
import math
import re
import sqlite3
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class AgentWorkspaceError(Exception):
    """Base error for managed engineering workspaces."""


class AgentWorkspaceValidationError(AgentWorkspaceError):
    """Invalid workspace input or configuration."""


class AgentWorkspaceConflictError(AgentWorkspaceError):
    """Workspace allocation conflicts with existing state."""


class AgentWorkspaceNotFoundError(AgentWorkspaceError):
    """Workspace does not exist for the requested tenant."""


class AgentWorkspaceGitError(AgentWorkspaceError):
    """Git worktree operation failed."""


class AgentWorkspaceIntegrityError(AgentWorkspaceError):
    """Persisted workspace state is invalid or inconsistent."""


@dataclass(frozen=True)
class AgentWorkspaceRecord:
    workspace_id: str
    tenant_id: str
    work_item_id: str
    repository_path: str
    git_common_dir: str
    workspace_path: str
    branch_name: str
    base_commit: str
    state: str
    created_at: datetime
    updated_at: datetime
    error_message: str | None = None


class AgentWorkspaceManager:
    """
    Tenant-scoped Git worktree allocation and lifecycle persistence.

    This class does not execute worker code and does not provide an OS-level
    sandbox. A Git worktree isolates checkout state, not process permissions,
    filesystem access, or network access.
    """

    _SCHEMA_VERSION = 1
    _MAX_IDENTIFIER_LENGTH = 200
    _GIT_TIMEOUT_SECONDS = 30

    def __init__(
        self,
        repository_path: str | Path,
        workspace_root: str | Path,
        *,
        timeout_seconds: float = 10.0,
    ) -> None:
        if (
            isinstance(timeout_seconds, bool)
            or not isinstance(timeout_seconds, (int, float))
            or not math.isfinite(timeout_seconds)
            or timeout_seconds <= 0
        ):
            raise AgentWorkspaceValidationError(
                "timeout_seconds must be a finite positive number"
            )

        self.timeout_seconds = float(timeout_seconds)

        requested_repository = Path(repository_path).expanduser().resolve()
        if not requested_repository.is_dir():
            raise AgentWorkspaceValidationError(
                "repository_path must be an existing directory"
            )

        self.repository_path = self._git_path(
            requested_repository,
            ["rev-parse", "--show-toplevel"],
        )

        common_dir_value = self._git(
            ["rev-parse", "--git-common-dir"]
        ).strip()
        common_dir = Path(common_dir_value)
        if not common_dir.is_absolute():
            common_dir = self.repository_path / common_dir
        self.git_common_dir = common_dir.resolve()

        requested_root = Path(workspace_root).expanduser().resolve()

        if requested_root == self.repository_path:
            raise AgentWorkspaceValidationError(
                "workspace_root must not equal the repository root"
            )

        if (
            self._is_within(requested_root, self.repository_path)
            or self._is_within(self.repository_path, requested_root)
        ):
            raise AgentWorkspaceValidationError(
                "workspace_root must not overlap the repository"
            )

        if (
            requested_root == self.git_common_dir
            or self._is_within(requested_root, self.git_common_dir)
            or self._is_within(self.git_common_dir, requested_root)
        ):
            raise AgentWorkspaceValidationError(
                "workspace_root must not overlap the Git common directory"
            )

        self.workspace_root = requested_root
        self.metadata_root = self.workspace_root / ".gagf-manager"
        self.database_path = self.metadata_root / "workspaces.sqlite3"

        self.metadata_root.mkdir(parents=True, exist_ok=True)
        self._initialize()

    @staticmethod
    def _is_within(candidate: Path, parent: Path) -> bool:
        try:
            candidate.relative_to(parent)
            return True
        except ValueError:
            return False

    def _git(
        self,
        arguments: list[str],
        *,
        timeout: int | None = None,
    ) -> str:
        try:
            result = subprocess.run(
                ["git", *arguments],
                cwd=str(self.repository_path),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                check=False,
                shell=False,
                timeout=timeout or self._GIT_TIMEOUT_SECONDS,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise AgentWorkspaceGitError(
                f"Git command could not complete: {type(exc).__name__}"
            ) from exc

        if result.returncode != 0:
            detail = (result.stderr or result.stdout).strip()
            raise AgentWorkspaceGitError(
                f"Git command failed ({result.returncode}): {detail[:1000]}"
            )

        return result.stdout

    def _git_path(
        self,
        cwd: Path,
        arguments: list[str],
    ) -> Path:
        try:
            result = subprocess.run(
                ["git", *arguments],
                cwd=str(cwd),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                check=False,
                shell=False,
                timeout=self._GIT_TIMEOUT_SECONDS,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise AgentWorkspaceGitError(
                "Unable to identify the Git repository"
            ) from exc

        if result.returncode != 0:
            raise AgentWorkspaceGitError(
                (result.stderr or result.stdout).strip()[:1000]
            )

        return Path(result.stdout.strip()).resolve()

    @staticmethod
    def _validate_identifier(value: str, field_name: str) -> str:
        if not isinstance(value, str):
            raise AgentWorkspaceValidationError(
                f"{field_name} must be a string"
            )

        normalized = value.strip()

        if (
            not normalized
            or len(normalized) > AgentWorkspaceManager._MAX_IDENTIFIER_LENGTH
            or any(ord(character) < 32 for character in normalized)
        ):
            raise AgentWorkspaceValidationError(
                f"{field_name} is invalid"
            )

        return normalized

    @staticmethod
    def _utc_now() -> datetime:
        return datetime.now(timezone.utc)

    @staticmethod
    def _serialize_time(value: datetime) -> str:
        if value.tzinfo is None or value.utcoffset() is None:
            raise AgentWorkspaceValidationError(
                "Timestamp must be timezone-aware"
            )
        return value.astimezone(timezone.utc).isoformat()

    @staticmethod
    def _parse_time(value: str) -> datetime:
        try:
            parsed = datetime.fromisoformat(value)
        except (TypeError, ValueError) as exc:
            raise AgentWorkspaceIntegrityError(
                "Persisted workspace timestamp is invalid"
            ) from exc

        if parsed.tzinfo is None or parsed.utcoffset() is None:
            raise AgentWorkspaceIntegrityError(
                "Persisted workspace timestamp is not timezone-aware"
            )

        return parsed.astimezone(timezone.utc)

    @staticmethod
    def _identity_digest(tenant_id: str, work_item_id: str) -> str:
        payload = f"{tenant_id}\0{work_item_id}".encode("utf-8")
        return hashlib.sha256(payload).hexdigest()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(
            str(self.database_path),
            timeout=self.timeout_seconds,
            isolation_level=None,
        )
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute(
            f"PRAGMA busy_timeout = {int(self.timeout_seconds * 1000)}"
        )
        return connection

    def _initialize(self) -> None:
        connection = self._connect()
        try:
            connection.execute("BEGIN IMMEDIATE")
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS gagf_agent_workspaces (
                    workspace_id TEXT PRIMARY KEY,
                    tenant_id TEXT NOT NULL,
                    work_item_id TEXT NOT NULL,
                    repository_path TEXT NOT NULL,
                    git_common_dir TEXT NOT NULL,
                    workspace_path TEXT NOT NULL UNIQUE,
                    branch_name TEXT NOT NULL UNIQUE,
                    base_commit TEXT NOT NULL,
                    state TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    error_message TEXT,
                    UNIQUE (tenant_id, work_item_id)
                )
                """
            )
            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS
                    idx_gagf_agent_workspaces_tenant_state
                ON gagf_agent_workspaces (tenant_id, state, created_at)
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS gagf_agent_workspace_metadata (
                    metadata_key TEXT PRIMARY KEY,
                    metadata_value TEXT NOT NULL
                )
                """
            )

            row = connection.execute(
                """
                SELECT metadata_value
                FROM gagf_agent_workspace_metadata
                WHERE metadata_key = 'schema_version'
                """
            ).fetchone()

            if row is None:
                connection.execute(
                    """
                    INSERT INTO gagf_agent_workspace_metadata (
                        metadata_key, metadata_value
                    ) VALUES ('schema_version', ?)
                    """,
                    (str(self._SCHEMA_VERSION),),
                )
            elif row["metadata_value"] != str(self._SCHEMA_VERSION):
                raise AgentWorkspaceIntegrityError(
                    "Unsupported workspace database schema version"
                )

            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    @staticmethod
    def _record(row: sqlite3.Row) -> AgentWorkspaceRecord:
        allowed_states = {"ALLOCATING", "ACTIVE", "FAILED", "RELEASED"}
        state = row["state"]

        if state not in allowed_states:
            raise AgentWorkspaceIntegrityError(
                f"Invalid persisted workspace state: {state}"
            )

        return AgentWorkspaceRecord(
            workspace_id=row["workspace_id"],
            tenant_id=row["tenant_id"],
            work_item_id=row["work_item_id"],
            repository_path=row["repository_path"],
            git_common_dir=row["git_common_dir"],
            workspace_path=row["workspace_path"],
            branch_name=row["branch_name"],
            base_commit=row["base_commit"],
            state=state,
            created_at=AgentWorkspaceManager._parse_time(
                row["created_at"]
            ),
            updated_at=AgentWorkspaceManager._parse_time(
                row["updated_at"]
            ),
            error_message=row["error_message"],
        )

    def _get_row(
        self,
        connection: sqlite3.Connection,
        *,
        tenant_id: str,
        work_item_id: str,
    ) -> sqlite3.Row | None:
        return connection.execute(
            """
            SELECT *
            FROM gagf_agent_workspaces
            WHERE tenant_id = ? AND work_item_id = ?
            """,
            (tenant_id, work_item_id),
        ).fetchone()

    def allocate_workspace(
        self,
        *,
        tenant_id: str,
        work_item_id: str,
    ) -> AgentWorkspaceRecord:
        tenant_id = self._validate_identifier(tenant_id, "tenant_id")
        work_item_id = self._validate_identifier(
            work_item_id, "work_item_id"
        )

        digest = self._identity_digest(tenant_id, work_item_id)
        workspace_id = f"ws_{digest[:24]}"
        branch_name = f"agent-work/{digest[:32]}"
        workspace_path = (
            self.workspace_root / "worktrees" / digest[:2] / digest
        ).resolve()

        if not self._is_within(workspace_path, self.workspace_root):
            raise AgentWorkspaceValidationError(
                "Calculated workspace path escaped workspace_root"
            )

        base_commit = self._git(["rev-parse", "HEAD"]).strip()
        if not re.fullmatch(r"[0-9a-fA-F]{40,64}", base_commit):
            raise AgentWorkspaceIntegrityError(
                "Git returned an invalid base commit identifier"
            )

        now = self._serialize_time(self._utc_now())
        connection = self._connect()

        try:
            connection.execute("BEGIN IMMEDIATE")

            existing = self._get_row(
                connection,
                tenant_id=tenant_id,
                work_item_id=work_item_id,
            )
            if existing is not None:
                raise AgentWorkspaceConflictError(
                    "A workspace record already exists for this tenant "
                    "and work item; inspect its state before recovery"
                )

            connection.execute(
                """
                INSERT INTO gagf_agent_workspaces (
                    workspace_id,
                    tenant_id,
                    work_item_id,
                    repository_path,
                    git_common_dir,
                    workspace_path,
                    branch_name,
                    base_commit,
                    state,
                    created_at,
                    updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'ALLOCATING', ?, ?)
                """,
                (
                    workspace_id,
                    tenant_id,
                    work_item_id,
                    str(self.repository_path),
                    str(self.git_common_dir),
                    str(workspace_path),
                    branch_name,
                    base_commit,
                    now,
                    now,
                ),
            )
            connection.commit()
        except sqlite3.IntegrityError as exc:
            connection.rollback()
            raise AgentWorkspaceConflictError(
                "Workspace identity or path is already registered"
            ) from exc
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

        try:
            workspace_path.parent.mkdir(parents=True, exist_ok=True)

            if workspace_path.exists():
                raise AgentWorkspaceConflictError(
                    "Workspace path already exists without a new allocation"
                )

            self._git(
                [
                    "worktree",
                    "add",
                    "-b",
                    branch_name,
                    str(workspace_path),
                    base_commit,
                ]
            )
        except Exception as exc:
            self._set_state(
                tenant_id=tenant_id,
                work_item_id=work_item_id,
                expected_state="ALLOCATING",
                new_state="FAILED",
                error_message=str(exc)[:1000],
            )
            raise

        self._set_state(
            tenant_id=tenant_id,
            work_item_id=work_item_id,
            expected_state="ALLOCATING",
            new_state="ACTIVE",
            error_message=None,
        )

        return self.get_workspace(
            tenant_id=tenant_id,
            work_item_id=work_item_id,
        )

    def _set_state(
        self,
        *,
        tenant_id: str,
        work_item_id: str,
        expected_state: str,
        new_state: str,
        error_message: str | None,
    ) -> None:
        connection = self._connect()
        try:
            connection.execute("BEGIN IMMEDIATE")
            cursor = connection.execute(
                """
                UPDATE gagf_agent_workspaces
                SET state = ?, updated_at = ?, error_message = ?
                WHERE tenant_id = ?
                  AND work_item_id = ?
                  AND state = ?
                """,
                (
                    new_state,
                    self._serialize_time(self._utc_now()),
                    error_message,
                    tenant_id,
                    work_item_id,
                    expected_state,
                ),
            )

            if cursor.rowcount != 1:
                raise AgentWorkspaceIntegrityError(
                    "Workspace state changed unexpectedly"
                )

            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def get_workspace(
        self,
        *,
        tenant_id: str,
        work_item_id: str,
    ) -> AgentWorkspaceRecord:
        tenant_id = self._validate_identifier(tenant_id, "tenant_id")
        work_item_id = self._validate_identifier(
            work_item_id, "work_item_id"
        )

        connection = self._connect()
        try:
            row = self._get_row(
                connection,
                tenant_id=tenant_id,
                work_item_id=work_item_id,
            )
            if row is None:
                raise AgentWorkspaceNotFoundError(
                    "Workspace not found for this tenant and work item"
                )
            return self._record(row)
        finally:
            connection.close()

    def list_workspaces(
        self,
        *,
        tenant_id: str,
        include_released: bool = False,
        limit: int = 100,
    ) -> tuple[AgentWorkspaceRecord, ...]:
        tenant_id = self._validate_identifier(tenant_id, "tenant_id")

        if (
            isinstance(limit, bool)
            or not isinstance(limit, int)
            or not 1 <= limit <= 500
        ):
            raise AgentWorkspaceValidationError(
                "limit must be an integer between 1 and 500"
            )

        if not isinstance(include_released, bool):
            raise AgentWorkspaceValidationError(
                "include_released must be a boolean"
            )

        connection = self._connect()
        try:
            if include_released:
                rows = connection.execute(
                    """
                    SELECT *
                    FROM gagf_agent_workspaces
                    WHERE tenant_id = ?
                    ORDER BY created_at, workspace_id
                    LIMIT ?
                    """,
                    (tenant_id, limit),
                ).fetchall()
            else:
                rows = connection.execute(
                    """
                    SELECT *
                    FROM gagf_agent_workspaces
                    WHERE tenant_id = ? AND state != 'RELEASED'
                    ORDER BY created_at, workspace_id
                    LIMIT ?
                    """,
                    (tenant_id, limit),
                ).fetchall()

            return tuple(self._record(row) for row in rows)
        finally:
            connection.close()

    def release_workspace(
        self,
        *,
        tenant_id: str,
        work_item_id: str,
    ) -> AgentWorkspaceRecord:
        tenant_id = self._validate_identifier(tenant_id, "tenant_id")
        work_item_id = self._validate_identifier(
            work_item_id, "work_item_id"
        )

        record = self.get_workspace(
            tenant_id=tenant_id,
            work_item_id=work_item_id,
        )

        if record.state != "ACTIVE":
            raise AgentWorkspaceConflictError(
                f"Only ACTIVE workspaces can be released; found "
                f"{record.state}"
            )

        workspace_path = Path(record.workspace_path).resolve()

        if not self._is_within(workspace_path, self.workspace_root):
            raise AgentWorkspaceIntegrityError(
                "Persisted workspace path escaped workspace_root"
            )

        if not workspace_path.exists():
            raise AgentWorkspaceIntegrityError(
                "Workspace directory is missing; manual recovery required"
            )

        # No --force: Git must refuse removal when the worktree has
        # uncommitted changes or otherwise cannot be safely removed.
        self._git(
            [
                "worktree",
                "remove",
                str(workspace_path),
            ]
        )

        self._set_state(
            tenant_id=tenant_id,
            work_item_id=work_item_id,
            expected_state="ACTIVE",
            new_state="RELEASED",
            error_message=None,
        )

        return self.get_workspace(
            tenant_id=tenant_id,
            work_item_id=work_item_id,
        )
