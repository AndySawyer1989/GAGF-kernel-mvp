"""Verify post-execution paid-assessment delivery readiness.

PILOT-006 CLI.

This command:
- reads a completed PA015 operator result;
- reads canonical assessment persistence through the governed readiness service;
- emits a delivery-readiness verification result.

It does not:
- authorize paid work;
- execute or recover an assessment;
- approve delivery;
- build a PA003 delivery envelope;
- deliver a report;
- acknowledge client receipt;
- establish client acceptance or customer outcome.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from backend.app.gagf.governance_real_paid_assessment_delivery_readiness import (
    GovernanceRealPaidAssessmentDeliveryReadinessService,
)


def _load_json_object(
    path: Path,
    *,
    field_name: str,
) -> dict[str, Any]:
    if not path.exists():
        raise ValueError(
            f"{field_name} does not exist: {path}"
        )

    if not path.is_file():
        raise ValueError(
            f"{field_name} is not a file: {path}"
        )

    try:
        payload = json.loads(
            path.read_text(
                encoding="utf-8"
            )
        )
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(
            f"{field_name} is not valid UTF-8 JSON"
        ) from exc

    if not isinstance(payload, dict):
        raise ValueError(
            f"{field_name} must contain a JSON object"
        )

    return payload


def _write_json_exclusive(
    path: Path,
    payload: dict[str, Any],
) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with path.open(
        "x",
        encoding="utf-8",
        newline="\n",
    ) as stream:
        json.dump(
            payload,
            stream,
            indent=2,
            sort_keys=True,
            ensure_ascii=False,
        )
        stream.write("\n")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Verify a completed real paid assessment against "
            "canonical persistence and produce a read-only "
            "delivery-readiness result."
        )
    )

    parser.add_argument(
        "--database",
        required=True,
        help="Canonical paid-assessment SQLite database.",
    )

    parser.add_argument(
        "--operator-result-json",
        required=True,
        help="Successful PA015 operator result JSON.",
    )

    parser.add_argument(
        "--output-json",
        required=True,
        help=(
            "New output path for the delivery-readiness "
            "verification result."
        ),
    )

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    database_path = Path(args.database).resolve()
    operator_result_path = Path(
        args.operator_result_json
    ).resolve()
    output_path = Path(
        args.output_json
    ).resolve()

    # H1-style fail-closed output preservation:
    # refuse before governed verification if the output already exists.
    if output_path.exists():
        print(
            json.dumps(
                {
                    "error": (
                        "output path already exists; refusing "
                        "to overwrite"
                    ),
                    "output_json": str(output_path),
                },
                sort_keys=True,
            ),
            file=sys.stderr,
        )
        return 1

    try:
        operator_payload = _load_json_object(
            operator_result_path,
            field_name="operator_result_json",
        )

        result = (
            GovernanceRealPaidAssessmentDeliveryReadinessService()
            .verify(
                database_path=database_path,
                operator_payload=operator_payload,
            )
        )

        payload = {
            "post_execution_verified": True,
            "ready_for_delivery_approval_review": True,
            "result": result.to_dict(),
            "boundaries": {
                "verification_command_is_not_paid_work_authorization": True,
                "verification_command_is_not_execution_authority": True,
                "verification_command_is_not_recovery_authority": True,
                "verification_command_is_not_delivery_approval": True,
                "verification_command_is_not_pa003_delivery_envelope": True,
                "verification_command_does_not_deliver_report": True,
                "pa003_remains_delivery_envelope_authority": True,
            },
        }

        _write_json_exclusive(
            output_path,
            payload,
        )

    except Exception as exc:
        print(
            json.dumps(
                {
                    "error": str(exc),
                    "error_type": type(exc).__name__,
                },
                sort_keys=True,
            ),
            file=sys.stderr,
        )
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())