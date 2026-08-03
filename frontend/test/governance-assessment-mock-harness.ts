import {
  vi
} from "vitest";

import {
  createAuditCheckpoint,
  createSignedAuditCheckpoint,
  fetchAuditCheckpoints,
  fetchAuditEvents,
  fetchAuditIntegrity,
  fetchSignedAuditCheckpointRecords,
  fetchSignedAuditCheckpointVerificationRecords,
  fetchSignedAuditCheckpoints,
  verifySignedAuditCheckpoints
} from "@/lib/governance-assessment-api";

import {
  detectSigningCapability
} from "@/lib/signing-capability";

export function createGovernanceAssessmentMockHarness() {
  return {
    createAuditCheckpoint:
      vi.mocked(createAuditCheckpoint),

    createSignedAuditCheckpoint:
      vi.mocked(
        createSignedAuditCheckpoint
      ),

    fetchAuditCheckpoints:
      vi.mocked(fetchAuditCheckpoints),

    fetchAuditEvents:
      vi.mocked(fetchAuditEvents),

    fetchAuditIntegrity:
      vi.mocked(fetchAuditIntegrity),

    fetchSignedAuditCheckpointRecords:
      vi.mocked(
        fetchSignedAuditCheckpointRecords
      ),

    fetchSignedAuditCheckpointVerificationRecords:
      vi.mocked(
        fetchSignedAuditCheckpointVerificationRecords
      ),

    fetchSignedAuditCheckpoints:
      vi.mocked(
        fetchSignedAuditCheckpoints
      ),

    verifySignedAuditCheckpoints:
      vi.mocked(
        verifySignedAuditCheckpoints
      ),

    detectSigningCapability:
      vi.mocked(
        detectSigningCapability
      ),

    clear() {
      vi.clearAllMocks();
    }
  };
}

export type GovernanceAssessmentMockHarness =
  ReturnType<
    typeof createGovernanceAssessmentMockHarness
  >;
