from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


REPO_ROOT = (
    Path(__file__).resolve().parents[1]
)


def run_http_preflight_probe(
    *,
    origin: str,
) -> subprocess.CompletedProcess[str]:
    probe_environment = os.environ.copy()

    for variable_name in (
        "GAGF_RELEASE_ENVIRONMENT",
        "GAGF_RELEASE_DATA_ROOT",
        "GAGF_RELEASE_CORS_ORIGINS",
    ):
        probe_environment.pop(
            variable_name,
            None,
        )

    release_root = (
        REPO_ROOT
        / ".pytest-cors-http-preflight"
    ).resolve()

    probe_environment.update(
        {
            "GAGF_RELEASE_ENVIRONMENT":
                "prelive",

            "GAGF_RELEASE_DATA_ROOT":
                str(
                    release_root
                ),

            "GAGF_RELEASE_CORS_ORIGINS":
                "https://operator.example.com",
        }
    )

    probe_environment[
        "GAGF_TEST_CORS_ORIGIN"
    ] = origin

    code = r'''
import os

from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)

response = client.options(
    "/api/v1/governance-release/storage-status",
    headers={
        "Origin":
            os.environ["GAGF_TEST_CORS_ORIGIN"],

        "Access-Control-Request-Method":
            "GET",

        "Access-Control-Request-Headers":
            (
                "X-Tenant-ID,"
                "X-Actor-ID,"
                "X-Actor-Roles"
            ),
    },
)

print(
    "STATUS="
    + str(
        response.status_code
    )
)

print(
    "ALLOW_ORIGIN="
    + response.headers.get(
        "access-control-allow-origin",
        ""
    )
)

print(
    "ALLOW_CREDENTIALS="
    + response.headers.get(
        "access-control-allow-credentials",
        ""
    )
)

print(
    "ALLOW_HEADERS="
    + response.headers.get(
        "access-control-allow-headers",
        ""
    )
)

print(
    "ALLOW_METHODS="
    + response.headers.get(
        "access-control-allow-methods",
        ""
    )
)
'''

    return subprocess.run(
        [
            sys.executable,
            "-c",
            code,
        ],
        cwd=REPO_ROOT,
        env=probe_environment,
        text=True,
        capture_output=True,
        check=False,
    )


def parse_probe(
    stdout: str,
) -> dict[str, str]:
    values: dict[str, str] = {}

    for line in stdout.splitlines():
        if "=" not in line:
            continue

        key, value = line.split(
            "=",
            1,
        )

        values[
            key.strip()
        ] = value.strip()

    return values


def test_approved_origin_passes_http_preflight(
) -> None:
    result = run_http_preflight_probe(
        origin="https://operator.example.com"
    )

    assert (
        result.returncode
        == 0
    ), result.stderr

    values = parse_probe(
        result.stdout
    )

    assert (
        values["STATUS"]
        == "200"
    )

    assert (
        values["ALLOW_ORIGIN"]
        == "https://operator.example.com"
    )

    assert (
        values["ALLOW_CREDENTIALS"].lower()
        == "true"
    )

    allowed_headers = {
        header.strip().lower()
        for header
        in values["ALLOW_HEADERS"].split(",")
        if header.strip()
    }

    assert "x-tenant-id" in allowed_headers
    assert "x-actor-id" in allowed_headers
    assert "x-actor-roles" in allowed_headers

    allowed_methods = {
        method.strip().upper()
        for method
        in values["ALLOW_METHODS"].split(",")
        if method.strip()
    }

    assert "GET" in allowed_methods


def test_unapproved_origin_is_not_granted_cors_access(
) -> None:
    result = run_http_preflight_probe(
        origin="https://unapproved.example.com"
    )

    assert (
        result.returncode
        == 0
    ), result.stderr

    values = parse_probe(
        result.stdout
    )

    assert (
        values["STATUS"]
        != "200"
    )

    assert (
        values["ALLOW_ORIGIN"]
        == ""
    )


def test_approved_origin_identity_headers_are_runtime_allowed(
) -> None:
    result = run_http_preflight_probe(
        origin="https://operator.example.com"
    )

    assert (
        result.returncode
        == 0
    ), result.stderr

    values = parse_probe(
        result.stdout
    )

    allowed_headers = (
        values["ALLOW_HEADERS"]
        .lower()
    )

    for required_header in (
        "x-tenant-id",
        "x-actor-id",
        "x-actor-roles",
    ):
        assert (
            required_header
            in allowed_headers
        )