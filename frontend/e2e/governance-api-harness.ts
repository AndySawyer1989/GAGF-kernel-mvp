import {
  expect,
  type Page,
  type Request
} from "@playwright/test";

import {
  TEST_ACTOR_ID,
  TEST_ACTOR_ROLES,
  TEST_SIGNING_KEY_ID,
  TEST_TENANT_ID,
  createActiveSigningKey,
  createAuditCheckpoint,
  createAuditEvent,
  createAuditIntegrity,
  createSignedCheckpointRecord,
  createSignedVerificationItem
} from "../test/governance-assessment-fixtures";

const API_ORIGIN =
  "http://127.0.0.1:8000";

const API_ROOT =
  "/api/v1/governance-assessments";

export const CREATED_CHECKPOINT_ID =
  "checkpoint-e2e-created-001";

type JsonRecord =
  Record<string, unknown>;

export type GovernanceApiHarness = {
  requests: Request[];
  signedRecords: JsonRecord[];
  verificationItems: JsonRecord[];
};

function createCheckpointAt(
  index: number
): JsonRecord {
  const checkpointId =
    `checkpoint-e2e-${String(index).padStart(
      3,
      "0"
    )}`;

  return createAuditCheckpoint({
    checkpoint_id: checkpointId,
    chain_head_hash:
      `chain-head-e2e-${index}`,
    checked_count:
      500 + index,
    created_at:
      `2026-08-${String(
        Math.min(index, 28)
      ).padStart(2, "0")}T12:00:00Z`
  });
}

function createSignedRecordAt(
  index: number
): JsonRecord {
  const checkpoint =
    createCheckpointAt(index);

  return createSignedCheckpointRecord({
    checkpoint,
    signature:
      `signature-e2e-${index}`
  });
}

function createVerificationAt(
  index: number
): JsonRecord {
  return createSignedVerificationItem({
    checkpoint_id:
      `checkpoint-e2e-${String(index).padStart(
        3,
        "0"
      )}`
  });
}

function signedList(
  items: JsonRecord[]
): JsonRecord {
  return {
    tenant_id: TEST_TENANT_ID,
    items,
    count: items.length,
    limit: 100
  };
}

function verificationList(
  items: JsonRecord[]
): JsonRecord {
  const validCount =
    items.filter(
      (item) => item.valid === true
    ).length;

  return {
    tenant_id: TEST_TENANT_ID,
    items,
    count: items.length,
    valid_count: validCount,
    invalid_count:
      items.length - validCount,
    limit: 100
  };
}

async function fulfillJson(
  route: Parameters<
    Parameters<Page["route"]>[1]
  >[0],
  body: unknown,
  status = 200
): Promise<void> {
  await route.fulfill({
    status,
    contentType: "application/json",
    body: JSON.stringify(body)
  });
}

