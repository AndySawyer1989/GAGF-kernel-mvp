from backend.app.gagf.schemas import RawSecurityEvent, TimestampQuality


class ServiceNowConnector:
    """
    Converts ServiceNow-style evidence into GAGF RawSecurityEvent objects.

    This connector is intentionally small for US-028.
    Later, it can be expanded to support real ServiceNow incidents,
    change requests, approvals, and workflow events.
    """

    def normalize_event(self, event: dict) -> RawSecurityEvent:
        event_type = self._map_servicenow_event_type(event)

        return RawSecurityEvent(
            event_id=event.get("sys_id", "servicenow-event-missing-id"),
            event_type=event_type,
            source_system="servicenow",
            event_occurred_at=event.get("opened_at") or event.get("sys_created_on"),
            event_created_at=event.get("sys_created_on") or event.get("opened_at"),
            timestamp_quality=TimestampQuality.SOURCE_OCCURRED_AT,
            sensor_reliability=0.88,
            cross_source_agreement=0.78,
            telemetry_completeness=0.82,
            kernel_eligible=True,
            metadata={
                "raw_payload": event,
            },
        )

    def normalize_events(self, events: list[dict]) -> list[RawSecurityEvent]:
        return [self.normalize_event(event) for event in events]

    def _map_servicenow_event_type(self, event: dict) -> str:
        table = event.get("table", "").lower()
        state = str(event.get("state", "")).lower()
        category = event.get("category", "").lower()
        approval = event.get("approval", "").lower()

        if approval in {"requested", "pending", "not requested"}:
            return "honeyfile_interaction"

        if table == "change_request" and state in {"new", "assess", "authorize"}:
            return "unauthorized_api_call"

        if table == "change_request" and state in {"closed", "closed complete"}:
            return "verification_passed"

        if table == "incident" and category in {"security", "cybersecurity"}:
            return "failed_auth_burst"

        if table == "incident":
            return "historically_valid_control"

        return "failed_auth_burst"