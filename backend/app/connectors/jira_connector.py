from backend.app.gagf.schemas import RawSecurityEvent, TimestampQuality


class JiraConnector:
    """
    Converts Jira-style evidence into GAGF RawSecurityEvent objects.

    This connector is intentionally small for US-043.
    Later, it can be expanded to support real Jira issues,
    workflow transitions, approvals, blockers, dependencies, and SLA events.
    """

    def normalize_event(self, event: dict) -> RawSecurityEvent:
        event_type = self._map_jira_event_type(event)

        return RawSecurityEvent(
            event_id=event.get("id", "jira-event-missing-id"),
            event_type=event_type,
            source_system="jira",
            event_occurred_at=event.get("created") or event.get("updated"),
            event_created_at=event.get("created") or event.get("updated"),
            timestamp_quality=TimestampQuality.SOURCE_OCCURRED_AT,
            sensor_reliability=0.86,
            cross_source_agreement=0.76,
            telemetry_completeness=0.84,
            kernel_eligible=True,
            metadata={
                "raw_payload": event,
            },
        )

    def normalize_events(self, events: list[dict]) -> list[RawSecurityEvent]:
        return [self.normalize_event(event) for event in events]

    def _map_jira_event_type(self, event: dict) -> str:
        issue_type = event.get("issue_type", "").lower()
        status = event.get("status", "").lower()
        priority = event.get("priority", "").lower()
        blocked = bool(event.get("blocked", False))

        if blocked:
            return "honeyfile_interaction"

        if issue_type in {"bug", "incident"} and priority in {"high", "critical"}:
            return "failed_auth_burst"

        if status in {"blocked", "waiting", "awaiting approval", "in review"}:
            return "unauthorized_api_call"

        if status in {"done", "closed", "resolved"}:
            return "verification_passed"

        return "historically_valid_control"