from backend.app.gagf.product_security_tier_service import (
    ProductSecurityTierService,
)
from backend.app.gagf.zta_control_mapping_service import (
    ZTAControlMappingService,
)


class ProductSecurityPortfolioService:
    def __init__(
        self,
        tier_service: ProductSecurityTierService | None = None,
        zta_service: ZTAControlMappingService | None = None,
    ):
        self.tier_service = tier_service or ProductSecurityTierService()
        self.zta_service = zta_service or ZTAControlMappingService()

    def classify_portfolio(self, product_profiles: list[dict]) -> dict:
        product_results = [
            self.classify_product(product_profile)
            for product_profile in product_profiles
        ]

        tier_counts = self.count_by_tier(product_results)
        zta_counts = self.count_zta_requirements(product_results)

        return {
            "status": "ok",
            "classification_type": "product_security_portfolio",
            "product_count": len(product_results),
            "tier_counts": tier_counts,
            "zta_counts": zta_counts,
            "highest_security_tier": self.get_highest_security_tier(
                product_results
            ),
            "highest_risk_products": self.get_highest_risk_products(
                product_results
            ),
            "regulated_or_federal_products": (
                self.get_regulated_or_federal_products(product_results)
            ),
            "fastest_productization_candidates": (
                self.get_fastest_productization_candidates(product_results)
            ),
            "portfolio_recommendation": self.get_portfolio_recommendation(
                product_results=product_results,
                tier_counts=tier_counts,
                zta_counts=zta_counts,
            ),
            "products": product_results,
        }

    def classify_product(self, product_profile: dict) -> dict:
        security_result = self.tier_service.classify_product(product_profile)
        zta_result = self.zta_service.map_product_tier(security_result)

        return {
            "product_name": security_result["product_name"],
            "product_category": security_result["product_category"],
            "security_tier": security_result["security_tier"],
            "security_tier_label": security_result["security_tier_label"],
            "compliance_alignment": security_result[
                "compliance_alignment"
            ],
            "required_controls": security_result["required_controls"],
            "deployment_models": security_result["deployment_models"],
            "evidence_requirements": security_result[
                "evidence_requirements"
            ],
            "tier_recommended_next_action": security_result[
                "recommended_next_action"
            ],
            "zta_required": zta_result["zta_required"],
            "zta_requirement_level": zta_result[
                "zta_requirement_level"
            ],
            "zta_recommended_next_action": zta_result[
                "recommended_next_action"
            ],
            "zta_controls": {
                "identity_controls": zta_result["identity_controls"],
                "access_enforcement_controls": zta_result[
                    "access_enforcement_controls"
                ],
                "session_and_device_controls": zta_result[
                    "session_and_device_controls"
                ],
                "segmentation_controls": zta_result[
                    "segmentation_controls"
                ],
                "telemetry_and_evidence_requirements": zta_result[
                    "telemetry_and_evidence_requirements"
                ],
                "deployment_implications": zta_result[
                    "deployment_implications"
                ],
            },
            "portfolio_priority": self.get_product_priority(
                security_result["security_tier"],
                zta_result["zta_required"],
            ),
            "classification_reason": security_result[
                "classification_reason"
            ],
        }

    def count_by_tier(self, product_results: list[dict]) -> dict:
        counts = {
            "tier_1_standard_commercial": 0,
            "tier_2_enterprise_secure": 0,
            "tier_3_regulated_sensitive": 0,
            "tier_4_federal_critical": 0,
        }

        for product in product_results:
            tier = product["security_tier"]
            counts[tier] = counts.get(tier, 0) + 1

        return counts

    def count_zta_requirements(self, product_results: list[dict]) -> dict:
        required = sum(
            1 for product in product_results if product["zta_required"]
        )
        recommended = sum(
            1
            for product in product_results
            if product["zta_requirement_level"] == "recommended"
        )
        not_required = sum(
            1
            for product in product_results
            if product["zta_requirement_level"] == "not_required"
        )

        return {
            "zta_required": required,
            "zta_recommended": recommended,
            "zta_not_required": not_required,
        }

    def get_highest_security_tier(
        self,
        product_results: list[dict],
    ) -> str:
        if not product_results:
            return "none"

        return max(
            (
                product["security_tier"]
                for product in product_results
            ),
            key=self.tier_rank,
        )

    def get_highest_risk_products(
        self,
        product_results: list[dict],
    ) -> list[str]:
        highest_tier = self.get_highest_security_tier(product_results)

        if highest_tier == "none":
            return []

        return [
            product["product_name"]
            for product in product_results
            if product["security_tier"] == highest_tier
        ]

    def get_regulated_or_federal_products(
        self,
        product_results: list[dict],
    ) -> list[str]:
        return [
            product["product_name"]
            for product in product_results
            if product["security_tier"]
            in {
                "tier_3_regulated_sensitive",
                "tier_4_federal_critical",
            }
        ]

    def get_fastest_productization_candidates(
        self,
        product_results: list[dict],
    ) -> list[str]:
        return [
            product["product_name"]
            for product in product_results
            if product["security_tier"]
            in {
                "tier_1_standard_commercial",
                "tier_2_enterprise_secure",
            }
        ]

    def get_portfolio_recommendation(
        self,
        product_results: list[dict],
        tier_counts: dict,
        zta_counts: dict,
    ) -> str:
        if not product_results:
            return "add_product_profiles_to_classify_portfolio"

        if tier_counts.get("tier_4_federal_critical", 0) > 0:
            return (
                "separate_federal_critical_products_into_hardened_track"
            )

        if tier_counts.get("tier_3_regulated_sensitive", 0) > 0:
            return (
                "separate_regulated_products_into_compliance_ready_track"
            )

        if zta_counts.get("zta_recommended", 0) > 0:
            return (
                "prioritize_enterprise_products_with_zta_readiness_review"
            )

        return "prioritize_standard_commercial_productization"

    def get_product_priority(
        self,
        security_tier: str,
        zta_required: bool,
    ) -> str:
        if security_tier == "tier_4_federal_critical":
            return "harden_before_productization"

        if security_tier == "tier_3_regulated_sensitive":
            return "define_compliance_boundary_before_productization"

        if zta_required:
            return "complete_zta_plan_before_productization"

        if security_tier == "tier_2_enterprise_secure":
            return "enterprise_ready_productization_candidate"

        return "fast_productization_candidate"

    def tier_rank(self, tier: str) -> int:
        ranks = {
            "tier_1_standard_commercial": 1,
            "tier_2_enterprise_secure": 2,
            "tier_3_regulated_sensitive": 3,
            "tier_4_federal_critical": 4,
        }

        return ranks.get(tier, 0)