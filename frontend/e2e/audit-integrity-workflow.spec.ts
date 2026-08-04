import {
  expect,
  test
} from "./browser-test";

import {
  CREATED_AUDIT_CHECKPOINT_ID,
  expectGovernanceHeaders,
  installAuditIntegrityApiHarness
} from "./governance-api-harness";

test.describe(
  "Audit Integrity real API workflow",
  () => {
    test(
      "filters and paginates audit events with navigable history",
      async ({ page }) => {
        await installAuditIntegrityApiHarness(
          page,
          {
            eventCount: 32,
            checkpointCount: 7
          }
        );

        await page.goto(
          "/audit-integrity"
        );

        const outcome =
          page.getByLabel(
            "Outcome"
          );

        await expect(
          outcome
        ).toHaveValue("ALL");

        await expect(
          page.getByLabel(
            "Audit events pagination"
          ).getByText(
            "Page 1 of 3"
          )
        ).toBeVisible();

        await expect(
          page.getByText(
            "/api/e2e/audit-route-001"
          )
        ).toBeVisible();

        await outcome.selectOption(
          "DENIED"
        );

        await expect(page).toHaveURL(
          /[?&]outcome=DENIED(?:&|$)/
        );

        await expect(
          outcome
        ).toHaveValue("DENIED");

        await expect(
          page.getByLabel(
            "Audit events pagination"
          ).getByText(
            "Page 1 of 2"
          )
        ).toBeVisible();

        await expect(
          page.getByText(
            "/api/e2e/audit-route-002"
          )
        ).toBeVisible();

        await expect(
          page.getByText(
            "/api/e2e/audit-route-001"
          )
        ).toHaveCount(0);

        await page.getByRole(
          "button",
          {
            name:
              "Next Audit events page"
          }
        ).click();

        await expect(page).toHaveURL(
          /[?&]auditPage=2(?:&|$)/
        );

        await expect(
          page.getByLabel(
            "Audit events pagination"
          ).getByText(
            "Page 2 of 2"
          )
        ).toBeVisible();

        await expect(
          page.getByText(
            "/api/e2e/audit-route-032"
          )
        ).toBeVisible();

        await page.goBack();

        await expect(page).not.toHaveURL(
          /[?&]auditPage=2(?:&|$)/
        );

        await expect(
          outcome
        ).toHaveValue("DENIED");

        await expect(
          page.getByLabel(
            "Audit events pagination"
          ).getByText(
            "Page 1 of 2"
          )
        ).toBeVisible();

        await page.goBack();

        await expect(
          outcome
        ).toHaveValue("ALL");

        await expect(page).not.toHaveURL(
          /[?&]outcome=DENIED(?:&|$)/
        );

        await expect(
          page.getByLabel(
            "Audit events pagination"
          ).getByText(
            "Page 1 of 3"
          )
        ).toBeVisible();
      }
    );

    test(
      "paginates checkpoint inventory through the rendered control",
      async ({ page }) => {
        await installAuditIntegrityApiHarness(
          page,
          {
            eventCount: 8,
            checkpointCount: 7
          }
        );

        await page.goto(
          "/audit-integrity"
        );

        await expect(
          page.getByText(
            "checkpoint-audit-e2e-001"
          )
        ).toBeVisible();

        await page.getByRole(
          "button",
          {
            name:
              /Next .*checkpoint.* page/i
          }
        ).click();

        await expect(page).toHaveURL(
          /[?&]checkpointPage=2(?:&|$)/
        );

        await expect(
          page.getByText(
            "checkpoint-audit-e2e-006"
          )
        ).toBeVisible();

        await expect(
          page.getByText(
            "checkpoint-audit-e2e-001"
          )
        ).toHaveCount(0);

        await page.goBack();

        await expect(page).not.toHaveURL(
          /[?&]checkpointPage=2(?:&|$)/
        );

        await expect(
          page.getByText(
            "checkpoint-audit-e2e-001"
          )
        ).toBeVisible();
      }
    );

    test(
      "creates a checkpoint and reloads the inventory",
      async ({ page }) => {
        const harness =
          await installAuditIntegrityApiHarness(
            page,
            {
              eventCount: 12,
              checkpointCount: 4
            }
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

        await expect(
          dialog
        ).toBeVisible();

        await dialog.getByRole(
          "button",
          {
            name:
              "Create checkpoint"
          }
        ).click();

        await expect(
          page.getByText(
            "A new tenant audit checkpoint was created."
          )
        ).toBeVisible();

        await expect(
          dialog
        ).toBeHidden();

        await expect(
          page.getByText(
            CREATED_AUDIT_CHECKPOINT_ID
          )
        ).toBeVisible();

        const createRequest =
          harness.requests.find(
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
                  "/api/v1/"
                  + "governance-assessments/"
                  + "audit-checkpoints"
              );
            }
          );

        expect(
          createRequest
        ).toBeDefined();

        await expectGovernanceHeaders(
          createRequest!
        );

        expect(
          harness.checkpoints[0]
        ).toMatchObject({
          checkpoint_id:
            CREATED_AUDIT_CHECKPOINT_ID,
          valid: true
        });

        const checkpointGets =
          harness.requests.filter(
            (request) => {
              const url =
                new URL(
                  request.url()
                );

              return (
                request.method()
                  === "GET"
                && url.pathname
                  ===
                  "/api/v1/"
                  + "governance-assessments/"
                  + "audit-checkpoints"
              );
            }
          );

        expect(
          checkpointGets.length
        ).toBeGreaterThanOrEqual(2);
      }
    );
  }
);
