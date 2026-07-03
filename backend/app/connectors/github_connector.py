from backend.app.gagf.schemas import RawSecurityEvent, TimestampQuality


class GitHubConnector:
    """
    Converts GitHub-style evidence into GAGF RawSecurityEvent objects.

    This connector is intentionally small for US-010.
    Later, it can be expanded to support real GitHub webhooks or API pulls.
    """

    def normalize_event(self, event: dict) -> RawSecurityEvent:
        event_type = self._map_github_event_type(event)

        return RawSecurityEvent(
            event_id=event.get("id", "github-event-missing-id"),
            event_type=event_type,
            source_system="github",
            event_occurred_at=event.get("created_at"),
            event_created_at=event.get("created_at"),
            timestamp_quality=TimestampQuality.SOURCE_OCCURRED_AT,
            sensor_reliability=0.90,
            cross_source_agreement=0.80,
            telemetry_completeness=0.85,
            kernel_eligible=True,
            metadata={
    "raw_payload": event
},
        )

    def normalize_events(self, events: list[dict]) -> list[RawSecurityEvent]:
        return [self.normalize_event(event) for event in events]

    def _map_github_event_type(self, event: dict) -> str:
        action = event.get("action", "").lower()
        event_name = event.get("event_name", "").lower()

        if event_name == "pull_request" and action in {"opened", "reopened"}:
            return "unauthorized_api_call"

        if event_name == "pull_request" and action == "review_requested":
            return "honeyfile_interaction"

        if event_name == "pull_request" and action == "closed":
            return "verification_passed"

        if event_name == "push":
            return "historically_valid_control"

        return "failed_auth_burst"