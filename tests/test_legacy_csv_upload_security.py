from pathlib import Path

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from backend.app import main as main_module
from backend.app.gagf.governance_assessment_auth import AssessmentActorContext


@pytest.fixture
def csv_client(tmp_path, monkeypatch):
    calls = []

    async def verify_test_identity(request):
        if request.headers.get("authorization") != "Bearer test-csv":
            raise HTTPException(status_code=401, detail="test_credentials_required")

        return AssessmentActorContext(
            tenant_id="tenant-csv-security",
            actor_id="csv-test-actor",
            roles=("assessment:execute",),
        )

    class FakeIngestionService:
        def ingest_csv(self, file_path, *, tenant_id):
            path = Path(file_path)
            calls.append({
                "path": path,
                "tenant_id": tenant_id,
                "content": path.read_bytes(),
            })
            return {"status": "ingested", "tenant_id": tenant_id}

    monkeypatch.setattr(
        main_module.app.state,
        "assessment_identity_verifier",
        verify_test_identity,
        raising=False,
    )
    monkeypatch.setattr(
        main_module,
        "IngestionService",
        FakeIngestionService,
    )
    monkeypatch.chdir(tmp_path)

    with TestClient(main_module.app) as client:
        yield client, calls, tmp_path


def post_csv(client, filename, content):
    return client.post(
        "/upload-csv",
        headers={"Authorization": "Bearer test-csv"},
        files={"file": (filename, content, "text/csv")},
    )


def test_client_filename_cannot_control_disk_path(csv_client):
    client, calls, tmp_path = csv_client

    response = post_csv(
        client,
        "../../outside.csv",
        b"col1,col2\none,two\n",
    )

    assert response.status_code == 200, response.text
    assert len(calls) == 1
    assert calls[0]["tenant_id"] == "tenant-csv-security"
    assert calls[0]["content"] == b"col1,col2\none,two\n"
    assert calls[0]["path"].name == "upload.csv"
    assert calls[0]["path"].parent.name.startswith("gagf_csv_")
    assert not calls[0]["path"].exists()
    assert not calls[0]["path"].parent.exists()
    assert not (tmp_path / "outside.csv").exists()


def test_existing_upload_is_not_overwritten(csv_client):
    client, calls, tmp_path = csv_client

    uploads = tmp_path / "uploads"
    uploads.mkdir()
    original = uploads / "sample_events.csv"
    original.write_bytes(b"existing-important-records")

    response = post_csv(
        client,
        "sample_events.csv",
        b"new,file\none,two\n",
    )

    assert response.status_code == 200
    assert original.read_bytes() == b"existing-important-records"
    assert len(calls) == 1
    assert not calls[0]["path"].exists()


def test_oversized_upload_is_rejected(csv_client):
    client, calls, _ = csv_client

    response = post_csv(
        client,
        "large.csv",
        b"x" * (10 * 1024 * 1024 + 1),
    )

    assert response.status_code == 413
    assert response.json()["detail"] == "csv_upload_too_large"
    assert calls == []


def test_empty_upload_is_rejected(csv_client):
    client, calls, _ = csv_client

    response = post_csv(client, "empty.csv", b"")

    assert response.status_code == 400
    assert response.json()["detail"] == "csv_upload_empty"
    assert calls == []


def test_temporary_file_is_removed_when_ingestion_fails(
    csv_client, monkeypatch
):
    client, calls, _ = csv_client
    captured = []

    class FailingIngestionService:
        def ingest_csv(self, file_path, *, tenant_id):
            captured.append(Path(file_path))
            assert Path(file_path).is_file()
            raise RuntimeError("simulated ingestion failure")

    monkeypatch.setattr(
        main_module,
        "IngestionService",
        FailingIngestionService,
    )

    with pytest.raises(RuntimeError, match="simulated ingestion failure"):
        post_csv(client, "error.csv", b"col\nvalue\n")

    assert len(captured) == 1
    assert not captured[0].exists()
    assert not captured[0].parent.exists()
    assert calls == []


def test_missing_credentials_are_rejected(csv_client):
    client, calls, _ = csv_client

    response = client.post(
        "/upload-csv",
        files={"file": ("data.csv", b"a\nb\n", "text/csv")},
    )

    assert response.status_code == 401
    assert calls == []
