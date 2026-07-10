from backend.app.gagf.snapshot_diagnostics_ledger import SnapshotDiagnosticsLedger


class SnapshotDiagnosticsSummaryService:
    def __init__(self, ledger: SnapshotDiagnosticsLedger | None = None):
        self.ledger = ledger or SnapshotDiagnosticsLedger()

    def get_summary(self) -> dict:
        records = self.ledger.list_diagnostics()

        confidence_scores = self.get_confidence_scores(records)
        confidence_band_counts = self.get_confidence_band_counts(records)
        diagnostic_band_counts = self.get_diagnostic_band_counts(records)
        conflict_summary = self.get_conflict_summary(records)
        source_summary = self.get_source_summary(records)

        return {
            "status": "ok",
            "record_count": len(records),
            "average_confidence_score": self.average(confidence_scores),
            "confidence_band_counts": confidence_band_counts,
            "diagnostic_band_counts": diagnostic_band_counts,
            "conflict_summary": conflict_summary,
            "source_summary": source_summary,
        }

    def get_confidence_scores(self, records: list[dict]) -> list[float]:
        scores = []

        for record in records:
            confidence_score = (
                record.get("diagnostics", {})
                .get("confidence_score")
            )

            if isinstance(confidence_score, int | float):
                scores.append(float(confidence_score))

        return scores

    def get_confidence_band_counts(self, records: list[dict]) -> dict:
        counts = {
            "high": 0,
            "medium": 0,
            "low": 0,
            "invalid": 0,
            "unknown": 0,
        }

        for record in records:
            confidence_band = (
                record.get("diagnostics", {})
                .get("confidence_band")
            )

            if confidence_band in counts:
                counts[confidence_band] += 1
            else:
                counts["unknown"] += 1

        return counts

    def get_diagnostic_band_counts(self, records: list[dict]) -> dict:
        counts = {
            "healthy": 0,
            "watch": 0,
            "degraded": 0,
            "invalid": 0,
            "unknown": 0,
        }

        for record in records:
            diagnostic_band = (
                record.get("diagnostics", {})
                .get("diagnostics", {})
                .get("diagnostic_band")
            )

            if diagnostic_band in counts:
                counts[diagnostic_band] += 1
            else:
                counts["unknown"] += 1

        return counts

    def get_conflict_summary(self, records: list[dict]) -> dict:
        total_conflicts = 0
        severity_counts = {
            "critical": 0,
            "warning": 0,
            "info": 0,
        }

        for record in records:
            conflicts = (
                record.get("diagnostics", {})
                .get("diagnostics", {})
                .get("conflicts", {})
            )

            total_conflicts += conflicts.get("conflict_count", 0)

            for severity, count in conflicts.get("severity_counts", {}).items():
                if severity not in severity_counts:
                    severity_counts[severity] = 0

                severity_counts[severity] += count

        return {
            "total_conflicts": total_conflicts,
            "severity_counts": severity_counts,
        }

    def get_source_summary(self, records: list[dict]) -> dict:
        source_counts = []
        supporting_sources = set()
        missing_kernel_roles = set()

        for record in records:
            agreement = (
                record.get("diagnostics", {})
                .get("diagnostics", {})
                .get("agreement", {})
            )

            source_count = agreement.get("source_count")

            if isinstance(source_count, int):
                source_counts.append(source_count)

            for source in agreement.get("supporting_sources", []):
                supporting_sources.add(source)

            for role in agreement.get("missing_roles", []):
                missing_kernel_roles.add(role)

        return {
            "average_source_count": self.average(source_counts),
            "supporting_sources": sorted(supporting_sources),
            "missing_kernel_roles": sorted(missing_kernel_roles),
        }

    def average(self, values: list[int | float]) -> float:
        if not values:
            return 0.0

        return round(sum(values) / len(values), 4)