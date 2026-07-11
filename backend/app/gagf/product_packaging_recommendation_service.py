class ProductPackagingRecommendationService:
    """Recommend product packaging tracks from portfolio dashboard output."""

    def recommend(self, portfolio_dashboard: dict) -> dict:
        dashboard = portfolio_dashboard or {}

        productization_tracks = dashboard.get("productization_tracks", {})
        risk_summary = dashboard.get("risk_summary", {})
        zta_distribution = dashboard.get("zta_distribution", {})

        first_candidate = self._first_packaging_candidate(
            productization_tracks
        )

        return {
            "status": "ok",
            "recommendation_type": "product_packaging_recommendation",
            "first_packaging_candidate": first_candidate,
            "primary_packaging_track": self._primary_packaging_track(
                first_candidate
            ),
            "demo_candidates": productization_tracks.get(
                "fast_productization",
                [],
            ),
            "enterprise_candidates": productization_tracks.get(
                "enterprise_ready",
                [],
            ),
            "regulated_candidates": productization_tracks.get(
                "regulated_boundary",
                [],
            ),
            "hardened_candidates": productization_tracks.get(
                "hardened_federal",
                [],
            ),
            "zta_planning_candidates": productization_tracks.get(
                "zta_planning",
                [],
            ),
            "security_blockers": self._security_blockers(
                risk_summary=risk_summary,
                zta_distribution=zta_distribution,
                productization_tracks=productization_tracks,
            ),
            "packaging_recommendation": self._packaging_recommendation(
                first_candidate
            ),
            "operator_message": self._operator_message(first_candidate),
            "next_action": self._next_action(first_candidate),
        }

    def _first_packaging_candidate(
        self,
        productization_tracks: dict,
    ) -> dict:
        fast_candidates = productization_tracks.get(
            "fast_productization",
            [],
        )
        enterprise_candidates = productization_tracks.get(
            "enterprise_ready",
            [],
        )
        regulated_candidates = productization_tracks.get(
            "regulated_boundary",
            [],
        )
        hardened_candidates = productization_tracks.get(
            "hardened_federal",
            [],
        )

        if fast_candidates:
            return {
                "product_name": fast_candidates[0],
                "track": "fast_productization",
                "reason": "lowest_security_burden",
            }

        if enterprise_candidates:
            return {
                "product_name": enterprise_candidates[0],
                "track": "enterprise_ready",
                "reason": "commercial_candidate_with_enterprise_controls",
            }

        if regulated_candidates:
            return {
                "product_name": regulated_candidates[0],
                "track": "regulated_boundary",
                "reason": "requires_compliance_boundary_before_packaging",
            }

        if hardened_candidates:
            return {
                "product_name": hardened_candidates[0],
                "track": "hardened_federal",
                "reason": "requires_hardened_security_track_before_packaging",
            }

        return {
            "product_name": "none",
            "track": "none",
            "reason": "no_packaging_candidate_available",
        }

    def _primary_packaging_track(self, first_candidate: dict) -> str:
        track = first_candidate.get("track", "none")

        track_map = {
            "fast_productization": "demo_or_early_revenue",
            "enterprise_ready": "enterprise_pilot",
            "regulated_boundary": "regulated_readiness_package",
            "hardened_federal": "federal_hardened_package",
            "none": "none",
        }

        return track_map.get(track, "review_required")

    def _security_blockers(
        self,
        risk_summary: dict,
        zta_distribution: dict,
        productization_tracks: dict,
    ) -> list[str]:
        blockers = []

        if risk_summary.get("requires_hardened_track") is True:
            blockers.append("federal_hardened_track_required")

        if risk_summary.get("requires_regulated_track") is True:
            blockers.append("regulated_compliance_boundary_required")

        if zta_distribution.get("required", 0) > 0:
            blockers.append("zta_required_for_some_products")

        if productization_tracks.get("hardened_federal", []):
            blockers.append("hardened_products_not_fast_packaging_candidates")

        if productization_tracks.get("regulated_boundary", []):
            blockers.append("regulated_products_need_boundary_definition")

        return blockers

    def _packaging_recommendation(self, first_candidate: dict) -> str:
        track = first_candidate.get("track", "none")

        recommendations = {
            "fast_productization": (
                "package_fast_demo_or_assessment_product_first"
            ),
            "enterprise_ready": (
                "package_enterprise_pilot_with_security_readiness"
            ),
            "regulated_boundary": (
                "define_regulated_boundary_before_product_packaging"
            ),
            "hardened_federal": (
                "define_hardened_federal_track_before_product_packaging"
            ),
            "none": "add_or_refine_product_candidates",
        }

        return recommendations.get(track, "review_packaging_path")

    def _operator_message(self, first_candidate: dict) -> str:
        product_name = first_candidate.get("product_name", "none")
        track = first_candidate.get("track", "none")

        if track == "fast_productization":
            return (
                f"Package {product_name} first as the fastest demo or "
                "early-revenue candidate."
            )

        if track == "enterprise_ready":
            return (
                f"Package {product_name} as an enterprise pilot with "
                "security readiness review."
            )

        if track == "regulated_boundary":
            return (
                f"Define the regulated compliance boundary for {product_name} "
                "before packaging."
            )

        if track == "hardened_federal":
            return (
                f"Define the hardened federal security track for "
                f"{product_name} before packaging."
            )

        return "No product packaging candidate is available yet."

    def _next_action(self, first_candidate: dict) -> str:
        track = first_candidate.get("track", "none")

        actions = {
            "fast_productization": "build_demo_package",
            "enterprise_ready": "build_enterprise_pilot_package",
            "regulated_boundary": "define_compliance_boundary",
            "hardened_federal": "define_hardened_security_boundary",
            "none": "add_product_candidates",
        }

        return actions.get(track, "review_product_packaging")