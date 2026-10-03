from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


REPO_ROOT = (
    Path(__file__).resolve().parents[1]
)


def run_main_probe(
    *,
    environment: dict[str, str],
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

    probe_environment.update(
        environment
    )

    code = r'''
from fastapi.middleware.cors import CORSMiddleware

from backend.app.main import app


config = (
    app.state
    .governance_release_cors_configuration
)

cors_middleware = next(
    middleware
    for middleware
    in app.user_middleware
    if middleware.cls is CORSMiddleware
)

print(
    "ENV="
    + config.release_environment
)

print(
    "EXPLICIT="
    + str(
        config.explicit_origins
    )
)

print(
    "CONFIG_ORIGINS="
    + "|".join(
        config.allow_origins
    )
)

print(
    "MIDDLEWARE_ORIGINS="
    + "|".join(
        cors_middleware.kwargs[
            "allow_origins"
        ]
    )
)

print(
    "CREDENTIALS="
    + str(
        cors_middleware.kwargs[
            "allow_credentials"
        ]
    )
)

print(
    "METHODS="
    + "|".join(
        cors_middleware.kwargs[
            "allow_methods"
        ]
    )
)

print(
    "HEADERS="
    + "|".join(
        cors_middleware.kwargs[
            "allow_headers"
        ]
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


def test_main_development_uses_authoritative_cors_configuration(
) -> None:
    result = run_main_probe(
        environment={}
    )

    assert (
        result.returncode
        == 0
    ), result.stderr

    values = parse_probe(
        result.stdout
    )

    expected_origins = (
        "http://localhost:3000"
        "|"
        "http://127.0.0.1:3000"
    )

    assert (
        values["ENV"]
        == "development"
    )

    assert (
        values["EXPLICIT"]
        == "False"
    )

    assert (
        values["CONFIG_ORIGINS"]
        == expected_origins
    )

    assert (
        values["MIDDLEWARE_ORIGINS"]
        == expected_origins
    )

    assert (
        values["CREDENTIALS"]
        == "True"
    )

    assert (
        values["METHODS"]
        == "*"
    )

    normalized_headers = {
        header.lower()
        for header
        in values["HEADERS"].split("|")
    }

    assert "x-tenant-id" in normalized_headers
    assert "x-actor-id" in normalized_headers
    assert "x-actor-roles" in normalized_headers


def test_main_paid_trial_uses_explicit_authoritative_cors_configuration(
    tmp_path: Path,
) -> None:
    release_root = (
        tmp_path
        / "paid-trial"
    ).resolve()

    result = run_main_probe(
        environment={
            "GAGF_RELEASE_ENVIRONMENT":
                "paid_trial",

            "GAGF_RELEASE_DATA_ROOT":
                str(
                    release_root
                ),

            "GAGF_RELEASE_CORS_ORIGINS":
                (
                    "https://operator.example.com,"
                    "https://customer.example.com"
                ),
        }
    )

    assert (
        result.returncode
        == 0
    ), result.stderr

    values = parse_probe(
        result.stdout
    )

    expected_origins = (
        "https://operator.example.com"
        "|"
        "https://customer.example.com"
    )

    assert (
        values["ENV"]
        == "paid_trial"
    )

    assert (
        values["EXPLICIT"]
        == "True"
    )

    assert (
        values["CONFIG_ORIGINS"]
        == expected_origins
    )

    assert (
        values["MIDDLEWARE_ORIGINS"]
        == expected_origins
    )


def test_main_prelive_uses_explicit_authoritative_cors_configuration(
    tmp_path: Path,
) -> None:
    release_root = (
        tmp_path
        / "prelive"
    ).resolve()

    result = run_main_probe(
        environment={
            "GAGF_RELEASE_ENVIRONMENT":
                "prelive",

            "GAGF_RELEASE_DATA_ROOT":
                str(
                    release_root
                ),

            "GAGF_RELEASE_CORS_ORIGINS":
                "https://prelive.example.com",
        }
    )

    assert (
        result.returncode
        == 0
    ), result.stderr

    values = parse_probe(
        result.stdout
    )

    assert (
        values["ENV"]
        == "prelive"
    )

    assert (
        values["EXPLICIT"]
        == "True"
    )

    assert (
        values["CONFIG_ORIGINS"]
        == "https://prelive.example.com"
    )

    assert (
        values["MIDDLEWARE_ORIGINS"]
        == "https://prelive.example.com"
    )


def test_main_paid_trial_fails_closed_without_explicit_cors_origins(
    tmp_path: Path,
) -> None:
    release_root = (
        tmp_path
        / "paid-trial"
    ).resolve()

    result = run_main_probe(
        environment={
            "GAGF_RELEASE_ENVIRONMENT":
                "paid_trial",

            "GAGF_RELEASE_DATA_ROOT":
                str(
                    release_root
                ),
        }
    )

    assert (
        result.returncode
        != 0
    )

    combined = (
        result.stdout
        + "\n"
        + result.stderr
    )

    assert (
        "prelive and paid_trial require explicit "
        "GAGF_RELEASE_CORS_ORIGINS"
        in combined
    )


def test_main_prelive_fails_closed_without_explicit_cors_origins(
    tmp_path: Path,
) -> None:
    release_root = (
        tmp_path
        / "prelive"
    ).resolve()

    result = run_main_probe(
        environment={
            "GAGF_RELEASE_ENVIRONMENT":
                "prelive",

            "GAGF_RELEASE_DATA_ROOT":
                str(
                    release_root
                ),
        }
    )

    assert (
        result.returncode
        != 0
    )

    combined = (
        result.stdout
        + "\n"
        + result.stderr
    )

    assert (
        "prelive and paid_trial require explicit "
        "GAGF_RELEASE_CORS_ORIGINS"
        in combined
    )