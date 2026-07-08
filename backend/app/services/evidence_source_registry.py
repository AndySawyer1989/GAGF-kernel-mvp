class EvidenceSourceRegistry:
    """
    Central registry for mapping snapshot ID prefixes to evidence source labels.

    This keeps source detection consistent across dashboard summaries,
    recent activity, future reports, and future connector expansion.
    """

    SOURCE_PREFIXES = {
        "github-": "GitHub",
        "servicenow-": "ServiceNow",
        "jira-": "Jira",
        "okta-": "Okta",
        "entra-": "Entra ID",
        "csv-": "CSV",
        "api-": "API",
    }

    DEFAULT_SOURCE = "Local / Manual"
    EMPTY_SOURCE = "None"

    @classmethod
    def detect_from_snapshot(cls, snapshot):
        if snapshot is None:
            return cls.EMPTY_SOURCE

        snapshot_id = snapshot.get("snapshot_id", "")

        return cls.detect_from_snapshot_id(snapshot_id)

    @classmethod
    def detect_from_snapshot_id(cls, snapshot_id: str) -> str:
        for prefix, label in cls.SOURCE_PREFIXES.items():
            if snapshot_id.startswith(prefix):
                return label

        return cls.DEFAULT_SOURCE