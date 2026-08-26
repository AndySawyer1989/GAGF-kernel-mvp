from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from backend.app.gagf.prelive_blind_assessment import (
    PreliveScenarioError,
)
from backend.app.gagf.prelive_multimodel_diagnostic_benchmark import (
    PreliveMultimodelDiagnosticBenchmarkService,
)


def load_json(
    path: str | Path,
) -> dict[str, Any]:
    file_path = Path(
        path
    )

    if not file_path.is_file():
        raise PreliveScenarioError(
            f"JSON file does not exist: {file_path}"
        )

    try:
        value = json.loads(
            file_path.read_text(
                encoding="utf-8"
            )
        )
    except json.JSONDecodeError as exc:
        raise PreliveScenarioError(
            f"Invalid JSON file: {file_path}"
        ) from exc

    if not isinstance(
        value,
        dict,
    ):
        raise PreliveScenarioError(
            f"JSON root must be an object: {file_path}"
        )

    return value


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=(
            "prelive-multimodel-diagnostic-benchmark"
        ),
        description=(
            "Run the frozen FIP diagnostic benchmark "
            "against a completed PRELIVE blind assessment."
        ),
    )

    parser.add_argument(
        "--scenario",
        required=True,
        help=(
            "Path to the PRELIVE scenario JSON."
        ),
    )

    parser.add_argument(
        "--oracle",
        required=True,
        help=(
            "Path to the sealed PRELIVE oracle JSON."
        ),
    )

    parser.add_argument(
        "--database",
        required=True,
        help=(
            "Path to the completed PRELIVE SQLite database."
        ),
    )

    parser.add_argument(
        "--output",
        required=True,
        help=(
            "Empty output directory for benchmark artifacts."
        ),
    )

    parser.add_argument(
        "--model",
        required=True,
        help=(
            "External model label, such as Claude or Copilot."
        ),
    )

    return parser


def run(
    argv: list[str] | None = None,
) -> int:
    parser = build_parser()

    args = parser.parse_args(
        argv
    )

    try:
        scenario = load_json(
            args.scenario
        )

        oracle = load_json(
            args.oracle
        )

        result = (
            PreliveMultimodelDiagnosticBenchmarkService()
            .benchmark(
                scenario=scenario,
                oracle=oracle,
                source_database_path=(
                    args.database
                ),
                output_directory=(
                    args.output
                ),
                model_label=(
                    args.model
                ),
            )
        )

    except PreliveScenarioError as exc:
        print(
            f"BENCHMARK FAILED: {exc}"
        )

        return 1

    print(
        json.dumps(
            result.to_dict(),
            indent=2,
            sort_keys=True,
            ensure_ascii=False,
        )
    )

    return 0


def main() -> None:
    raise SystemExit(
        run()
    )


if __name__ == "__main__":
    main()