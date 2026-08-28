from __future__ import annotations

import argparse
import sys
from pathlib import Path

from backend.app.gagf.diagnostic_calibration_blind_evidence_intake_bridge import (
    CommercialHierarchyContext,
)
from backend.app.gagf.diagnostic_calibration_blind_run_harness import (
    CalibrationBlindRunHarnessError,
    CalibrationBlindRunPaths,
    DiagnosticCalibrationBlindRunHarnessService,
)


SUPPORTED_MODELS = (
    "gemini",
    "claude",
    "copilot",
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=(
            "python -m "
            "backend.app.gagf."
            "diagnostic_calibration_blind_run_cli"
        ),
        description=(
            "Execute one governed independent blind "
            "FIP diagnostic calibration run."
        ),
    )

    parser.add_argument(
        "--model",
        required=True,
        choices=SUPPORTED_MODELS,
        help=(
            "External blind evidence generator."
        ),
    )

    parser.add_argument(
        "--scenario",
        required=True,
        help=(
            "Calibration scenario ID, for example "
            "FIP-CAL-001-002."
        ),
    )

    parser.add_argument(
        "--corpus-root",
        default=(
            "artifacts/"
            "fip_calibration_corpus_001"
        ),
        help=(
            "Directory containing sealed calibration "
            "scenario packages."
        ),
    )

    parser.add_argument(
        "--run-root",
        default=(
            "artifacts/"
            "fip_calibration_blind_runs_001"
        ),
        help=(
            "Directory containing external blind "
            "generator outputs and execution artifacts."
        ),
    )

    return parser


def normalize_scenario_id(
    value: str,
) -> str:
    normalized = (
        value.strip()
    )

    if not normalized:
        raise ValueError(
            "scenario must not be empty"
        )

    if not normalized.startswith(
        "FIP-CAL-"
    ):
        raise ValueError(
            "scenario must be a FIP calibration "
            "scenario ID"
        )

    return normalized


def build_paths(
    *,
    model: str,
    scenario_id: str,
    corpus_root: Path,
    run_root: Path,
) -> CalibrationBlindRunPaths:
    model_root = (
        run_root
        / model
    )

    scenario_root = (
        corpus_root
        / scenario_id
    )

    return (
        CalibrationBlindRunPaths(
            public_scenario_path=(
                scenario_root
                / "public_scenario.json"
            ),

            generator_payload_path=(
                model_root
                / f"{scenario_id}.json"
            ),

            sealed_oracle_path=(
                scenario_root
                / "sealed_oracle.json"
            ),

            database_path=(
                model_root
                / f"{scenario_id}.sqlite3"
            ),

            validated_evidence_path=(
                model_root
                / f"{scenario_id}-validated.json"
            ),

            diagnostic_freeze_path=(
                model_root
                / (
                    f"{scenario_id}"
                    "-diagnostic-freeze.json"
                )
            ),

            evaluation_path=(
                model_root
                / f"{scenario_id}-evaluation.json"
            ),
        )
    )


def build_context(
    *,
    model: str,
    scenario_id: str,
) -> CommercialHierarchyContext:
    return (
        CommercialHierarchyContext(
            tenant_id=(
                "fip-calibration"
            ),

            client_id=(
                "independent-blind-corpus"
            ),

            engagement_id=(
                "fip-cal-001"
            ),

            assessment_id=(
                f"{model}-{scenario_id}"
                .lower()
            ),
        )
    )


