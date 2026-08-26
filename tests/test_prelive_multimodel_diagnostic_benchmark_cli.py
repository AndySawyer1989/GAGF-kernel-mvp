from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

import backend.app.gagf.prelive_multimodel_diagnostic_benchmark_cli as cli
from backend.app.gagf.prelive_blind_assessment import (
    PreliveScenarioError,
)


def write_json(
    path: Path,
    value,
) -> Path:
    path.write_text(
        json.dumps(
            value
        ),
        encoding="utf-8",
    )

    return path


def test_load_json_reads_object(
    tmp_path,
):
    path = write_json(
        tmp_path
        / "value.json",
        {
            "hello":
                "world"
        },
    )

    assert (
        cli.load_json(
            path
        )
        == {
            "hello":
                "world"
        }
    )


def test_load_json_rejects_missing_file(
    tmp_path,
):
    with pytest.raises(
        PreliveScenarioError,
        match="does not exist",
    ):
        cli.load_json(
            tmp_path
            / "missing.json"
        )


def test_load_json_rejects_invalid_json(
    tmp_path,
):
    path = (
        tmp_path
        / "bad.json"
    )

    path.write_text(
        "{",
        encoding="utf-8",
    )

    with pytest.raises(
        PreliveScenarioError,
        match="Invalid JSON",
    ):
        cli.load_json(
            path
        )


def test_load_json_rejects_non_object(
    tmp_path,
):
    path = write_json(
        tmp_path
        / "array.json",
        [
            1,
            2,
            3,
        ],
    )

    with pytest.raises(
        PreliveScenarioError,
        match="root must be an object",
    ):
        cli.load_json(
            path
        )


def test_parser_requires_inputs():
    parser = (
        cli.build_parser()
    )

    args = parser.parse_args(
        [
            "--scenario",
            "scenario.json",
            "--oracle",
            "oracle.json",
            "--database",
            "prelive.sqlite3",
            "--output",
            "benchmark",
            "--model",
            "Claude",
        ]
    )

    assert (
        args.scenario
        == "scenario.json"
    )

    assert (
        args.model
        == "Claude"
    )


def test_run_executes_benchmark(
    tmp_path,
    monkeypatch,
    capsys,
):
    scenario_path = write_json(
        tmp_path
        / "scenario.json",
        {
            "scenario_id":
                "TEST"
        },
    )

    oracle_path = write_json(
        tmp_path
        / "oracle.json",
        {
            "oracle_status":
                "SEALED"
        },
    )

    database_path = (
        tmp_path
        / "prelive.sqlite3"
    )

    database_path.write_bytes(
        b"database"
    )

    output_path = (
        tmp_path
        / "benchmark"
    )

    calls = []

    class FakeService:
        def benchmark(
            self,
            **kwargs,
        ):
            calls.append(
                kwargs
            )

            return SimpleNamespace(
                to_dict=lambda: {
                    "benchmark_status":
                        "complete",
                    "precision":
                        1.0,
                }
            )

    monkeypatch.setattr(
        cli,
        "PreliveMultimodelDiagnosticBenchmarkService",
        FakeService,
    )

    exit_code = cli.run(
        [
            "--scenario",
            str(
                scenario_path
            ),
            "--oracle",
            str(
                oracle_path
            ),
            "--database",
            str(
                database_path
            ),
            "--output",
            str(
                output_path
            ),
            "--model",
            "Claude",
        ]
    )

    assert exit_code == 0

    assert (
        calls[0][
            "model_label"
        ]
        == "Claude"
    )

    output = (
        capsys
        .readouterr()
        .out
    )

    assert (
        '"precision": 1.0'
        in output
    )


def test_run_returns_one_on_benchmark_error(
    tmp_path,
    monkeypatch,
    capsys,
):
    scenario_path = write_json(
        tmp_path
        / "scenario.json",
        {},
    )

    oracle_path = write_json(
        tmp_path
        / "oracle.json",
        {},
    )

    class FakeService:
        def benchmark(
            self,
            **kwargs,
        ):
            raise (
                PreliveScenarioError(
                    "forced failure"
                )
            )

    monkeypatch.setattr(
        cli,
        "PreliveMultimodelDiagnosticBenchmarkService",
        FakeService,
    )

    exit_code = cli.run(
        [
            "--scenario",
            str(
                scenario_path
            ),
            "--oracle",
            str(
                oracle_path
            ),
            "--database",
            str(
                tmp_path
                / "db.sqlite3"
            ),
            "--output",
            str(
                tmp_path
                / "benchmark"
            ),
            "--model",
            "Claude",
        ]
    )

    assert exit_code == 1

    output = (
        capsys
        .readouterr()
        .out
    )

    assert (
        "BENCHMARK FAILED"
        in output
    )

    assert (
        "forced failure"
        in output
    )