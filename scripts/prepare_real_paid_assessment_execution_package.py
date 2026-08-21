from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

from scripts.run_real_paid_assessment import (
    _build_governed_inputs,
)


PACKAGE_TYPE = (
    "first_real_paid_assessment_execution_package"
)

PACKAGE_VERSION = "1.0.0"
PACKAGE_SCHEMA_VERSION = "1.0"


class RealPaidAssessmentExecutionPackageError(ValueError):
    """Raised when an execution package cannot be prepared safely."""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Prepare a controlled first-real-paid-assessment "
            "execution package without executing the assessment."
        )
    )

    parser.add_argument("--database", required=True)
    parser.add_argument("--intake-json", required=True)
    parser.add_argument("--authorization-json", required=True)
    parser.add_argument("--contract-event-json", required=True)
    parser.add_argument("--request-json", required=True)

    parser.add_argument(
        "--evidence-approvals-json",
        required=True,
    )

    parser.add_argument(
        "--preflight-json",
        required=True,
    )

    parser.add_argument(
        "--execution-output-json",
        required=True,
    )

    parser.add_argument(
        "--output-json",
        required=True,
    )

    return parser


def _read_bytes(path: Path, label: str) -> bytes:
    try:
        return path.read_bytes()
    except OSError as exc:
        raise RealPaidAssessmentExecutionPackageError(
            f"could not read {label}: {path}: {exc}"
        ) from exc


def _load_json(
    path: Path,
    label: str,
) -> dict[str, Any]:
    raw = _read_bytes(path, label)

    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise RealPaidAssessmentExecutionPackageError(
            f"{label} must be UTF-8: {path}"
        ) from exc

    try:
        value = json.loads(text)
    except json.JSONDecodeError as exc:
        raise RealPaidAssessmentExecutionPackageError(
            f"{label} is not valid JSON: {path}: {exc}"
        ) from exc

    if not isinstance(value, dict):
        raise RealPaidAssessmentExecutionPackageError(
            f"{label} must be a JSON object"
        )

    return value


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _file_commitment(
    *,
    label: str,
    path: Path,
) -> dict[str, Any]:
    resolved = path.resolve()
    raw = _read_bytes(resolved, label)

    return {
        "label": label,
        "path": str(resolved),
        "sha256": _sha256_bytes(raw),
        "byte_count": len(raw),
    }


def _canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )


def _package_hash(
    payload: dict[str, Any],
) -> str:
    return _sha256_bytes(
        _canonical_json(payload).encode("utf-8")
    )


def _resolve_evidence_paths(
    *,
    request_json_path: Path,
    request_payload: dict[str, Any],
) -> tuple[dict[str, Any], ...]:
    raw_inputs = request_payload.get(
        "evidence_inputs"
    )

    if not isinstance(raw_inputs, list):
        raise RealPaidAssessmentExecutionPackageError(
            "request.evidence_inputs must be a JSON array"
        )

    commitments: list[dict[str, Any]] = []

    for index, raw_item in enumerate(raw_inputs):
        if not isinstance(raw_item, dict):
            raise RealPaidAssessmentExecutionPackageError(
                "request.evidence_inputs"
                f"[{index}] must be a JSON object"
            )

        source_id = raw_item.get("source_id")
        csv_path = raw_item.get("csv_path")

        if (
            not isinstance(source_id, str)
            or not source_id.strip()
        ):
            raise RealPaidAssessmentExecutionPackageError(
                "request.evidence_inputs"
                f"[{index}].source_id must be non-empty text"
            )

        if (
            not isinstance(csv_path, str)
            or not csv_path.strip()
        ):
            raise RealPaidAssessmentExecutionPackageError(
                "request.evidence_inputs"
                f"[{index}].csv_path must be non-empty text"
            )

        candidate = Path(csv_path)

        if not candidate.is_absolute():
            candidate = (
                request_json_path.parent
                / candidate
            )

        commitment = _file_commitment(
            label=f"evidence:{source_id}",
            path=candidate,
        )

        commitment["source_id"] = source_id
        commitments.append(commitment)

    return tuple(commitments)