export async function installGovernanceApiHarness(
  page: Page,
  recordCount = 12,
  fallbackUnhandled = false
): Promise<GovernanceApiHarness> {
  const requests: Request[] = [];

  const signedRecords =
    Array.from(
      {
        length: recordCount
      },
      (_, index) =>
        createSignedRecordAt(
          index + 1
        )
    );

  const verificationItems =
    Array.from(
      {
        length: recordCount
      },
      (_, index) =>
        createVerificationAt(
          index + 1
        )
    );

  await page.route(
    `${API_ORIGIN}/**`,
    async (route) => {
      const request =
        route.request();

      requests.push(request);

      const url =
        new URL(request.url());

      const path =
        url.pathname;

      if (
        request.method() === "GET"
        && path ===
          `${API_ROOT}`
          + "/checkpoint-signing-keys/active"
      ) {
        await fulfillJson(
          route,
          createActiveSigningKey()
        );

        return;
      }

      if (
        request.method() === "GET"
        && path ===
          `${API_ROOT}`
          + "/audit-checkpoints/signed"
      ) {
        await fulfillJson(
          route,
          signedList(
            signedRecords
          )
        );

        return;
      }

      if (
        request.method() === "GET"
        && path ===
          `${API_ROOT}`
          + "/audit-checkpoints/signed/verification"
      ) {
        await fulfillJson(
          route,
          verificationList(
            verificationItems
          )
        );

        return;
      }

      if (
        request.method() === "POST"
        && path ===
          `${API_ROOT}`
          + "/audit-checkpoints"
      ) {
        const checkpoint =
          createAuditCheckpoint({
            checkpoint_id:
              CREATED_CHECKPOINT_ID,
            chain_head_hash:
              "chain-head-e2e-created",
            checked_count: 777,
            created_at:
              "2026-08-03T20:00:00Z"
          });

        const signedRecord =
          createSignedCheckpointRecord({
            checkpoint,
            signature:
              "signature-e2e-created"
          });

        const verification =
          createSignedVerificationItem({
            checkpoint_id:
              CREATED_CHECKPOINT_ID
          });

        signedRecords.unshift(
          signedRecord
        );

        verificationItems.unshift(
          verification
        );

        await fulfillJson(
          route,
          {
            checkpoint,
            signed: true,
            key_id:
              TEST_SIGNING_KEY_ID,
            signature:
              "signature-e2e-created",
            signature_algorithm:
              "hmac-sha256",
            signature_version:
              "1.0.0"
          },
          201
        );

        return;
      }

      if (fallbackUnhandled) {
        await route.fallback();
        return;
      }

      await fulfillJson(
        route,
        {
          detail:
            `Unhandled E2E endpoint: `
            + `${request.method()} ${path}`
        },
        501
      );
    }
  );

  return {
    requests,
    signedRecords,
    verificationItems
  };
}

export async function expectGovernanceHeaders(
  request: Request
): Promise<void> {
  const headers =
    request.headers();

  expect(
    headers["x-tenant-id"]
  ).toBe(TEST_TENANT_ID);

  expect(
    headers["x-actor-id"]
  ).toBe(TEST_ACTOR_ID);

  expect(
    headers["x-actor-roles"]
  ).toBe(TEST_ACTOR_ROLES);
}

export const CREATED_AUDIT_CHECKPOINT_ID =
  "checkpoint-audit-e2e-created-001";

export type AuditIntegrityApiHarness = {
  requests: Request[];
  auditEvents: JsonRecord[];
  checkpoints: JsonRecord[];
  signedCheckpoints: JsonRecord[];
};

function createAuditEventAt(
  index: number
): JsonRecord {
  const denied =
    index % 2 === 0;

  return createAuditEvent({
    event_id:
      `audit-event-e2e-${String(index).padStart(
        3,
        "0"
      )}`,
    request_id:
      `audit-request-e2e-${String(index).padStart(
        3,
        "0"
      )}`,
    route:
      `/api/e2e/audit-route-${String(
        index
      ).padStart(3, "0")}`,
    method: denied
      ? "POST"
      : "GET",
    status_code: denied
      ? 403
      : 200,
    outcome: denied
      ? "denied"
      : "allowed",
    event_hash:
      `audit-event-hash-e2e-${index}`,
    created_at:
      `2026-08-${String(
        ((index - 1) % 28) + 1
      ).padStart(2, "0")}T10:00:00Z`
  });
}

function createAuditCheckpointAt(
  index: number
): JsonRecord {
  return createAuditCheckpoint({
    checkpoint_id:
      `checkpoint-audit-e2e-${String(
        index
      ).padStart(3, "0")}`,
    chain_head_hash:
      `audit-chain-head-e2e-${index}`,
    checked_count:
      600 + index,
    created_at:
      `2026-07-${String(
        ((index - 1) % 28) + 1
      ).padStart(2, "0")}T09:00:00Z`
  });
}

