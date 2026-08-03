import {
  beforeEach,
  describe,
  expect,
  it,
  vi
} from "vitest";

import {
  fetchAuditEvents
} from "@/lib/governance-assessment-api";

import {
  detectSigningCapability
} from "@/lib/signing-capability";

import {
  createAuditEventList,
  createAvailableSigningCapability
} from "./governance-assessment-fixtures";

import {
  createGovernanceAssessmentMockHarness
} from "./governance-assessment-mock-harness";

vi.mock(
  "@/lib/governance-assessment-api",
  async (importOriginal) => {
    const actual =
      await importOriginal<
        typeof import(
          "@/lib/governance-assessment-api"
        )
      >();

    return {
      ...actual,
      fetchAuditEvents: vi.fn(),
      fetchAuditIntegrity: vi.fn(),
      fetchAuditCheckpoints: vi.fn(),
      fetchSignedAuditCheckpoints:
        vi.fn(),
      verifySignedAuditCheckpoints:
        vi.fn(),
      fetchSignedAuditCheckpointRecords:
        vi.fn(),
      fetchSignedAuditCheckpointVerificationRecords:
        vi.fn(),
      createAuditCheckpoint: vi.fn(),
      createSignedAuditCheckpoint:
        vi.fn()
    };
  }
);

vi.mock(
  "@/lib/signing-capability",
  async (importOriginal) => {
    const actual =
      await importOriginal<
        typeof import(
          "@/lib/signing-capability"
        )
      >();

    return {
      ...actual,
      detectSigningCapability:
        vi.fn()
    };
  }
);

describe(
  "governance assessment mock harness",
  () => {
    const harness =
      createGovernanceAssessmentMockHarness();

    beforeEach(() => {
      harness.clear();
    });

    it(
      "exposes typed governance API mocks",
      async () => {
        harness.fetchAuditEvents
          .mockResolvedValue(
            createAuditEventList()
          );

        const result =
          await fetchAuditEvents({
            baseUrl:
              "http://127.0.0.1:8000",
            tenantId: "tenant-alpha",
            actorId: "console-admin",
            actorRoles:
              "assessment:admin"
          });

        expect(result.count).toBe(1);

        expect(
          harness.fetchAuditEvents
        ).toHaveBeenCalledTimes(1);
      }
    );

    it(
      "exposes the signing capability mock",
      async () => {
        harness.detectSigningCapability
          .mockResolvedValue(
            createAvailableSigningCapability()
          );

        const result =
          await detectSigningCapability({
            baseUrl:
              "http://127.0.0.1:8000",
            tenantId: "tenant-alpha",
            actorId: "console-admin",
            actorRoles:
              "assessment:admin"
          });

        expect(result.available).toBe(
          true
        );

        expect(
          harness.detectSigningCapability
        ).toHaveBeenCalledTimes(1);
      }
    );

    it(
      "clears all recorded mock calls",
      () => {
        harness.fetchAuditEvents({
          baseUrl:
            "http://127.0.0.1:8000",
          tenantId: "tenant-alpha",
          actorId: "console-admin",
          actorRoles:
            "assessment:admin"
        });

        expect(
          harness.fetchAuditEvents
        ).toHaveBeenCalledTimes(1);

        harness.clear();

        expect(
          harness.fetchAuditEvents
        ).not.toHaveBeenCalled();
      }
    );
  }
);
