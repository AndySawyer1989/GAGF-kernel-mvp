from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path
from typing import Any


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]

if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))


from backend.app.gagf.governance_assessment_application import (
    AssessmentExecutionRequest,
)
from backend.app.gagf.governance_assessment_demonstration import (
    DemonstrationEvidenceInput,
)
from backend.app.gagf.governance_assessment_domain import (
    EvidenceSourceKind,
    EvidenceSourceReference,
)
from backend.app.gagf.governance_assessment_scope_configuration import (
    EvidenceRequirement,
)
from backend.app.gagf.governance_paid_assessment_execution_handoff import (
    PaidAssessmentWorkAuthorization,
)
from backend.app.gagf.governance_real_paid_assessment_authorization_bridge import (
    GovernanceRealPaidAssessmentAuthorizationBridgeService,
)
from backend.app.gagf.governance_real_paid_assessment_execution_evidence import (
    GovernanceRealPaidAssessmentExecutionEvidenceService,
    RealAssessmentExecutionEvidenceApproval,
)
from backend.app.gagf.governance_real_paid_assessment_execution_recovery import (
    GovernanceRealPaidAssessmentExecutionRecoveryService,
)
from backend.app.gagf.governance_real_paid_assessment_readiness import (
    EvidenceDataClassification,
    GovernanceRealPaidAssessmentReadinessService,
    RealAssessmentEvidenceDeclaration,
    RealAssessmentStorageDeclaration,
    RealPaidAssessmentIntake,
)


class RealPaidAssessmentOperatorError(ValueError):
    """Raised when controlled operator input cannot be constructed safely."""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run or recover one governed real paid assessment through "
            "the PA014 execution-recovery path."
        )
    )

    parser.add_argument(
        "--database",
        required=True,
        help=(
            "SQLite database for the governed paid assessment. "
            "A matching PA014 execution may be resumed or reconciled."
        ),
    )

    parser.add_argument(
        "--intake-json",
        required=True,
        help="Controlled real paid-assessment intake JSON.",
    )

    parser.add_argument(
        "--authorization-json",
        required=True,
        help="Independent paid-work authorization JSON.",
    )

    parser.add_argument(
        "--contract-event-json",
        required=True,
        help="Executed-contract event JSON.",
    )

    parser.add_argument(
        "--request-json",
        required=True,
        help=(
            "Assessment execution request JSON. CSV evidence entries "
            "reference files using csv_path."
        ),
    )

    parser.add_argument(
        "--evidence-approvals-json",
        required=True,
        help=(
            "Execution-evidence approvals JSON containing the exact "
            "approved SHA-256 digest for each evidence source."
        ),
    )

    parser.add_argument(
        "--output-json",
        help=(
            "Optional path for the governed operator result. "
            "Existing files are never overwritten."
        ),
    )

    return parser


def _load_json(path: Path, label: str) -> Any:
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise RealPaidAssessmentOperatorError(
            f"could not read {label}: {path}: {exc}"
        ) from exc

    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise RealPaidAssessmentOperatorError(
            f"{label} must be UTF-8: {path}"
        ) from exc

    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise RealPaidAssessmentOperatorError(
            f"{label} is not valid JSON: {path}: {exc}"
        ) from exc


