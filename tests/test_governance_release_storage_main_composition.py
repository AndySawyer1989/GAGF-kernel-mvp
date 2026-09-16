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

    probe_environment.pop(
        "GAGF_RELEASE_ENVIRONMENT",
        None,
    )

    probe_environment.pop(
        "GAGF_RELEASE_DATA_ROOT",
        None,
    )

    probe_environment.update(
        environment
    )

    code = r'''
from backend.app.main import app

config = (
    app.state
    .governance_release_storage_configuration
)

print("ENV=" + config.release_environment)
print("ROOT=" + str(config.data_root))
print(
    "ASSESSMENT="
    + str(config.assessment_database_path)
)
print(
    "PREFLIGHT="
    + str(config.customer_trial_preflight_database_path)
)
print(
    "HANDOFF="
    + str(config.customer_trial_execution_handoff_database_path)
)
print(
    "CLOSEOUT="
    + str(
        config
        .customer_trial_administrative_closeout_observation_database_path
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


def test_main_default_preserves_development_storage(
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

    expected_root = (
        REPO_ROOT
        / "backend"
        / "app"
        / "data"
    )

    assert (
        values["ENV"]
        == "development"
    )

    assert (
        Path(values["ROOT"])
        == expected_root
    )

    assert (
        Path(values["ASSESSMENT"])
        == expected_root
        / "governance_assessments.sqlite3"
    )


def test_main_paid_trial_uses_isolated_root(
    tmp_path: Path,
) -> None:
    paid_trial_root = (
        tmp_path
        / "paid-trial"
    ).resolve()

    result = run_main_probe(
        environment={
            "GAGF_RELEASE_ENVIRONMENT":
                "paid_trial",

            "GAGF_RELEASE_DATA_ROOT":
                str(
                    paid_trial_root
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

    assert (
        values["ENV"]
        == "paid_trial"
    )

    assert (
        Path(values["ROOT"])
        == paid_trial_root
    )

    assert (
        Path(values["ASSESSMENT"])
        == paid_trial_root
        / "paid_trial"
        / "governance_assessments.sqlite3"
    )

    assert (
        Path(values["PREFLIGHT"])
        == paid_trial_root
        / "paid_trial"
        / "controlled_trial"
        / "preflight.sqlite3"
    )

    assert (
        Path(values["HANDOFF"])
        == paid_trial_root
        / "paid_trial"
        / "controlled_trial"
        / "execution_handoff.sqlite3"
    )

    assert (
        Path(values["CLOSEOUT"])
        == paid_trial_root
        / "paid_trial"
        / "controlled_trial"
        / "administrative_closeout_observation.sqlite3"
    )


def test_main_prelive_uses_isolated_root(
    tmp_path: Path,
) -> None:
    prelive_root = (
        tmp_path
        / "prelive"
    ).resolve()

    result = run_main_probe(
        environment={
            "GAGF_RELEASE_ENVIRONMENT":
                "prelive",

            "GAGF_RELEASE_DATA_ROOT":
                str(
                    prelive_root
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

    assert (
        values["ENV"]
        == "prelive"
    )

    assert (
        Path(values["ROOT"])
        == prelive_root
    )

    assert (
        Path(values["ASSESSMENT"])
        == prelive_root
        / "prelive"
        / "governance_assessments.sqlite3"
    )

    assert (
        Path(values["ASSESSMENT"])
        != (
            REPO_ROOT
            / "backend"
            / "app"
            / "data"
            / "governance_assessments.sqlite3"
        )
    )


def test_main_paid_trial_fails_closed_without_root(
) -> None:
    result = run_main_probe(
        environment={
            "GAGF_RELEASE_ENVIRONMENT":
                "paid_trial",
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
        "paid_trial requires GAGF_RELEASE_DATA_ROOT"
        in combined
    )


def test_main_prelive_fails_closed_without_root(
) -> None:
    result = run_main_probe(
        environment={
            "GAGF_RELEASE_ENVIRONMENT":
                "prelive",
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
        "prelive requires GAGF_RELEASE_DATA_ROOT"
        in combined
    )


def test_main_rejects_unknown_release_environment(
) -> None:
    result = run_main_probe(
        environment={
            "GAGF_RELEASE_ENVIRONMENT":
                "customer-production-maybe",
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
        "unsupported GAGF_RELEASE_ENVIRONMENT"
        in combined
    )
