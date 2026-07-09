from backend.app.gagf.source_registry import SourceRegistry


class SourceTrustTierService:
    def get_trust_tier_summary(self) -> dict:
        sources = SourceRegistry().list_sources()
        trust_tiers = {}

        for source in sources:
            trust_tier = source["trust_tier"]

            if trust_tier not in trust_tiers:
                trust_tiers[trust_tier] = {
                    "trust_tier": trust_tier,
                    "source_count": 0,
                    "sources": [],
                }

            trust_tiers[trust_tier]["source_count"] += 1
            trust_tiers[trust_tier]["sources"].append(source)

        trust_tier_list = sorted(
            trust_tiers.values(),
            key=lambda item: item["trust_tier"],
        )

        return {
            "status": "ok",
            "trust_tier_count": len(trust_tier_list),
            "trust_tiers": trust_tier_list,
        }

    def get_sources_for_trust_tier(self, trust_tier: str) -> list[dict]:
        sources = SourceRegistry().list_sources()

        return [
            source
            for source in sources
            if source["trust_tier"] == trust_tier
        ]

    def get_trust_tier_detail(self, trust_tier: str) -> dict:
        sources = self.get_sources_for_trust_tier(trust_tier)

        if not sources:
            return {
                "status": "failed",
                "error": "trust_tier_not_found",
                "trust_tier": trust_tier,
                "source_count": 0,
                "sources": [],
            }

        return {
            "status": "ok",
            "trust_tier": trust_tier,
            "source_count": len(sources),
            "sources": sources,
        }