def _validate_preflight(
    *,
    preflight_payload: dict[str, Any],
    database_path: Path,
    hierarchy_key: str,
) -> dict[str, Any]:
    if preflight_payload.get("preflight_passed") is not True:
        raise RealPaidAssessmentExecutionPackageError(
            "PILOT-004 preflight did not pass"
        )

    result = preflight_payload.get("result")

    if not isinstance(result, dict):
        raise RealPaidAssessmentExecutionPackageError(
            "preflight result must be a JSON object"
        )

    if result.get("status") != "ready":
        raise RealPaidAssessmentExecutionPackageError(
            "preflight status must be ready"
        )

    if (
        result.get("ready_for_operator_execution")
        is not True
    ):
        raise RealPaidAssessmentExecutionPackageError(
            "preflight is not ready for operator execution"
        )

    if result.get("database_exists") is not False:
        raise RealPaidAssessmentExecutionPackageError(
            "preflight must describe a fresh database target"
        )

    if result.get("hierarchy_key") != hierarchy_key:
        raise RealPaidAssessmentExecutionPackageError(
            "preflight hierarchy does not match governed inputs"
        )

    result_database = result.get("database_path")

    if (
        not isinstance(result_database, str)
        or not result_database.strip()
    ):
        raise RealPaidAssessmentExecutionPackageError(
            "preflight database_path is required"
        )

    if (
        Path(result_database).resolve()
        != database_path.resolve()
    ):
        raise RealPaidAssessmentExecutionPackageError(
            "preflight database does not match execution target"
        )

    return result


