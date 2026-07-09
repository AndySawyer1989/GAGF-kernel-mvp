class EvidenceConflictService:
    def detect_conflicts(self, events: list) -> dict:
        conflicts = []

        conflicts.extend(self.detect_security_resolution_conflicts(events))
        conflicts.extend(self.detect_workflow_state_conflicts(events))
        conflicts.extend(self.detect_identity_outcome_conflicts(events))

        return {
            "status": "ok",
            "event_count": len(events),
            "conflict_count": len(conflicts),
            "severity_counts": self.build_severity_counts(conflicts),
            "conflicts": conflicts,
        }

    def detect_security_resolution_conflicts(self, events: list) -> list[dict]:
        unresolved_sources = set()
        resolved_sources = set()

        for event in events:
            source_system = self.get_source_system(event)
            event_type = self.get_event_type(event)
            metadata = self.get_metadata(event)

            if not source_system:
                continue

            if self.is_security_unresolved(event_type, metadata):
                unresolved_sources.add(source_system)

            if self.is_security_resolved(event_type, metadata):
                resolved_sources.add(source_system)

        if unresolved_sources and resolved_sources:
            return [
                {
                    "conflict_type": "security_resolution_mismatch",
                    "severity": "warning",
                    "sources": sorted(unresolved_sources | resolved_sources),
                    "message": (
                        "One or more security sources report unresolved risk while "
                        "another source reports mitigation or resolution."
                    ),
                }
            ]

        return []

    def detect_workflow_state_conflicts(self, events: list) -> list[dict]:
        blocked_sources = set()
        completed_sources = set()

        for event in events:
            source_system = self.get_source_system(event)
            event_type = self.get_event_type(event)
            metadata = self.get_metadata(event)

            if not source_system:
                continue

            if self.is_workflow_blocked(event_type, metadata):
                blocked_sources.add(source_system)

            if self.is_workflow_completed(event_type, metadata):
                completed_sources.add(source_system)

        if blocked_sources and completed_sources:
            return [
                {
                    "conflict_type": "workflow_state_mismatch",
                    "severity": "warning",
                    "sources": sorted(blocked_sources | completed_sources),
                    "message": (
                        "One or more workflow sources report blocked work while "
                        "another source reports completion or merge."
                    ),
                }
            ]

        return []

    def detect_identity_outcome_conflicts(self, events: list) -> list[dict]:
        failed_sources = set()
        successful_sources = set()

        for event in events:
            source_system = self.get_source_system(event)
            event_type = self.get_event_type(event)
            metadata = self.get_metadata(event)

            if not source_system:
                continue

            if self.is_identity_failed(event_type, metadata):
                failed_sources.add(source_system)

            if self.is_identity_successful(event_type, metadata):
                successful_sources.add(source_system)

        if failed_sources and successful_sources:
            return [
                {
                    "conflict_type": "identity_outcome_mismatch",
                    "severity": "warning",
                    "sources": sorted(failed_sources | successful_sources),
                    "message": (
                        "One or more identity sources report failed access while "
                        "another source reports successful access."
                    ),
                }
            ]

        return []

    def build_severity_counts(self, conflicts: list[dict]) -> dict:
        counts = {
            "critical": 0,
            "warning": 0,
            "info": 0,
        }

        for conflict in conflicts:
            severity = conflict.get("severity", "info")

            if severity not in counts:
                counts[severity] = 0

            counts[severity] += 1

        return counts

    def is_security_unresolved(self, event_type: str, metadata: dict) -> bool:
        text = self.combined_text(event_type, metadata)

        unresolved_terms = {
            "unauthorized_api_call",
            "threat_detected",
            "malware",
            "ransomware",
            "critical",
            "high",
            "unresolved",
            "active",
            "open",
            "true_positive",
            "malicious",
        }

        return any(term in text for term in unresolved_terms)

    def is_security_resolved(self, event_type: str, metadata: dict) -> bool:
        text = self.combined_text(event_type, metadata)

        resolved_terms = {
            "verification_passed",
            "mitigated",
            "remediated",
            "resolved",
            "closed",
            "benign",
            "clean",
        }

        return any(term in text for term in resolved_terms)

    def is_workflow_blocked(self, event_type: str, metadata: dict) -> bool:
        text = self.combined_text(event_type, metadata)

        blocked_terms = {
            "work_blocked",
            "blocked",
            "approval_delayed",
            "dependency_wait",
            "stalled",
            "waiting",
        }

        return any(term in text for term in blocked_terms)

    def is_workflow_completed(self, event_type: str, metadata: dict) -> bool:
        text = self.combined_text(event_type, metadata)

        completed_terms = {
            "merged",
            "closed",
            "done",
            "completed",
            "resolved",
            "deployed",
            "verification_passed",
        }

        return any(term in text for term in completed_terms)

    def is_identity_failed(self, event_type: str, metadata: dict) -> bool:
        text = self.combined_text(event_type, metadata)

        failed_terms = {
            "login_failed",
            "sign_in_failed",
            "authentication_failed",
            "mfa_denied",
            "access_denied",
            "failure",
            "failed",
        }

        return any(term in text for term in failed_terms)

    def is_identity_successful(self, event_type: str, metadata: dict) -> bool:
        text = self.combined_text(event_type, metadata)

        success_terms = {
            "login_success",
            "sign_in_success",
            "authentication_success",
            "mfa_success",
            "access_granted",
            "success",
            "successful",
            "verification_passed",
        }

        return any(term in text for term in success_terms)

    def combined_text(self, event_type: str, metadata: dict) -> str:
        metadata_values = []

        if isinstance(metadata, dict):
            metadata_values = [
                str(value)
                for value in metadata.values()
                if value is not None
            ]

        return " ".join([str(event_type), *metadata_values]).lower()

    def get_source_system(self, event) -> str:
        return str(getattr(event, "source_system", "") or "")

    def get_event_type(self, event) -> str:
        return str(getattr(event, "event_type", "") or "")

    def get_metadata(self, event) -> dict:
        metadata = getattr(event, "metadata", {}) or {}

        if isinstance(metadata, dict):
            return metadata

        return {}