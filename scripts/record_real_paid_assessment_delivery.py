from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from backend.app.gagf.governance_real_paid_assessment_delivery_recording import (
    GovernanceRealPaidAssessmentDeliveryRecordingService,
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
            "Record an explicitly completed human delivery action "
            "for a real paid assessment and persist the governed "
            "delivery event."
        )
    )

    parser.add_argument(
        "--database",
        required=True,
        help="Canonical paid-assessment SQLite database.",
    )

    parser.add_argument(
        "--approved-delivery-json",
        required=True,
        help=(
            "Serialized PILOT-007 approved-for-human-delivery "
            "operator result JSON."
        ),
    )

    parser.add_argument(
        "--human-delivery-confirmation-json",
        required=True,
        help=(
            "Separate explicit human confirmation that delivery "
            "was completed."
        ),
    )

    parser.add_argument(
        "--output-json",
        required=True,
        help=(
            "Exclusive output path for the governed real-delivery "
            "recording result."
        ),
    )

    return parser


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()

    database_path = Path(
        args.database
    ).resolve()

    approved_delivery_path = Path(
        args.approved_delivery_json
    ).resolve()

    human_confirmation_path = Path(
        args.human_delivery_confirmation_json
    ).resolve()

    output_path = Path(
        args.output_json
    ).resolve()

    try:
        if output_path.exists():
            raise RuntimeError(
                f"output path already exists: {output_path}"
            )

        approved_delivery_payload = _load_json_object(
            approved_delivery_path,
            "approved_delivery_json",
        )

        human_confirmation_payload = _load_json_object(
            human_confirmation_path,
            "human_delivery_confirmation_json",
        )

        result = (
            GovernanceRealPaidAssessmentDeliveryRecordingService()
            .record(
                database_path=database_path,
                approved_delivery_payload=(
                    approved_delivery_payload
                ),
                human_confirmation_payload=(
                    human_confirmation_payload
                ),
            )
        )

        output_payload = {
            "delivery_recording_passed": True,
            "delivery_recorded": True,
            "result": result.to_dict(),
            "boundaries": {
                "command_does_not_authorize_paid_work": True,
                "command_does_not_execute_assessment": True,
                "command_does_not_approve_for_delivery": True,
                "human_delivery_confirmation_must_preexist_command": True,
                "command_does_not_infer_delivery_from_approval": True,
                "pa005_remains_delivery_event_authority": True,
                "pa013_remains_operator_coordination_authority": True,
                "pa012_remains_lifecycle_persistence_authority": True,
                "delivery_is_not_client_receipt": True,
                "delivery_is_not_client_acknowledgment": True,
                "delivery_is_not_client_acceptance": True,
                "delivery_is_not_customer_outcome": True,
            },
        }

        _write_json_exclusive(
            output_path,
            output_payload,
        )

        return 0

    except Exception as exc:
        error_payload = {
            "error": str(exc),
            "error_type": type(exc).__name__,
        }

        print(
            json.dumps(
                error_payload,
                sort_keys=True,
            ),
            file=sys.stderr,
        )

        return 1


if __name__ == "__main__":
    raise SystemExit(main())