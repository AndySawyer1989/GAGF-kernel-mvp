class AssessmentFactoryLiteDemoSampleRowsService:
    """Provide deterministic canned sample rows for Assessment Factory Lite demos."""

    def get_sample_rows(self, scenario: str = "standard") -> dict:
        normalized_scenario = (scenario or "standard").strip().lower()

        if normalized_scenario in {"standard", "valid", "approval_delay"}:
            return self._standard_scenario()

        if normalized_scenario in {"invalid", "unsafe"}:
            return self._invalid_scenario()

        if normalized_scenario in {"empty", "blank"}:
            return self._empty_scenario()

        return {
            "status": "not_found",
            "sample_type": "assessment_factory_lite_demo_sample_rows",
            "scenario": normalized_scenario,
            "rows": [],
            "row_count": 0,
            "available_scenarios": self.available_scenarios(),
            "operator_message": (
                "Requested sample row scenario was not found."
            ),
            "recommended_action": "choose_available_sample_scenario",
        }

    def available_scenarios(self) -> list[str]:
        return [
            "standard",
            "valid",
            "approval_delay",
            "invalid",
            "unsafe",
            "empty",
            "blank",
        ]

    def _standard_scenario(self) -> dict:
        rows = [
            {
                "event_id": "evt-001",
                "case_id": "case-001",
                "event_type": "approval_requested",
                "actor": "requester",
                "team": "operations",
                "timestamp": "2026-01-01T09:00:00Z",
                "severity": "medium",
                "description": "Synthetic approval request submitted.",
                "constraint_label": "approval_required",
                "duration_minutes": 0,
            },
            {
                "event_id": "evt-002",
                "case_id": "case-001",
                "event_type": "approval_delayed",
                "actor": "approver",
                "team": "operations",
                "timestamp": "2026-01-01T13:00:00Z",
                "severity": "high",
                "description": "Synthetic approval delayed.",
                "constraint_label": "approval_delay",
                "duration_minutes": 240,
            },
            {
                "event_id": "evt-003",
                "case_id": "case-002",
                "event_type": "work_blocked",
                "actor": "operator",
                "team": "engineering",
                "timestamp": "2026-01-01T14:00:00Z",
                "severity": "critical",
                "description": "Synthetic work blocked.",
                "constraint_label": "work_blocked",
                "duration_minutes": 120,
            },
        ]

        return {
            "status": "ok",
            "sample_type": "assessment_factory_lite_demo_sample_rows",
            "scenario": "standard",
            "scenario_label": "Approval Delay and Blocked Work",
            "boundary_type": "demo_only_sample_data",
            "is_valid_sample": True,
            "rows": rows,
            "row_count": len(rows),
            "expected_demo_outcome": {
                "validation_status": "passed",
                "top_friction_label": "approval_delay",
                "recommended_intervention": "streamline_approval_path",
                "recommended_action": "run_demo_diagnostics",
            },
            "operator_message": (
                "Standard Assessment Factory Lite sample rows are ready "
                "for demo diagnostics."
            ),
            "recommended_action": "load_sample_rows_into_demo",
        }

    def _invalid_scenario(self) -> dict:
        rows = [
            {
                "event_id": "evt-invalid-001",
                "case_id": "case-invalid-001",
                "event_type": "real_customer_incident",
                "actor": "operator",
                "team": "security",
                "timestamp": "2026-01-01T15:00:00Z",
                "severity": "urgent",
                "description": "Invalid row with prohibited customer data flag.",
                "contains_real_customer_data": True,
            }
        ]

        return {
            "status": "ok",
            "sample_type": "assessment_factory_lite_demo_sample_rows",
            "scenario": "invalid",
            "scenario_label": "Unsafe Data Boundary Example",
            "boundary_type": "demo_only_sample_data",
            "is_valid_sample": False,
            "rows": rows,
            "row_count": len(rows),
            "expected_demo_outcome": {
                "validation_status": "failed",
                "top_friction_label": "none",
                "recommended_intervention": "repair_sample_csv_before_demo",
                "recommended_action": "repair_sample_csv_before_demo",
            },
            "operator_message": (
                "Invalid sample rows are available for testing demo boundary "
                "rejection behavior."
            ),
            "recommended_action": "test_sample_data_boundary_rejection",
        }

    def _empty_scenario(self) -> dict:
        return {
            "status": "ok",
            "sample_type": "assessment_factory_lite_demo_sample_rows",
            "scenario": "empty",
            "scenario_label": "Empty Demo Starting State",
            "boundary_type": "demo_only_sample_data",
            "is_valid_sample": True,
            "rows": [],
            "row_count": 0,
            "expected_demo_outcome": {
                "validation_status": "passed",
                "top_friction_label": "none",
                "recommended_intervention": "add_demo_rows",
                "recommended_action": "add_synthetic_sample_rows",
            },
            "operator_message": (
                "Empty sample rows are available for initializing the demo "
                "screen before sample data is loaded."
            ),
            "recommended_action": "initialize_empty_demo_screen",
        }