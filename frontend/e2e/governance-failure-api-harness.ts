import {
  type Page,
  type Request,
  type Route
} from "@playwright/test";

import {
  TEST_TENANT_ID,
  createActiveSigningKey,
  createAuditCheckpoint,
  createAuditEvent,
  createAuditIntegrity
} from "../test/governance-assessment-fixtures";

const API_ORIGIN =
  "http://127.0.0.1:8000";

const API_ROOT =
  "/api/v1/governance-assessments";

export const RECOVERED_CHECKPOINT_ID =
  "checkpoint-recovered-e2e-001";

type JsonRecord =
  Record<string, unknown>;

export type GovernanceFailureMode =
  | "required-load"
  | "optional-degradation"
  | "post-retry";

export type GovernanceFailureHarness = {
  requests: Request[];
  postAttempts: () => number;
  checkpoints: JsonRecord[];
};

async function fulfillJson(
  route: Route,
  body: unknown,
  status = 200
): Promise<void> {
  await route.fulfill({
    status,
    contentType: "application/json",
    body: JSON.stringify(body)
  });
}

function createEvent(
  index: number
): JsonRecord {
  return createAuditEvent({
    event_id:
      `audit-failure-e2e-${index}`,
    request_id:
      `request-failure-e2e-${index}`,
    route:
      `/api/e2e/failure-route-${index}`,
    method: "GET",
    status_code: 200,
    outcome: "allowed",
    event_hash:
      `failure-event-hash-${index}`,
    created_at:
      `2026-08-0${index}T08:00:00Z`
  });
}

function listPayload(
  items: JsonRecord[]
): JsonRecord {
  return {
    tenant_id: TEST_TENANT_ID,
    items,
    count: items.length,
    limit: 100
  };
}

export async function installGovernanceFailureHarness(
  page: Page,
  mode: GovernanceFailureMode
): Promise<GovernanceFailureHarness> {
  const requests: Request[] = [];

  const events = [
    createEvent(1),
    createEvent(2),
    createEvent(3)
  ];

  const checkpoints: JsonRecord[] = [
    createAuditCheckpoint({
      checkpoint_id:
        "checkpoint-existing-e2e-001",
      chain_head_hash:
        "existing-chain-head-e2e",
      checked_count: 3,
      created_at:
        "2026-08-01T08:00:00Z"
    })
  ];

  let postAttemptCount = 0;

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
          `${API_ROOT}/audit-events`
      ) {
        if (
          mode === "required-load"
        ) {
          await fulfillJson(
            route,
            {
              detail:
                "Required audit service unavailable"
            },
            503
          );

          return;
        }

        await fulfillJson(
          route,
          listPayload(events)
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
              events.length
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
          listPayload(
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
          listPayload([])
        );

        return;
      }

      if (
        request.method() === "GET"
        && path ===
          `${API_ROOT}`
          + "/audit-checkpoints/signed/verification"
      ) {
        if (
          mode ===
            "optional-degradation"
        ) {
          await fulfillJson(
            route,
            {
              detail:
                "Verification temporarily unavailable"
            },
            503
          );

          return;
        }

        await fulfillJson(
          route,
          {
            available: true,
            valid: true,
            checked_count: 0,
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
        if (
          mode ===
            "optional-degradation"
        ) {
          await fulfillJson(
            route,
            {
              detail:
                "Signing capability unavailable"
            },
            503
          );

          return;
        }

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
        postAttemptCount += 1;

        if (
          mode === "post-retry"
          && postAttemptCount === 1
        ) {
          await fulfillJson(
            route,
            {
              detail:
                "Checkpoint creation is forbidden"
            },
            403
          );

          return;
        }

        const checkpoint =
          createAuditCheckpoint({
            checkpoint_id:
              RECOVERED_CHECKPOINT_ID,
            chain_head_hash:
              "recovered-chain-head-e2e",
            checked_count:
              events.length,
            created_at:
              "2026-08-04T04:45:00Z"
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

      await fulfillJson(
        route,
        {
          detail:
            `Unhandled failure-harness endpoint: `
            + `${request.method()} ${path}`
        },
        501
      );
    }
  );

  return {
    requests,
    checkpoints,
    postAttempts:
      () => postAttemptCount
  };
}
