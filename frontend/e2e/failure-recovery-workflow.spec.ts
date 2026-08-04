import {
  expect,
  test
} from "@playwright/test";

import {
  expectGovernanceHeaders
} from "./governance-api-harness";

import {
  RECOVERED_CHECKPOINT_ID,
  installGovernanceFailureHarness
} from "./governance-failure-api-harness";

test.describe(
  "Governance failure and recovery workflows",
  () => {
    test(
      "shows a safe failure when required audit data is unavailable",
      async ({ page }) => {
        await installGovernanceFailureHarness(
          page,
          "required-load"
        );

        await page.goto(
          "/audit-integrity"
        );

        await expect(
          page.getByText(
            /Backend returned 503 while loading required audit integrity data/
          )
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
      }
    );

    test(
      "keeps required audit data usable during optional-service degradation",
      async ({ page }) => {
        await installGovernanceFailureHarness(
          page,
          "optional-degradation"
        );

        await page.goto(
          "/audit-integrity"
        );

        await expect(
          page.getByRole(
            "heading",
            {
              name:
                "Audit Integrity",
              level: 1
            }
          )
        ).toBeVisible();

        await expect(
          page.getByText(
            "/api/e2e/failure-route-1"
          )
        ).toBeVisible();

        const warning =
          page.locator(
            ".optional-service-warning"
          );

        await expect(
          warning
        ).toBeVisible();

        await expect(
          warning
        ).toContainText(
          "signed checkpoint verification"
        );

        await expect(
          warning
        ).toContainText(
          "durable signing"
        );

        await expect(
          page.getByText(
            /Backend returned 503 while loading required audit integrity data/
          )
        ).toHaveCount(0);
      }
    );

    test(
      "rejects an unauthorized checkpoint and recovers on retry",
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
          harness.checkpoints
        ).toHaveLength(1);

        expect(
          harness.postAttempts()
        ).toBe(1);

        const firstPost =
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
          firstPost
        ).toBeDefined();

        await expectGovernanceHeaders(
          firstPost!
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
            "A new tenant audit checkpoint was created."
          )
        ).toBeVisible();

        await expect(
          dialog
        ).toBeHidden();

        await expect(
          page.getByText(
            RECOVERED_CHECKPOINT_ID
          )
        ).toBeVisible();

        expect(
          harness.postAttempts()
        ).toBe(2);

        expect(
          harness.checkpoints
        ).toHaveLength(2);

        expect(
          harness.checkpoints[0]
        ).toMatchObject({
          checkpoint_id:
            RECOVERED_CHECKPOINT_ID,
          valid: true
        });
      }
    );
  }
);
