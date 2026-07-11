class ProductSecurityPortfolioDashboardService:
    """Build dashboard-ready summaries for product security portfolios."""

    def build_summary(self, portfolio_result: dict) -> dict:
        result = portfolio_result or {}

        product_count = result.get("product_count", 0)
        tier_counts = result.get("tier_counts", {})
        zta_counts = result.get("zta_counts", {})
        products = result.get("products", [])

        return {
            "status": "ok",
            "summary_type": "product_security_portfolio_dashboard",
            "product_count": product_count,
            "portfolio_recommendation": result.get(
                "portfolio_recommendation",
                "add_product_profiles_to_classify_portfolio",
            ),
            "operator_message": self._operator_message(result),
            "recommended_action": self._recommended_action(result),
            "tier_distribution": self._tier_distribution(tier_counts),
            "zta_distribution": self._zta_distribution(zta_counts),
            "productization_tracks": self._productization_tracks(products),
            "risk_summary": self._risk_summary(result),
            "highest_risk_summary": self._highest_risk_summary(result),
            "dashboard_cards": self._dashboard_cards(
                product_count=product_count,
                tier_counts=tier_counts,
                zta_counts=zta_counts,
                result=result,
            ),
        }

    def _tier_distribution(self, tier_counts: dict) -> dict:
        return {
            "standard_commercial": tier_counts.get(
                "tier_1_standard_commercial",
                0,
            ),
            "enterprise_secure": tier_counts.get(
                "tier_2_enterprise_secure",
                0,
            ),
            "regulated_sensitive": tier_counts.get(
                "tier_3_regulated_sensitive",
                0,
            ),
            "federal_critical": tier_counts.get(
                "tier_4_federal_critical",
                0,
            ),
        }

    def _zta_distribution(self, zta_counts: dict) -> dict:
        return {
            "required": zta_counts.get("zta_required", 0),
            "recommended": zta_counts.get("zta_recommended", 0),
            "not_required": zta_counts.get("zta_not_required", 0),
        }

    def _productization_tracks(self, products: list[dict]) -> dict:
        tracks = {
            "fast_productization": [],
            "enterprise_ready": [],
            "regulated_boundary": [],
            "hardened_federal": [],
            "zta_planning": [],
        }

        for product in products:
            product_name = product.get("product_name", "unknown_product")
            priority = product.get("portfolio_priority", "unknown")

            if priority == "fast_productization_candidate":
                tracks["fast_productization"].append(product_name)
            elif priority == "enterprise_ready_productization_candidate":
                tracks["enterprise_ready"].append(product_name)
            elif priority == "define_compliance_boundary_before_productization":
                tracks["regulated_boundary"].append(product_name)
            elif priority == "harden_before_productization":
                tracks["hardened_federal"].append(product_name)
            elif priority == "complete_zta_plan_before_productization":
                tracks["zta_planning"].append(product_name)

        return tracks

    def _risk_summary(self, result: dict) -> dict:
        regulated_or_federal = result.get("regulated_or_federal_products", [])
        highest_risk = result.get("highest_risk_products", [])
        highest_tier = result.get("highest_security_tier", "none")

        return {
            "highest_security_tier": highest_tier,
            "highest_risk_product_count": len(highest_risk),
            "regulated_or_federal_product_count": len(regulated_or_federal),
            "requires_hardened_track": highest_tier
            == "tier_4_federal_critical",
            "requires_regulated_track": highest_tier
            in {
                "tier_3_regulated_sensitive",
                "tier_4_federal_critical",
            },
        }

    def _highest_risk_summary(self, result: dict) -> dict:
        return {
            "highest_security_tier": result.get(
                "highest_security_tier",
                "none",
            ),
            "highest_risk_products": result.get(
                "highest_risk_products",
                [],
            ),
            "regulated_or_federal_products": result.get(
                "regulated_or_federal_products",
                [],
            ),
            "fastest_productization_candidates": result.get(
                "fastest_productization_candidates",
                [],
            ),
        }

    def _dashboard_cards(
        self,
        product_count: int,
        tier_counts: dict,
        zta_counts: dict,
        result: dict,
    ) -> list[dict]:
        return [
            {
                "label": "Products Classified",
                "value": product_count,
                "status": "ok",
            },
            {
                "label": "Federal / Critical Products",
                "value": tier_counts.get("tier_4_federal_critical", 0),
                "status": self._card_status(
                    tier_counts.get("tier_4_federal_critical", 0)
                ),
            },
            {
                "label": "Regulated / Sensitive Products",
                "value": tier_counts.get("tier_3_regulated_sensitive", 0),
                "status": self._card_status(
                    tier_counts.get("tier_3_regulated_sensitive", 0)
                ),
            },
            {
                "label": "ZTA Required",
                "value": zta_counts.get("zta_required", 0),
                "status": self._card_status(
                    zta_counts.get("zta_required", 0)
                ),
            },
            {
                "label": "Fast Productization Candidates",
                "value": len(
                    result.get("fastest_productization_candidates", [])
                ),
                "status": "ok",
            },
        ]

    def _card_status(self, value: int) -> str:
        if value > 0:
            return "attention_required"
        return "ok"

    def _operator_message(self, result: dict) -> str:
        recommendation = result.get(
            "portfolio_recommendation",
            "add_product_profiles_to_classify_portfolio",
        )

        messages = {
            "add_product_profiles_to_classify_portfolio": (
                "Add product profiles to classify portfolio security posture."
            ),
            "prioritize_standard_commercial_productization": (
                "Portfolio is ready for standard commercial productization."
            ),
            "prioritize_enterprise_products_with_zta_readiness_review": (
                "Prioritize enterprise products while reviewing ZTA readiness."
            ),
            "separate_regulated_products_into_compliance_ready_track": (
                "Separate regulated products into a compliance-ready track."
            ),
            "separate_federal_critical_products_into_hardened_track": (
                "Separate federal or critical products into a hardened track."
            ),
        }

        return messages.get(
            recommendation,
            "Review portfolio security recommendation.",
        )

    def _recommended_action(self, result: dict) -> str:
        recommendation = result.get(
            "portfolio_recommendation",
            "add_product_profiles_to_classify_portfolio",
        )

        actions = {
            "add_product_profiles_to_classify_portfolio": (
                "add_product_profiles"
            ),
            "prioritize_standard_commercial_productization": (
                "package_standard_commercial_product"
            ),
            "prioritize_enterprise_products_with_zta_readiness_review": (
                "package_enterprise_product_with_zta_review"
            ),
            "separate_regulated_products_into_compliance_ready_track": (
                "define_regulated_compliance_boundary"
            ),
            "separate_federal_critical_products_into_hardened_track": (
                "define_federal_hardened_product_track"
            ),
        }

        return actions.get(
            recommendation,
            "review_product_security_portfolio",
        )