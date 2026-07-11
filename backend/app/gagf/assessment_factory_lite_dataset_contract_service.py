class AssessmentFactoryLiteDatasetContractService:
    """Define and validate the Assessment Factory Lite demo dataset contract."""

    def get_contract(self) -> dict:
        return {
            "status": "ok",
            "contract_type": "assessment_factory_lite_demo_dataset_contract",
            "dataset_name": "assessment_factory_lite_sample_csv",
            "boundary_type": "demo_only_sample_data",
            "required_fields": self._required_fields(),
            "optional_fields": self._optional_fields(),
            "allowed_event_types": self._allowed_event_types(),
            "allowed_severity_values": self._allowed_severity_values(),
            "validation_rules": self._validation_rules(),
            "failure_modes": self._failure_modes(),
            "sample_rows": self._sample_rows(),
            "excluded_scope": self._excluded_scope(),
            "operator_message": (
                "Assessment Factory Lite sample CSV contract is ready for "
                "demo-only synthetic workflow events."
            ),
            "recommended_action": "build_sample_csv_validator",
        }

    def validate_rows(self, rows: list[dict]) -> dict:
        contract = self.get_contract()
        required_fields = {
            field["field_name"] for field in contract["required_fields"]
        }
        allowed_event_types = set(contract["allowed_event_types"])
        allowed_severities = set(contract["allowed_severity_values"])

        errors = []

        for index, row in enumerate(rows):
            row_number = index + 1

            missing_fields = [
                field for field in required_fields if not row.get(field)
            ]

            if missing_fields:
                errors.append(
                    {
                        "row_number": row_number,
                        "error_type": "missing_required_fields",
                        "fields": sorted(missing_fields),
                    }
                )

            event_type = row.get("event_type")
            if event_type and event_type not in allowed_event_types:
                errors.append(
                    {
                        "row_number": row_number,
                        "error_type": "invalid_event_type",
                        "value": event_type,
                    }
                )

            severity = row.get("severity")
            if severity and severity not in allowed_severities:
                errors.append(
                    {
                        "row_number": row_number,
                        "error_type": "invalid_severity",
                        "value": severity,
                    }
                )

            if row.get("contains_real_customer_data") is True:
                errors.append(
                    {
                        "row_number": row_number,
                        "error_type": "real_customer_data_not_allowed",
                        "value": True,
                    }
                )

            if row.get("contains_regulated_data") is True:
                errors.append(
                    {
                        "row_number": row_number,
                        "error_type": "regulated_data_not_allowed",
                        "value": True,
                    }
                )

            if row.get("contains_federal_data") is True:
                errors.append(
                    {
                        "row_number": row_number,
                        "error_type": "federal_data_not_allowed",
                        "value": True,
                    }
                )

        is_valid = len(errors) == 0

        return {
            "status": "ok",
            "validation_type": "assessment_factory_lite_dataset_validation",
            "row_count": len(rows),
            "is_valid": is_valid,
            "error_count": len(errors),
            "errors": errors,
            "accepted_boundary": "demo_only_sample_data" if is_valid else "none",
            "recommended_action": (
                "run_demo_diagnostics"
                if is_valid
                else "repair_sample_csv_before_demo"
            ),
        }

    def _required_fields(self) -> list[dict]:
        return [
            {
                "field_name": "event_id",
                "description": "Unique synthetic event identifier.",
                "type": "string",
            },
            {
                "field_name": "case_id",
                "description": "Synthetic workflow or request identifier.",
                "type": "string",
            },
            {
                "field_name": "event_type",
                "description": "Demo workflow event type.",
                "type": "string",
            },
            {
                "field_name": "actor",
                "description": "Synthetic actor or role responsible for event.",
                "type": "string",
            },
            {
                "field_name": "team",
                "description": "Synthetic team or function name.",
                "type": "string",
            },
            {
                "field_name": "timestamp",
                "description": "Synthetic event timestamp.",
                "type": "iso8601_string",
            },
            {
                "field_name": "severity",
                "description": "Demo severity rating.",
                "type": "string",
            },
            {
                "field_name": "description",
                "description": "Plain-language demo event description.",
                "type": "string",
            },
        ]

    def _optional_fields(self) -> list[dict]:
        return [
            {
                "field_name": "expected_state",
                "description": "Expected workflow state before event.",
                "type": "string",
            },
            {
                "field_name": "observed_state",
                "description": "Observed workflow state after event.",
                "type": "string",
            },
            {
                "field_name": "duration_minutes",
                "description": "Synthetic delay duration.",
                "type": "number",
            },
            {
                "field_name": "constraint_label",
                "description": "Plain-language constraint or friction label.",
                "type": "string",
            },
            {
                "field_name": "contains_real_customer_data",
                "description": "Must be false or omitted.",
                "type": "boolean",
            },
            {
                "field_name": "contains_regulated_data",
                "description": "Must be false or omitted.",
                "type": "boolean",
            },
            {
                "field_name": "contains_federal_data",
                "description": "Must be false or omitted.",
                "type": "boolean",
            },
        ]

    def _allowed_event_types(self) -> list[str]:
        return [
            "approval_requested",
            "approval_delayed",
            "approval_granted",
            "approval_rejected",
            "work_blocked",
            "dependency_wait",
            "handoff_delayed",
            "ownership_gap",
            "environment_failure",
            "escalation",
        ]

    def _allowed_severity_values(self) -> list[str]:
        return [
            "low",
            "medium",
            "high",
            "critical",
        ]

    def _validation_rules(self) -> list[str]:
        return [
            "all_required_fields_must_be_present",
            "event_type_must_be_allowed",
            "severity_must_be_allowed",
            "dataset_must_be_demo_only",
            "real_customer_data_is_not_allowed",
            "regulated_data_is_not_allowed",
            "federal_data_is_not_allowed",
            "certification_claims_are_not_allowed",
        ]

    def _failure_modes(self) -> list[dict]:
        return [
            {
                "failure_mode": "missing_required_fields",
                "action": "repair_sample_csv_before_demo",
            },
            {
                "failure_mode": "invalid_event_type",
                "action": "map_event_to_allowed_demo_event_type",
            },
            {
                "failure_mode": "invalid_severity",
                "action": "map_severity_to_allowed_value",
            },
            {
                "failure_mode": "real_customer_data_not_allowed",
                "action": "remove_real_customer_data_or_use_synthetic_data",
            },
            {
                "failure_mode": "regulated_data_not_allowed",
                "action": "remove_regulated_data_from_demo_dataset",
            },
            {
                "failure_mode": "federal_data_not_allowed",
                "action": "remove_federal_data_from_demo_dataset",
            },
        ]

    def _sample_rows(self) -> list[dict]:
        return [
            {
                "event_id": "evt-001",
                "case_id": "case-001",
                "event_type": "approval_requested",
                "actor": "requester",
                "team": "operations",
                "timestamp": "2026-01-01T09:00:00Z",
                "severity": "medium",
                "description": "Synthetic approval request submitted.",
                "expected_state": "request_submitted",
                "observed_state": "approval_pending",
                "duration_minutes": 0,
                "constraint_label": "approval_required",
            },
            {
                "event_id": "evt-002",
                "case_id": "case-001",
                "event_type": "approval_delayed",
                "actor": "approver",
                "team": "operations",
                "timestamp": "2026-01-01T13:00:00Z",
                "severity": "high",
                "description": "Synthetic approval delayed for four hours.",
                "expected_state": "approval_granted",
                "observed_state": "approval_pending",
                "duration_minutes": 240,
                "constraint_label": "approval_delay",
            },
        ]

    def _excluded_scope(self) -> list[str]:
        return [
            "production_customer_data",
            "regulated_data",
            "federal_data",
            "live_security_telemetry",
            "customer_secrets",
            "fedramp_or_hipaa_certification_claims",
        ]