function auditEventList(
  items: JsonRecord[]
): JsonRecord {
  return {
    tenant_id: TEST_TENANT_ID,
    items,
    count: items.length,
    limit: 100
  };
}

function auditCheckpointList(
  items: JsonRecord[]
): JsonRecord {
  return {
    tenant_id: TEST_TENANT_ID,
    items,
    count: items.length,
    limit: 100
  };
}

export async function installAuditIntegrityApiHarness(
  page: Page,
  options: {
    eventCount?: number;
    checkpointCount?: number;
    fallbackUnhandled?: boolean;
  } = {}
): Promise<AuditIntegrityApiHarness> {
  const eventCount =
    options.eventCount ?? 32;

  const checkpointCount =
    options.checkpointCount ?? 7;

  const requests: Request[] = [];

  const auditEvents =
    Array.from(
      {
        length: eventCount
      },
      (_, index) =>
        createAuditEventAt(
          index + 1
        )
    );

  const checkpoints =
    Array.from(
      {
        length: checkpointCount
      },
      (_, index) =>
        createAuditCheckpointAt(
          index + 1
        )
    );

  const signedCheckpoints =
    checkpoints.slice(
      0,
      Math.min(
        checkpoints.length,
        3
      )
    );

  await page.route(
    `${API_ORIGIN}/**`,
    async (route) => {
      const request =
        route.request();

      requests.push(request);

      const url =
        new URL(
          request.url()
        );

      const path =
        url.pathname;

      if (
        request.method() === "GET"
        && path ===
          `${API_ROOT}/audit-events`
      ) {
        await fulfillJson(
          route,
          auditEventList(
            auditEvents
          )
        );

        return;
      }

      if (
        request.method() === "GET"
        && path ===
          `${API_ROOT}/audit-integrity`
      ) {
        await fulfillJson(
          route,
          createAuditIntegrity({
            checked_count:
              auditEvents.length
          })
        );

        return;
      }

      if (
        request.method() === "GET"
        && path ===
          `${API_ROOT}/audit-checkpoints`
      ) {
        await fulfillJson(
          route,
          auditCheckpointList(
            checkpoints
          )
        );

        return;
      }

      if (
        request.method() === "GET"
        && path ===
          `${API_ROOT}`
          + "/audit-checkpoints/signed"
      ) {
        await fulfillJson(
          route,
          auditCheckpointList(
            signedCheckpoints
          )
        );

        return;
      }

      if (
        request.method() === "GET"
        && path ===
          `${API_ROOT}`
          + "/audit-checkpoints/signed/verification"
      ) {
        await fulfillJson(
          route,
          {
            available: true,
            valid: true,
            checked_count:
              signedCheckpoints.length,
            invalid_count: 0,
            failures: []
          }
        );

        return;
      }

      if (
        request.method() === "GET"
        && path ===
          `${API_ROOT}`
          + "/checkpoint-signing-keys/active"
      ) {
        await fulfillJson(
          route,
          createActiveSigningKey()
        );

        return;
      }

      if (
        request.method() === "POST"
        && path ===
          `${API_ROOT}/audit-checkpoints`
      ) {
        const checkpoint =
          createAuditCheckpoint({
            checkpoint_id:
              CREATED_AUDIT_CHECKPOINT_ID,
            chain_head_hash:
              "audit-chain-head-e2e-created",
            checked_count:
              auditEvents.length,
            created_at:
              "2026-08-03T20:30:00Z"
          });

        checkpoints.unshift(
          checkpoint
        );

        await fulfillJson(
          route,
          checkpoint,
          201
        );

        return;
      }

      if (options.fallbackUnhandled === true) {
        await route.fallback();
        return;
      }

      await fulfillJson(
        route,
        {
          detail:
            `Unhandled Audit Integrity E2E endpoint: `
            + `${request.method()} ${path}`
        },
        501
      );
    }
  );

  return {
    requests,
    auditEvents,
    checkpoints,
    signedCheckpoints
  };
}

