from dataclasses import FrozenInstanceError

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.app.gagf.tenant_application_router_registry import (
    TENANT_APPLICATION_ROUTER_REGISTRY_ID,
    TENANT_APPLICATION_ROUTER_REGISTRY_VERSION,
    TenantApplicationDatabasePaths,
    register_tenant_application_routers,
)


def route_paths(app):
    return list(
        app.openapi()["paths"].keys()
    )

def build_application(tmp_path):
    app = FastAPI()

    paths = TenantApplicationDatabasePaths.from_directory(
        database_directory=tmp_path / "databases"
    )

    registration = register_tenant_application_routers(
        app=app,
        database_paths=paths,
    )

    return app, TestClient(app), paths, registration


def test_registry_has_stable_identity():
    assert TENANT_APPLICATION_ROUTER_REGISTRY_ID == (
        "tenant-application-router-registry"
    )
    assert TENANT_APPLICATION_ROUTER_REGISTRY_VERSION == (
        "0.1.0"
    )


def test_database_paths_are_derived_from_directory(
    tmp_path,
):
    directory = tmp_path / "databases"

    paths = TenantApplicationDatabasePaths.from_directory(
        database_directory=directory
    )

    assert paths.authority_database_path == (
        directory / "scientific-authority.db"
    )
    assert paths.audit_database_path == (
        directory / "scientific-audit.db"
    )
    assert paths.checkpoint_database_path == (
        directory / "scientific-checkpoints.db"
    )
    assert paths.journal_database_path == (
        directory / "scientific-journal.db"
    )
    assert paths.context_binding_database_path == (
        directory / "scientific-context-bindings.db"
    )
    assert paths.namespace_database_path == (
        directory / "tenant-artifact-namespaces.db"
    )
    assert paths.boundary_audit_database_path == (
        directory / "tenant-boundary-audit.db"
    )


def test_database_directory_is_created(tmp_path):
    directory = tmp_path / "nested" / "databases"

    paths = TenantApplicationDatabasePaths.from_directory(
        database_directory=directory
    )

    assert directory.exists() is False

    paths.ensure_directories()

    assert directory.exists() is True
    assert directory.is_dir() is True


def test_authority_api_paths_preserve_all_paths(
    tmp_path,
):
    paths = TenantApplicationDatabasePaths.from_directory(
        database_directory=tmp_path
    )

    authority_paths = paths.to_authority_api_paths()

    assert authority_paths.authority_database_path == (
        paths.authority_database_path
    )
    assert authority_paths.audit_database_path == (
        paths.audit_database_path
    )
    assert authority_paths.checkpoint_database_path == (
        paths.checkpoint_database_path
    )
    assert authority_paths.journal_database_path == (
        paths.journal_database_path
    )
    assert (
        authority_paths.context_binding_database_path
        == paths.context_binding_database_path
    )
    assert authority_paths.namespace_database_path == (
        paths.namespace_database_path
    )
    assert (
        authority_paths.boundary_audit_database_path
        == paths.boundary_audit_database_path
    )


def test_registration_returns_configuration_proof(
    tmp_path,
):
    _, _, paths, registration = build_application(
        tmp_path
    )

    assert registration.registered is True
    assert registration.registry_id == (
        TENANT_APPLICATION_ROUTER_REGISTRY_ID
    )
    assert registration.registry_version == (
        TENANT_APPLICATION_ROUTER_REGISTRY_VERSION
    )
    assert registration.database_paths == paths

    serialized = registration.to_dict()

    assert serialized["scientific_authority_prefix"] == (
        "/tenant-namespaced-scientific-authority"
    )
    assert serialized["boundary_audit_prefix"] == (
        "/tenant-boundary-audit"
    )


def test_scientific_authority_router_is_registered(
    tmp_path,
):
    app, _, _, _ = build_application(tmp_path)

    paths = set(route_paths(app))

    assert (
        "/tenant-namespaced-scientific-authority/"
        "evaluate"
    ) in paths

    assert (
        "/tenant-namespaced-scientific-authority/"
        "checkpoints/{public_id}"
    ) in paths


def test_boundary_audit_router_is_registered(
    tmp_path,
):
    app, _, _, _ = build_application(tmp_path)

    paths = set(route_paths(app))

    assert "/tenant-boundary-audit/records" in paths

    assert (
        "/tenant-boundary-audit/records/"
        "{public_record_id}"
    ) in paths


def test_missing_authority_headers_reach_real_router(
    tmp_path,
):
    _, client, _, _ = build_application(tmp_path)

    response = client.post(
        "/tenant-namespaced-scientific-authority/"
        "evaluate",
        json={},
    )

    assert response.status_code == 422


def test_missing_audit_headers_reach_real_router(
    tmp_path,
):
    _, client, _, _ = build_application(tmp_path)

    response = client.get(
        "/tenant-boundary-audit/records"
    )

    assert response.status_code == 422


def test_both_routers_share_boundary_audit_database(
    tmp_path,
):
    _, _, paths, _ = build_application(tmp_path)

    assert paths.boundary_audit_database_path.name == (
        "tenant-boundary-audit.db"
    )

    assert (
        paths.boundary_audit_database_path.parent
        == paths.authority_database_path.parent
    )


def test_registration_does_not_duplicate_routes(
    tmp_path,
):
    app, _, _, _ = build_application(tmp_path)

    schema_paths = app.openapi()["paths"]

    authority_path = (
        "/tenant-namespaced-scientific-authority/"
        "evaluate"
    )
    audit_path = "/tenant-boundary-audit/records"

    assert authority_path in schema_paths
    assert audit_path in schema_paths

    assert set(schema_paths[authority_path]) == {
        "post"
    }
    assert set(schema_paths[audit_path]) == {
        "get"
    }

def test_database_paths_are_immutable(tmp_path):
    paths = TenantApplicationDatabasePaths.from_directory(
        database_directory=tmp_path
    )

    with pytest.raises(FrozenInstanceError):
        paths.authority_database_path = (
            tmp_path / "changed.db"
        )


def test_registration_result_is_immutable(tmp_path):
    _, _, _, registration = build_application(
        tmp_path
    )

    with pytest.raises(FrozenInstanceError):
        registration.registered = False




