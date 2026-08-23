from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from backend.app.gagf.governance_real_paid_assessment_closeout import (
    GovernanceRealPaidAssessmentCloseoutService,
)


def _load_json_object(
    path: Path,
    field_name: str,
) -> dict[str, Any]:
    if not path.exists():
        raise RuntimeError(
            f"{field_name} does not exist: {path}"
        )

    if not path.is_file():
        raise RuntimeError(
            f"{field_name} is not a file: {path}"
        )

    try:
        payload = json.loads(
            path.read_text(
                encoding="utf-8"
            )
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuntimeError(
            f"{field_name} is not valid UTF-8 JSON"
        ) from exc

    if not isinstance(payload, dict):
        raise RuntimeError(
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

    serialized = json.dumps(
        payload,
        indent=2,
        sort_keys=True,
    )

    with path.open(
        "x",
        encoding="utf-8",
        newline="\n",
    ) as handle:
        handle.write(serialized)
        handle.write("\n")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Record explicit administrative closeout for a real paid "
            "assessment after governed client-response recording."
        )
    )

    parser.add_argument(
        "--database",
        required=True,
        help="Canonical paid-assessment SQLite database.",
    )

    parser.add_argument(
        "--client-response-json",
        required=True,
        help=(
            "Serialized PILOT-010 durable client-response result JSON."
        ),
    )

    parser.add_argument(
        "--closeout-json",
        required=True,
        help=(
            "Separate explicit administrative closeout confirmation JSON."
        ),
    )

    parser.add_argument(
        "--output-json",
        required=True,
        help=(
            "Exclusive output path for the governed administrative "
            "closeout result."
        ),
    )

    return parser


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()

    database_path = Path(
        args.database
    ).resolve()

    client_response_path = Path(
        args.client_response_json
    ).resolve()

    closeout_path = Path(
        args.closeout_json
    ).resolve()

    output_path = Path(
        args.output_json
    ).resolve()

    try:
        if output_path.exists():
            raise RuntimeError(
                f"output path already exists: {output_path}"
            )

        client_response_payload = _load_json_object(
            client_response_path,
            "client_response_json",
        )

        closeout_payload = _load_json_object(
            closeout_path,
            "closeout_json",
        )

        result = (
            GovernanceRealPaidAssessmentCloseoutService()
            .record(
                database_path=database_path,
                client_response_payload=client_response_payload,
                closeout_payload=closeout_payload,
            )
        )

        output_payload = {
            "administrative_closeout_recording_passed": True,
            "assessment_closed": True,
            "result": result.to_dict(),
            "boundaries": {
                "client_response_is_not_closeout": True,
                "closeout_confirmation_must_be_explicit": True,
                "pa010_remains_closeout_authority": True,
                "pa013_remains_operator_coordination_authority": True,
                "closeout_is_not_recommendation_implementation": True,
                "closeout_is_not_intervention_request": True,
                "closeout_is_not_intervention_authorization": True,
                "closeout_is_not_execution": True,
                "closeout_is_not_causation": True,
                "closeout_is_not_roi_verification": True,
                "closeout_is_not_remediation_success": True,
                "closeout_is_not_customer_outcome": True,
            },
        }

        _write_json_exclusive(
            output_path,
            output_payload,
        )

        return 0

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


if __name__ == "__main__":
    raise SystemExit(main())