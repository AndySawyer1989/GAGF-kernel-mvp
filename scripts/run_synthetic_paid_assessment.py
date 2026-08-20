from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]

if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))


from backend.app.gagf.governance_synthetic_paid_assessment_dry_run import (
    SyntheticPaidAssessmentDryRunError,
    SyntheticPaidAssessmentDryRunService,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run the governed synthetic paid-assessment dry-run "
            "through the real PA-001 through PA-011 service chain."
        )
    )

    parser.add_argument(
        "--database",
        required=True,
        help=(
            "Path for a NEW SQLite database. "
            "The runner refuses to overwrite an existing file."
        ),
    )

    parser.add_argument(
        "--output-json",
        help=(
            "Optional path to write the final governed dry-run "
            "result as JSON."
        ),
    )

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    database_path = Path(args.database)

    try:
        result = SyntheticPaidAssessmentDryRunService().run(
            database_path=database_path
        )
    except SyntheticPaidAssessmentDryRunError as exc:
        print(
            json.dumps(
                {
                    "dry_run_passed": False,
                    "error": str(exc),
                },
                indent=2,
                sort_keys=True,
            ),
            file=sys.stderr,
        )
        return 1
    except Exception as exc:
        print(
            json.dumps(
                {
                    "dry_run_passed": False,
                    "error": (
                        "unexpected synthetic dry-run failure: "
                        f"{type(exc).__name__}: {exc}"
                    ),
                },
                indent=2,
                sort_keys=True,
            ),
            file=sys.stderr,
        )
        return 1

    payload = result.to_dict()

    if payload.get("dry_run_passed") is not True:
        print(
            json.dumps(
                {
                    "dry_run_passed": False,
                    "error": (
                        "service returned without a positive "
                        "dry-run proof"
                    ),
                },
                indent=2,
                sort_keys=True,
            ),
            file=sys.stderr,
        )
        return 1

    serialized = json.dumps(
        payload,
        indent=2,
        sort_keys=True,
    )

    print(serialized)

    if args.output_json:
        output_path = Path(args.output_json)

        if output_path.parent and not output_path.parent.exists():
            output_path.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

        output_path.write_text(
            serialized + "\n",
            encoding="utf-8",
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())