import {
  expect,
  test,
  type Request
} from "@playwright/test";

import {
  TEST_ACTOR_ID,
  TEST_ACTOR_ROLES,
  TEST_TENANT_ID
} from "../test/governance-assessment-fixtures";

import {
  expectGovernanceHeaders,
  installAuditIntegrityApiHarness
} from "./governance-api-harness";

import {
  RECOVERED_CHECKPOINT_ID,
  installGovernanceFailureHarness
} from "./governance-failure-api-harness";

const GOVERNANCE_PATH =
  "/api/v1/governance-assessments";

function governanceRequests(
  requests: Request[]
): Request[] {
  return requests.filter(
    (request) => {
      const url =
        new URL(request.url());

      return url.pathname.startsWith(
        GOVERNANCE_PATH
      );
    }
  );
}

test.describe(
  "Governance Console tenant boundary",
  () => {
    test(
      "binds every governance request to one tenant and identity",
      async ({ page }) => {
        const harness =
          await installAuditIntegrityApiHarness(
            page,
            {
              eventCount: 32,
              checkpointCount: 6
            }
          );

        await page.goto(
          "/audit-integrity"
        );

        await expect(
          page.getByRole(
            "heading",
            {
              name: "Audit Integrity",
              level: 1
            }
          )
        ).toBeVisible();

        await page.getByLabel(
          "Outcome"
        ).selectOption(
          "DENIED"
        );

        await page.getByRole(
          "button",
          {
            name:
              "Next Audit events page"
          }
        ).click();

        const requests =
          governanceRequests(
            harness.requests
          );

        expect(
          requests.length
        ).toBeGreaterThan(0);

        for (
          const request
          of requests
        ) {
          await expectGovernanceHeaders(
            request
          );

          const url =
            new URL(
              request.url()
            );

          expect(
            url.searchParams.get(
              "tenant_id"
            )
          ).toBe(TEST_TENANT_ID);

          expect(
            url.searchParams.getAll(
              "tenant_id"
            )
          ).toEqual([
            TEST_TENANT_ID
          ]);
        }

        const distinctTenantHeaders =
          new Set(
            requests.map(
              (request) =>
                request.headers()[
                  "x-tenant-id"
                ]
            )
          );

        expect(
          [
            ...distinctTenantHeaders
          ]
        ).toEqual([
          TEST_TENANT_ID
        ]);

        const distinctActors =
          new Set(
            requests.map(
              (request) =>
                request.headers()[
                  "x-actor-id"
                ]
            )
          );

        expect(
          [
            ...distinctActors
          ]
        ).toEqual([
          TEST_ACTOR_ID
        ]);

        const distinctRoles =
          new Set(
            requests.map(
              (request) =>
                request.headers()[
                  "x-actor-roles"
                ]
            )
          );

        expect(
          [
            ...distinctRoles
          ]
        ).toEqual([
          TEST_ACTOR_ROLES
        ]);
      }
    );

    test(
      "does not allow URL state to override the configured tenant",
      async ({ page }) => {
        const harness =
          await installAuditIntegrityApiHarness(
            page,
            {
              eventCount: 8,
              checkpointCount: 3
            }
          );

        await page.goto(
          "/audit-integrity"
          + "?tenant_id=tenant-hostile"
          + "&outcome=DENIED"
        );

        await expect(
          page.getByLabel(
            "Outcome"
          )
        ).toHaveValue(
          "DENIED"
        );

        const browserUrl =
          new URL(
            page.url()
          );

        expect(
          browserUrl.searchParams.get(
            "tenant_id"
          )
        ).toBe(
          "tenant-hostile"
        );

        const requests =
          governanceRequests(
            harness.requests
          );

        expect(
          requests.length
        ).toBeGreaterThan(0);

        for (
          const request
          of requests
        ) {
          const requestUrl =
            new URL(
              request.url()
            );

          expect(
            requestUrl.searchParams.get(
              "tenant_id"
            )
          ).toBe(
            TEST_TENANT_ID
          );

          expect(
            request.headers()[
              "x-tenant-id"
            ]
          ).toBe(
            TEST_TENANT_ID
          );

          expect(
            request.url()
          ).not.toContain(
            "tenant-hostile"
          );
        }

        await page.reload();

        await expect(
          page.getByRole(
            "heading",
            {
              name: "Audit Integrity",
              level: 1
            }
          )
        ).toBeVisible();

        const postReloadRequests =
          governanceRequests(
            harness.requests
          );

        for (
          const request
          of postReloadRequests
        ) {
          expect(
            request.headers()[
              "x-tenant-id"
            ]
          ).toBe(
            TEST_TENANT_ID
          );
        }

        const browserStorage =
          await page.evaluate(
            () => {
              const localValues =
                Object.keys(
                  window.localStorage
                ).map(
                  (key) =>
                    window.localStorage
                      .getItem(key)
                );

              const sessionValues =
                Object.keys(
                  window.sessionStorage
                ).map(
                  (key) =>
                    window.sessionStorage
                      .getItem(key)
                );

              return [
                ...localValues,
                ...sessionValues
              ]
                .filter(
                  (
                    value
                  ): value is string =>
                    typeof value
                      === "string"
                )
                .join("\n");
            }
          );

        expect(
          browserStorage
        ).not.toContain(
          "tenant-hostile"
        );
      }
    );

    test(
      "does not expose protected checkpoint data after authorization failure",
      async ({ page }) => {
        const harness =
          await installGovernanceFailureHarness(
            page,
            "post-retry"
          );

        await page.goto(
          "/audit-integrity"
        );

        await page.getByRole(
          "button",
          {
            name:
              "Create checkpoint"
          }
        ).first().click();

        const dialog =
          page.getByRole(
            "dialog",
            {
              name:
                "Create an audit checkpoint?"
            }
          );

        await dialog.getByRole(
          "button",
          {
            name:
              "Create checkpoint"
          }
        ).click();

        await expect(
          page.getByText(
            "Checkpoint creation failed with status 403."
          )
        ).toBeVisible();

        await expect(
          dialog
        ).toBeVisible();

        await expect(
          page.getByText(
            "A new tenant audit checkpoint was created."
          )
        ).toHaveCount(0);

        await expect(
          page.getByText(
            RECOVERED_CHECKPOINT_ID
          )
        ).toHaveCount(0);

        expect(
          harness.postAttempts()
        ).toBe(1);

        expect(
          harness.checkpoints
        ).toHaveLength(1);

        const posts =
          harness.requests.filter(
            (request) => {
              const url =
                new URL(
                  request.url()
                );

              return (
                request.method()
                  === "POST"
                && url.pathname
                  ===
                  `${GOVERNANCE_PATH}`
                  + "/audit-checkpoints"
              );
            }
          );

        expect(
          posts
        ).toHaveLength(1);

        await expectGovernanceHeaders(
          posts[0]
        );

        expect(
          posts[0].headers()[
            "x-tenant-id"
          ]
        ).toBe(
          TEST_TENANT_ID
        );

        const pageContent =
          await page.locator(
            "body"
          ).innerText();

        expect(
          pageContent
        ).not.toContain(
          "recovered-chain-head-e2e"
        );

        expect(
          pageContent
        ).not.toContain(
          RECOVERED_CHECKPOINT_ID
        );
      }
    );
  }
);
