from backend.app.gagf.schemas import RawSecurityEvent


class EventNormalizer:
    def normalize_rows(self, rows):
        events = []

        for row in rows:
            events.append(
                RawSecurityEvent(
                    event_id=row.get("event_id"),
                    event_type=row.get("event_type"),
                    timestamp_quality=row.get("timestamp_quality"),
                    source_system=row.get("source_system") or "CSV",
                    event_occurred_at=row.get("event_occurred_at") or None,
                    event_created_at=row.get("event_created_at") or None,
                )
            )

        return events