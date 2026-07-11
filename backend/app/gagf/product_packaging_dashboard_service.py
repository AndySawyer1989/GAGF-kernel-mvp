class ProductPackagingDashboardService:
    """Build dashboard-ready summaries for product packaging recommendations."""

    def build_summary(self, recommendation: dict) -> dict:
        result = recommendation or {}

        first_candidate = result.get(
            "first_packaging_candidate",
            {
                "product_name": "none",
                "track": "none",
                "reason": "no_packaging_candidate_available",
            },
        )

        security_blockers = result.get("security_blockers", [])

        return {
            "status": "ok",
            "summary_type": "product_packaging_dashboard",
            "first_candidate_card": self._first_candidate_card(
                first_candidate
            ),
            "packaging_track_summary": self._packaging_track_summary(result),
            "candidate_summary": self._candidate_summary(result),
            "blocker_summary": self._blocker_summary(security_blockers),
            "operator_message": result.get(
                "operator_message",
                "No product packaging candidate is available yet.",
            ),
            "recommended_action": result.get(
                "next_action",
                "add_product_candidates",
            ),
            "packaging_recommendation": result.get(
                "packaging_recommendation",
                "add_or_refine_product_candidates",
            ),
            "dashboard_cards": self._dashboard_cards(
                result=result,
                first_candidate=first_candidate,
                security_blockers=security_blockers,
            ),
        }

    def _first_candidate_card(self, first_candidate: dict) -> dict:
        product_name = first_candidate.get("product_name", "none")
        track = first_candidate.get("track", "none")
        reason = first_candidate.get(
            "reason",
            "no_packaging_candidate_available",
        )

        return {
            "product_name": product_name,
            "track": track,
            "reason": reason,
            "is_available": product_name != "none",
            "display_label": self._display_label(product_name, track),
        }

    def _display_label(self, product_name: str, track: str) -> str:
        if product_name == "none":
            return "No packaging candidate"

        track_labels = {
            "fast_productization": "Fast Productization",
            "enterprise_ready": "Enterprise Pilot",
            "regulated_boundary": "Regulated Boundary",
            "hardened_federal": "Hardened Federal",
            "none": "None",
        }

        return f"{product_name} — {track_labels.get(track, 'Review')}"

    def _packaging_track_summary(self, result: dict) -> dict:
        return {
            "primary_packaging_track": result.get(
                "primary_packaging_track",
                "none",
            ),
            "recommendation_type": result.get(
                "recommendation_type",
                "product_packaging_recommendation",
            ),
            "is_demo_or_revenue_candidate": result.get(
                "primary_packaging_track"
            )
            == "demo_or_early_revenue",
            "requires_enterprise_review": result.get(
                "primary_packaging_track"
            )
            == "enterprise_pilot",
            "requires_regulated_boundary": result.get(
                "primary_packaging_track"
            )
            == "regulated_readiness_package",
            "requires_hardened_boundary": result.get(
                "primary_packaging_track"
            )
            == "federal_hardened_package",
        }

    def _candidate_summary(self, result: dict) -> dict:
        demo_candidates = result.get("demo_candidates", [])
        enterprise_candidates = result.get("enterprise_candidates", [])
        regulated_candidates = result.get("regulated_candidates", [])
        hardened_candidates = result.get("hardened_candidates", [])
        zta_planning_candidates = result.get("zta_planning_candidates", [])

        return {
            "demo_candidate_count": len(demo_candidates),
            "enterprise_candidate_count": len(enterprise_candidates),
            "regulated_candidate_count": len(regulated_candidates),
            "hardened_candidate_count": len(hardened_candidates),
            "zta_planning_candidate_count": len(zta_planning_candidates),
            "demo_candidates": demo_candidates,
            "enterprise_candidates": enterprise_candidates,
            "regulated_candidates": regulated_candidates,
            "hardened_candidates": hardened_candidates,
            "zta_planning_candidates": zta_planning_candidates,
        }

    def _blocker_summary(self, security_blockers: list[str]) -> dict:
        return {
            "blocker_count": len(security_blockers),
            "security_blockers": security_blockers,
            "has_federal_blocker": (
                "federal_hardened_track_required" in security_blockers
            ),
            "has_regulated_blocker": (
                "regulated_compliance_boundary_required"
                in security_blockers
            ),
            "has_zta_blocker": (
                "zta_required_for_some_products" in security_blockers
            ),
            "has_packaging_blocker": len(security_blockers) > 0,
        }

    def _dashboard_cards(
        self,
        result: dict,
        first_candidate: dict,
        security_blockers: list[str],
    ) -> list[dict]:
        return [
            {
                "label": "First Packaging Candidate",
                "value": first_candidate.get("product_name", "none"),
                "status": self._candidate_status(first_candidate),
            },
            {
                "label": "Primary Packaging Track",
                "value": result.get("primary_packaging_track", "none"),
                "status": self._track_status(
                    result.get("primary_packaging_track", "none")
                ),
            },
            {
                "label": "Demo Candidates",
                "value": len(result.get("demo_candidates", [])),
                "status": "ok",
            },
            {
                "label": "Security Blockers",
                "value": len(security_blockers),
                "status": self._blocker_status(security_blockers),
            },
            {
                "label": "Next Action",
                "value": result.get("next_action", "add_product_candidates"),
                "status": "ok",
            },
        ]

    def _candidate_status(self, first_candidate: dict) -> str:
        if first_candidate.get("product_name", "none") == "none":
            return "attention_required"
        return "ok"

    def _track_status(self, track: str) -> str:
        if track in {
            "regulated_readiness_package",
            "federal_hardened_package",
        }:
            return "attention_required"

        if track == "none":
            return "attention_required"

        return "ok"

    def _blocker_status(self, security_blockers: list[str]) -> str:
        if security_blockers:
            return "attention_required"
        return "ok"