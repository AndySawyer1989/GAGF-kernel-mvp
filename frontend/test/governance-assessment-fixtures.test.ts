import {
  describe,
  expect,
  it
} from "vitest";

import {
  TEST_SIGNING_KEY_ID,
  TEST_TENANT_ID,
  createActiveSigningKey,
  createAuditCheckpoint,
  createAuditCheckpointList,
  createAuditEvent,
  createAuditIntegrity,
  createAvailableSigningCapability,
  createSignedCheckpointRecord,
  createSignedVerificationList,
  createUnauthorizedSigningCapability,
  createUnconfiguredSigningCapability,
  createUnreachableSigningCapability,
  createTestApiConfig
} from "./governance-assessment-fixtures";

describe(
  "governance assessment test factories",
  () => {
    it(
      "creates a deterministic tenant API configuration",
      () => {
        expect(
          createTestApiConfig()
        ).toEqual({
          baseUrl:
            "http://127.0.0.1:8000",
          tenantId: TEST_TENANT_ID,
          actorId: "console-admin",
          actorRoles:
            "assessment:admin"
        });
      }
    );

    it(
      "allows factory properties to be overridden",
      () => {
        const checkpoint =
          createAuditCheckpoint({
            checkpoint_id:
              "checkpoint-override",
            checked_count: 900
          });

        expect(
          checkpoint.checkpoint_id
        ).toBe(
          "checkpoint-override"
        );

        expect(
          checkpoint.checked_count
        ).toBe(900);

        expect(
          checkpoint.tenant_id
        ).toBe(TEST_TENANT_ID);
      }
    );

    it(
      "creates internally consistent signed evidence",
      () => {
        const key =
          createActiveSigningKey();

        const record =
          createSignedCheckpointRecord();

        const verification =
          createSignedVerificationList();

        expect(key.key_id).toBe(
          TEST_SIGNING_KEY_ID
        );

        expect(record.key_id).toBe(
          TEST_SIGNING_KEY_ID
        );

        expect(
          verification.items[0].key_id
        ).toBe(
          TEST_SIGNING_KEY_ID
        );

        expect(
          verification.items[0]
            .checkpoint_id
        ).toBe(
          record.checkpoint
            .checkpoint_id
        );
      }
    );

    it(
      "creates consistent core audit evidence",
      () => {
        const event =
          createAuditEvent();

        const integrity =
          createAuditIntegrity();

        const checkpoints =
          createAuditCheckpointList();

        expect(event.tenant_id).toBe(
          TEST_TENANT_ID
        );

        expect(
          integrity.tenant_id
        ).toBe(TEST_TENANT_ID);

        expect(
          checkpoints.tenant_id
        ).toBe(TEST_TENANT_ID);

        expect(integrity.valid).toBe(
          true
        );

        expect(
          checkpoints.items[0].valid
        ).toBe(true);
      }
    );

    it(
      "creates every supported signing capability state",
      () => {
        expect(
          createAvailableSigningCapability()
            .status
        ).toBe("available");

        expect(
          createUnconfiguredSigningCapability()
            .status
        ).toBe("unconfigured");

        expect(
          createUnauthorizedSigningCapability()
            .status
        ).toBe("unauthorized");

        expect(
          createUnreachableSigningCapability()
            .status
        ).toBe("unreachable");
      }
    );

    it(
      "marks only the healthy capability as available",
      () => {
        expect(
          createAvailableSigningCapability()
            .available
        ).toBe(true);

        expect(
          createUnconfiguredSigningCapability()
            .available
        ).toBe(false);

        expect(
          createUnauthorizedSigningCapability()
            .available
        ).toBe(false);

        expect(
          createUnreachableSigningCapability()
            .available
        ).toBe(false);
      }
    );
  }
);
