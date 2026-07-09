from backend.app.gagf.source_registry import SourceRegistry


class SourceKernelRoleService:
    def get_kernel_role_summary(self) -> dict:
        sources = SourceRegistry().list_sources()
        kernel_roles = {}

        for source in sources:
            kernel_role = source["kernel_role"]

            if kernel_role not in kernel_roles:
                kernel_roles[kernel_role] = {
                    "kernel_role": kernel_role,
                    "source_count": 0,
                    "sources": [],
                }

            kernel_roles[kernel_role]["source_count"] += 1
            kernel_roles[kernel_role]["sources"].append(source)

        kernel_role_list = sorted(
            kernel_roles.values(),
            key=lambda item: item["kernel_role"],
        )

        return {
            "status": "ok",
            "kernel_role_count": len(kernel_role_list),
            "kernel_roles": kernel_role_list,
        }

    def get_sources_for_kernel_role(self, kernel_role: str) -> list[dict]:
        sources = SourceRegistry().list_sources()

        return [
            source
            for source in sources
            if source["kernel_role"] == kernel_role
        ]

    def get_kernel_role_detail(self, kernel_role: str) -> dict:
        sources = self.get_sources_for_kernel_role(kernel_role)

        if not sources:
            return {
                "status": "failed",
                "error": "kernel_role_not_found",
                "kernel_role": kernel_role,
                "source_count": 0,
                "sources": [],
            }

        return {
            "status": "ok",
            "kernel_role": kernel_role,
            "source_count": len(sources),
            "sources": sources,
        }