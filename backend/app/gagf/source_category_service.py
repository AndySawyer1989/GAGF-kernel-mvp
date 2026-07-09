from backend.app.gagf.source_registry import SourceRegistry


class SourceCategoryService:
    def get_category_summary(self) -> dict:
        sources = SourceRegistry().list_sources()
        categories = {}

        for source in sources:
            category = source["category"]

            if category not in categories:
                categories[category] = {
                    "category": category,
                    "source_count": 0,
                    "sources": [],
                }

            categories[category]["source_count"] += 1
            categories[category]["sources"].append(source)

        category_list = sorted(
            categories.values(),
            key=lambda item: item["category"],
        )

        return {
            "status": "ok",
            "category_count": len(category_list),
            "categories": category_list,
        }

    def get_sources_for_category(self, category: str) -> list[dict]:
        sources = SourceRegistry().list_sources()

        return [
            source
            for source in sources
            if source["category"] == category
        ]

    def get_category_detail(self, category: str) -> dict:
        sources = self.get_sources_for_category(category)

        if not sources:
            return {
                "status": "failed",
                "error": "category_not_found",
                "category": category,
                "source_count": 0,
                "sources": [],
            }

        return {
            "status": "ok",
            "category": category,
            "source_count": len(sources),
            "sources": sources,
        }