def _error_payload(message: str) -> dict[str, Any]:
    return {
        "package_preparation_passed": False,
        "error": message,
        "boundaries": {
            "package_is_not_paid_work_authorization": True,
            "package_is_not_human_go_no_go": True,
            "package_is_not_execution": True,
            "package_is_not_execution_authority": True,
            "package_is_not_recovery_authority": True,
            "package_is_not_delivery_approval": True,
        },
    }


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    database_path = Path(args.database)
    intake_path = Path(args.intake_json)
    authorization_path = Path(args.authorization_json)
    contract_event_path = Path(args.contract_event_json)
    request_path = Path(args.request_json)
    approvals_path = Path(args.evidence_approvals_json)
    preflight_path = Path(args.preflight_json)

    execution_output_path = Path(
        args.execution_output_json
    )

    output_path = Path(args.output_json)

    if output_path.exists():
        print(
            json.dumps(
                _error_payload(
                    "execution-package JSON already exists; "
                    "refusing to overwrite evidence: "
                    f"{output_path}"
                ),
                indent=2,
                sort_keys=True,
            ),
            file=sys.stderr,
        )
        return 1

    if execution_output_path.exists():
        print(
            json.dumps(
                _error_payload(
                    "PA015 execution output already exists; "
                    "fresh execution evidence target required: "
                    f"{execution_output_path}"
                ),
                indent=2,
                sort_keys=True,
            ),
            file=sys.stderr,
        )
        return 1

    try:
        (
            intake,
            bridge,
            authorization,
            request,
            evidence_binding,
            contract_event,
        ) = _build_governed_inputs(
            database_path=database_path,
            intake_json_path=intake_path,
            authorization_json_path=authorization_path,
            contract_event_json_path=contract_event_path,
            request_json_path=request_path,
            evidence_approvals_json_path=approvals_path,
        )

        hierarchy_key = request.context.hierarchy_key

        preflight_payload = _load_json(
            preflight_path,
            "PILOT-004 preflight JSON",
        )

        preflight_result = _validate_preflight(
            preflight_payload=preflight_payload,
            database_path=database_path,
            hierarchy_key=hierarchy_key,
        )

        if database_path.exists():
            raise RealPaidAssessmentExecutionPackageError(
                "execution database now exists; "
                "PILOT-004 READY evidence is stale"
            )

        request_payload = _load_json(
            request_path,
            "request JSON",
        )

        controlled_inputs = (
            _file_commitment(
                label="intake_json",
                path=intake_path,
            ),
            _file_commitment(
                label="authorization_json",
                path=authorization_path,
            ),
            _file_commitment(
                label="contract_event_json",
                path=contract_event_path,
            ),
            _file_commitment(
                label="request_json",
                path=request_path,
            ),
            _file_commitment(
                label="evidence_approvals_json",
                path=approvals_path,
            ),
        )

        evidence_commitments = (
            _resolve_evidence_paths(
                request_json_path=request_path,
                request_payload=request_payload,
            )
        )

        preflight_commitment = _file_commitment(
            label="pilot004_preflight_json",
            path=preflight_path,
        )

        execution_argv = [
            sys.executable,
            "-m",
            "scripts.run_real_paid_assessment",
            "--database",
            str(database_path.resolve()),
            "--intake-json",
            str(intake_path.resolve()),
            "--authorization-json",
            str(authorization_path.resolve()),
            "--contract-event-json",
            str(contract_event_path.resolve()),
            "--request-json",
            str(request_path.resolve()),
            "--evidence-approvals-json",
            str(approvals_path.resolve()),
            "--output-json",
            str(execution_output_path.resolve()),
        ]

        package_body = {
            "package_type": PACKAGE_TYPE,
            "version": PACKAGE_VERSION,
            "schema_version": PACKAGE_SCHEMA_VERSION,
            "hierarchy_key": hierarchy_key,
            "tenant_id": request.context.tenant_id,
            "client_id": request.context.client_id,
            "engagement_id": request.context.engagement_id,
            "assessment_id": request.context.assessment_id,
            "database_path": str(
                database_path.resolve()
            ),
            "controlled_inputs": list(
                controlled_inputs
            ),
            "evidence_files": list(
                evidence_commitments
            ),
            "pilot004_preflight": {
                "commitment": preflight_commitment,
                "status": preflight_result["status"],
                "ready_for_operator_execution": (
                    preflight_result[
                        "ready_for_operator_execution"
                    ]
                ),
            },
            "execution": {
                "entry_point": "PA015",
                "argv": execution_argv,
                "output_json": str(
                    execution_output_path.resolve()
                ),
                "human_go_no_go_required": True,
                "automatically_execute": False,
            },
            "post_execution_verification": {
                "operator_run_passed_required": True,
                "required_recovery_fields": [
                    "attempt_hash",
                    "record_hash",
                    "hierarchy_key",
                    "disposition",
                    "artifact_count_before",
                    "artifact_count_after",
                    "execution_result",
                ],
                "allowed_dispositions": [
                    "executed",
                    "resumed",
                    "reconciled",
                ],
                "expected_core_artifact_count_after": 10,
                "completion_is_not_customer_outcome": True,
                "delivery_requires_separate_governed_process": True,
            },
            "boundaries": {
                "package_is_not_paid_work_authorization": True,
                "package_is_not_human_go_no_go": True,
                "package_is_not_execution": True,
                "package_is_not_execution_authority": True,
                "package_is_not_recovery_authority": True,
                "package_is_not_delivery_approval": True,
                "pilot004_ready_does_not_mean_executed": True,
                "pa015_remains_operator_execution_entry_point": True,
                "pa014_recovery_remains_governed_recovery_path": True,
            },
        }

        payload = {
            **package_body,
            "package_hash": _package_hash(
                package_body
            ),
        }

        serialized = json.dumps(
            payload,
            indent=2,
            sort_keys=True,
        )

        if (
            output_path.parent
            and not output_path.parent.exists()
        ):
            output_path.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

        try:
            with output_path.open(
                "x",
                encoding="utf-8",
                newline="\n",
            ) as output_file:
                output_file.write(serialized + "\n")
        except FileExistsError:
            raise RealPaidAssessmentExecutionPackageError(
                "execution-package JSON appeared during "
                "preparation; refusing to overwrite evidence: "
                f"{output_path}"
            )

    except Exception as exc:
        print(
            json.dumps(
                _error_payload(
                    "real paid-assessment execution-package "
                    f"preparation failure: "
                    f"{type(exc).__name__}: {exc}"
                ),
                indent=2,
                sort_keys=True,
            ),
            file=sys.stderr,
        )
        return 1

    print(serialized)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