def _require_object(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise RealPaidAssessmentOperatorError(
            f"{label} must be a JSON object"
        )

    return value


def _require_list(
    value: Any,
    label: str,
) -> list[Any]:
    if not isinstance(value, list):
        raise RealPaidAssessmentOperatorError(
            f"{label} must be a JSON array"
        )

    return value


def _parse_date(value: Any, label: str) -> date:
    if not isinstance(value, str) or not value.strip():
        raise RealPaidAssessmentOperatorError(
            f"{label} must be an ISO-8601 date string"
        )

    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise RealPaidAssessmentOperatorError(
            f"{label} must be an ISO-8601 date"
        ) from exc


def _string_tuple(value: Any, label: str) -> tuple[str, ...]:
    items = _require_list(value, label)

    result: list[str] = []

    for index, item in enumerate(items):
        if not isinstance(item, str) or not item.strip():
            raise RealPaidAssessmentOperatorError(
                f"{label}[{index}] must be non-empty text"
            )

        result.append(item)

    return tuple(result)


def _build_intake(
    *,
    payload: dict[str, Any],
    database_path: Path,
) -> RealPaidAssessmentIntake:
    evidence_payload = _require_list(
        payload.get("evidence"),
        "intake.evidence",
    )

    evidence = tuple(
        RealAssessmentEvidenceDeclaration(
            evidence_id=item["evidence_id"],
            source_kind=item["source_kind"],
            description=item["description"],
            classification=EvidenceDataClassification(
                item["classification"]
            ),
            client_authorized_for_assessment=(
                item["client_authorized_for_assessment"]
            ),
            minimization_review_completed=(
                item["minimization_review_completed"]
            ),
            direct_identifiers_removed=(
                item["direct_identifiers_removed"]
            ),
        )
        for item in (
            _require_object(
                raw_item,
                f"intake.evidence[{index}]",
            )
            for index, raw_item in enumerate(evidence_payload)
        )
    )

    storage_payload = _require_object(
        payload.get("storage"),
        "intake.storage",
    )

    declared_repository = Path(
        storage_payload["repository_path"]
    )

    if declared_repository.resolve() != database_path.resolve():
        raise RealPaidAssessmentOperatorError(
            "intake storage repository_path does not match "
            "the --database execution target"
        )

    storage = RealAssessmentStorageDeclaration(
        repository_path=storage_payload["repository_path"],
        operator_controlled_location=(
            storage_payload["operator_controlled_location"]
        ),
        access_restricted=storage_payload["access_restricted"],
        storage_protection_confirmed=(
            storage_payload["storage_protection_confirmed"]
        ),
        backup_plan_recorded=(
            storage_payload["backup_plan_recorded"]
        ),
        retention_period_recorded=(
            storage_payload["retention_period_recorded"]
        ),
        deletion_plan_recorded=(
            storage_payload["deletion_plan_recorded"]
        ),
    )

    return RealPaidAssessmentIntake(
        tenant_id=payload["tenant_id"],
        client_id=payload["client_id"],
        engagement_id=payload["engagement_id"],
        assessment_id=payload["assessment_id"],
        client_display_name=payload["client_display_name"],
        assessment_name=payload["assessment_name"],
        operator_name=payload["operator_name"],
        client_contact_name=payload["client_contact_name"],
        assessment_scope_confirmed=(
            payload["assessment_scope_confirmed"]
        ),
        evidence_scope_confirmed=(
            payload["evidence_scope_confirmed"]
        ),
        client_data_use_confirmed=(
            payload["client_data_use_confirmed"]
        ),
        operator_readiness_confirmed=(
            payload["operator_readiness_confirmed"]
        ),
        evidence=evidence,
        storage=storage,
    )


def _build_authorization(
    payload: dict[str, Any],
) -> PaidAssessmentWorkAuthorization:
    return PaidAssessmentWorkAuthorization(
        authorization_id=payload["authorization_id"],
        tenant_id=payload["tenant_id"],
        client_id=payload["client_id"],
        engagement_id=payload["engagement_id"],
        assessment_id=payload["assessment_id"],
        contract_execution_event_id=(
            payload["contract_execution_event_id"]
        ),
        authorized_by=payload["authorized_by"],
        authorized_at=payload["authorized_at"],
        paid_assessment_authorized=(
            payload["paid_assessment_authorized"]
        ),
    )


def _resolve_evidence_path(
    *,
    request_json_path: Path,
    csv_path: str,
) -> Path:
    candidate = Path(csv_path)

    if candidate.is_absolute():
        return candidate

    return request_json_path.parent / candidate


def _read_exact_utf8_csv(
    *,
    path: Path,
    label: str,
) -> str:
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise RealPaidAssessmentOperatorError(
            f"could not read {label}: {path}: {exc}"
        ) from exc

    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise RealPaidAssessmentOperatorError(
            f"{label} must contain UTF-8 CSV bytes: {path}"
        ) from exc

    if text.encode("utf-8") != raw:
        raise RealPaidAssessmentOperatorError(
            f"{label} did not round-trip as exact UTF-8 bytes: {path}"
        )

    return text


def _build_request(
    *,
    payload: dict[str, Any],
    intake: RealPaidAssessmentIntake,
    request_json_path: Path,
) -> AssessmentExecutionRequest:
    requirement_payload = _require_list(
        payload.get("evidence_requirements"),
        "request.evidence_requirements",
    )

    requirements = tuple(
        EvidenceRequirement(
            requirement_id=item["requirement_id"],
            source_kind=EvidenceSourceKind(
                item["source_kind"]
            ),
            description=item["description"],
            required=item.get("required", True),
            minimum_record_count=item.get(
                "minimum_record_count",
                1,
            ),
        )
        for item in (
            _require_object(
                raw_item,
                f"request.evidence_requirements[{index}]",
            )
            for index, raw_item in enumerate(
                requirement_payload
            )
        )
    )

    evidence_payload = _require_list(
        payload.get("evidence_inputs"),
        "request.evidence_inputs",
    )

    evidence_inputs: list[DemonstrationEvidenceInput] = []

    for index, raw_item in enumerate(evidence_payload):
        item = _require_object(
            raw_item,
            f"request.evidence_inputs[{index}]",
        )

        kind = EvidenceSourceKind(item["kind"])

        if kind is not EvidenceSourceKind.CSV:
            raise RealPaidAssessmentOperatorError(
                "PA015 operator v0.1 supports only CSV "
                "demonstration evidence inputs"
            )

        csv_path = _resolve_evidence_path(
            request_json_path=request_json_path,
            csv_path=item["csv_path"],
        )

        csv_text = _read_exact_utf8_csv(
            path=csv_path,
            label=(
                f"request.evidence_inputs[{index}].csv_path"
            ),
        )

        source = EvidenceSourceReference(
            source_id=item["source_id"],
            kind=kind,
            display_name=item["display_name"],
            source_location=item.get("source_location"),
        )

        evidence_inputs.append(
            DemonstrationEvidenceInput(
                source=source,
                csv_text=csv_text,
            )
        )

    return AssessmentExecutionRequest(
        context=intake.context,
        assessment_name=payload["assessment_name"],
        workflow_names=_string_tuple(
            payload["workflow_names"],
            "request.workflow_names",
        ),
        organizational_units=_string_tuple(
            payload["organizational_units"],
            "request.organizational_units",
        ),
        period_start=_parse_date(
            payload["period_start"],
            "request.period_start",
        ),
        period_end=_parse_date(
            payload["period_end"],
            "request.period_end",
        ),
        objectives=_string_tuple(
            payload["objectives"],
            "request.objectives",
        ),
        expected_outcomes=_string_tuple(
            payload["expected_outcomes"],
            "request.expected_outcomes",
        ),
        evidence_requirements=requirements,
        evidence_inputs=tuple(evidence_inputs),
        client_display_name=payload["client_display_name"],
        prepared_by=payload["prepared_by"],
        exclusions=_string_tuple(
            payload.get("exclusions", []),
            "request.exclusions",
        ),
        maximum_priorities=payload.get(
            "maximum_priorities",
            3,
        ),
    )


def _build_evidence_approvals(
    payload: dict[str, Any],
) -> tuple[
    RealAssessmentExecutionEvidenceApproval,
    ...
]:
    approval_payload = _require_list(
        payload.get("approvals"),
        "evidence_approvals.approvals",
    )

    return tuple(
        RealAssessmentExecutionEvidenceApproval(
            evidence_id=item["evidence_id"],
            approved_content_sha256=(
                item["approved_content_sha256"]
            ),
            approved_by=item["approved_by"],
            approved_at=item["approved_at"],
            execution_evidence_approved=(
                item["execution_evidence_approved"]
            ),
        )
        for item in (
            _require_object(
                raw_item,
                f"evidence_approvals.approvals[{index}]",
            )
            for index, raw_item in enumerate(
                approval_payload
            )
        )
    )


def _build_governed_inputs(
    *,
    database_path: Path,
    intake_json_path: Path,
    authorization_json_path: Path,
    contract_event_json_path: Path,
    request_json_path: Path,
    evidence_approvals_json_path: Path,
) -> tuple[
    RealPaidAssessmentIntake,
    Any,
    PaidAssessmentWorkAuthorization,
    AssessmentExecutionRequest,
    Any,
    dict[str, Any],
]:
    intake_payload = _require_object(
        _load_json(
            intake_json_path,
            "intake JSON",
        ),
        "intake JSON",
    )

    authorization_payload = _require_object(
        _load_json(
            authorization_json_path,
            "authorization JSON",
        ),
        "authorization JSON",
    )

    contract_event = _require_object(
        _load_json(
            contract_event_json_path,
            "contract-event JSON",
        ),
        "contract-event JSON",
    )

    request_payload = _require_object(
        _load_json(
            request_json_path,
            "request JSON",
        ),
        "request JSON",
    )

    approvals_payload = _require_object(
        _load_json(
            evidence_approvals_json_path,
            "evidence-approvals JSON",
        ),
        "evidence-approvals JSON",
    )

    intake = _build_intake(
        payload=intake_payload,
        database_path=database_path,
    )

    readiness = (
        GovernanceRealPaidAssessmentReadinessService()
        .evaluate(
            intake=intake
        )
    )

    authorization = _build_authorization(
        authorization_payload
    )

    bridge = (
        GovernanceRealPaidAssessmentAuthorizationBridgeService()
        .bind(
            intake=intake,
            readiness=readiness,
            paid_work_authorization=authorization,
        )
    )

    request = _build_request(
        payload=request_payload,
        intake=intake,
        request_json_path=request_json_path,
    )

    approvals = _build_evidence_approvals(
        approvals_payload
    )

    evidence_binding = (
        GovernanceRealPaidAssessmentExecutionEvidenceService()
        .bind(
            intake=intake,
            request=request,
            approvals=approvals,
        )
    )

    return (
        intake,
        bridge,
        authorization,
        request,
        evidence_binding,
        contract_event,
    )


def _error_payload(message: str) -> dict[str, Any]:
    return {
        "operator_run_passed": False,
        "error": message,
        "boundaries": {
            "operator_command_is_not_paid_work_authorization": True,
            "operator_command_is_not_execution_authority": True,
            "operator_command_is_not_recovery_authority": True,
        },
    }


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    database_path = Path(args.database)

    intake_json_path = Path(args.intake_json)
    authorization_json_path = Path(args.authorization_json)
    contract_event_json_path = Path(args.contract_event_json)
    request_json_path = Path(args.request_json)
    evidence_approvals_json_path = Path(
        args.evidence_approvals_json
    )

    output_path = (
        None
        if not args.output_json
        else Path(args.output_json)
    )

    # H1: output collision is checked before any governed execution.
    if output_path is not None and output_path.exists():
        print(
            json.dumps(
                _error_payload(
                    "output JSON already exists; refusing to "
                    f"overwrite evidence: {output_path}"
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
            intake_json_path=intake_json_path,
            authorization_json_path=authorization_json_path,
            contract_event_json_path=contract_event_json_path,
            request_json_path=request_json_path,
            evidence_approvals_json_path=(
                evidence_approvals_json_path
            ),
        )

        result = (
            GovernanceRealPaidAssessmentExecutionRecoveryService()
            .execute(
                database_path=database_path,
                intake=intake,
                authorization_bridge=bridge,
                evidence_binding=evidence_binding,
                contract_execution_event=contract_event,
                paid_work_authorization=authorization,
                request=request,
            )
        )
    except Exception as exc:
        print(
            json.dumps(
                _error_payload(
                    "governed real paid-assessment operator "
                    f"failure: {type(exc).__name__}: {exc}"
                ),
                indent=2,
                sort_keys=True,
            ),
            file=sys.stderr,
        )
        return 1

    payload = {
        "operator_run_passed": True,
        "result": result.to_dict(),
        "boundaries": {
            "operator_command_is_not_paid_work_authorization": True,
            "operator_command_is_not_execution_authority": True,
            "operator_command_is_not_recovery_authority": True,
            "recovery_service_remains_governed_authority_path": True,
        },
    }

    serialized = json.dumps(
        payload,
        indent=2,
        sort_keys=True,
    )

    print(serialized)

    if output_path is not None:
        if output_path.parent and not output_path.parent.exists():
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
            print(
                json.dumps(
                    _error_payload(
                        "output JSON appeared during execution; "
                        "refusing to overwrite evidence: "
                        f"{output_path}"
                    ),
                    indent=2,
                    sort_keys=True,
                ),
                file=sys.stderr,
            )
            return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())