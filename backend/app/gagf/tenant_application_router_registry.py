from dataclasses import dataclass
from pathlib import Path

from fastapi import FastAPI

from backend.app.gagf.tenant_boundary_audit_query_api import (
    create_tenant_boundary_audit_query_router,
)
from backend.app.gagf.tenant_namespaced_authority_api import (
    TenantNamespacedAuthorityApiPaths,
    create_tenant_namespaced_authority_router,
)


TENANT_APPLICATION_ROUTER_REGISTRY_ID = (
    "tenant-application-router-registry"
)
TENANT_APPLICATION_ROUTER_REGISTRY_VERSION = "0.1.0"


@dataclass(frozen=True, slots=True)
class TenantApplicationDatabasePaths:
    authority_database_path: Path
    audit_database_path: Path
    checkpoint_database_path: Path
    journal_database_path: Path
    context_binding_database_path: Path
    namespace_database_path: Path
    boundary_audit_database_path: Path

    @classmethod
    def from_directory(
        cls,
        *,
        database_directory: str | Path,
    ) -> "TenantApplicationDatabasePaths":
        directory = Path(database_directory)

        return cls(
            authority_database_path=(
                directory / "scientific-authority.db"
            ),
            audit_database_path=(
                directory / "scientific-audit.db"
            ),
            checkpoint_database_path=(
                directory / "scientific-checkpoints.db"
            ),
            journal_database_path=(
                directory / "scientific-journal.db"
            ),
            context_binding_database_path=(
                directory / "scientific-context-bindings.db"
            ),
            namespace_database_path=(
                directory / "tenant-artifact-namespaces.db"
            ),
            boundary_audit_database_path=(
                directory / "tenant-boundary-audit.db"
            ),
        )

    def ensure_directories(self) -> None:
        for database_path in self.to_dict().values():
            Path(database_path).parent.mkdir(
                parents=True,
                exist_ok=True,
            )

    def to_dict(self) -> dict[str, str]:
        return {
            "authority_database_path": str(
                self.authority_database_path
            ),
            "audit_database_path": str(
                self.audit_database_path
            ),
            "checkpoint_database_path": str(
                self.checkpoint_database_path
            ),
            "journal_database_path": str(
                self.journal_database_path
            ),
            "context_binding_database_path": str(
                self.context_binding_database_path
            ),
            "namespace_database_path": str(
                self.namespace_database_path
            ),
            "boundary_audit_database_path": str(
                self.boundary_audit_database_path
            ),
        }

    def to_authority_api_paths(
        self,
    ) -> TenantNamespacedAuthorityApiPaths:
        return TenantNamespacedAuthorityApiPaths(
            authority_database_path=(
                self.authority_database_path
            ),
            audit_database_path=(
                self.audit_database_path
            ),
            checkpoint_database_path=(
                self.checkpoint_database_path
            ),
            journal_database_path=(
                self.journal_database_path
            ),
            context_binding_database_path=(
                self.context_binding_database_path
            ),
            namespace_database_path=(
                self.namespace_database_path
            ),
            boundary_audit_database_path=(
                self.boundary_audit_database_path
            ),
        )


@dataclass(frozen=True, slots=True)
class TenantApplicationRouterRegistration:
    registry_id: str
    registry_version: str
    registered: bool
    scientific_authority_prefix: str
    boundary_audit_prefix: str
    database_paths: TenantApplicationDatabasePaths

    def to_dict(self) -> dict:
        return {
            "registry_id": self.registry_id,
            "registry_version": self.registry_version,
            "registered": self.registered,
            "scientific_authority_prefix": (
                self.scientific_authority_prefix
            ),
            "boundary_audit_prefix": (
                self.boundary_audit_prefix
            ),
            "database_paths": (
                self.database_paths.to_dict()
            ),
        }


def register_tenant_application_routers(
    *,
    app: FastAPI,
    database_paths: TenantApplicationDatabasePaths,
) -> TenantApplicationRouterRegistration:
    database_paths.ensure_directories()

    app.include_router(
        create_tenant_namespaced_authority_router(
            paths=(
                database_paths.to_authority_api_paths()
            )
        )
    )

    app.include_router(
        create_tenant_boundary_audit_query_router(
            database_path=(
                database_paths
                .boundary_audit_database_path
            )
        )
    )

    return TenantApplicationRouterRegistration(
        registry_id=(
            TENANT_APPLICATION_ROUTER_REGISTRY_ID
        ),
        registry_version=(
            TENANT_APPLICATION_ROUTER_REGISTRY_VERSION
        ),
        registered=True,
        scientific_authority_prefix=(
            "/tenant-namespaced-scientific-authority"
        ),
        boundary_audit_prefix=(
            "/tenant-boundary-audit"
        ),
        database_paths=database_paths,
    )