def print_result(
    result,
) -> None:
    evaluation = (
        result.evaluation
    )

    print()
    print(
        "=" * 72
    )

    print(
        "FIP BLIND CALIBRATION RESULT"
    )

    print(
        "=" * 72
    )

    print(
        f"scenario_id: {result.scenario_id}"
    )

    print(
        f"generator_id: {result.generator_id}"
    )

    print(
        f"generation_id: {result.generation_id}"
    )

    print(
        "evidence_hash: "
        f"{result.evidence.evidence_hash}"
    )

    print(
        "freeze_hash: "
        f"{result.freeze.freeze_hash}"
    )

    print(
        "leading_candidate: "
        f"{evaluation.leading_candidate_category}"
    )

    print(
        "ranked_conditions: "
        + ", ".join(
            evaluation.ranked_conditions
        )
    )

    print(
        "planted_primary_conditions: "
        + ", ".join(
            evaluation.planted_primary_conditions
        )
    )

    print(
        "first_primary_rank: "
        f"{evaluation.first_primary_rank}"
    )

    print(
        "reciprocal_rank: "
        f"{evaluation.reciprocal_rank}"
    )

    print(
        "rank_1_hit: "
        f"{evaluation.rank_1_hit}"
    )

    print(
        "top_2_hit: "
        f"{evaluation.top_2_hit}"
    )

    print(
        "top_3_hit: "
        f"{evaluation.top_3_hit}"
    )

    print(
        "candidate_count: "
        f"{evaluation.candidate_count}"
    )

    print(
        "leading_structural_level: "
        f"{evaluation.leading_structural_level}"
    )

    print(
        "leading_evidence_quality: "
        f"{evaluation.leading_evidence_quality}"
    )

    print(
        "absolute_separation: "
        f"{evaluation.absolute_separation}"
    )

    print(
        "relative_separation: "
        f"{evaluation.relative_separation}"
    )

    print(
        "evaluation_hash: "
        f"{evaluation.evaluation_hash}"
    )

    print()
    print(
        "database: "
        f"{result.paths.database_path}"
    )

    print(
        "freeze: "
        f"{result.paths.diagnostic_freeze_path}"
    )

    print(
        "evaluation: "
        f"{result.paths.evaluation_path}"
    )

    print()
    print(
        "BLIND CALIBRATION RUN COMPLETE"
    )


def main(
    argv: list[str] | None = None,
) -> int:
    parser = build_parser()

    arguments = parser.parse_args(
        argv
    )

    try:
        scenario_id = (
            normalize_scenario_id(
                arguments.scenario
            )
        )

        model = (
            arguments.model
            .strip()
            .lower()
        )

        corpus_root = Path(
            arguments.corpus_root
        )

        run_root = Path(
            arguments.run_root
        )

        paths = build_paths(
            model=model,
            scenario_id=scenario_id,
            corpus_root=corpus_root,
            run_root=run_root,
        )

        context = build_context(
            model=model,
            scenario_id=scenario_id,
        )

        print(
            "=" * 72
        )

        print(
            "FIP INDEPENDENT BLIND CALIBRATION"
        )

        print(
            f"Scenario: {scenario_id}"
        )

        print(
            f"Model: {model}"
        )

        print(
            "=" * 72
        )

        print()
        print(
            "Public scenario:"
        )

        print(
            f"  {paths.public_scenario_path}"
        )

        print(
            "Blind evidence:"
        )

        print(
            f"  {paths.generator_payload_path}"
        )

        print()
        print(
            "Executing:"
        )

        print(
            "  001D validation"
        )

        print(
            "  001E real intake"
        )

        print(
            "  001F governed diagnostic"
        )

        print(
            "  diagnostic freeze"
        )

        print(
            "  001G sealed-oracle evaluation"
        )

        harness = (
            DiagnosticCalibrationBlindRunHarnessService()
        )

        result = harness.run(
            context=context,
            paths=paths,
        )

        print_result(
            result
        )

        return 0

    except (
        CalibrationBlindRunHarnessError,
        ValueError,
        KeyError,
        TypeError,
    ) as exc:
        print(
            file=sys.stderr,
        )

        print(
            "FIP BLIND CALIBRATION RUN FAILED",
            file=sys.stderr,
        )

        print(
            str(
                exc
            ),
            file=sys.stderr,
        )

        return 1


if __name__ == "__main__":
    raise SystemExit(
        main()
    )