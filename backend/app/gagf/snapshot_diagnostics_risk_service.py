from backend.app.gagf.snapshot_diagnostics_ledger import SnapshotDiagnosticsLedger


class SnapshotDiagnosticsRiskService:
    def __init__(self, ledger: SnapshotDiagnosticsLedger | None = None):
        self.ledger = ledger or SnapshotDiagnosticsLedger()

    def get_risk_summary(self) -> dict:
        records = self.ledger.list_diagnostics()
        risk_records = [self.score_record(record) for record in records]

        risk_records = sorted(
            risk_records,
            key=lambda record: record["risk_score"],
            reverse=True,
        )

        return {
            "status": "ok",
            "record_count": len(records),
            "risk_record_count": len(
                [
                    record
                    for record in risk_records
                    if record["risk_score"] > 0.0
                ]
            ),
            "risk_band_counts": self.get_risk_band_counts(risk_records),
            "top_risks": risk_records,
        }

    def score_record(self, record: dict) -> dict:
        diagnostics_wrapper = record.get("diagnostics", {})
        diagnostics = diagnostics_wrapper.get("diagnostics", {})
        conflicts = diagnostics.get("conflicts", {})
        agreement = diagnostics.get("agreement", {})

        confidence_score = diagnostics_wrapper.get("confidence_score", 0.0)
        confidence_band = diagnostics_wrapper.get("confidence_band", "unknown")
        diagnostic_band = diagnostics.get("diagnostic_band", "unknown")
        conflict_count = conflicts.get("conflict_count", 0)
        severity_counts = conflicts.get("severity_counts", {})
        missing_roles = agreement.get("missing_roles", [])
        source_count = agreement.get("source_count", 0)

        factors = {
            "low_confidence": self.score_low_confidence(confidence_score),
            "diagnostic_degradation": self.score_diagnostic_degradation(
                diagnostic_band
            ),
            "conflict_pressure": self.score_conflict_pressure(
                conflict_count,
                severity_counts,
            ),
            "missing_kernel_roles": self.score_missing_kernel_roles(
                missing_roles
            ),
            "low_source_support": self.score_low_source_support(source_count),
        }

        risk_score = self.calculate_risk_score(factors)

        return {
            "snapshot_id": record.get("snapshot_id"),
            "saved_at": record.get("saved_at"),
            "risk_score": risk_score,
            "risk_band": self.get_risk_band(risk_score),
            "confidence_score": confidence_score,
            "confidence_band": confidence_band,
            "diagnostic_band": diagnostic_band,
            "conflict_count": conflict_count,
            "missing_roles": missing_roles,
            "source_count": source_count,
            "factors": factors,
        }

    def score_low_confidence(self, confidence_score) -> float:
        if not isinstance(confidence_score, (int, float)):
            return 0.5

        if confidence_score >= 0.85:
            return 0.0

        if confidence_score >= 0.65:
            return 0.35

        if confidence_score > 0.0:
            return 0.75

        return 1.0

    def score_diagnostic_degradation(self, diagnostic_band: str) -> float:
        if diagnostic_band == "healthy":
            return 0.0

        if diagnostic_band == "watch":
            return 0.35

        if diagnostic_band == "degraded":
            return 0.75

        if diagnostic_band == "invalid":
            return 1.0

        return 0.5

    def score_conflict_pressure(
        self,
        conflict_count: int,
        severity_counts: dict,
    ) -> float:
        if severity_counts.get("critical", 0) > 0:
            return 1.0

        if conflict_count >= 2:
            return 0.75

        if conflict_count == 1:
            return 0.5

        return 0.0

    def score_missing_kernel_roles(self, missing_roles: list) -> float:
        missing_count = len(missing_roles)

        if missing_count == 0:
            return 0.0

        if missing_count <= 2:
            return 0.35

        if missing_count <= 4:
            return 0.65

        return 1.0

    def score_low_source_support(self, source_count) -> float:
        if not isinstance(source_count, int):
            return 0.5

        if source_count >= 3:
            return 0.0

        if source_count == 2:
            return 0.35

        if source_count == 1:
            return 0.75

        return 1.0

    def calculate_risk_score(self, factors: dict) -> float:
        score = (
            factors["low_confidence"] * 0.30
            + factors["diagnostic_degradation"] * 0.25
            + factors["conflict_pressure"] * 0.20
            + factors["missing_kernel_roles"] * 0.15
            + factors["low_source_support"] * 0.10
        )

        return round(score, 4)

    def get_risk_band(self, risk_score: float) -> str:
        if risk_score >= 0.75:
            return "critical"

        if risk_score >= 0.50:
            return "high"

        if risk_score > 0.0:
            return "watch"

        return "none"

    def get_risk_band_counts(self, risk_records: list[dict]) -> dict:
        counts = {
            "critical": 0,
            "high": 0,
            "watch": 0,
            "none": 0,
        }

        for record in risk_records:
            risk_band = record.get("risk_band", "none")

            if risk_band not in counts:
                counts[risk_band] = 0

            counts[risk_band] += 1

        return counts